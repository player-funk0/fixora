"""
python manage.py seed_demo

Creates demo users + realistic submission history for the analytics dashboard.
"""

import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from api.models import ErrorLog, Submission, User

LANGUAGES  = ["python", "javascript", "cpp", "java", "typescript"]
PLAN_DIST  = ["free"] * 7 + ["pro"] * 2 + ["enterprise"] * 1

ERROR_POOL = [
    ("Missing colon at end of function definition", "error"),
    ("Undefined variable referenced before assignment", "error"),
    ("Off-by-one error in loop bounds", "error"),
    ("Missing closing parenthesis", "error"),
    ("Assignment (=) used instead of comparison (==)", "error"),
    ("Division by zero possible", "warning"),
    ("Unreachable code after return statement", "warning"),
    ("Variable declared but never used", "warning"),
    ("Implicit type conversion may lose data", "warning"),
    ("Null pointer dereference not checked", "error"),
    ("Array index out of bounds", "error"),
    ("Infinite loop — condition never becomes False", "error"),
    ("Function called with wrong number of arguments", "error"),
    ("Missing import statement", "error"),
    ("Incorrect indentation breaks logic", "error"),
]


class Command(BaseCommand):
    help = "Seed the database with demo users and submission data."

    def add_arguments(self, parser):
        parser.add_argument("--users",    type=int, default=20,  help="Number of student accounts")
        parser.add_argument("--days",     type=int, default=30,  help="Days of history to generate")
        parser.add_argument("--clear",    action="store_true",   help="Clear existing demo data first")

    def handle(self, *args, **options):
        if options["clear"]:
            User.objects.filter(email__endswith="@demo.fixora").delete()
            self.stdout.write(self.style.WARNING("Cleared existing demo data."))

        n_users = options["users"]
        n_days  = options["days"]

        # ── Create teacher ────────────────────────────────────────────────────
        teacher, _ = User.objects.get_or_create(
            email="teacher@demo.fixora",
            defaults={
                "plan": "enterprise",
                "role": "teacher",
            },
        )
        teacher.set_password("teacher123")
        teacher.save()
        self.stdout.write(f"  ✓ Teacher: teacher@demo.fixora / teacher123")

        # ── Create admin ──────────────────────────────────────────────────────
        admin_user, _ = User.objects.get_or_create(
            email="admin@demo.fixora",
            defaults={
                "plan": "enterprise",
                "role": "admin",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin_user.set_password("admin123")
        admin_user.save()
        self.stdout.write(f"  ✓ Admin:   admin@demo.fixora / admin123")

        # ── Create students ───────────────────────────────────────────────────
        students = []
        for i in range(1, n_users + 1):
            email = f"student{i:02d}@demo.fixora"
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "plan": random.choice(PLAN_DIST),
                    "role": "student",
                },
            )
            if created:
                user.set_password("student123")
                user.save()
            students.append(user)

        self.stdout.write(f"  ✓ {n_users} student accounts (password: student123)")

        # ── Generate submissions ──────────────────────────────────────────────
        subs_created = 0
        now = timezone.now()

        for student in students:
            # Each student makes 2–12 submissions per week on average
            activity_level = random.uniform(0.3, 1.0)
            for day_offset in range(n_days, 0, -1):
                dt = now - timedelta(days=day_offset)
                n_subs = random.choices(
                    [0, 1, 2, 3, 4],
                    weights=[
                        1 - activity_level,
                        activity_level * 0.4,
                        activity_level * 0.3,
                        activity_level * 0.2,
                        activity_level * 0.1,
                    ],
                )[0]

                for _ in range(n_subs):
                    lang     = random.choice(LANGUAGES)
                    n_errors = max(0, int(random.gauss(2, 1.5)))
                    n_warns  = max(0, int(random.gauss(1, 0.8)))
                    learning = random.random() < 0.25

                    # Students get slightly better over time
                    improvement = day_offset / n_days   # 1.0 = oldest, 0.0 = today
                    n_errors = max(0, int(n_errors * (0.5 + improvement * 0.8)))

                    sub = Submission.objects.create(
                        user          = student,
                        language      = lang,
                        code_hash     = f"{random.randint(0, 0xFFFFFFFF):08x}",
                        code_length   = random.randint(80, 600),
                        error_count   = n_errors,
                        warning_count = n_warns,
                        learning_mode = learning,
                        via_upload    = random.random() < 0.15,
                        # Use timezone.datetime.replace to stay timezone-aware
                        submitted_at  = dt.replace(
                            hour=random.randint(8, 22),
                            minute=random.randint(0, 59),
                            second=random.randint(0, 59),
                        ),
                        response_ms   = random.randint(800, 3500),
                        ip_address    = f"10.0.{random.randint(0,255)}.{random.randint(1,254)}",
                    )
                    subs_created += 1

                    # Log individual errors
                    chosen_errors = random.sample(
                        ERROR_POOL, min(n_errors + n_warns, len(ERROR_POOL))
                    )
                    ErrorLog.objects.bulk_create([
                        ErrorLog(
                            submission  = sub,
                            error_type  = etype,
                            line_number = random.randint(1, 60),
                            title       = title,
                        )
                        for title, etype in chosen_errors
                    ])

        self.stdout.write(f"  ✓ {subs_created} submissions generated over {n_days} days")
        self.stdout.write(self.style.SUCCESS("\n🎉 Demo data seeded successfully!"))
        self.stdout.write("\nLogin credentials:")
        self.stdout.write("  Teacher:  teacher@demo.fixora / teacher123")
        self.stdout.write("  Admin:    admin@demo.fixora   / admin123")
        self.stdout.write("  Students: student01@demo.fixora … / student123")
