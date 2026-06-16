"""Employee endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.employee import Employee
from app.schemas.employee import EmployeeCreate, EmployeeOut

router = APIRouter(prefix="/api/employees", tags=["employees"])


@router.get("", response_model=list[EmployeeOut])
async def list_employees(session: AsyncSession = Depends(get_session)) -> list[Employee]:
    """Return all employees."""
    result = await session.execute(select(Employee).order_by(Employee.name))
    return list(result.scalars().all())


@router.get("/{employee_id}", response_model=EmployeeOut)
async def get_employee(
    employee_id: str,
    session: AsyncSession = Depends(get_session),
) -> Employee:
    """Return a single employee by ID."""
    emp = await session.get(Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")
    return emp


@router.post("", response_model=EmployeeOut, status_code=201)
async def create_employee(
    payload: EmployeeCreate,
    session: AsyncSession = Depends(get_session),
) -> Employee:
    """Create a new employee."""
    existing = await session.get(Employee, payload.id)
    if existing:
        raise HTTPException(status_code=409, detail=f"Employee {payload.id} already exists")

    employee = Employee(**payload.model_dump())
    session.add(employee)
    await session.commit()
    await session.refresh(employee)
    return employee
