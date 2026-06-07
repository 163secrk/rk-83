from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, date, timezone, timedelta
from database import get_db
from models import Appointment, Customer, WorkOrder
from schemas import Appointment as AppointmentSchema, AppointmentCreate, AppointmentUpdate, CustomerCreate

router = APIRouter()

TZ_OFFSET = timedelta(hours=8)


def _to_local_datetime(dt: datetime) -> datetime:
    if dt.tzinfo is not None:
        return dt.astimezone(timezone(TZ_OFFSET)).replace(tzinfo=None)
    return dt


# #region debug-point helper
import json, urllib.request, threading
DEBUG_SERVER_URL = "http://127.0.0.1:7777/event"
DEBUG_SESSION_ID = "maintenance-system-bugs"
def _send_debug_log(hypothesis_id, location, msg, data):
    def _send():
        try:
            payload = {
                "sessionId": DEBUG_SESSION_ID,
                "runId": "pre-fix",
                "hypothesisId": hypothesis_id,
                "location": location,
                "msg": "[DEBUG] " + msg,
                "data": data
            }
            req = urllib.request.Request(
                DEBUG_SERVER_URL,
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(req, timeout=2).read()
        except:
            pass
    threading.Thread(target=_send).start()
# #endregion

@router.get("/", response_model=List[AppointmentSchema])
def get_appointments(
    status: str = None,
    start_date: date = None,
    end_date: date = None,
    db: Session = Depends(get_db)
):
    # #region debug-point H3,H4:date-filter-received
    _send_debug_log("H3,H4", "appointments.py:12", "后端收到的日期筛选参数", {
        "start_date": str(start_date),
        "start_date_type": str(type(start_date)),
        "end_date": str(end_date),
        "end_date_type": str(type(end_date)),
        "server_today": str(date.today()),
        "server_now": str(datetime.now())
    })
    # #endregion
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
    # #region debug-point H3,H4:date-filter-query-result
    _send_debug_log("H3,H4", "appointments.py:28", "日期筛选查询结果", {
        "result_count": len(result),
        "results": [
            {
                "id": a.id,
                "appointment_date": str(a.appointment_date),
                "appointment_date_iso": a.appointment_date.isoformat() if hasattr(a.appointment_date, 'isoformat') else None
            } for a in result
        ]
    })
    # #endregion
    return result


@router.get("/{appointment_id}", response_model=AppointmentSchema)
def get_appointment(appointment_id: int, db: Session = Depends(get_db)):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="预约不存在")
    return appointment


@router.post("/", response_model=AppointmentSchema)
def create_appointment(appointment: AppointmentCreate, db: Session = Depends(get_db)):
    # #region debug-point H1:appointment-time-received
    _send_debug_log("H1", "appointments.py:40", "后端收到的预约时间", {
        "received_appointment_date": str(appointment.appointment_date),
        "received_type": str(type(appointment.appointment_date)),
        "received_iso": appointment.appointment_date.isoformat() if hasattr(appointment.appointment_date, 'isoformat') else None
    })
    # #endregion
    from models import Vehicle
    
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
    
    local_appointment_date = _to_local_datetime(appointment.appointment_date)
    db_appointment = Appointment(
        customer_id=customer.id,
        vehicle_id=vehicle_id,
        service_type=appointment.service_type,
        description=appointment.description,
        appointment_date=local_appointment_date,
        status="pending"
    )
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    # #region debug-point H1:appointment-time-saved
    _send_debug_log("H1", "appointments.py:62", "数据库保存的预约时间", {
        "saved_appointment_date": str(db_appointment.appointment_date),
        "saved_type": str(type(db_appointment.appointment_date)),
        "saved_iso": db_appointment.appointment_date.isoformat() if hasattr(db_appointment.appointment_date, 'isoformat') else None
    })
    # #endregion
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
