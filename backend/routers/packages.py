from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import (
    MaintenancePackage,
    MaintenancePackageService,
    MaintenancePackagePart,
    Part,
    Appointment,
    WorkOrder
)
from schemas import (
    MaintenancePackage as MaintenancePackageSchema,
    MaintenancePackageCreate,
    MaintenancePackageUpdate
)

router = APIRouter()


@router.get("/", response_model=List[MaintenancePackageSchema])
def get_packages(
    is_active: int = None,
    keyword: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(MaintenancePackage).order_by(MaintenancePackage.created_at.desc())
    
    if is_active is not None:
        query = query.filter(MaintenancePackage.is_active == is_active)
    if keyword:
        query = query.filter(
            (MaintenancePackage.name.contains(keyword)) |
            (MaintenancePackage.description.contains(keyword))
        )
    
    return query.all()


@router.get("/{package_id}", response_model=MaintenancePackageSchema)
def get_package(package_id: int, db: Session = Depends(get_db)):
    package = db.query(MaintenancePackage).filter(MaintenancePackage.id == package_id).first()
    if not package:
        raise HTTPException(status_code=404, detail="套餐不存在")
    return package


@router.post("/", response_model=MaintenancePackageSchema)
def create_package(package: MaintenancePackageCreate, db: Session = Depends(get_db)):
    existing = db.query(MaintenancePackage).filter(MaintenancePackage.name == package.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="套餐名称已存在")
    
    if package.package_price <= 0:
        raise HTTPException(status_code=400, detail="套餐价格必须大于0")
    
    db_package = MaintenancePackage(
        name=package.name,
        description=package.description,
        package_price=package.package_price,
        is_active=package.is_active
    )
    
    for service in package.services:
        db_service = MaintenancePackageService(service_type=service.service_type)
        db_package.services.append(db_service)
    
    for part_item in package.parts:
        part = db.query(Part).filter(Part.id == part_item.part_id).first()
        if not part:
            raise HTTPException(status_code=404, detail=f"配件ID {part_item.part_id} 不存在")
        db_part = MaintenancePackagePart(
            part_id=part_item.part_id,
            quantity=part_item.quantity
        )
        db_package.parts.append(db_part)
    
    db.add(db_package)
    db.commit()
    db.refresh(db_package)
    return db_package


@router.put("/{package_id}", response_model=MaintenancePackageSchema)
def update_package(
    package_id: int,
    package_update: MaintenancePackageUpdate,
    db: Session = Depends(get_db)
):
    db_package = db.query(MaintenancePackage).filter(MaintenancePackage.id == package_id).first()
    if not db_package:
        raise HTTPException(status_code=404, detail="套餐不存在")
    
    if package_update.name:
        existing = db.query(MaintenancePackage).filter(
            MaintenancePackage.name == package_update.name,
            MaintenancePackage.id != package_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="套餐名称已存在")
    
    if package_update.package_price is not None and package_update.package_price <= 0:
        raise HTTPException(status_code=400, detail="套餐价格必须大于0")
    
    update_data = package_update.model_dump(exclude_unset=True, exclude={"services", "parts"})
    for key, value in update_data.items():
        setattr(db_package, key, value)
    
    if package_update.services is not None:
        db.query(MaintenancePackageService).filter(
            MaintenancePackageService.package_id == package_id
        ).delete()
        
        for service in package_update.services:
            db_service = MaintenancePackageService(service_type=service.service_type)
            db_package.services.append(db_service)
    
    if package_update.parts is not None:
        db.query(MaintenancePackagePart).filter(
            MaintenancePackagePart.package_id == package_id
        ).delete()
        
        for part_item in package_update.parts:
            part = db.query(Part).filter(Part.id == part_item.part_id).first()
            if not part:
                raise HTTPException(status_code=404, detail=f"配件ID {part_item.part_id} 不存在")
            db_part = MaintenancePackagePart(
                part_id=part_item.part_id,
                quantity=part_item.quantity
            )
            db_package.parts.append(db_part)
    
    db.commit()
    db.refresh(db_package)
    return db_package


@router.delete("/{package_id}")
def delete_package(package_id: int, db: Session = Depends(get_db)):
    db_package = db.query(MaintenancePackage).filter(MaintenancePackage.id == package_id).first()
    if not db_package:
        raise HTTPException(status_code=404, detail="套餐不存在")
    
    used_in_appointments = db.query(Appointment).filter(
        Appointment.package_id == package_id
    ).first()
    if used_in_appointments:
        raise HTTPException(status_code=400, detail="该套餐已被预约使用，无法删除")
    
    used_in_work_orders = db.query(WorkOrder).filter(
        WorkOrder.package_id == package_id
    ).first()
    if used_in_work_orders:
        raise HTTPException(status_code=400, detail="该套餐已被工单使用，无法删除")
    
    db.delete(db_package)
    db.commit()
    return {"message": "删除成功"}


@router.patch("/{package_id}/toggle-active")
def toggle_package_active(package_id: int, db: Session = Depends(get_db)):
    db_package = db.query(MaintenancePackage).filter(MaintenancePackage.id == package_id).first()
    if not db_package:
        raise HTTPException(status_code=404, detail="套餐不存在")
    
    db_package.is_active = 0 if db_package.is_active == 1 else 1
    db.commit()
    db.refresh(db_package)
    return db_package
