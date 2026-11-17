import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.monitor import MonitorCreate, MonitorResponse, MonitorUpdate
from app.services import monitor_service

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
