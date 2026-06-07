from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, date
from database import get_db
from models import Technician, WorkOrder
from schemas import (
    Technician as TechnicianSchema,
    TechnicianCreate,
    TechnicianDetail,
    TechnicianWithStats,
    TechnicianMonthStats
)

router = APIRouter()


def get_technician_month_stats(technician_id: int, db: Session) -> TechnicianMonthStats:
    today = date.today()
    month_start = datetime(today.year, today.month, 1)
    
    completed_orders = db.query(func.count(WorkOrder.id)).filter(
        WorkOrder.technician_id == technician_id,
        WorkOrder.status == "completed",
        WorkOrder.actual_end >= month_start
    ).scalar() or 0
    
    total_hours = db.query(func.sum(
        func.extract('epoch', WorkOrder.actual_end - WorkOrder.actual_start) / 3600
    )).filter(
        WorkOrder.technician_id == technician_id,
        WorkOrder.status == "completed",
        WorkOrder.actual_end >= month_start,
        WorkOrder.actual_start.isnot(None),
        WorkOrder.actual_end.isnot(None)
    ).scalar() or 0
    
    total_income = db.query(func.sum(WorkOrder.total_amount)).filter(
        WorkOrder.technician_id == technician_id,
        WorkOrder.status == "completed",
        WorkOrder.actual_end >= month_start
    ).scalar() or 0
    
    return TechnicianMonthStats(
        completed_orders=completed_orders,
        total_hours=round(float(total_hours), 2),
        total_income=round(float(total_income), 2)
    )


@router.get("/", response_model=List[TechnicianWithStats])
def get_technicians(
    status: Optional[str] = None,
    specialty: Optional[str] = None,
    sort_by: Optional[str] = "workload",
    db: Session = Depends(get_db)
):
    query = db.query(Technician)
    
    if status:
        query = query.filter(Technician.status == status)
    if specialty:
        query = query.filter(Technician.specialty == specialty)
    
    technicians = query.all()
    
    result = []
    for tech in technicians:
        month_stats = get_technician_month_stats(tech.id, db)
        tech_dict = {
            "id": tech.id,
            "name": tech.name,
            "phone": tech.phone,
            "specialty": tech.specialty,
            "status": tech.status,
            "created_at": tech.created_at,
            "month_stats": month_stats
        }
        result.append(tech_dict)
    
    if sort_by == "workload":
        result.sort(key=lambda x: x["month_stats"].completed_orders, reverse=True)
    elif sort_by == "hours":
        result.sort(key=lambda x: x["month_stats"].total_hours, reverse=True)
    elif sort_by == "income":
        result.sort(key=lambda x: x["month_stats"].total_income, reverse=True)
    elif sort_by == "name":
        result.sort(key=lambda x: x["name"])
    
    return result


@router.get("/{technician_id}", response_model=TechnicianSchema)
def get_technician(technician_id: int, db: Session = Depends(get_db)):
    technician = db.query(Technician).filter(Technician.id == technician_id).first()
    if not technician:
        raise HTTPException(status_code=404, detail="技师不存在")
    return technician


@router.get("/{technician_id}/detail", response_model=TechnicianDetail)
def get_technician_detail(technician_id: int, db: Session = Depends(get_db)):
    technician = db.query(Technician).filter(Technician.id == technician_id).first()
    if not technician:
        raise HTTPException(status_code=404, detail="技师不存在")
    
    month_stats = get_technician_month_stats(technician_id, db)
    
    return {
        "id": technician.id,
        "name": technician.name,
        "phone": technician.phone,
        "specialty": technician.specialty,
        "status": technician.status,
        "created_at": technician.created_at,
        "month_stats": month_stats
    }


@router.post("/", response_model=TechnicianSchema)
def create_technician(technician: TechnicianCreate, db: Session = Depends(get_db)):
    existing = db.query(Technician).filter(Technician.phone == technician.phone).first()
    if existing:
        raise HTTPException(status_code=400, detail="该手机号已注册")
    
    db_technician = Technician(**technician.model_dump())
    db.add(db_technician)
    db.commit()
    db.refresh(db_technician)
    return db_technician


@router.put("/{technician_id}", response_model=TechnicianSchema)
def update_technician(
    technician_id: int,
    technician: TechnicianCreate,
    db: Session = Depends(get_db)
):
    db_technician = db.query(Technician).filter(Technician.id == technician_id).first()
    if not db_technician:
        raise HTTPException(status_code=404, detail="技师不存在")
    
    for key, value in technician.model_dump().items():
        setattr(db_technician, key, value)
    
    db.commit()
    db.refresh(db_technician)
    return db_technician


@router.put("/{technician_id}/status")
def update_technician_status(
    technician_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    db_technician = db.query(Technician).filter(Technician.id == technician_id).first()
    if not db_technician:
        raise HTTPException(status_code=404, detail="技师不存在")
    
    db_technician.status = status
    db.commit()
    db.refresh(db_technician)
    return db_technician


@router.delete("/{technician_id}")
def delete_technician(technician_id: int, db: Session = Depends(get_db)):
    db_technician = db.query(Technician).filter(Technician.id == technician_id).first()
    if not db_technician:
        raise HTTPException(status_code=404, detail="技师不存在")
    
    work_orders = db.query(WorkOrder).filter(
        WorkOrder.technician_id == technician_id,
        WorkOrder.status.in_(["assigned", "in_progress"])
    ).first()
    
    if work_orders:
        raise HTTPException(status_code=400, detail="该技师有未完成的工单，无法删除")
    
    db.delete(db_technician)
    db.commit()
    return {"message": "删除成功"}


@router.get("/{technician_id}/work-orders")
def get_technician_work_orders(
    technician_id: int,
    status: str = None,
    db: Session = Depends(get_db)
):
    db_technician = db.query(Technician).filter(Technician.id == technician_id).first()
    if not db_technician:
        raise HTTPException(status_code=404, detail="技师不存在")
    
    query = db.query(WorkOrder).filter(WorkOrder.technician_id == technician_id)
    if status:
        query = query.filter(WorkOrder.status == status)
    
    return query.order_by(WorkOrder.created_at.desc()).all()


@router.get("/statistics/summary")
def get_technician_statistics(db: Session = Depends(get_db)):
    total = db.query(Technician).count()
    available = db.query(Technician).filter(Technician.status == "available").count()
    busy = db.query(Technician).filter(Technician.status == "busy").count()
    off_duty = db.query(Technician).filter(Technician.status == "off_duty").count()
    
    return {
        "total": total,
        "available": available,
        "busy": busy,
        "off_duty": off_duty
    }
