from rest_framework import serializers
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


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_staff",
            "date_joined",
        ]
        read_only_fields = ["id", "is_staff", "date_joined"]


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "role",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        if attrs.get("password") != attrs.get("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        
        role = attrs.get("role", User.Role.STUDENT)
        # Default fallback to student if invalid
        if role not in [User.Role.STUDENT, User.Role.INSTRUCTOR, User.Role.ADMIN]:
            attrs["role"] = User.Role.STUDENT

        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LearningMaterialSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source="topic.name", read_only=True)
    subject_name = serializers.CharField(source="topic.subject.name", read_only=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = LearningMaterial
        fields = [
            "id",
            "topic",
            "topic_name",
            "subject_name",
            "title",
            "description",
            "material_type",
            "content",
            "resource_url",
            "estimated_minutes",
            "created_by",
            "created_by_username",
            "is_published",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class TopicSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    materials = serializers.SerializerMethodField()
    student_progress = serializers.SerializerMethodField()
    materials_count = serializers.IntegerField(source="materials.count", read_only=True)
    questions_count = serializers.IntegerField(source="questions.count", read_only=True)

    class Meta:
        model = Topic
        fields = [
            "id",
            "subject",
            "subject_name",
            "name",
            "slug",
            "description",
            "difficulty",
            "order",
            "is_active",
            "materials_count",
            "questions_count",
            "materials",
            "student_progress",
        ]
        read_only_fields = ["id"]

    def get_materials(self, obj):
        # Only return published materials
        published = obj.materials.filter(is_published=True)
        return LearningMaterialSerializer(published, many=True).data

    def get_student_progress(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated and request.user.role == User.Role.STUDENT:
            progress = TopicProgress.objects.filter(student=request.user, topic=obj).first()
            if progress:
                return {
                    "status": progress.status,
                    "percent_complete": float(progress.percent_complete),
                    "completed_at": progress.completed_at,
                }
        return {"status": "not_started", "percent_complete": 0.0, "completed_at": None}


class SubjectSerializer(serializers.ModelSerializer):
    topics_count = serializers.IntegerField(source="topics.count", read_only=True)
    topics = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "is_active",
            "created_at",
            "topics_count",
            "topics",
        ]
        read_only_fields = ["id", "created_at"]

    def get_topics(self, obj):
        active_topics = obj.topics.filter(is_active=True).order_by("order")
        return TopicSerializer(active_topics, many=True, context=self.context).data


class TopicProgressSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source="topic.name", read_only=True)
    subject_name = serializers.CharField(source="topic.subject.name", read_only=True)
    student_username = serializers.CharField(source="student.username", read_only=True)

    class Meta:
        model = TopicProgress
        fields = [
            "id",
            "student",
            "student_username",
            "topic",
            "topic_name",
            "subject_name",
            "status",
            "percent_complete",
            "started_at",
            "completed_at",
            "updated_at",
        ]
        read_only_fields = ["id", "updated_at"]


# Client-safe Question Serializer (Does NOT leak correct answer)
class QuizQuestionStudentSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source="topic.name", read_only=True)

    class Meta:
        model = QuizQuestion
        fields = [
            "id",
            "topic",
            "topic_name",
            "difficulty",
            "question_text",
            "option_a",
            "option_b",
            "option_c",
            "option_d",
        ]


# Full Quiz Question Serializer for Instructors/Admins and Post-Attempt Review
class QuizQuestionAdminSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source="topic.name", read_only=True)

    class Meta:
        model = QuizQuestion
        fields = [
            "id",
            "topic",
            "topic_name",
            "difficulty",
            "question_text",
            "option_a",
            "option_b",
            "option_c",
            "option_d",
            "correct_option",
            "explanation",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class QuizResponseSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source="question.question_text", read_only=True)
    correct_option = serializers.CharField(source="question.correct_option", read_only=True)
    explanation = serializers.CharField(source="question.explanation", read_only=True)
    option_a = serializers.CharField(source="question.option_a", read_only=True)
    option_b = serializers.CharField(source="question.option_b", read_only=True)
    option_c = serializers.CharField(source="question.option_c", read_only=True)
    option_d = serializers.CharField(source="question.option_d", read_only=True)

    class Meta:
        model = QuizResponse
        fields = [
            "id",
            "question",
            "question_text",
            "option_a",
            "option_b",
            "option_c",
            "option_d",
            "selected_option",
            "correct_option",
            "is_correct",
            "explanation",
            "answered_at",
        ]


class QuizAttemptSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source="topic.name", read_only=True)
    subject_name = serializers.CharField(source="topic.subject.name", read_only=True)
    student_username = serializers.CharField(source="student.username", read_only=True)
    responses = QuizResponseSerializer(many=True, read_only=True)

    class Meta:
        model = QuizAttempt
        fields = [
            "id",
            "student",
            "student_username",
            "topic",
            "topic_name",
            "subject_name",
            "difficulty",
            "score",
            "total_questions",
            "correct_answers",
            "started_at",
            "completed_at",
            "responses",
        ]
        read_only_fields = ["id", "score", "correct_answers", "completed_at"]


class QuizSubmissionSerializer(serializers.Serializer):
    topic_id = serializers.IntegerField()
    difficulty = serializers.ChoiceField(
        choices=Topic.Difficulty.choices,
        default=Topic.Difficulty.BEGINNER,
    )
    # Mapping of question_id (as str or int) -> selected_option ("A", "B", "C", "D")
    answers = serializers.DictField(
        child=serializers.ChoiceField(choices=["A", "B", "C", "D"])
    )


class RecommendationSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source="topic.name", read_only=True)
    topic_slug = serializers.CharField(source="topic.slug", read_only=True)
    subject_name = serializers.CharField(source="topic.subject.name", read_only=True)
    material_title = serializers.CharField(source="material.title", read_only=True, default=None)
    material_type = serializers.CharField(source="material.material_type", read_only=True, default=None)
    resource_url = serializers.CharField(source="material.resource_url", read_only=True, default="")
    estimated_minutes = serializers.IntegerField(source="material.estimated_minutes", read_only=True, default=0)

    class Meta:
        model = Recommendation
        fields = [
            "id",
            "student",
            "topic",
            "topic_name",
            "topic_slug",
            "subject_name",
            "material",
            "material_title",
            "material_type",
            "resource_url",
            "estimated_minutes",
            "kind",
            "reason",
            "target_difficulty",
            "priority",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
