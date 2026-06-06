from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, date
from database import get_db
from models import WorkOrder, WorkOrderPart, Appointment, Technician, Part
from schemas import (
    WorkOrder as WorkOrderSchema,
    WorkOrderCreate,
    WorkOrderUpdate,
    WorkOrderPartCreate,
    DashboardStats
)

router = APIRouter()


@router.get("/", response_model=List[WorkOrderSchema])
def get_work_orders(
    status: str = None,
    technician_id: int = None,
    start_date: date = None,
    end_date: date = None,
    db: Session = Depends(get_db)
):
    query = db.query(WorkOrder).order_by(WorkOrder.created_at.desc())
    
    if status:
        query = query.filter(WorkOrder.status == status)
    if technician_id:
        query = query.filter(WorkOrder.technician_id == technician_id)
    if start_date:
        query = query.filter(WorkOrder.created_at >= start_date)
    if end_date:
        query = query.filter(WorkOrder.created_at <= end_date)
    
    return query.all()


@router.get("/{work_order_id}", response_model=WorkOrderSchema)
def get_work_order(work_order_id: int, db: Session = Depends(get_db)):
    work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not work_order:
        raise HTTPException(status_code=404, detail="工单不存在")
    return work_order


@router.post("/", response_model=WorkOrderSchema)
def create_work_order(work_order: WorkOrderCreate, db: Session = Depends(get_db)):
    appointment = db.query(Appointment).filter(Appointment.id == work_order.appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="预约不存在")
    
    if appointment.status == "completed":
        raise HTTPException(status_code=400, detail="该预约已完成，无法创建工单")
    
    existing_work_order = db.query(WorkOrder).filter(WorkOrder.appointment_id == work_order.appointment_id).first()
    if existing_work_order:
        raise HTTPException(status_code=400, detail="该预约已有工单")
    
    technician = db.query(Technician).filter(Technician.id == work_order.technician_id).first()
    if not technician:
        raise HTTPException(status_code=404, detail="技师不存在")
    
    if technician.status != "available":
        raise HTTPException(status_code=400, detail="该技师当前不可接单")
    
    db_work_order = WorkOrder(**work_order.model_dump())
    db.add(db_work_order)
    
    appointment.status = "confirmed"
    technician.status = "busy"
    
    db.commit()
    db.refresh(db_work_order)
    return db_work_order


@router.put("/{work_order_id}", response_model=WorkOrderSchema)
def update_work_order(
    work_order_id: int,
    work_order_update: WorkOrderUpdate,
    db: Session = Depends(get_db)
):
    db_work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not db_work_order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    update_data = work_order_update.model_dump(exclude_unset=True, exclude={"parts"})
    for key, value in update_data.items():
        setattr(db_work_order, key, value)
    
    if work_order_update.parts:
        for part_item in work_order_update.parts:
            part = db.query(Part).filter(Part.id == part_item.part_id).first()
            if not part:
                raise HTTPException(status_code=404, detail=f"配件ID {part_item.part_id} 不存在")
            
            if part.stock < part_item.quantity:
                raise HTTPException(status_code=400, detail=f"配件 {part.name} 库存不足")
            
            existing_part = db.query(WorkOrderPart).filter(
                WorkOrderPart.work_order_id == work_order_id,
                WorkOrderPart.part_id == part_item.part_id
            ).first()
            
            if existing_part:
                part.stock += existing_part.quantity
                existing_part.quantity = part_item.quantity
                existing_part.unit_price = part.price
                existing_part.subtotal = part.price * part_item.quantity
            else:
                work_order_part = WorkOrderPart(
                    work_order_id=work_order_id,
                    part_id=part_item.part_id,
                    quantity=part_item.quantity,
                    unit_price=part.price,
                    subtotal=part.price * part_item.quantity
                )
                db.add(work_order_part)
            
            part.stock -= part_item.quantity
    
    db.commit()
    db.refresh(db_work_order)
    
    parts_total = sum(p.subtotal for p in db_work_order.parts)
    db_work_order.total_amount = db_work_order.labor_cost + parts_total
    db.commit()
    
    return db_work_order


