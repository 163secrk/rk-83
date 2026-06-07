from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False, unique=True)
    car_model = Column(String(100), nullable=False)
    car_plate = Column(String(20), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.now)

    appointments = relationship("Appointment", back_populates="customer")


class Technician(Base):
    __tablename__ = "technicians"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    specialty = Column(String(100), nullable=False)
    status = Column(String(20), default="available")
    created_at = Column(DateTime, default=datetime.now)

    work_orders = relationship("WorkOrder", back_populates="technician")


class Part(Base):
    __tablename__ = "parts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False, unique=True)
    specification = Column(String(200))
    category = Column(String(50), nullable=False)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    min_stock = Column(Integer, default=10)
    unit = Column(String(20), default="个")
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

    work_order_parts = relationship("WorkOrderPart", back_populates="part")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    service_type = Column(String(50), nullable=False)
    description = Column(Text)
    appointment_date = Column(DateTime, nullable=False)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.now)

    customer = relationship("Customer", back_populates="appointments")
    work_order = relationship("WorkOrder", back_populates="appointment", uselist=False)


class WorkOrder(Base):
    __tablename__ = "work_orders"

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False)
    technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=False)
    status = Column(String(20), default="assigned")
    actual_start = Column(DateTime)
    actual_end = Column(DateTime)
    labor_cost = Column(Float, default=0)
    total_amount = Column(Float, default=0)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

    appointment = relationship("Appointment", back_populates="work_order")
    technician = relationship("Technician", back_populates="work_orders")
    parts = relationship("WorkOrderPart", back_populates="work_order")


class WorkOrderPart(Base):
    __tablename__ = "work_order_parts"

    id = Column(Integer, primary_key=True, index=True)
    work_order_id = Column(Integer, ForeignKey("work_orders.id"), nullable=False)
    part_id = Column(Integer, ForeignKey("parts.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    work_order = relationship("WorkOrder", back_populates="parts")
    part = relationship("Part", back_populates="work_order_parts")
