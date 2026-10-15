from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q


class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        INSTRUCTOR = "instructor", "Instructor"
        ADMIN = "admin", "Admin"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=12, choices=Role.choices, default=Role.STUDENT)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Subject(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Topic(models.Model):
    class Difficulty(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="topics")
    name = models.CharField(max_length=140)
    slug = models.SlugField(max_length=160)
    description = models.TextField(blank=True)
    difficulty = models.CharField(
        max_length=12,
        choices=Difficulty.choices,
        default=Difficulty.BEGINNER,
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["subject__name", "order", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["subject", "slug"],
                name="unique_topic_slug_per_subject",
            ),
        ]

    def __str__(self):
        return f"{self.subject.name}: {self.name}"


class LearningMaterial(models.Model):
    class MaterialType(models.TextChoices):
        NOTES = "notes", "Study notes"
        VIDEO = "video", "Video"
        ARTICLE = "article", "Article"
        EXTERNAL = "external", "External resource"

    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="materials",
    )
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    material_type = models.CharField(
        max_length=12,
        choices=MaterialType.choices,
        default=MaterialType.NOTES,
    )
    content = models.TextField(blank=True)
    resource_url = models.URLField(blank=True)
    estimated_minutes = models.PositiveSmallIntegerField(default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_materials",
    )
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["topic__subject__name", "topic__order", "title"]

    def __str__(self):
        return self.title


class TopicProgress(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = "not_started", "Not started"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="topic_progress",
        limit_choices_to={"role": User.Role.STUDENT},
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="student_progress",
    )
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.NOT_STARTED,
    )
    percent_complete = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "topic"],
                name="unique_student_topic_progress",
            ),
        ]

    def __str__(self):
        return f"{self.student} - {self.topic} ({self.get_status_display()})"


class QuizQuestion(models.Model):
    class Option(models.TextChoices):
        A = "A", "Option A"
        B = "B", "Option B"
        C = "C", "Option C"
        D = "D", "Option D"

    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    difficulty = models.CharField(
        max_length=12,
        choices=Topic.Difficulty.choices,
        default=Topic.Difficulty.BEGINNER,
    )
    question_text = models.TextField()
    option_a = models.CharField(max_length=500)
    option_b = models.CharField(max_length=500)
    option_c = models.CharField(max_length=500)
    option_d = models.CharField(max_length=500)
    correct_option = models.CharField(max_length=1, choices=Option.choices)
    explanation = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_questions",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["topic__subject__name", "topic__order", "id"]

    def __str__(self):
        return f"{self.topic}: {self.question_text[:80]}"


class QuizAttempt(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quiz_attempts",
        limit_choices_to={"role": User.Role.STUDENT},
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="quiz_attempts",
    )
    difficulty = models.CharField(
        max_length=12,
        choices=Topic.Difficulty.choices,
    )
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    total_questions = models.PositiveSmallIntegerField()
    correct_answers = models.PositiveSmallIntegerField(default=0)
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(correct_answers__lte=models.F("total_questions")),
                name="quiz_correct_answers_not_over_total",
            ),
        ]

    def __str__(self):
        return f"{self.student} - {self.topic} ({self.score}%)"


class QuizResponse(models.Model):
    attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.CASCADE,
        related_name="responses",
    )
    question = models.ForeignKey(
        QuizQuestion,
        on_delete=models.PROTECT,
        related_name="responses",
    )
    selected_option = models.CharField(
        max_length=1,
        choices=QuizQuestion.Option.choices,
    )
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["attempt", "question"],
                name="unique_question_per_quiz_attempt",
            ),
        ]

    def __str__(self):
        return f"Attempt {self.attempt_id} - question {self.question_id}"


class Recommendation(models.Model):
    class Kind(models.TextChoices):
        REVIEW = "review", "Review"
        NEXT_TOPIC = "next_topic", "Next topic"
        CHALLENGE = "challenge", "Challenge"

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recommendations",
        limit_choices_to={"role": User.Role.STUDENT},
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="recommendations",
    )
    material = models.ForeignKey(
        LearningMaterial,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="recommendations",
    )
    kind = models.CharField(max_length=12, choices=Kind.choices)
    reason = models.TextField()
    target_difficulty = models.CharField(
        max_length=12,
        choices=Topic.Difficulty.choices,
    )
    priority = models.PositiveSmallIntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-priority", "-created_at"]

    def __str__(self):
        return f"{self.student} - {self.get_kind_display()}: {self.topic}"
