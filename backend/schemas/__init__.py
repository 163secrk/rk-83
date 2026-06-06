from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class CustomerBase(BaseModel):
    name: str
    phone: str
    car_model: str
    car_plate: str


class CustomerCreate(CustomerBase):
    pass


class Customer(CustomerBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class TechnicianBase(BaseModel):
    name: str
    phone: str
    specialty: str
    status: Optional[str] = "available"


class TechnicianCreate(TechnicianBase):
    pass


class Technician(TechnicianBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PartBase(BaseModel):
    name: str
    code: str
    category: str
    price: float
    stock: Optional[int] = 0
    min_stock: Optional[int] = 10
    unit: Optional[str] = "个"
    description: Optional[str] = None


class PartCreate(PartBase):
    pass


class PartUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    min_stock: Optional[int] = None
    unit: Optional[str] = None
    description: Optional[str] = None


class Part(PartBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class AppointmentBase(BaseModel):
    customer_id: int
    service_type: str
    description: Optional[str] = None
    appointment_date: datetime


class AppointmentCreate(AppointmentBase):
    customer: Optional[CustomerCreate] = None


class AppointmentUpdate(BaseModel):
    status: Optional[str] = None
    service_type: Optional[str] = None
    description: Optional[str] = None
    appointment_date: Optional[datetime] = None


class Appointment(AppointmentBase):
    id: int
    status: str
    created_at: datetime
    customer: Customer

    class Config:
        from_attributes = True


class WorkOrderPartBase(BaseModel):
    part_id: int
    quantity: int


class WorkOrderPartCreate(WorkOrderPartBase):
    pass


class WorkOrderPart(WorkOrderPartBase):
    id: int
    unit_price: float
    subtotal: float
    part: Part

    class Config:
        from_attributes = True


class WorkOrderBase(BaseModel):
    appointment_id: int
    technician_id: int


class WorkOrderCreate(WorkOrderBase):
    pass


class WorkOrderUpdate(BaseModel):
    status: Optional[str] = None
    labor_cost: Optional[float] = None
    notes: Optional[str] = None
    parts: Optional[List[WorkOrderPartCreate]] = None


class WorkOrder(WorkOrderBase):
    id: int
    status: str
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    labor_cost: float
    total_amount: float
    notes: Optional[str] = None
    created_at: datetime
    appointment: Appointment
    technician: Technician
    parts: List[WorkOrderPart] = []

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_appointments: int
    pending_appointments: int
    today_appointments: int
    total_work_orders: int
    in_progress_work_orders: int
    completed_work_orders: int
    total_parts: int
    low_stock_parts: int
    total_revenue: float
