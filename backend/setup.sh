#!/usr/bin/env bash
# ────────────────────────────────────────────
# Fixora — One-command Django backend setup
# Usage: bash setup.sh
# ────────────────────────────────────────────
set -e

echo ""
echo "██████╗ ██╗██╗  ██╗ ██████╗ ██████╗  █████╗ "
echo "██╔════╝██║╚██╗██╔╝██╔═══██╗██╔══██╗██╔══██╗"
echo "█████╗  ██║ ╚███╔╝ ██║   ██║██████╔╝███████║"
echo "██╔══╝  ██║ ██╔██╗ ██║   ██║██╔══██╗██╔══██║"
echo "██║     ██║██╔╝ ██╗╚██████╔╝██║  ██║██║  ██║"
echo "╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝"
echo ""
echo "Django Backend Setup"
echo "───────────────────────────────────────"

# 1. Check Python
python3 --version || { echo "❌ Python 3 not found"; exit 1; }

# 2. Create venv
if [ ! -d ".venv" ]; then
  echo "→ Creating virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate

# 3. Install deps
echo "→ Installing dependencies..."
pip install -q -r requirements.txt

# 4. Create .env if missing
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo ""
  echo "⚠️  Created .env from template."
  echo ""
fi

# 5. Migrate
echo "→ Running database migrations..."
python manage.py migrate --run-syncdb

# 6. Create superuser (optional)
read -p "→ Create a superuser now? [y/N] " CREATE_SUPER
if [[ "$CREATE_SUPER" =~ ^[Yy]$ ]]; then
  python manage.py createsuperuser
fi

# 7. Seed demo data (optional)
read -p "→ Seed demo data (20 students, 30 days history)? [y/N] " SEED
if [[ "$SEED" =~ ^[Yy]$ ]]; then
  python manage.py seed_demo
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Start the server:    source .venv/bin/activate && python manage.py runserver"
echo "Admin panel:         http://localhost:8000/admin/"
echo "API base:            http://localhost:8000/api/"
echo ""
