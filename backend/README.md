# Smart E-Learning Backend

This stage contains the Django project configuration and core database models.
The database is configured for MySQL through environment variables. API endpoints,
authentication flows, recommendation rules, and frontend integration are later
implementation stages.

## Windows PowerShell setup

Run these commands from the project root:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend\.env` and replace the placeholder secret and MySQL password with
values for your machine. Do not commit `.env`. Before applying migrations, create
the database and a dedicated MySQL user with permissions on that database. For a
MySQL installation supporting `utf8mb4`, run the following in a MySQL client,
replacing the sample password:

```sql
CREATE DATABASE smart_learning CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'smart_learning_user'@'127.0.0.1' IDENTIFIED BY 'replace-with-your-local-mysql-password';
GRANT ALL PRIVILEGES ON smart_learning.* TO 'smart_learning_user'@'127.0.0.1';
```

Then, while still in `backend` with the virtual environment activated, generate
and apply the initial migrations:

```powershell
python manage.py makemigrations learning
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The Django admin will be available at `http://127.0.0.1:8000/admin/`.

## Core data model

- `User` extends Django's `AbstractUser`, retains Django password hashing, and
  adds student, instructor, and admin roles.
- `Subject` contains a subject; `Topic` belongs to a subject and has a difficulty.
- `LearningMaterial` stores notes or a resource link for a topic.
- `TopicProgress` stores each student's status and completion percentage per topic.
- `QuizQuestion` stores a topic-linked multiple-choice question and explanation.
- `QuizAttempt` and `QuizResponse` store quiz scores and per-question answers.
- `Recommendation` stores a student's topic/material suggestion, reason, target
  difficulty, and priority. Rule-based generation is not implemented in this stage.

After migrations are applied, the admin site can be used to enter initial subjects,
topics, questions, materials, and test records. Seed data and API endpoints will be
added in later stages.
