# Fixora — AI Code Correction Platform

```
fixora/
├── backend/    Django REST API + SQLite analytics
└── frontend/   React + Vite + Monaco Editor
```

---

## Quick Start

### 1 · Backend

```bash
cd backend

# Create virtual environment & install deps
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env → set ANTHROPIC_API_KEY

# Run migrations & seed demo data
python manage.py migrate
python manage.py seed_demo         # optional: 20 demo students + 30 days history

# Start server (runs on http://localhost:8000)
python manage.py runserver
```

Or use the one-command setup script:
```bash
cd backend && bash setup.sh
```

---

### 2 · Frontend

```bash
cd frontend
npm install
npm run dev        # runs on http://localhost:3000
```

Open **http://localhost:3000** — the Vite dev server proxies all `/api/*`
requests to Django automatically, so no CORS setup needed.

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/register/` | — | Create account |
| POST | `/api/auth/login/` | — | Get JWT tokens |
| POST | `/api/auth/logout/` | ✓ | Blacklist refresh token |
| POST | `/api/auth/refresh/` | — | Refresh access token |
| GET  | `/api/auth/me/` | ✓ | Current user info |
| POST | `/api/analyze/` | optional | Analyze code |
| POST | `/api/analyze/upload/` | optional | Analyze uploaded file |
| GET  | `/api/usage/` | optional | Daily usage status |
| POST | `/api/upgrade/` | ✓ | Change plan |
| GET  | `/api/health/` | — | Health check |
| GET  | `/api/analytics/overview/` | teacher | Platform stats |
| GET  | `/api/analytics/languages/` | teacher | By language |
| GET  | `/api/analytics/top-errors/` | teacher | Most common errors |
| GET  | `/api/analytics/daily/` | teacher | Daily activity |
| GET  | `/api/analytics/users/` | teacher | Student list |
| GET  | `/api/analytics/users/<id>/` | teacher | Student detail |
| GET  | `/api/analytics/quota/` | teacher | Today's quota usage |

---

## Plans

| Plan | Daily Analyses |
|------|---------------|
| Free | 5 / day |
| Pro  | Unlimited |
| Enterprise | Unlimited |

---

## Demo Accounts (after `seed_demo`)

| Role | Email | Password |
|------|-------|----------|
| Teacher | teacher@demo.fixora | teacher123 |
| Admin   | admin@demo.fixora   | admin123   |
| Student | student01@demo.fixora | student123 |

Django admin panel: **http://localhost:8000/admin/**

---

## Supported Languages

Python · JavaScript · TypeScript · C++ · C · Java · Go · Rust · C# · Ruby

File upload auto-detects language from extension:
`.py .js .ts .cpp .cc .c .java .go .rs .cs .rb`
