from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from database import get_db
from models import Customer, Vehicle, Appointment, WorkOrder
from schemas import (
    Customer as CustomerSchema,
    CustomerCreate,
    CustomerDetail,
    VehicleMaintenanceTimeline,
    MaintenanceRecord,
    MaintenanceRecordPart
)

router = APIRouter()


@router.get("/", response_model=List[CustomerSchema])
def get_customers(
    name: Optional[str] = None,
    phone: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Customer).order_by(Customer.created_at.desc())
    
    if name:
        query = query.filter(Customer.name.contains(name))
    if phone:
        query = query.filter(Customer.phone.contains(phone))
    
    return query.all()


@router.get("/{customer_id}", response_model=CustomerDetail)
def get_customer_detail(
    customer_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    service_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    
    vehicles_timeline = []
    total_maintenance_count = 0
    total_cost = 0
    
    for vehicle in customer.vehicles:
        appointments = db.query(Appointment).filter(
            Appointment.vehicle_id == vehicle.id
        ).order_by(Appointment.appointment_date.desc()).all()
        
        records = []
        vehicle_total_cost = 0
        
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
                vehicle_total_cost += work_order.total_amount or 0
        
        dates = [r.date for r in records]
        first_date = min(dates) if dates else None
        last_date = max(dates) if dates else None
        
        vehicle_timeline = VehicleMaintenanceTimeline(
            vehicle_id=vehicle.id,
            car_model=vehicle.car_model,
            car_plate=vehicle.car_plate,
            vin=vehicle.vin,
            total_maintenance_count=len(records),
            total_cost=vehicle_total_cost,
            first_maintenance_date=first_date,
            last_maintenance_date=last_date,
            records=records
        )
        
        vehicles_timeline.append(vehicle_timeline)
        total_maintenance_count += len(records)
        total_cost += vehicle_total_cost
    
    return CustomerDetail(
        id=customer.id,
        name=customer.name,
        phone=customer.phone,
        created_at=customer.created_at,
        vehicles=vehicles_timeline,
        total_maintenance_count=total_maintenance_count,
        total_cost=total_cost
    )


@router.post("/", response_model=CustomerSchema)
def create_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    existing_customer = db.query(Customer).filter(Customer.phone == customer.phone).first()
    if existing_customer:
        raise HTTPException(status_code=400, detail="该手机号已存在")
    
    db_customer = Customer(**customer.model_dump())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer


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


@router.get("/{customer_id}/service-types")
def get_customer_service_types(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    
    vehicle_ids = [v.id for v in customer.vehicles]
    if not vehicle_ids:
        return []
    
    service_types = db.query(Appointment.service_type).filter(
        Appointment.vehicle_id.in_(vehicle_ids)
    ).distinct().all()
    
    return [st[0] for st in service_types]
