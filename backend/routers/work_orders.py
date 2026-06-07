from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, update
from typing import List
from datetime import datetime, date
from database import get_db
from models import WorkOrder, WorkOrderPart, Appointment, Technician, Part, MaintenancePackage, MaintenancePackagePart
from schemas import (
    WorkOrder as WorkOrderSchema,
    WorkOrderCreate,
    WorkOrderUpdate,
    WorkOrderPartCreate,
    WorkOrderPartUpdate,
    DashboardStats
)

router = APIRouter()


def _deduct_stock_atomic(db: Session, part_id: int, quantity: int) -> Part:
    stmt = (
        update(Part)
        .where(Part.id == part_id, Part.stock >= quantity)
        .values(stock=Part.stock - quantity)
        .execution_options(synchronize_session="fetch")
    )
    result = db.execute(stmt)
    if result.rowcount == 0:
        part = db.query(Part).filter(Part.id == part_id).first()
        part_name = part.name if part else f"ID {part_id}"
        raise HTTPException(status_code=400, detail=f"配件 {part_name} 库存不足")
    return db.query(Part).filter(Part.id == part_id).first()


def _add_stock_atomic(db: Session, part_id: int, quantity: int) -> Part:
    stmt = (
        update(Part)
        .where(Part.id == part_id)
        .values(stock=Part.stock + quantity)
        .execution_options(synchronize_session="fetch")
    )
    db.execute(stmt)
    return db.query(Part).filter(Part.id == part_id).first()


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
        start_datetime = datetime.combine(start_date, datetime.min.time())
        query = query.filter(WorkOrder.created_at >= start_datetime)
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        query = query.filter(WorkOrder.created_at <= end_datetime)
    
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
    
    package_id = None
    package_price = None
    total_amount = 0
    
    if appointment.package_id:
        package = db.query(MaintenancePackage).filter(
            MaintenancePackage.id == appointment.package_id,
            MaintenancePackage.is_active == 1
        ).first()
        if package:
            package_id = package.id
            package_price = package.package_price
            total_amount = package_price
    
    db_work_order = WorkOrder(
        **work_order.model_dump(),
        package_id=package_id,
        package_price=package_price,
        total_amount=total_amount
    )
    db.add(db_work_order)
    db.flush()
    
    if package_id:
        package_parts = db.query(MaintenancePackagePart).filter(
            MaintenancePackagePart.package_id == package_id
        ).all()
        
        for pkg_part in package_parts:
            part = db.query(Part).filter(Part.id == pkg_part.part_id).first()
            if part:
                _deduct_stock_atomic(db, pkg_part.part_id, pkg_part.quantity)
                work_order_part = WorkOrderPart(
                    work_order_id=db_work_order.id,
                    part_id=pkg_part.part_id,
                    quantity=pkg_part.quantity,
                    unit_price=part.price,
                    subtotal=part.price * pkg_part.quantity
                )
                db.add(work_order_part)
    
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
        existing_parts = {wp.part_id: wp for wp in db_work_order.parts}
        
        for part_item in work_order_update.parts:
            part = db.query(Part).filter(Part.id == part_item.part_id).first()
            if not part:
                raise HTTPException(status_code=404, detail=f"配件ID {part_item.part_id} 不存在")
            
            unit_price = getattr(part_item, 'unit_price', None) or part.price
            existing_part = existing_parts.get(part_item.part_id)
            
            if existing_part:
                quantity_diff = part_item.quantity - existing_part.quantity
                if quantity_diff > 0:
                    _deduct_stock_atomic(db, part_item.part_id, quantity_diff)
                elif quantity_diff < 0:
                    _add_stock_atomic(db, part_item.part_id, -quantity_diff)
                existing_part.quantity = part_item.quantity
                existing_part.unit_price = unit_price
                existing_part.subtotal = unit_price * part_item.quantity
            else:
                _deduct_stock_atomic(db, part_item.part_id, part_item.quantity)
                work_order_part = WorkOrderPart(
                    work_order_id=work_order_id,
                    part_id=part_item.part_id,
                    quantity=part_item.quantity,
                    unit_price=unit_price,
                    subtotal=unit_price * part_item.quantity
                )
                db.add(work_order_part)
    
    if work_order_update.package_price is not None:
        db_work_order.package_price = work_order_update.package_price
    
    db.commit()
    db.refresh(db_work_order)
    
    if db_work_order.package_id and db_work_order.package_price is not None:
        db_work_order.total_amount = db_work_order.package_price
    else:
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
    
    unit_price = part_data.unit_price if part_data.unit_price is not None else part.price
    
    existing_part = db.query(WorkOrderPart).filter(
        WorkOrderPart.work_order_id == work_order_id,
        WorkOrderPart.part_id == part_data.part_id
    ).first()
    
    if existing_part:
        _deduct_stock_atomic(db, part_data.part_id, part_data.quantity)
        existing_part.quantity += part_data.quantity
        existing_part.unit_price = unit_price
        existing_part.subtotal = existing_part.quantity * unit_price
    else:
        _deduct_stock_atomic(db, part_data.part_id, part_data.quantity)
        work_order_part = WorkOrderPart(
            work_order_id=work_order_id,
            part_id=part_data.part_id,
            quantity=part_data.quantity,
            unit_price=unit_price,
            subtotal=unit_price * part_data.quantity
        )
        db.add(work_order_part)
    
    db.commit()
    db.refresh(db_work_order)
    
    if db_work_order.package_id and db_work_order.package_price is not None:
        db_work_order.total_amount = db_work_order.package_price
    else:
        parts_total = sum(p.subtotal for p in db_work_order.parts)
        db_work_order.total_amount = db_work_order.labor_cost + parts_total
    db.commit()
    
    return db_work_order


