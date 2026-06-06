from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Technician, WorkOrder
from schemas import Technician as TechnicianSchema, TechnicianCreate

router = APIRouter()


@router.get("/", response_model=List[TechnicianSchema])
def get_technicians(status: str = None, db: Session = Depends(get_db)):
    query = db.query(Technician).order_by(Technician.created_at.desc())
    if status:
        query = query.filter(Technician.status == status)
    return query.all()


@router.get("/{technician_id}", response_model=TechnicianSchema)
def get_technician(technician_id: int, db: Session = Depends(get_db)):
    technician = db.query(Technician).filter(Technician.id == technician_id).first()
    if not technician:
        raise HTTPException(status_code=404, detail="技师不存在")
    return technician


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
