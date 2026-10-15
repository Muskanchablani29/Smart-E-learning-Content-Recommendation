from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

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


@admin.register(User)
class LearningUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Learning platform", {"fields": ("role",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Learning platform", {"fields": ("email", "role")}),
    )
    list_display = ("username", "email", "first_name", "last_name", "role", "is_staff")
    list_filter = ("role", "is_staff", "is_active")


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("name", "subject", "difficulty", "order", "is_active")
    list_filter = ("subject", "difficulty", "is_active")
    search_fields = ("name", "description", "subject__name")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(LearningMaterial)
class LearningMaterialAdmin(admin.ModelAdmin):
    list_display = ("title", "topic", "material_type", "is_published", "created_at")
    list_filter = ("material_type", "is_published", "topic__subject")
    search_fields = ("title", "description", "content")


@admin.register(TopicProgress)
class TopicProgressAdmin(admin.ModelAdmin):
    list_display = ("student", "topic", "status", "percent_complete", "updated_at")
    list_filter = ("status", "topic__subject")
    search_fields = ("student__username", "topic__name")


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ("__str__", "topic", "difficulty", "is_active")
    list_filter = ("difficulty", "is_active", "topic__subject")
    search_fields = ("question_text", "explanation")


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "topic",
        "difficulty",
        "score",
        "correct_answers",
        "total_questions",
        "started_at",
    )
    list_filter = ("difficulty", "topic__subject")
    search_fields = ("student__username", "topic__name")


@admin.register(QuizResponse)
class QuizResponseAdmin(admin.ModelAdmin):
    list_display = ("attempt", "question", "selected_option", "is_correct", "answered_at")
    list_filter = ("is_correct", "question__topic__subject")


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "topic",
        "kind",
        "target_difficulty",
        "priority",
        "is_active",
        "created_at",
    )
    list_filter = ("kind", "target_difficulty", "is_active", "topic__subject")
    search_fields = ("student__username", "topic__name", "reason")
