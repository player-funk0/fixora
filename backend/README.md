# Fixora — AI Code Correction Platform

> **Django + Claude AI + SQLite + Monaco Editor + React**

---

## Architecture

```
fixora_django/
├── fixora/               # Django project config
│   ├── settings.py       # All settings (env-driven)
│   ├── urls.py           # Root URL routing
│   └── wsgi.py
├── api/                  # Core app
│   ├── models.py         # User, Submission, ErrorLog, DailyUsage
│   ├── views.py          # All API endpoints
│   ├── serializers.py    # DRF serializers + validation
│   ├── services.py       # Claude AI calls, rate-limit logic, file validation
│   ├── permissions.py    # IsTeacherOrAdmin, IsOwnerOrTeacher
│   ├── admin.py          # Django admin registrations
│   ├── urls/
│   │   ├── auth.py       # /api/auth/* routes
│   │   └── core.py       # /api/analyze, /api/usage, etc.
│   └── management/
│       └── commands/
│           └── seed_demo.py   # Demo data generator
├── analytics/            # Teacher analytics app
│   ├── views.py          # Overview, language breakdown, user progress
│   └── urls.py
├── frontend/
│   └── fixora.jsx        # React frontend (Monaco Editor, file upload, auth)
├── requirements.txt
├── manage.py
├── setup.sh              # One-command setup
└── .env.example
```

---

## Quick Start

### 1 · Clone & setup

```bash
git clone <your-repo>
cd fixora_django
bash setup.sh
```

The setup script will:
- Create a Python virtual environment
- Install all dependencies
- Run database migrations
- Optionally create a superuser
- Optionally seed 20 demo students with 30 days of submission history

### 2 · Configure environment

Edit `.env`:

```env
# No API key needed — AI responses are mocked.
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_PATH=db.sqlite3
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

### 3 · Run the server

```bash
source .venv/bin/activate
python manage.py runserver
```

API runs at: `http://localhost:8000`  
Admin panel: `http://localhost:8000/admin/`

### 4 · Connect the frontend

```bash
cd frontend
npm install          # React + Vite project of your choice
npm run dev          # Runs at http://localhost:3000
```

Copy `fixora.jsx` into your React project's `src/` directory and use it as the root component.

---

## API Reference

### Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Create account (`email`, `password`, `role`) |
| POST | `/api/auth/login/` | Get JWT tokens |
| POST | `/api/auth/logout/` | Blacklist refresh token |
| POST | `/api/auth/refresh/` | Refresh access token |
| GET  | `/api/auth/me/` | Current user info |

### Core

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/analyze/` | Analyze code (`code`, `language`, `learningMode`) |
| POST | `/api/analyze/upload/` | Analyze uploaded file (multipart: `file`, `learningMode`) |
| GET  | `/api/usage/` | Daily usage status |
| POST | `/api/upgrade/` | Change plan (`plan`: free/pro/enterprise) |
| GET  | `/api/health/` | Health check |

### Analytics (teacher/admin only)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics/overview/?days=7` | Platform-wide stats |
| GET | `/api/analytics/languages/?days=7` | Submissions by language |
| GET | `/api/analytics/top-errors/?days=7&limit=10` | Most common mistakes |
| GET | `/api/analytics/daily/?days=14` | Daily activity chart data |
| GET | `/api/analytics/users/` | All students with stats |
| GET | `/api/analytics/users/<id>/` | Individual student detail + progress |
| GET | `/api/analytics/quota/` | Today's usage by user key |

---

## Plans & Rate Limits

| Plan | Daily Analyses | Price |
|------|---------------|-------|
| Free | 5 / day | $0 |
| Pro  | Unlimited | $9/mo |
| Enterprise | Unlimited | $29/mo |

Rate limits are tracked per user ID (authenticated) or hashed IP (guest). Implemented atomically in Django ORM using `select_for_update()`.

---

## Database Schema

**users** — Custom AbstractBaseUser with `plan` + `role` fields  
**submissions** — Every analysis: language, error counts, response time, IP  
**error_logs** — Individual errors per submission (type, line, title)  
**daily_usage** — Per-user per-day counter for freemium enforcement  

---

## Supported Languages

Python · JavaScript · TypeScript · C++ · C · Java · Go · Rust · C# · Ruby

File upload auto-detects language from extension.

---

## Features

### Monaco Editor
- VS Code-quality syntax highlighting for all supported languages
- Custom `fixora-dark` theme with green cursor + line numbers
- Font ligatures, smooth cursor animation, drag-and-drop support

### File Upload
- Drag & drop onto the editor area
- Click "📁 Upload" button
- Auto language detection from file extension
- 50,000 character limit with clear error messages

### Learning Mode 🎓
- Toggle per-submission
- Claude returns 3 progressive thinking hints instead of the full fix
- Corrected code is hidden until the user turns off Learning Mode
- Logged in `submissions.learning_mode` for analytics

### Teacher Analytics
- Overview: total submissions, avg errors, unique users, response times
- Language breakdown chart data
- Top 10 most common errors across all students
- Per-student progress curve (are they making fewer errors over time?)
- Daily activity feed

---

## Production Deployment

```bash
# Switch to PostgreSQL in settings.py:
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST", "localhost"),
    }
}

# Collect static files
python manage.py collectstatic

# Run with gunicorn
gunicorn fixora.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

Add your payment provider (Stripe) to the `/api/upgrade/` endpoint to monetize the Pro plan.

---

## Demo Credentials (after running seed_demo)

| Role | Email | Password |
|------|-------|----------|
| Teacher | teacher@demo.fixora | teacher123 |
| Admin | admin@demo.fixora | admin123 |
| Student | student01@demo.fixora | student123 |
