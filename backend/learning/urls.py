from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import (
    AdminStatsView,
    AdminUserViewSet,
    InstructorDashboardView,
    LearningMaterialViewSet,
    QuizAPIView,
    QuizAttemptDetailView,
    QuizHistoryView,
    QuizQuestionManageViewSet,
    RecommendationViewSet,
    RegisterView,
    StudentDashboardView,
    SubjectViewSet,
    TopicProgressViewSet,
    TopicViewSet,
    UserProfileView,
)

router = DefaultRouter()
router.register(r"subjects", SubjectViewSet, basename="subject")
router.register(r"topics", TopicViewSet, basename="topic")
router.register(r"materials", LearningMaterialViewSet, basename="material")
router.register(r"progress", TopicProgressViewSet, basename="progress")
router.register(r"recommendations", RecommendationViewSet, basename="recommendation")
router.register(r"quizzes/questions", QuizQuestionManageViewSet, basename="quiz-question")
router.register(r"admin/users", AdminUserViewSet, basename="admin-user")

urlpatterns = [
    # Authentication
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/profile/", UserProfileView.as_view(), name="auth-profile"),
    path("auth/token/", TokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),

    # Quizzes
    path("quizzes/topic/<int:topic_id>/", QuizAPIView.as_view(), name="quiz-questions"),
    path("quizzes/submit/", QuizAPIView.as_view(), name="quiz-submit"),
    path("quizzes/history/", QuizHistoryView.as_view(), name="quiz-history"),
    path("quizzes/attempts/<int:pk>/", QuizAttemptDetailView.as_view(), name="quiz-attempt-detail"),

    # Dashboards
    path("dashboard/student/", StudentDashboardView.as_view(), name="dashboard-student"),
    path("dashboard/instructor/", InstructorDashboardView.as_view(), name="dashboard-instructor"),
    path("admin/stats/", AdminStatsView.as_view(), name="admin-stats"),

    # Router endpoints
    path("", include(router.urls)),
]
