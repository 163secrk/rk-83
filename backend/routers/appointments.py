from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, date, timezone, timedelta
from database import get_db
from models import Appointment, Customer, WorkOrder, MaintenancePackage
from schemas import Appointment as AppointmentSchema, AppointmentCreate, AppointmentUpdate, CustomerCreate

router = APIRouter()

TZ_OFFSET = timedelta(hours=8)


def _to_local_datetime(dt: datetime) -> datetime:
    if dt.tzinfo is not None:
        return dt.astimezone(timezone(TZ_OFFSET)).replace(tzinfo=None)
    return dt


@router.get("/", response_model=List[AppointmentSchema])
def get_appointments(
    status: str = None,
    start_date: date = None,
    end_date: date = None,
    db: Session = Depends(get_db)
):
    query = db.query(Appointment).order_by(Appointment.appointment_date.desc())
    
    if status:
        query = query.filter(Appointment.status == status)
    if start_date:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        query = query.filter(Appointment.appointment_date >= start_datetime)
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        query = query.filter(Appointment.appointment_date <= end_datetime)
    
    result = query.all()
    return result


@router.get("/{appointment_id}", response_model=AppointmentSchema)
def get_appointment(appointment_id: int, db: Session = Depends(get_db)):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="预约不存在")
    return appointment


@router.post("/", response_model=AppointmentSchema)
def create_appointment(appointment: AppointmentCreate, db: Session = Depends(get_db)):
    from models import Vehicle
    
    if not appointment.service_type and not appointment.package_id:
        raise HTTPException(status_code=400, detail="请选择服务类型或保养套餐")
    
    if not appointment.customer and not appointment.customer_id:
        raise HTTPException(status_code=400, detail="请填写客户信息或选择客户")
    
    if appointment.vehicle and not (appointment.vehicle.car_model and appointment.vehicle.car_plate):
        raise HTTPException(status_code=400, detail="请填写完整的车辆信息")
    
    customer = db.query(Customer).filter(Customer.phone == appointment.customer.phone).first() if appointment.customer else None
    
    if not customer and appointment.customer:
        customer = Customer(**appointment.customer.model_dump())
        db.add(customer)
        db.commit()
        db.refresh(customer)
    elif not customer:
        customer = db.query(Customer).filter(Customer.id == appointment.customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="客户不存在")
    
    vehicle_id = appointment.vehicle_id
    if not vehicle_id and appointment.vehicle:
        appointment.vehicle.customer_id = customer.id
        existing_vehicle = db.query(Vehicle).filter(Vehicle.car_plate == appointment.vehicle.car_plate).first()
        if existing_vehicle:
            vehicle_id = existing_vehicle.id
        else:
            db_vehicle = Vehicle(**appointment.vehicle.model_dump())
            db.add(db_vehicle)
            db.commit()
            db.refresh(db_vehicle)
            vehicle_id = db_vehicle.id
    
    package_id = appointment.package_id
    service_type = appointment.service_type
    
    if package_id:
        package = db.query(MaintenancePackage).filter(
            MaintenancePackage.id == package_id,
            MaintenancePackage.is_active == 1
        ).first()
        if not package:
            raise HTTPException(status_code=404, detail="套餐不存在或已停用")
        if package.services:
            service_type = package.services[0].service_type
    
    local_appointment_date = _to_local_datetime(appointment.appointment_date)
    db_appointment = Appointment(
        customer_id=customer.id,
        vehicle_id=vehicle_id,
        package_id=package_id,
        service_type=service_type,
        description=appointment.description,
        appointment_date=local_appointment_date,
        status="pending"
    )
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment


@router.put("/{appointment_id}", response_model=AppointmentSchema)
def update_appointment(
    appointment_id: int,
    appointment_update: AppointmentUpdate,
    db: Session = Depends(get_db)
):
    db_appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not db_appointment:
        raise HTTPException(status_code=404, detail="预约不存在")
    
    update_data = appointment_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_appointment, key, value)
    
    db.commit()
    db.refresh(db_appointment)
    return db_appointment


@router.delete("/{appointment_id}")
def delete_appointment(appointment_id: int, db: Session = Depends(get_db)):
    db_appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not db_appointment:
        raise HTTPException(status_code=404, detail="预约不存在")
    
    work_order = db.query(WorkOrder).filter(WorkOrder.appointment_id == appointment_id).first()
    if work_order:
        raise HTTPException(status_code=400, detail="该预约已有相关工单，无法删除")
    
    db.delete(db_appointment)
    db.commit()
    return {"message": "删除成功"}


@router.get("/statistics/today")
def get_today_stats(db: Session = Depends(get_db)):
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    total = db.query(Appointment).filter(
        Appointment.appointment_date >= today_start,
        Appointment.appointment_date <= today_end
    ).count()
    
    pending = db.query(Appointment).filter(
        Appointment.appointment_date >= today_start,
        Appointment.appointment_date <= today_end,
        Appointment.status == "pending"
    ).count()
    
    confirmed = db.query(Appointment).filter(
        Appointment.appointment_date >= today_start,
        Appointment.appointment_date <= today_end,
        Appointment.status == "confirmed"
    ).count()
    
    completed = db.query(Appointment).filter(
        Appointment.appointment_date >= today_start,
        Appointment.appointment_date <= today_end,
        Appointment.status == "completed"
    ).count()
    
    return {
        "total": total,
        "pending": pending,
        "confirmed": confirmed,
        "completed": completed
    }
