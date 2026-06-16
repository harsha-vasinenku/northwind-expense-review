"""Seed 5 employees from submission JSON files on startup."""

import json
from pathlib import Path

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee

logger = structlog.get_logger(__name__)

SUBMISSIONS_DIR = Path(__file__).parent.parent.parent / "bundle" / "submissions"


async def seed_employees(session: AsyncSession) -> None:
    """Upsert all 5 employees from employee_info.json files."""
    json_files = list(SUBMISSIONS_DIR.rglob("employee_info.json"))

    for json_path in json_files:
        try:
            data = json.loads(json_path.read_text())
        except (json.JSONDecodeError, OSError):
            logger.exception("Failed to read employee JSON", path=str(json_path))
            continue

        emp_id = data.get("employee_id")
        if not emp_id:
            continue

        existing = await session.get(Employee, emp_id)
        if existing:
            continue

        employee = Employee(
            id=emp_id,
            name=data["name"],
            grade=data["grade"],
            title=data["title"],
            department=data["department"],
            manager_id=data.get("manager_id"),
            home_base=data["home_base"],
        )
        session.add(employee)
        logger.info("Employee seeded", id=emp_id, name=data["name"])

    await session.commit()

    result = await session.execute(select(Employee))
    count = len(result.scalars().all())
    logger.info("Employee seed complete", total=count)
