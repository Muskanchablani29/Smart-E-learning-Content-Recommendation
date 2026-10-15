from datetime import datetime
from django.db.models import Avg, Count, Max, Q
from django.utils import timezone
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    LearningMaterial,
    QuizAttempt,
    QuizQuestion,
    QuizResponse,
    Recommendation,
    Subject,
    Topic,
    TopicProgress,
    User,
)
from .permissions import (
    IsAdminUserRole,
    IsInstructor,
    IsInstructorOrReadOnly,
    IsStudent,
)
from .recommendation_engine import generate_recommendations_for_student
from .serializers import (
    LearningMaterialSerializer,
    QuizAttemptSerializer,
    QuizQuestionAdminSerializer,
    QuizQuestionStudentSerializer,
    QuizSubmissionSerializer,
    RecommendationSerializer,
    SubjectSerializer,
    TopicProgressSerializer,
    TopicSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)


class RegisterView(generics.CreateAPIView):
    """Register a new student, instructor, or admin and return JWT tokens."""
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens immediately
        refresh = RefreshToken.for_user(user)
        user_data = UserSerializer(user).data

        return Response(
            {
                "user": user_data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                "message": "Registration successful.",
            },
            status=status.HTTP_201_CREATED,
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Retrieve or update profile of authenticated user."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class SubjectViewSet(viewsets.ModelViewSet):
    """List and manage subjects."""
    serializer_class = SubjectSerializer
    permission_classes = [IsInstructorOrReadOnly]

    def get_queryset(self):
        queryset = Subject.objects.all()
        # Non-staff only see active subjects
        if not (self.request.user.is_staff or self.request.user.role in [User.Role.INSTRUCTOR, User.Role.ADMIN]):
            queryset = queryset.filter(is_active=True)
        return queryset.order_by("name")


class TopicViewSet(viewsets.ModelViewSet):
    """List and manage topics."""
    serializer_class = TopicSerializer
    permission_classes = [IsInstructorOrReadOnly]

    def get_queryset(self):
        queryset = Topic.objects.all()
        subject_id = self.request.query_params.get("subject")
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        if not (self.request.user.is_staff or self.request.user.role in [User.Role.INSTRUCTOR, User.Role.ADMIN]):
            queryset = queryset.filter(is_active=True)
        return queryset.order_by("subject__name", "order", "name")


class LearningMaterialViewSet(viewsets.ModelViewSet):
    """List and manage learning materials."""
    serializer_class = LearningMaterialSerializer
    permission_classes = [IsInstructorOrReadOnly]

    def get_queryset(self):
        queryset = LearningMaterial.objects.all()
        topic_id = self.request.query_params.get("topic")
        material_type = self.request.query_params.get("type")
        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)
        if material_type:
            queryset = queryset.filter(material_type=material_type)
        if not (self.request.user.is_staff or self.request.user.role in [User.Role.INSTRUCTOR, User.Role.ADMIN]):
            queryset = queryset.filter(is_published=True)
        return queryset.order_by("topic__order", "title")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class TopicProgressViewSet(viewsets.ModelViewSet):
    """View and update student topic progress."""
    serializer_class = TopicProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in [User.Role.INSTRUCTOR, User.Role.ADMIN] or user.is_staff:
            return TopicProgress.objects.all().order_by("-updated_at")
        return TopicProgress.objects.filter(student=user).order_by("-updated_at")

    @action(detail=False, methods=["post"])
    def mark(self, request):
        """Update or toggle topic progress (status and percent)."""
        user = request.user
        if user.role != User.Role.STUDENT:
            return Response(
                {"detail": "Only students can mark topic progress."},
                status=status.HTTP_403_FORBIDDEN,
            )

        topic_id = request.data.get("topic_id")
        target_status = request.data.get("status", TopicProgress.Status.IN_PROGRESS)
        percent = request.data.get("percent_complete", 50.0)

        if not topic_id:
            return Response({"detail": "topic_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            topic = Topic.objects.get(id=topic_id, is_active=True)
        except Topic.DoesNotExist:
            return Response({"detail": "Topic not found."}, status=status.HTTP_404_NOT_FOUND)

        progress, created = TopicProgress.objects.get_or_create(
            student=user,
            topic=topic,
            defaults={
                "status": target_status,
                "percent_complete": percent,
                "started_at": timezone.now(),
            },
        )

        if not created:
            progress.status = target_status
            progress.percent_complete = percent
            if target_status == TopicProgress.Status.COMPLETED and not progress.completed_at:
                progress.completed_at = timezone.now()
                progress.percent_complete = 100.0
            elif target_status == TopicProgress.Status.IN_PROGRESS and not progress.started_at:
                progress.started_at = timezone.now()
            progress.save()

        # Re-evaluate recommendations
        generate_recommendations_for_student(user)

        return Response(TopicProgressSerializer(progress).data, status=status.HTTP_200_OK)


class QuizQuestionManageViewSet(viewsets.ModelViewSet):
    """Manage quiz questions (for instructors and admins)."""
    serializer_class = QuizQuestionAdminSerializer
    permission_classes = [IsInstructor]

    def get_queryset(self):
        queryset = QuizQuestion.objects.all()
        topic_id = self.request.query_params.get("topic")
        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)
        return queryset.order_by("topic__name", "id")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class QuizAPIView(APIView):
    """Fetch questions for a topic quiz, submit attempts, and view history."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, topic_id=None):
        """Fetch active questions for a topic (answers omitted for students)."""
        if not topic_id:
            return Response({"detail": "topic_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        difficulty = request.query_params.get("difficulty")
        questions = QuizQuestion.objects.filter(topic_id=topic_id, is_active=True)
        if difficulty:
            questions = questions.filter(difficulty=difficulty)

        serializer = QuizQuestionStudentSerializer(questions, many=True)
        return Response({
            "topic_id": topic_id,
            "total_questions": questions.count(),
            "questions": serializer.data,
        })

    def post(self, request):
        """Submit quiz answers, compute score, update progress, and generate recommendations."""
        user = request.user
        if user.role != User.Role.STUDENT:
            return Response({"detail": "Only students can submit quiz attempts."}, status=status.HTTP_403_FORBIDDEN)

        serializer = QuizSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        topic_id = serializer.validated_data["topic_id"]
        difficulty = serializer.validated_data.get("difficulty", Topic.Difficulty.BEGINNER)
        answers = serializer.validated_data["answers"]

        try:
            topic = Topic.objects.get(id=topic_id, is_active=True)
        except Topic.DoesNotExist:
            return Response({"detail": "Topic not found."}, status=status.HTTP_404_NOT_FOUND)

        questions = QuizQuestion.objects.filter(topic=topic, is_active=True)
        if difficulty:
            diff_questions = questions.filter(difficulty=difficulty)
            if diff_questions.exists():
                questions = diff_questions

        total_questions = questions.count()
        if total_questions == 0:
            return Response({"detail": "No questions available for this topic."}, status=status.HTTP_400_BAD_REQUEST)

        # Create attempt
        attempt = QuizAttempt.objects.create(
            student=user,
            topic=topic,
            difficulty=difficulty,
            total_questions=total_questions,
            correct_answers=0,
            score=0,
            started_at=timezone.now(),
        )

        correct_count = 0
        responses_to_create = []

        for question in questions:
            selected_option = answers.get(str(question.id)) or answers.get(question.id)
            if selected_option:
                is_correct = (selected_option.upper() == question.correct_option.upper())
                if is_correct:
                    correct_count += 1
                responses_to_create.append(
                    QuizResponse(
                        attempt=attempt,
                        question=question,
                        selected_option=selected_option.upper(),
                        is_correct=is_correct,
                    )
                )

        QuizResponse.objects.bulk_create(responses_to_create)

        score_percent = round((correct_count / total_questions) * 100, 2)
        attempt.correct_answers = correct_count
        attempt.score = score_percent
        attempt.completed_at = timezone.now()
        attempt.save()

        # Update student topic progress
        progress, _ = TopicProgress.objects.get_or_create(
            student=user,
            topic=topic,
            defaults={"started_at": timezone.now()},
        )
        if score_percent >= 70.0:
            progress.status = TopicProgress.Status.COMPLETED
            progress.percent_complete = 100.0
            progress.completed_at = timezone.now()
        else:
            if progress.status != TopicProgress.Status.COMPLETED:
                progress.status = TopicProgress.Status.IN_PROGRESS
                progress.percent_complete = max(float(progress.percent_complete), 50.0)
        progress.save()

        # Run Recommendation Engine
        generate_recommendations_for_student(user)

        # Return attempt detail with full feedback
        return Response(
            QuizAttemptSerializer(attempt).data,
            status=status.HTTP_201_CREATED,
        )


class QuizHistoryView(generics.ListAPIView):
    """List quiz attempts history for the authenticated student or for instructor review."""
    serializer_class = QuizAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        topic_id = self.request.query_params.get("topic")
        queryset = QuizAttempt.objects.all()

        if user.role == User.Role.STUDENT:
            queryset = queryset.filter(student=user)
        elif topic_id:
            queryset = queryset.filter(topic_id=topic_id)

        return queryset.order_by("-started_at")


class QuizAttemptDetailView(generics.RetrieveAPIView):
    """Retrieve full breakdown and answer explanations for a specific attempt."""
    serializer_class = QuizAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in [User.Role.INSTRUCTOR, User.Role.ADMIN] or user.is_staff:
            return QuizAttempt.objects.all()
        return QuizAttempt.objects.filter(student=user)


class RecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    """Personalized recommendations powered by rule-based and content-based algorithms."""
    serializer_class = RecommendationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.STUDENT:
            # Trigger fresh recommendations if none exist
            recs = Recommendation.objects.filter(student=user, is_active=True)
            if not recs.exists():
                recs = generate_recommendations_for_student(user)
            return recs.order_by("-priority", "-created_at")
        # Instructors can inspect all recommendations
        return Recommendation.objects.filter(is_active=True).order_by("-priority", "-created_at")

    @action(detail=False, methods=["post"])
    def refresh(self, request):
        """Force re-run the recommendation engine for the current student."""
        if request.user.role != User.Role.STUDENT:
            return Response({"detail": "Only students receive personalized recommendations."}, status=status.HTTP_403_FORBIDDEN)
        
        recs = generate_recommendations_for_student(request.user)
        return Response(RecommendationSerializer(recs, many=True).data)


class StudentDashboardView(APIView):
    """Aggregates all metrics, recent activities, and charts for Student Dashboard."""
    permission_classes = [IsStudent]

    def get(self, request):
        user = request.user

        # 1. Total available subjects & enrolled/engaged subjects
        total_subjects = Subject.objects.filter(is_active=True).count()
        progress_qs = TopicProgress.objects.filter(student=user)
        
        completed_topics_count = progress_qs.filter(status=TopicProgress.Status.COMPLETED).count()
        in_progress_topics_count = progress_qs.filter(status=TopicProgress.Status.IN_PROGRESS).count()
        total_topics_count = Topic.objects.filter(is_active=True).count()

        # Overall completion rate
        overall_progress = round((completed_topics_count / max(total_topics_count, 1)) * 100, 1)

        # 2. Quiz performance
        attempts = QuizAttempt.objects.filter(student=user).order_by("-started_at")
        total_quizzes_taken = attempts.count()
        avg_score_data = attempts.aggregate(avg_score=Avg("score"))
        average_quiz_score = round(avg_score_data["avg_score"] or 0, 1)

        # 3. Recent activity list
        recent_attempts = QuizAttemptSerializer(attempts[:5], many=True).data

        # 4. Chart Data: Progress per subject
        subjects = Subject.objects.filter(is_active=True)
        subject_progress_chart = []
        for s in subjects:
            s_topics = s.topics.filter(is_active=True)
            s_total = s_topics.count()
            s_completed = progress_qs.filter(topic__in=s_topics, status=TopicProgress.Status.COMPLETED).count()
            rate = round((s_completed / max(s_total, 1)) * 100, 1)
            subject_progress_chart.append({
                "subject": s.name,
                "total": s_total,
                "completed": s_completed,
                "progress": rate,
            })

        # 5. Chart Data: Quiz score trend (last 7 attempts in chronological order)
        last_attempts = list(attempts[:7])
        last_attempts.reverse()
        score_trend_chart = [
            {
                "topic": att.topic.name[:12],
                "score": float(att.score),
                "date": att.started_at.strftime("%b %d"),
            }
            for att in last_attempts
        ]

        # 6. Active Recommendations
        recs = Recommendation.objects.filter(student=user, is_active=True).order_by("-priority", "-created_at")
        if not recs.exists():
            recs = generate_recommendations_for_student(user)
        recommendations_data = RecommendationSerializer(recs[:4], many=True).data

        return Response({
            "metrics": {
                "total_subjects": total_subjects,
                "completed_topics": completed_topics_count,
                "in_progress_topics": in_progress_topics_count,
                "total_topics": total_topics_count,
                "overall_progress_rate": overall_progress,
                "total_quizzes_taken": total_quizzes_taken,
                "average_quiz_score": average_quiz_score,
            },
            "recent_attempts": recent_attempts,
            "subject_progress": subject_progress_chart,
            "score_trend": score_trend_chart,
            "recommendations": recommendations_data,
        })


class InstructorDashboardView(APIView):
    """Aggregates cohort analytics, weak topics, and quiz metrics for Instructor Dashboard."""
    permission_classes = [IsInstructor]

    def get(self, request):
        students_count = User.objects.filter(role=User.Role.STUDENT).count()
        total_materials = LearningMaterial.objects.count()
        total_quizzes = QuizQuestion.objects.count()

        # Quiz attempts stats
        all_attempts = QuizAttempt.objects.all()
        total_attempts = all_attempts.count()
        avg_score = round(all_attempts.aggregate(avg=Avg("score"))["avg"] or 0, 1)

        # Topic-wise performance analytics
        topic_stats = []
        for topic in Topic.objects.filter(is_active=True).order_by("subject__name", "order"):
            t_attempts = all_attempts.filter(topic=topic)
            t_count = t_attempts.count()
            t_avg = round(t_attempts.aggregate(avg=Avg("score"))["avg"] or 0, 1) if t_count > 0 else 0
            
            # Completion count
            t_completed = TopicProgress.objects.filter(topic=topic, status=TopicProgress.Status.COMPLETED).count()
            t_rate = round((t_completed / max(students_count, 1)) * 100, 1)

            topic_stats.append({
                "id": topic.id,
                "name": topic.name,
                "subject": topic.subject.name,
                "difficulty": topic.difficulty,
                "attempts_count": t_count,
                "average_score": t_avg,
                "completion_rate": t_rate,
            })

        # Identify weak topics across the cohort (topics with avg score < 65% and at least 1 attempt)
        weak_topics = [
            t for t in topic_stats
            if t["attempts_count"] > 0 and t["average_score"] < 65.0
        ]
        weak_topics.sort(key=lambda x: x["average_score"])

        # Chart: Distribution of scores (<50, 50-70, 70-85, 85-100)
        score_distribution = [
            {"range": "< 50%", "count": all_attempts.filter(score__lt=50).count()},
            {"range": "50% - 69%", "count": all_attempts.filter(score__gte=50, score__lt=70).count()},
            {"range": "70% - 84%", "count": all_attempts.filter(score__gte=70, score__lt=85).count()},
            {"range": "85% - 100%", "count": all_attempts.filter(score__gte=85).count()},
        ]

        return Response({
            "metrics": {
                "students_count": students_count,
                "total_materials": total_materials,
                "total_questions": total_quizzes,
                "total_attempts": total_attempts,
                "average_quiz_score": avg_score,
            },
            "topic_stats": topic_stats,
            "weak_topics": weak_topics[:5],
            "score_distribution": score_distribution,
        })


class AdminStatsView(APIView):
    """System-wide management statistics for Administrator."""
    permission_classes = [IsAdminUserRole]

    def get(self, request):
        return Response({
            "total_users": User.objects.count(),
            "students": User.objects.filter(role=User.Role.STUDENT).count(),
            "instructors": User.objects.filter(role=User.Role.INSTRUCTOR).count(),
            "admins": User.objects.filter(role=User.Role.ADMIN).count(),
            "subjects": Subject.objects.count(),
            "topics": Topic.objects.count(),
            "materials": LearningMaterial.objects.count(),
            "questions": QuizQuestion.objects.count(),
            "attempts": QuizAttempt.objects.count(),
        })


class AdminUserViewSet(viewsets.ModelViewSet):
    """Admin endpoint to view, search, and update user roles and statuses."""
    serializer_class = UserSerializer
    permission_classes = [IsAdminUserRole]
    queryset = User.objects.all().order_by("-date_joined")
