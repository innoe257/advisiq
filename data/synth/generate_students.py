"""Generate synthetic student records for AdvisIQ.

Every value is synthetic. Student codes and the demo tenant name carry a
SYNTH prefix so no output can be mistaken for real institutional data.

Usage:
    python generate_students.py                     # write data/synth/students.csv
    python generate_students.py --count 200          # generate a different count
    python generate_students.py --seed-db            # also insert into Postgres
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import random
import sys
from pathlib import Path
from typing import Any

PROGRAMMES = [
    "Computer Science",
    "Business Administration",
    "Nursing",
    "Mechanical Engineering",
    "Psychology",
    "Data Science",
    "Biology",
    "Economics",
]

OUTPUT_PATH = Path(__file__).resolve().parent / "students.csv"


def _generate_one(index: int, rng: random.Random) -> dict[str, Any]:
    year_of_study = rng.randint(1, 4)
    age = 17 + year_of_study + rng.randint(0, 3)

    # A latent "engagement" factor loosely drives GPA, attendance, and credit
    # completion together, so the dataset has realistic-ish correlations for
    # later use as ML training data (Phase 2) rather than pure independent noise.
    engagement = rng.betavariate(2, 2)

    gpa = round(min(4.0, max(0.0, rng.gauss(1.5 + 2.5 * engagement, 0.4))), 2)
    attendance_rate = round(min(1.0, max(0.0, rng.gauss(0.5 + 0.45 * engagement, 0.12))), 2)

    credits_attempted = year_of_study * 30
    completion_ratio = min(1.0, max(0.0, rng.gauss(0.6 + 0.35 * engagement, 0.1)))
    credits_completed = round(credits_attempted * completion_ratio)

    return {
        "synth_student_code": f"SYNTH-STU-{index:04d}",
        "programme": rng.choice(PROGRAMMES),
        "year_of_study": year_of_study,
        "gpa": gpa,
        "attendance_rate": attendance_rate,
        "credits_attempted": credits_attempted,
        "credits_completed": credits_completed,
        "age": age,
    }


def generate_students(count: int, *, seed: int | None = None) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    return [_generate_one(i, rng) for i in range(1, count + 1)]


def write_csv(students: list[dict[str, Any]], path: Path) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(students[0].keys()))
        writer.writeheader()
        writer.writerows(students)


async def seed_database(students: list[dict[str, Any]], tenant_name: str) -> None:
    # Imported lazily, and only for --seed-db, so generating a CSV never
    # requires the backend package or a running database.
    backend_root = Path(__file__).resolve().parent.parent.parent / "backend"
    sys.path.insert(0, str(backend_root))

    from sqlalchemy import select

    from app.database import AsyncSessionLocal
    from app.models.student import Student
    from app.models.tenant import Tenant

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Tenant).where(Tenant.name == tenant_name))
        tenant = result.scalar_one_or_none()
        if tenant is None:
            tenant = Tenant(name=tenant_name)
            db.add(tenant)
            await db.flush()

        for record in students:
            existing = await db.execute(
                select(Student).where(
                    Student.tenant_id == tenant.id,
                    Student.synth_student_code == record["synth_student_code"],
                )
            )
            if existing.scalar_one_or_none() is not None:
                continue
            db.add(Student(tenant_id=tenant.id, **record))

        await db.commit()

    print(f"Seeded {len(students)} students into tenant '{tenant_name}'.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=500, help="Number of students to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument(
        "--seed-db", action="store_true", help="Also insert the generated students into Postgres"
    )
    parser.add_argument(
        "--tenant-name",
        default="SYNTH Demo University",
        help="Tenant to seed students into when --seed-db is passed",
    )
    args = parser.parse_args()

    students = generate_students(args.count, seed=args.seed)
    write_csv(students, OUTPUT_PATH)
    print(f"Wrote {len(students)} synthetic students to {OUTPUT_PATH}")

    if args.seed_db:
        asyncio.run(seed_database(students, args.tenant_name))


if __name__ == "__main__":
    main()
