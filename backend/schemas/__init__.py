from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class CustomerBase(BaseModel):
    name: str
    phone: str


class CustomerCreate(CustomerBase):
    pass


class Customer(CustomerBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class VehicleBase(BaseModel):
    customer_id: int
    car_model: str
    car_plate: str
    vin: Optional[str] = None
    mileage: Optional[int] = 0
    color: Optional[str] = None
    purchase_date: Optional[datetime] = None
    remarks: Optional[str] = None


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    car_model: Optional[str] = None
    car_plate: Optional[str] = None
    vin: Optional[str] = None
    mileage: Optional[int] = None
    color: Optional[str] = None
    purchase_date: Optional[datetime] = None
    remarks: Optional[str] = None


class Vehicle(VehicleBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class VehicleWithCustomer(VehicleBase):
    id: int
    created_at: datetime
    customer: Optional[Customer] = None

    class Config:
        from_attributes = True


class CustomerWithVehicles(CustomerBase):
    id: int
    created_at: datetime
    vehicles: List[Vehicle] = []

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


class TechnicianMonthStats(BaseModel):
    completed_orders: int = 0
    total_hours: float = 0.0
    total_income: float = 0.0

    class Config:
        from_attributes = True


class TechnicianDetail(TechnicianBase):
    id: int
    created_at: datetime
    month_stats: TechnicianMonthStats

    class Config:
        from_attributes = True


class TechnicianWithStats(TechnicianBase):
    id: int
    created_at: datetime
    month_stats: TechnicianMonthStats

    class Config:
        from_attributes = True


class PartBase(BaseModel):
    name: str
    code: str
    specification: Optional[str] = None
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
    specification: Optional[str] = None
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
    vehicle_id: Optional[int] = None
    service_type: str
    description: Optional[str] = None
    appointment_date: datetime


class AppointmentCreate(AppointmentBase):
    customer: Optional[CustomerCreate] = None
    vehicle: Optional[VehicleCreate] = None


class AppointmentUpdate(BaseModel):
    status: Optional[str] = None
    service_type: Optional[str] = None
    description: Optional[str] = None
    appointment_date: Optional[datetime] = None
    vehicle_id: Optional[int] = None


class Appointment(AppointmentBase):
    id: int
    status: str
    created_at: datetime
    customer: Customer
    vehicle: Optional[Vehicle] = None

    class Config:
        from_attributes = True


class MaintenanceRecordPart(BaseModel):
    part_id: int
    part_name: str
    part_code: str
    quantity: int
    unit_price: float
    subtotal: float

    class Config:
        from_attributes = True


class MaintenanceRecord(BaseModel):
    id: int
    type: str
    service_type: str
    description: Optional[str] = None
    date: datetime
    status: str
    technician_name: Optional[str] = None
    labor_cost: float = 0
    parts_total: float = 0
    total_amount: float = 0
    mileage: Optional[int] = None
    notes: Optional[str] = None
    parts: List[MaintenanceRecordPart] = []
    appointment_id: Optional[int] = None
    work_order_id: Optional[int] = None

    class Config:
        from_attributes = True


class VehicleMaintenanceTimeline(BaseModel):
    vehicle_id: int
    car_model: str
    car_plate: str
    vin: Optional[str] = None
    total_maintenance_count: int
    total_cost: float
    first_maintenance_date: Optional[datetime] = None
    last_maintenance_date: Optional[datetime] = None
    records: List[MaintenanceRecord] = []

    class Config:
        from_attributes = True


class CustomerDetail(BaseModel):
    id: int
    name: str
    phone: str
    created_at: datetime
    vehicles: List[VehicleMaintenanceTimeline] = []
    total_maintenance_count: int = 0
    total_cost: float = 0

    class Config:
        from_attributes = True


class WorkOrderPartBase(BaseModel):
    part_id: int
    quantity: int


class WorkOrderPartCreate(WorkOrderPartBase):
    unit_price: Optional[float] = None


class WorkOrderPartUpdate(BaseModel):
    quantity: Optional[int] = None
    unit_price: Optional[float] = None


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
    low_stock_parts_list: List[Part] = []
