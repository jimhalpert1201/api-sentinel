import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.check_result import CheckResult
from app.models.user import User
from app.schemas.check_result import CheckResultResponse
from app.schemas.common import PaginatedResponse
from app.schemas.monitor import MonitorCreate, MonitorResponse, MonitorUpdate
from app.services import check_service, monitor_service

router = APIRouter()


@router.post(
    "",
    response_model=MonitorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new monitor",
)
def create_monitor(
    data: MonitorCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new monitor for current user."""
    return monitor_service.create_monitor(db=db, user_id=current_user.id, data=data)


@router.get(
    "",
    response_model=list[MonitorResponse],
    summary="List all monitors",
)
def list_monitors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all monitors owned by current user."""
    return monitor_service.list_monitors(db=db, user_id=current_user.id)


@router.get(
    "/{id}",
    response_model=MonitorResponse,
    summary="Get monitor details",
)
def get_monitor(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get details of a single monitor."""
    monitor = monitor_service.get_monitor(db=db, monitor_id=id, user_id=current_user.id)
    if not monitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitor not found",
        )
    return monitor


@router.patch(
    "/{id}",
    response_model=MonitorResponse,
    summary="Update monitor",
)
def update_monitor(
    id: uuid.UUID,
    data: MonitorUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Partially update an existing monitor."""
    monitor = monitor_service.get_monitor(db=db, monitor_id=id, user_id=current_user.id)
    if not monitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitor not found",
        )
    return monitor_service.update_monitor(db=db, monitor=monitor, data=data)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete monitor",
)
def delete_monitor(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a monitor and all associated checks and incidents."""
    monitor = monitor_service.get_monitor(db=db, monitor_id=id, user_id=current_user.id)
    if not monitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitor not found",
        )
    monitor_service.delete_monitor(db=db, monitor=monitor)


@router.post(
    "/{id}/check",
    response_model=CheckResultResponse,
    summary="Trigger manual health check",
)
async def trigger_manual_check(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Trigger an immediate manual health check for an owned monitor."""
    monitor = monitor_service.get_monitor(db=db, monitor_id=id, user_id=current_user.id)
    if not monitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitor not found",
        )
    return await check_service.run_monitor_check(db=db, monitor=monitor)


@router.get(
    "/{id}/checks",
    response_model=PaginatedResponse[CheckResultResponse],
    summary="Get monitor check history",
)
def get_monitor_checks(
    id: uuid.UUID,
    is_successful: bool | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve paginated historical check results with date range and status filtering."""
    monitor = monitor_service.get_monitor(db=db, monitor_id=id, user_id=current_user.id)
    if not monitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitor not found",
        )

    query = db.query(CheckResult).filter(CheckResult.monitor_id == monitor.id)

    if is_successful is not None:
        query = query.filter(CheckResult.is_successful == is_successful)
    if from_date is not None:
        query = query.filter(CheckResult.checked_at >= from_date)
    if to_date is not None:
        query = query.filter(CheckResult.checked_at <= to_date)

    total = query.count()
    items = (
        query.order_by(CheckResult.checked_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )
