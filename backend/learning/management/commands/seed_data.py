from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from learning.models import (
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
from learning.recommendation_engine import generate_recommendations_for_student


class Command(BaseCommand):
    help = "Seeds initial subjects, topics, materials, questions, and demo users."

    def handle(self, *args, **options):
        self.stdout.write("Seeding data for Smart E-Learning Platform...")

        # 1. Demo Users
        admin_user, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@example.com",
                "first_name": "System",
                "last_name": "Administrator",
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin_user.set_password("Password123!")
        admin_user.role = User.Role.ADMIN
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()

        instructor_user, _ = User.objects.get_or_create(
            username="instructor1",
            defaults={
                "email": "instructor1@example.com",
                "first_name": "Dr. Sarah",
                "last_name": "Jenkins",
                "role": User.Role.INSTRUCTOR,
            },
        )
        instructor_user.set_password("Password123!")
        instructor_user.role = User.Role.INSTRUCTOR
        instructor_user.save()

        student_user, _ = User.objects.get_or_create(
            username="student1",
            defaults={
                "email": "student1@example.com",
                "first_name": "Alex",
                "last_name": "Rivera",
                "role": User.Role.STUDENT,
            },
        )
        student_user.set_password("Password123!")
        student_user.role = User.Role.STUDENT
        student_user.save()

        self.stdout.write("Created demo users: admin, instructor1, student1 (password: Password123!)")

        # 2. Subjects and Topics
        catalog = [
            {
                "name": "Artificial Intelligence & Machine Learning",
                "slug": "ai-ml",
                "description": "Master machine learning foundations, loss functions, algorithms, and deep neural architectures.",
                "topics": [
                    {
                        "name": "Introduction to Machine Learning",
                        "slug": "intro-machine-learning",
                        "difficulty": Topic.Difficulty.BEGINNER,
                        "order": 1,
                        "description": "Supervised, unsupervised, reinforcement learning paradigms, and data preprocessing pipelines.",
                        "materials": [
                            {
                                "title": "Comprehensive Guide to ML Paradigms",
                                "material_type": LearningMaterial.MaterialType.NOTES,
                                "estimated_minutes": 15,
                                "content": (
                                    "# Machine Learning Paradigms\n\n"
                                    "Machine Learning is a subset of AI that trains mathematical models to find patterns from empirical data.\n\n"
                                    "### 1. Supervised Learning\n"
                                    "- **Classification**: Predicting categorical labels (e.g., spam vs non-spam, disease detection).\n"
                                    "- **Regression**: Predicting continuous values (e.g., housing prices, stock valuations).\n\n"
                                    "### 2. Unsupervised Learning\n"
                                    "- Finds hidden structures in unlabeled data.\n"
                                    "- Common approaches: K-Means Clustering, Principal Component Analysis (PCA).\n\n"
                                    "### 3. Model Evaluation\n"
                                    "- Training Set vs Validation Set vs Test Set.\n"
                                    "- Avoid data leakage and test for generalization."
                                ),
                            },
                            {
                                "title": "Video: How Machine Learning Actually Works",
                                "material_type": LearningMaterial.MaterialType.VIDEO,
                                "resource_url": "https://www.youtube.com/watch?v=ukzFI9rgwfU",
                                "estimated_minutes": 20,
                                "content": "Visual introduction explaining training data, weight adjustment, and feature representations.",
                            },
                        ],
                        "questions": [
                            {
                                "question_text": "Which type of machine learning algorithm is used when the target variable is continuous (e.g., predicting temperature)?",
                                "difficulty": Topic.Difficulty.BEGINNER,
                                "option_a": "Classification",
                                "option_b": "Regression",
                                "option_c": "Clustering",
                                "option_d": "Reinforcement Learning",
                                "correct_option": "B",
                                "explanation": "Regression algorithms predict continuous real-valued outputs such as prices, scores, or temperatures.",
                            },
                            {
                                "question_text": "In unsupervised learning, what is the nature of the training dataset?",
                                "difficulty": Topic.Difficulty.BEGINNER,
                                "option_a": "Labeled with ground truth targets",
                                "option_b": "Partially labeled with human feedback",
                                "option_c": "Unlabeled data without predefined target outputs",
                                "option_d": "Only binary target variables",
                                "correct_option": "C",
                                "explanation": "Unsupervised learning algorithms uncover underlying patterns, distributions, or groupings from unlabeled data.",
                            },
                            {
                                "question_text": "What is the primary danger of training and evaluating a model on the exact same dataset?",
                                "difficulty": Topic.Difficulty.BEGINNER,
                                "option_a": "Underfitting",
                                "option_b": "Overfitting and poor generalization",
                                "option_c": "Gradient explosion",
                                "option_d": "Premature convergence",
                                "correct_option": "B",
                                "explanation": "Evaluating on training data yields overly optimistic accuracy because the model may simply memorize noise without generalizing.",
                            },
                        ],
                    },
                    {
                        "name": "Linear Regression & Gradient Descent",
                        "slug": "linear-regression-gradient-descent",
                        "difficulty": Topic.Difficulty.INTERMEDIATE,
                        "order": 2,
                        "description": "Ordinary Least Squares, Mean Squared Error loss functions, and optimizing parameters using Gradient Descent.",
                        "materials": [
                            {
                                "title": "Linear Regression and Loss Minimization",
                                "material_type": LearningMaterial.MaterialType.NOTES,
                                "estimated_minutes": 25,
                                "content": (
                                    "# Linear Regression & Gradient Descent\n\n"
                                    "Linear regression models the relationship between dependent variable Y and independent features X:\n"
                                    "$$\\hat{y} = \\theta_0 + \\theta_1 x_1 + ... + \\theta_n x_n$$\n\n"
                                    "### Mean Squared Error (MSE)\n"
                                    "$$J(\\theta) = \\frac{1}{2m} \\sum_{i=1}^m (\\hat{y}^{(i)} - y^{(i)})^2$$\n\n"
                                    "### Gradient Descent Algorithm\n"
                                    "Update parameters in the opposite direction of the gradient:\n"
                                    "$$\\theta_j := \\theta_j - \\alpha \\frac{\\partial J}{\\partial \\theta_j}$$\n"
                                    "Here, $\\alpha$ is the learning rate."
                                ),
                            },
                        ],
                        "questions": [
                            {
                                "question_text": "What happens in gradient descent if the learning rate alpha is chosen too large?",
                                "difficulty": Topic.Difficulty.INTERMEDIATE,
                                "option_a": "The model converges in 1 iteration",
                                "option_b": "It will oscillate and may fail to converge or even diverge",
                                "option_c": "The cost function becomes zero immediately",
                                "option_d": "The gradient stops computing",
                                "correct_option": "B",
                                "explanation": "An overly large learning rate causes step updates that overshoot minimum loss, causing divergence.",
                            },
                            {
                                "question_text": "What is the loss function standardly minimized in Ordinary Least Squares Linear Regression?",
                                "difficulty": Topic.Difficulty.INTERMEDIATE,
                                "option_a": "Cross-Entropy Loss",
                                "option_b": "Mean Squared Error (MSE)",
                                "option_c": "Hinge Loss",
                                "option_d": "Kullback-Leibler Divergence",
                                "correct_option": "B",
                                "explanation": "Mean Squared Error penalizes larger errors quadratically and forms a convex surface for linear models.",
                            },
                            {
                                "question_text": "What technique prevents overfitting in linear models by penalizing large weights?",
                                "difficulty": Topic.Difficulty.INTERMEDIATE,
                                "option_a": "Regularization (L1 Lasso / L2 Ridge)",
                                "option_b": "Data augmentations",
                                "option_c": "Increasing learning rate",
                                "option_d": "Removing bias term",
                                "correct_option": "A",
                                "explanation": "L1 and L2 regularization add weight penalties to the cost function, reducing variance.",
                            },
                        ],
                    },
                    {
                        "name": "Neural Networks & Deep Learning",
                        "slug": "neural-networks-deep-learning",
                        "difficulty": Topic.Difficulty.ADVANCED,
                        "order": 3,
                        "description": "Multi-layer perceptrons, forward propagation, activation functions, and backpropagation.",
                        "materials": [
                            {
                                "title": "Deep Neural Network Architecture",
                                "material_type": LearningMaterial.MaterialType.NOTES,
                                "estimated_minutes": 30,
                                "content": (
                                    "# Neural Networks and Deep Learning\n\n"
                                    "A neural network is composed of layers of artificial neurons (nodes):\n\n"
                                    "- **Input Layer**: Features\n"
                                    "- **Hidden Layers**: Non-linear transformations with activations like ReLU, GeLU, Sigmoid\n"
                                    "- **Output Layer**: Predictions\n\n"
                                    "### Backpropagation\n"
                                    "Calculates the partial derivative of the loss function with respect to every weight using the calculus chain rule."
                                ),
                            },
                        ],
                        "questions": [
                            {
                                "question_text": "Why are non-linear activation functions necessary in multi-layer neural networks?",
                                "difficulty": Topic.Difficulty.ADVANCED,
                                "option_a": "They speed up GPU compilation",
                                "option_b": "Without non-linearity, stacking layers is mathematically equivalent to a single linear layer",
                                "option_c": "They guarantee zero loss",
                                "option_d": "They eliminate negative numbers",
                                "correct_option": "B",
                                "explanation": "Any composition of linear transformations is simply another linear transformation. Non-linear activations allow networks to learn complex decision boundaries.",
                            },
                            {
                                "question_text": "What mathematical principle powers the backpropagation algorithm?",
                                "difficulty": Topic.Difficulty.ADVANCED,
                                "option_a": "Bayes Theorem",
                                "option_b": "The Calculus Chain Rule",
                                "option_c": "Central Limit Theorem",
                                "option_d": "Euler's Formula",
                                "correct_option": "B",
                                "explanation": "The chain rule allows propagation of loss gradients backward through successive layers.",
                            },
                            {
                                "question_text": "Which activation function is most widely adopted in hidden layers of modern deep feedforward networks to mitigate vanishing gradients?",
                                "difficulty": Topic.Difficulty.ADVANCED,
                                "option_a": "Sigmoid",
                                "option_b": "Tanh",
                                "option_c": "ReLU (Rectified Linear Unit)",
                                "option_d": "Step function",
                                "correct_option": "C",
                                "explanation": "ReLU maintains a constant derivative of 1 for positive activations, mitigating vanishing gradient issues.",
                            },
                        ],
                    },
                ],
            },
            {
                "name": "Python & Data Structures",
                "slug": "python-ds",
                "description": "Deep dive into clean Python programming, algorithms, OOP design, and algorithmic complexity.",
                "topics": [
                    {
                        "name": "Python Collections & Idiomatic Syntax",
                        "slug": "python-collections-syntax",
                        "difficulty": Topic.Difficulty.BEGINNER,
                        "order": 1,
                        "description": "List comprehensions, dict/set operations, generators, and time complexities of built-in collections.",
                        "materials": [
                            {
                                "title": "Efficient Python Collections and Comprehensions",
                                "material_type": LearningMaterial.MaterialType.NOTES,
                                "estimated_minutes": 20,
                                "content": (
                                    "# Python Collections\n\n"
                                    "- **List**: Dynamic array, O(1) index lookup, O(n) search.\n"
                                    "- **Dict**: Hash table, average O(1) key lookup and insert.\n"
                                    "- **Set**: Hash-based collection of unique elements, average O(1) membership check.\n\n"
                                    "### Comprehensions\n"
                                    "```python\n"
                                    "squares = [x**2 for x in range(10) if x % 2 == 0]\n"
                                    "mapping = {k: v for k, v in zip(keys, values)}\n"
                                    "```"
                                ),
                            },
                        ],
                        "questions": [
                            {
                                "question_text": "What is the average time complexity for checking membership (`item in collection`) in a Python `set`?",
                                "difficulty": Topic.Difficulty.BEGINNER,
                                "option_a": "O(1)",
                                "option_b": "O(n)",
                                "option_c": "O(log n)",
                                "option_d": "O(n log n)",
                                "correct_option": "A",
                                "explanation": "Sets in Python are implemented as hash tables, giving average O(1) lookup and membership testing.",
                            },
                            {
                                "question_text": "Which of the following creates a generator in Python without holding all items in memory at once?",
                                "difficulty": Topic.Difficulty.BEGINNER,
                                "option_a": "`[x*2 for x in range(100)]`",
                                "option_b": "`(x*2 for x in range(100))`",
                                "option_c": "`{x*2 for x in range(100)}`",
                                "option_d": "`{x: x*2 for x in range(100)}`",
                                "correct_option": "B",
                                "explanation": "Parentheses with comprehension syntax create a lazy generator expression in Python.",
                            },
                            {
                                "question_text": "Are Python dictionary keys mutable or immutable?",
                                "difficulty": Topic.Difficulty.BEGINNER,
                                "option_a": "Must be mutable",
                                "option_b": "Must be hashable (typically immutable types)",
                                "option_c": "Can be any arbitrary Python object including lists",
                                "option_d": "Must be strictly strings",
                                "correct_option": "B",
                                "explanation": "Dictionary keys must implement __hash__ and __eq__, which requires them to be hashable (such as tuples, strings, numbers).",
                            },
                        ],
                    },
                    {
                        "name": "Object-Oriented Programming in Python",
                        "slug": "python-oop",
                        "difficulty": Topic.Difficulty.INTERMEDIATE,
                        "order": 2,
                        "description": "Encapsulation, inheritance, polymorphism, dunder methods, and design patterns.",
                        "materials": [
                            {
                                "title": "Advanced OOP: Dunder Methods and Inheritance",
                                "material_type": LearningMaterial.MaterialType.NOTES,
                                "estimated_minutes": 25,
                                "content": (
                                    "# Python Object Oriented Programming\n\n"
                                    "Learn how to design clean class hierarchies:\n"
                                    "- `__init__` and `__str__`\n"
                                    "- Multiple inheritance and Method Resolution Order (MRO)\n"
                                    "- Properties with `@property` and `@setter`\n"
                                    "- `@classmethod` vs `@staticmethod`"
                                ),
                            },
                        ],
                        "questions": [
                            {
                                "question_text": "What does Python use to determine method lookup order in multiple inheritance?",
                                "difficulty": Topic.Difficulty.INTERMEDIATE,
                                "option_a": "Breadth-First Alphabetical Search",
                                "option_b": "C3 Superclass Linearization (MRO)",
                                "option_c": "Random resolution",
                                "option_d": "First class declared always overrides everything",
                                "correct_option": "B",
                                "explanation": "Python uses the C3 linearization algorithm to establish the Method Resolution Order (MRO).",
                            },
                            {
                                "question_text": "Which decorator in Python allows a method to receive the class itself as its first argument instead of an instance?",
                                "difficulty": Topic.Difficulty.INTERMEDIATE,
                                "option_a": "@staticmethod",
                                "option_b": "@classmethod",
                                "option_c": "@property",
                                "option_d": "@abstractmethod",
                                "correct_option": "B",
                                "explanation": "@classmethod passes the class (cls) as the first argument, allowing alternative constructors.",
                            },
                            {
                                "question_text": "Which special method is invoked when you call `len(obj)` in Python?",
                                "difficulty": Topic.Difficulty.INTERMEDIATE,
                                "option_a": "__size__",
                                "option_b": "__count__",
                                "option_c": "__len__",
                                "option_d": "__length__",
                                "correct_option": "C",
                                "explanation": "The built-in len() function delegates directly to the object's __len__() dunder method.",
                            },
                        ],
                    },
                    {
                        "name": "Trees, Graphs & Algorithm Complexity",
                        "slug": "trees-graphs-algorithms",
                        "difficulty": Topic.Difficulty.ADVANCED,
                        "order": 3,
                        "description": "Binary search trees, graph representations, breadth-first search, depth-first search, and asymptotic bounds.",
                        "materials": [
                            {
                                "title": "Graph Traversal and Asymptotic Notation",
                                "material_type": LearningMaterial.MaterialType.NOTES,
                                "estimated_minutes": 30,
                                "content": (
                                    "# Trees and Graph Algorithms\n\n"
                                    "### Traversal Algorithms\n"
                                    "- **BFS**: Queue-based, shortest path in unweighted graphs, $O(V + E)$.\n"
                                    "- **DFS**: Stack/recursion-based, topological sorting, cycle detection, $O(V + E)$.\n\n"
                                    "### Binary Search Tree Invariant\n"
                                    "For every node: left subtree keys < node key < right subtree keys."
                                ),
                            },
                        ],
                        "questions": [
                            {
                                "question_text": "What is the worst-case time complexity of searching in an unbalanced Binary Search Tree of n nodes?",
                                "difficulty": Topic.Difficulty.ADVANCED,
                                "option_a": "O(1)",
                                "option_b": "O(log n)",
                                "option_c": "O(n)",
                                "option_d": "O(n^2)",
                                "correct_option": "C",
                                "explanation": "If a BST is completely skewed (degenerate like a linked list), search degrades to O(n).",
                            },
                            {
                                "question_text": "Which data structure is fundamentally used to implement Breadth-First Search (BFS)?",
                                "difficulty": Topic.Difficulty.ADVANCED,
                                "option_a": "Queue (FIFO)",
                                "option_b": "Stack (LIFO)",
                                "option_c": "Binary Heap",
                                "option_d": "Disjoint Set",
                                "correct_option": "A",
                                "explanation": "BFS explores vertices level by level using a FIFO Queue.",
                            },
                            {
                                "question_text": "What is the time complexity of Breadth-First Search on a graph with V vertices and E edges?",
                                "difficulty": Topic.Difficulty.ADVANCED,
                                "option_a": "O(V * E)",
                                "option_b": "O(V + E)",
                                "option_c": "O(V^2)",
                                "option_d": "O(log(V + E))",
                                "correct_option": "B",
                                "explanation": "Every vertex is visited once and every edge is explored once or twice, yielding O(V + E).",
                            },
                        ],
                    },
                ],
            },
            {
                "name": "Fullstack Web & React Development",
                "slug": "web-dev",
                "description": "Modern frontend development with React, asynchronous APIs, component architectures, and REST integration.",
                "topics": [
                    {
                        "name": "JavaScript ES6+ and Asynchronous Programming",
                        "slug": "javascript-es6-async",
                        "difficulty": Topic.Difficulty.BEGINNER,
                        "order": 1,
                        "description": "Arrow functions, destructuring, promises, async/await, and event loops.",
                        "materials": [
                            {
                                "title": "Modern JavaScript ES6+ Essentials",
                                "material_type": LearningMaterial.MaterialType.NOTES,
                                "estimated_minutes": 15,
                                "content": (
                                    "# Modern JS Foundations\n\n"
                                    "- `const` and `let` scope rules\n"
                                    "- Destructuring: `const { title, id } = item;`\n"
                                    "- Async / Await with Promises and `try / catch` error handling"
                                ),
                            },
                        ],
                        "questions": [
                            {
                                "question_text": "What does an `async` function always return in JavaScript?",
                                "difficulty": Topic.Difficulty.BEGINNER,
                                "option_a": "A boolean",
                                "option_b": "A Promise",
                                "option_c": "A callback function",
                                "option_d": "An Observable",
                                "correct_option": "B",
                                "explanation": "An async function always wraps its return value in a resolved Promise.",
                            },
                            {
                                "question_text": "What is the scope of a variable declared with `const` or `let`?",
                                "difficulty": Topic.Difficulty.BEGINNER,
                                "option_a": "Function scope only",
                                "option_b": "Block scope",
                                "option_c": "Global scope exclusively",
                                "option_d": "Module scope only",
                                "correct_option": "B",
                                "explanation": "`let` and `const` provide block-scoping within the enclosing curly braces `{}`.",
                            },
                            {
                                "question_text": "Which array method creates a new array populated with the results of calling a provided function on every element?",
                                "difficulty": Topic.Difficulty.BEGINNER,
                                "option_a": ".forEach()",
                                "option_b": ".filter()",
                                "option_c": ".map()",
                                "option_d": ".reduce()",
                                "correct_option": "C",
                                "explanation": ".map() transforms each element and returns a newly created array of identical length.",
                            },
                        ],
                    },
                    {
                        "name": "React Hooks & Component Lifecycle",
                        "slug": "react-hooks-lifecycle",
                        "difficulty": Topic.Difficulty.INTERMEDIATE,
                        "order": 2,
                        "description": "Functional components, useState, useEffect, useContext, and custom reusable hooks.",
                        "materials": [
                            {
                                "title": "Mastering React Hooks",
                                "material_type": LearningMaterial.MaterialType.NOTES,
                                "estimated_minutes": 20,
                                "content": (
                                    "# React Hooks Architecture\n\n"
                                    "Hooks allow functional components to manage state and side-effects:\n\n"
                                    "```jsx\n"
                                    "const [data, setData] = useState([]);\n"
                                    "useEffect(() => {\n"
                                    "  fetchData();\n"
                                    "}, []); // Empty dependency array runs once on mount\n"
                                    "```"
                                ),
                            },
                        ],
                        "questions": [
                            {
                                "question_text": "When does the callback inside `useEffect(callback, [])` execute?",
                                "difficulty": Topic.Difficulty.INTERMEDIATE,
                                "option_a": "On every component re-render",
                                "option_b": "Once after initial mount",
                                "option_c": "Only right before component unmounts",
                                "option_d": "Before DOM paint synchronously",
                                "correct_option": "B",
                                "explanation": "An empty dependency array signals that the effect does not depend on any state or props and runs once after mount.",
                            },
                            {
                                "question_text": "Which hook is designed to pass data deep through the component tree without prop drilling?",
                                "difficulty": Topic.Difficulty.INTERMEDIATE,
                                "option_a": "useState",
                                "option_b": "useRef",
                                "option_c": "useContext",
                                "option_d": "useReducer",
                                "correct_option": "C",
                                "explanation": "useContext provides access to shared context state without passing props through intermediate layers.",
                            },
                            {
                                "question_text": "What is the primary rule of React Hooks?",
                                "difficulty": Topic.Difficulty.INTERMEDIATE,
                                "option_a": "Must only be called at the top level of React functions, not inside loops or conditions",
                                "option_b": "Must only be called inside class components",
                                "option_c": "Must be async functions",
                                "option_d": "Must return a JSX element",
                                "correct_option": "A",
                                "explanation": "Hooks must be called at top level so React maintains consistent state across renders.",
                            },
                        ],
                    },
                ],
            },
        ]

        # Insert subjects, topics, materials, questions
        for s_data in catalog:
            subject, _ = Subject.objects.get_or_create(
                slug=s_data["slug"],
                defaults={
                    "name": s_data["name"],
                    "description": s_data["description"],
                    "is_active": True,
                },
            )
            for t_data in s_data["topics"]:
                topic, _ = Topic.objects.get_or_create(
                    subject=subject,
                    slug=t_data["slug"],
                    defaults={
                        "name": t_data["name"],
                        "difficulty": t_data["difficulty"],
                        "order": t_data["order"],
                        "description": t_data["description"],
                        "is_active": True,
                    },
                )
                # Materials
                for m_data in t_data.get("materials", []):
                    LearningMaterial.objects.get_or_create(
                        topic=topic,
                        title=m_data["title"],
                        defaults={
                            "material_type": m_data["material_type"],
                            "content": m_data.get("content", ""),
                            "resource_url": m_data.get("resource_url", ""),
                            "estimated_minutes": m_data.get("estimated_minutes", 10),
                            "is_published": True,
                            "created_by": instructor_user,
                        },
                    )
                # Questions
                for q_data in t_data.get("questions", []):
                    QuizQuestion.objects.get_or_create(
                        topic=topic,
                        question_text=q_data["question_text"],
                        defaults={
                            "difficulty": q_data["difficulty"],
                            "option_a": q_data["option_a"],
                            "option_b": q_data["option_b"],
                            "option_c": q_data["option_c"],
                            "option_d": q_data["option_d"],
                            "correct_option": q_data["correct_option"],
                            "explanation": q_data["explanation"],
                            "created_by": instructor_user,
                            "is_active": True,
                        },
                    )

        self.stdout.write("Created subjects, topics, materials, and quiz questions.")

        # 3. Simulate initial progress and quiz attempts for student1
        # Topic 1: Introduction to Machine Learning -> Completed with 100% score
        t1 = Topic.objects.get(slug="intro-machine-learning")
        t1_questions = list(t1.questions.all())
        
        att1, _ = QuizAttempt.objects.get_or_create(
            student=student_user,
            topic=t1,
            difficulty=Topic.Difficulty.BEGINNER,
            defaults={
                "total_questions": len(t1_questions),
                "correct_answers": len(t1_questions),
                "score": 100.0,
                "started_at": timezone.now() - timedelta(days=2),
                "completed_at": timezone.now() - timedelta(days=2),
            },
        )
        for q in t1_questions:
            QuizResponse.objects.get_or_create(
                attempt=att1,
                question=q,
                defaults={"selected_option": q.correct_option, "is_correct": True},
            )
        TopicProgress.objects.get_or_create(
            student=student_user,
            topic=t1,
            defaults={
                "status": TopicProgress.Status.COMPLETED,
                "percent_complete": 100.0,
                "completed_at": timezone.now() - timedelta(days=2),
            },
        )

        # Topic 2: Linear Regression -> Weak score (33.3%) to test weak-topic review recommendation
        t2 = Topic.objects.get(slug="linear-regression-gradient-descent")
        t2_questions = list(t2.questions.all())
        att2, _ = QuizAttempt.objects.get_or_create(
            student=student_user,
            topic=t2,
            difficulty=Topic.Difficulty.INTERMEDIATE,
            defaults={
                "total_questions": len(t2_questions),
                "correct_answers": 1,
                "score": 33.33,
                "started_at": timezone.now() - timedelta(hours=5),
                "completed_at": timezone.now() - timedelta(hours=5),
            },
        )
        for idx, q in enumerate(t2_questions):
            # 1st correct, others incorrect
            sel = q.correct_option if idx == 0 else ("A" if q.correct_option != "A" else "B")
            QuizResponse.objects.get_or_create(
                attempt=att2,
                question=q,
                defaults={"selected_option": sel, "is_correct": (idx == 0)},
            )
        TopicProgress.objects.get_or_create(
            student=student_user,
            topic=t2,
            defaults={
                "status": TopicProgress.Status.IN_PROGRESS,
                "percent_complete": 50.0,
                "started_at": timezone.now() - timedelta(hours=6),
            },
        )

        # Topic: Python Collections -> Completed with 100% score
        t_py1 = Topic.objects.get(slug="python-collections-syntax")
        t_py1_q = list(t_py1.questions.all())
        att3, _ = QuizAttempt.objects.get_or_create(
            student=student_user,
            topic=t_py1,
            difficulty=Topic.Difficulty.BEGINNER,
            defaults={
                "total_questions": len(t_py1_q),
                "correct_answers": len(t_py1_q),
                "score": 100.0,
                "started_at": timezone.now() - timedelta(days=1),
                "completed_at": timezone.now() - timedelta(days=1),
            },
        )
        for q in t_py1_q:
            QuizResponse.objects.get_or_create(
                attempt=att3,
                question=q,
                defaults={"selected_option": q.correct_option, "is_correct": True},
            )
        TopicProgress.objects.get_or_create(
            student=student_user,
            topic=t_py1,
            defaults={
                "status": TopicProgress.Status.COMPLETED,
                "percent_complete": 100.0,
                "completed_at": timezone.now() - timedelta(days=1),
            },
        )

        # 4. Generate recommendations for student1
        recs = generate_recommendations_for_student(student_user)
        self.stdout.write(f"Generated {recs.count()} initial recommendations for student1.")

        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