@router.put("/{work_order_id}/status")
def update_work_order_status(
    work_order_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    db_work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not db_work_order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    if status == "in_progress" and db_work_order.status == "assigned":
        db_work_order.actual_start = datetime.now()
    elif status == "completed":
        db_work_order.actual_end = datetime.now()
        db_work_order.appointment.status = "completed"
        db_work_order.technician.status = "available"
    
    db_work_order.status = status
    db.commit()
    db.refresh(db_work_order)
    return db_work_order


@router.post("/{work_order_id}/parts")
def add_work_order_part(
    work_order_id: int,
    part_data: WorkOrderPartCreate,
    db: Session = Depends(get_db)
):
    db_work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not db_work_order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    if db_work_order.status == "completed":
        raise HTTPException(status_code=400, detail="工单已完成，无法添加配件")
    
    part = db.query(Part).filter(Part.id == part_data.part_id).first()
    if not part:
        raise HTTPException(status_code=404, detail="配件不存在")
    
    if part.stock < part_data.quantity:
        raise HTTPException(status_code=400, detail="库存不足")
    
    existing_part = db.query(WorkOrderPart).filter(
        WorkOrderPart.work_order_id == work_order_id,
        WorkOrderPart.part_id == part_data.part_id
    ).first()
    
    if existing_part:
        part.stock += existing_part.quantity
        existing_part.quantity += part_data.quantity
        existing_part.subtotal = existing_part.quantity * existing_part.unit_price
    else:
        work_order_part = WorkOrderPart(
            work_order_id=work_order_id,
            part_id=part_data.part_id,
            quantity=part_data.quantity,
            unit_price=part.price,
            subtotal=part.price * part_data.quantity
        )
        db.add(work_order_part)
    
    part.stock -= part_data.quantity
    
    db.commit()
    db.refresh(db_work_order)
    
    parts_total = sum(p.subtotal for p in db_work_order.parts)
    db_work_order.total_amount = db_work_order.labor_cost + parts_total
    db.commit()
    
    return db_work_order


@router.delete("/{work_order_id}/parts/{part_id}")
def remove_work_order_part(
    work_order_id: int,
    part_id: int,
    db: Session = Depends(get_db)
):
    db_work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not db_work_order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    if db_work_order.status == "completed":
        raise HTTPException(status_code=400, detail="工单已完成，无法删除配件")
    
    work_order_part = db.query(WorkOrderPart).filter(
        WorkOrderPart.work_order_id == work_order_id,
        WorkOrderPart.part_id == part_id
    ).first()
    
    if not work_order_part:
        raise HTTPException(status_code=404, detail="该工单中无此配件")
    
    part = db.query(Part).filter(Part.id == part_id).first()
    part.stock += work_order_part.quantity
    
    db.delete(work_order_part)
    db.commit()
    db.refresh(db_work_order)
    
    parts_total = sum(p.subtotal for p in db_work_order.parts)
    db_work_order.total_amount = db_work_order.labor_cost + parts_total
    db.commit()
    
    return {"message": "配件已从工单中移除"}


@router.delete("/{work_order_id}")
def delete_work_order(work_order_id: int, db: Session = Depends(get_db)):
    db_work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not db_work_order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    if db_work_order.status in ["in_progress", "completed"]:
        raise HTTPException(status_code=400, detail="进行中或已完成的工单无法删除")
    
    for work_order_part in db_work_order.parts:
        part = db.query(Part).filter(Part.id == work_order_part.part_id).first()
        part.stock += work_order_part.quantity
        db.delete(work_order_part)
    
    if db_work_order.appointment:
        db_work_order.appointment.status = "pending"
    
    if db_work_order.technician:
        db_work_order.technician.status = "available"
    
    db.delete(db_work_order)
    db.commit()
    return {"message": "删除成功"}


@router.get("/statistics/dashboard", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    total_appointments = db.query(Appointment).count()
    pending_appointments = db.query(Appointment).filter(Appointment.status == "pending").count()
    today_appointments = db.query(Appointment).filter(
        Appointment.appointment_date >= today_start,
        Appointment.appointment_date <= today_end
    ).count()
    
    total_work_orders = db.query(WorkOrder).count()
    in_progress_work_orders = db.query(WorkOrder).filter(WorkOrder.status == "in_progress").count()
    completed_work_orders = db.query(WorkOrder).filter(WorkOrder.status == "completed").count()
    
    total_parts = db.query(Part).count()
    low_stock_parts = db.query(Part).filter(Part.stock <= Part.min_stock).count()
    
    total_revenue = db.query(func.sum(WorkOrder.total_amount)).filter(
        WorkOrder.status == "completed"
    ).scalar() or 0
    
    return DashboardStats(
        total_appointments=total_appointments,
        pending_appointments=pending_appointments,
        today_appointments=today_appointments,
        total_work_orders=total_work_orders,
        in_progress_work_orders=in_progress_work_orders,
        completed_work_orders=completed_work_orders,
        total_parts=total_parts,
        low_stock_parts=low_stock_parts,
        total_revenue=float(total_revenue)
    )


@router.get("/{work_order_id}/invoice")
def get_invoice(work_order_id: int, db: Session = Depends(get_db)):
    db_work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not db_work_order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    parts_list = [
        {
            "name": p.part.name,
            "code": p.part.code,
            "quantity": p.quantity,
            "unit": p.part.unit,
            "unit_price": p.unit_price,
            "subtotal": p.subtotal
        }
        for p in db_work_order.parts
    ]
    
    parts_total = sum(p.subtotal for p in db_work_order.parts)
    
    return {
        "work_order_id": db_work_order.id,
        "customer_name": db_work_order.appointment.customer.name,
        "customer_phone": db_work_order.appointment.customer.phone,
        "car_model": db_work_order.appointment.customer.car_model,
        "car_plate": db_work_order.appointment.customer.car_plate,
        "service_type": db_work_order.appointment.service_type,
        "technician_name": db_work_order.technician.name,
        "labor_cost": db_work_order.labor_cost,
        "parts": parts_list,
        "parts_total": parts_total,
        "total_amount": db_work_order.total_amount,
        "status": db_work_order.status,
        "created_at": db_work_order.created_at,
        "actual_start": db_work_order.actual_start,
        "actual_end": db_work_order.actual_end
    }