@router.put("/{work_order_id}/parts/{part_id}")
def update_work_order_part(
    work_order_id: int,
    part_id: int,
    part_data: WorkOrderPartUpdate,
    db: Session = Depends(get_db)
):
    db_work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not db_work_order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    if db_work_order.status == "completed":
        raise HTTPException(status_code=400, detail="工单已完成，无法修改配件")
    
    work_order_part = db.query(WorkOrderPart).filter(
        WorkOrderPart.work_order_id == work_order_id,
        WorkOrderPart.part_id == part_id
    ).first()
    
    if not work_order_part:
        raise HTTPException(status_code=404, detail="该工单中无此配件")
    
    part = db.query(Part).filter(Part.id == part_id).first()
    
    if part_data.quantity is not None:
        quantity_diff = part_data.quantity - work_order_part.quantity
        if quantity_diff > 0:
            _deduct_stock_atomic(db, part_id, quantity_diff)
        elif quantity_diff < 0:
            _add_stock_atomic(db, part_id, -quantity_diff)
        work_order_part.quantity = part_data.quantity
    
    if part_data.unit_price is not None:
        work_order_part.unit_price = part_data.unit_price
    
    work_order_part.subtotal = work_order_part.quantity * work_order_part.unit_price
    
    db.commit()
    db.refresh(db_work_order)
    
    if db_work_order.package_id and db_work_order.package_price is not None:
        db_work_order.total_amount = db_work_order.package_price
    else:
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
    
    _add_stock_atomic(db, part_id, work_order_part.quantity)
    
    db.delete(work_order_part)
    db.commit()
    db.refresh(db_work_order)
    
    if db_work_order.package_id and db_work_order.package_price is not None:
        db_work_order.total_amount = db_work_order.package_price
    else:
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
        _add_stock_atomic(db, work_order_part.part_id, work_order_part.quantity)
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
    low_stock_parts_list = db.query(Part).filter(Part.stock <= Part.min_stock).order_by(Part.stock.asc()).all()
    low_stock_parts = len(low_stock_parts_list)
    
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
        total_revenue=float(total_revenue),
        low_stock_parts_list=low_stock_parts_list
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
            "specification": p.part.specification,
            "quantity": p.quantity,
            "unit": p.part.unit,
            "unit_price": p.unit_price,
            "subtotal": p.subtotal
        }
        for p in db_work_order.parts
    ]
    
    parts_total = sum(p.subtotal for p in db_work_order.parts)
    
    car_model = None
    car_plate = None
    if db_work_order.appointment and db_work_order.appointment.vehicle:
        car_model = db_work_order.appointment.vehicle.car_model
        car_plate = db_work_order.appointment.vehicle.car_plate
    
    package_name = None
    package_price = None
    if db_work_order.package:
        package_name = db_work_order.package.name
        package_price = db_work_order.package_price
    
    return {
        "work_order_id": db_work_order.id,
        "customer_name": db_work_order.appointment.customer.name,
        "customer_phone": db_work_order.appointment.customer.phone,
        "car_model": car_model,
        "car_plate": car_plate,
        "service_type": db_work_order.appointment.service_type,
        "technician_name": db_work_order.technician.name,
        "package_name": package_name,
        "package_price": package_price,
        "labor_cost": db_work_order.labor_cost,
        "parts": parts_list,
        "parts_total": parts_total,
        "total_amount": db_work_order.total_amount,
        "status": db_work_order.status,
        "created_at": db_work_order.created_at,
        "actual_start": db_work_order.actual_start,
        "actual_end": db_work_order.actual_end
    }
