import logging
from django.db.models import Avg, Max
from .models import LearningMaterial, QuizAttempt, Recommendation, Subject, Topic, TopicProgress, User

logger = logging.getLogger(__name__)


def generate_recommendations_for_student(student: User):
    """
    Evaluates rule-based logic and content-based filtering to create
    explainable personalized recommendations for the student.
    Persists results into the Recommendation model.
    """
    if not student or student.role != User.Role.STUDENT:
        return Recommendation.objects.none()

    # 1. Gather student history
    quiz_attempts = QuizAttempt.objects.filter(student=student).order_by("-started_at")
    progress_records = TopicProgress.objects.filter(student=student)
    
    completed_topic_ids = set(
        progress_records.filter(status=TopicProgress.Status.COMPLETED).values_list("topic_id", flat=True)
    )
    in_progress_topic_ids = set(
        progress_records.filter(status=TopicProgress.Status.IN_PROGRESS).values_list("topic_id", flat=True)
    )
    
    # Topic performance map: average score and latest score per topic
    topic_scores = {}
    for attempt in quiz_attempts:
        if attempt.topic_id not in topic_scores:
            topic_scores[attempt.topic_id] = {
                "latest_score": float(attempt.score),
                "scores": [float(attempt.score)],
                "difficulty": attempt.difficulty,
            }
        else:
            topic_scores[attempt.topic_id]["scores"].append(float(attempt.score))

    for t_id, data in topic_scores.items():
        data["avg_score"] = sum(data["scores"]) / len(data["scores"])

    # We will collect recommendation candidates as dicts:
    # { topic, material, kind, reason, target_difficulty, priority }
    candidates = []

    # -------------------------------------------------------------
    # RULE 1: Weak Topic Revision (Review)
    # If recent quiz score < 60% or avg score < 60%, recommend review.
    # -------------------------------------------------------------
    for topic_id, score_data in topic_scores.items():
        if score_data["latest_score"] < 60.0 or score_data["avg_score"] < 60.0:
            try:
                topic = Topic.objects.get(id=topic_id, is_active=True)
                # Find best review material (prefer study notes or video)
                material = (
                    LearningMaterial.objects.filter(topic=topic, is_published=True)
                    .order_by("-estimated_minutes")
                    .first()
                )
                candidates.append({
                    "topic": topic,
                    "material": material,
                    "kind": Recommendation.Kind.REVIEW,
                    "reason": f"Weak performance detected on '{topic.name}' (Latest quiz score: {score_data['latest_score']:.1f}%). Revision recommended before proceeding.",
                    "target_difficulty": topic.difficulty,
                    "priority": 5, # Highest priority
                })
            except Topic.DoesNotExist:
                continue

    # -------------------------------------------------------------
    # RULE 2: Next Topic Progression
    # For subjects where the student has completed a topic or scored >= 70%,
    # recommend the next consecutive topic in order.
    # -------------------------------------------------------------
    active_subjects = Subject.objects.filter(is_active=True)
    for subject in active_subjects:
        subject_topics = list(subject.topics.filter(is_active=True).order_by("order", "id"))
        for idx, topic in enumerate(subject_topics):
            topic_completed = (
                topic.id in completed_topic_ids or
                (topic.id in topic_scores and topic_scores[topic.id]["latest_score"] >= 70.0)
            )
            if topic_completed and (idx + 1 < len(subject_topics)):
                next_topic = subject_topics[idx + 1]
                if next_topic.id not in completed_topic_ids:
                    material = (
                        LearningMaterial.objects.filter(topic=next_topic, is_published=True).first()
                    )
                    candidates.append({
                        "topic": next_topic,
                        "material": material,
                        "kind": Recommendation.Kind.NEXT_TOPIC,
                        "reason": f"Building on your mastery of '{topic.name}', the next recommended concept in {subject.name} is '{next_topic.name}'.",
                        "target_difficulty": next_topic.difficulty,
                        "priority": 4,
                    })
                    break  # Recommend just the immediate next topic per subject

    # -------------------------------------------------------------
    # RULE 3: Mastery Challenge
    # If student scored >= 85% on beginner/intermediate topics,
    # find available advanced topics in that subject.
    # -------------------------------------------------------------
    for topic_id, score_data in topic_scores.items():
        if score_data["latest_score"] >= 85.0:
            try:
                topic = Topic.objects.get(id=topic_id, is_active=True)
                challenge_topic = (
                    Topic.objects.filter(
                        subject=topic.subject,
                        difficulty=Topic.Difficulty.ADVANCED,
                        is_active=True,
                    )
                    .exclude(id__in=completed_topic_ids)
                    .first()
                )
                if challenge_topic and challenge_topic.id != topic.id:
                    material = LearningMaterial.objects.filter(topic=challenge_topic, is_published=True).first()
                    candidates.append({
                        "topic": challenge_topic,
                        "material": material,
                        "kind": Recommendation.Kind.CHALLENGE,
                        "reason": f"Excellent mastery on '{topic.name}' ({score_data['latest_score']:.1f}%). Challenge yourself with advanced topic '{challenge_topic.name}'.",
                        "target_difficulty": Topic.Difficulty.ADVANCED,
                        "priority": 3,
                    })
            except Topic.DoesNotExist:
                continue

    # -------------------------------------------------------------
    # RULE 4: Content-Based Filtering
    # Recommend topics similar in difficulty or subject keywords
    # to topics where the student has engaged or shown interest.
    # -------------------------------------------------------------
    engaged_topic_ids = set(topic_scores.keys()) | completed_topic_ids | in_progress_topic_ids
    if engaged_topic_ids:
        engaged_topics = Topic.objects.filter(id__in=engaged_topic_ids)
        preferred_difficulties = [t.difficulty for t in engaged_topics]
        preferred_subjects = [t.subject_id for t in engaged_topics]

        similar_topics = (
            Topic.objects.filter(is_active=True)
            .exclude(id__in=engaged_topic_ids)
            .filter(subject_id__in=preferred_subjects)
            .order_by("order")[:3]
        )
        for sim_topic in similar_topics:
            material = LearningMaterial.objects.filter(topic=sim_topic, is_published=True).first()
            candidates.append({
                "topic": sim_topic,
                "material": material,
                "kind": Recommendation.Kind.NEXT_TOPIC,
                "reason": f"Content-based match: Recommended based on your interest and activity in '{sim_topic.subject.name}'.",
                "target_difficulty": sim_topic.difficulty,
                "priority": 3,
            })

    # -------------------------------------------------------------
    # RULE 5: Cold Start / Fallback for New Students
    # If the candidate list is empty or student has limited history,
    # recommend foundational Beginner topics across available subjects.
    # -------------------------------------------------------------
    if len(candidates) < 3:
        foundational_topics = (
            Topic.objects.filter(
                is_active=True,
                difficulty=Topic.Difficulty.BEGINNER,
            )
            .exclude(id__in=completed_topic_ids)
            .order_by("order", "id")[:4]
        )
        for f_topic in foundational_topics:
            # avoid duplicating if already in candidates
            if any(c["topic"].id == f_topic.id for c in candidates):
                continue
            material = LearningMaterial.objects.filter(topic=f_topic, is_published=True).first()
            candidates.append({
                "topic": f_topic,
                "material": material,
                "kind": Recommendation.Kind.NEXT_TOPIC,
                "reason": f"Foundational Starter: Recommended introduction to kickstart your '{f_topic.subject.name}' learning track.",
                "target_difficulty": Topic.Difficulty.BEGINNER,
                "priority": 3,
            })

    # -------------------------------------------------------------
    # Deduplicate & Persist to Database
    # -------------------------------------------------------------
    seen_topic_ids = set()
    unique_candidates = []
    for c in candidates:
        if c["topic"].id not in seen_topic_ids:
            seen_topic_ids.add(c["topic"].id)
            unique_candidates.append(c)

    # Deactivate older recommendations no longer in active candidate set
    active_cand_topic_ids = [c["topic"].id for c in unique_candidates]
    Recommendation.objects.filter(student=student, is_active=True).exclude(
        topic_id__in=active_cand_topic_ids
    ).update(is_active=False)

    # Upsert candidates
    for c in unique_candidates:
        Recommendation.objects.update_or_create(
            student=student,
            topic=c["topic"],
            defaults={
                "material": c["material"],
                "kind": c["kind"],
                "reason": c["reason"],
                "target_difficulty": c["target_difficulty"],
                "priority": c["priority"],
                "is_active": True,
            },
        )

    return Recommendation.objects.filter(student=student, is_active=True).order_by("-priority", "-created_at")
