from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from database import get_db
from models import Vehicle, Customer, Appointment, WorkOrder, WorkOrderPart
from schemas import (
    Vehicle as VehicleSchema,
    VehicleCreate,
    VehicleUpdate,
    MaintenanceRecord,
    VehicleMaintenanceTimeline,
    MaintenanceRecordPart
)

router = APIRouter()


@router.get("/", response_model=List[VehicleSchema])
def get_vehicles(
    customer_id: Optional[int] = None,
    car_plate: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Vehicle).order_by(Vehicle.created_at.desc())
    
    if customer_id:
        query = query.filter(Vehicle.customer_id == customer_id)
    if car_plate:
        query = query.filter(Vehicle.car_plate.contains(car_plate))
    
    return query.all()


@router.get("/{vehicle_id}", response_model=VehicleSchema)
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="车辆不存在")
    return vehicle


@router.post("/", response_model=VehicleSchema)
def create_vehicle(vehicle: VehicleCreate, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == vehicle.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    
    existing_vehicle = db.query(Vehicle).filter(Vehicle.car_plate == vehicle.car_plate).first()
    if existing_vehicle:
        raise HTTPException(status_code=400, detail="该车牌号已存在")
    
    db_vehicle = Vehicle(**vehicle.model_dump())
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle


@router.put("/{vehicle_id}", response_model=VehicleSchema)
def update_vehicle(
    vehicle_id: int,
    vehicle_update: VehicleUpdate,
    db: Session = Depends(get_db)
):
    db_vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not db_vehicle:
        raise HTTPException(status_code=404, detail="车辆不存在")
    
    update_data = vehicle_update.model_dump(exclude_unset=True)
    
    if "car_plate" in update_data and update_data["car_plate"] != db_vehicle.car_plate:
        existing_vehicle = db.query(Vehicle).filter(
            Vehicle.car_plate == update_data["car_plate"],
            Vehicle.id != vehicle_id
        ).first()
        if existing_vehicle:
            raise HTTPException(status_code=400, detail="该车牌号已存在")
    
    for key, value in update_data.items():
        setattr(db_vehicle, key, value)
    
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle


@router.delete("/{vehicle_id}")
def delete_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    db_vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not db_vehicle:
        raise HTTPException(status_code=404, detail="车辆不存在")
    
    appointments = db.query(Appointment).filter(Appointment.vehicle_id == vehicle_id).count()
    if appointments > 0:
        raise HTTPException(status_code=400, detail="该车辆已有预约记录，无法删除")
    
    db.delete(db_vehicle)
    db.commit()
    return {"message": "删除成功"}


def _build_maintenance_record(appointment, work_order=None):
    parts = []
    parts_total = 0
    labor_cost = 0
    total_amount = 0
    
    if work_order:
        labor_cost = work_order.labor_cost or 0
        for wp in work_order.parts:
            part_item = MaintenanceRecordPart(
                part_id=wp.part_id,
                part_name=wp.part.name,
                part_code=wp.part.code,
                quantity=wp.quantity,
                unit_price=wp.unit_price,
                subtotal=wp.subtotal
            )
            parts.append(part_item)
            parts_total += wp.subtotal
        total_amount = work_order.total_amount or 0
    
    record_type = "work_order" if work_order else "appointment"
    status = work_order.status if work_order else appointment.status
    
    return MaintenanceRecord(
        id=work_order.id if work_order else appointment.id,
        type=record_type,
        service_type=appointment.service_type,
        description=appointment.description,
        date=work_order.actual_end if work_order and work_order.actual_end else appointment.appointment_date,
        status=status,
        technician_name=work_order.technician.name if work_order and work_order.technician else None,
        labor_cost=labor_cost,
        parts_total=parts_total,
        total_amount=total_amount,
        mileage=appointment.vehicle.mileage if appointment.vehicle else None,
        notes=work_order.notes if work_order else None,
        parts=parts,
        appointment_id=appointment.id,
        work_order_id=work_order.id if work_order else None
    )


@router.get("/{vehicle_id}/maintenance-timeline", response_model=VehicleMaintenanceTimeline)
def get_vehicle_maintenance_timeline(
    vehicle_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    service_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="车辆不存在")
    
    appointments = db.query(Appointment).filter(
        Appointment.vehicle_id == vehicle_id
    ).order_by(Appointment.appointment_date.desc()).all()
    
    records = []
    total_cost = 0
    
    for apt in appointments:
        if start_date or end_date or service_type:
            apt_date = apt.appointment_date.date()
            if start_date and apt_date < start_date:
                continue
            if end_date and apt_date > end_date:
                continue
            if service_type and apt.service_type != service_type:
                continue
        
        work_order = apt.work_order if hasattr(apt, 'work_order') else None
        record = _build_maintenance_record(apt, work_order)
        records.append(record)
        
        if work_order and work_order.status == "completed":
            total_cost += work_order.total_amount or 0
    
    dates = [r.date for r in records]
    first_date = min(dates) if dates else None
    last_date = max(dates) if dates else None
    
    return VehicleMaintenanceTimeline(
        vehicle_id=vehicle.id,
        car_model=vehicle.car_model,
        car_plate=vehicle.car_plate,
        vin=vehicle.vin,
        total_maintenance_count=len(records),
        total_cost=total_cost,
        first_maintenance_date=first_date,
        last_maintenance_date=last_date,
        records=records
    )


@router.get("/{vehicle_id}/service-types")
def get_vehicle_service_types(vehicle_id: int, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="车辆不存在")
    
    service_types = db.query(Appointment.service_type).filter(
        Appointment.vehicle_id == vehicle_id
    ).distinct().all()
    
    return [st[0] for st in service_types]
