from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime
from database import get_db
from models import Part, WorkOrderPart
from schemas import Part as PartSchema, PartCreate, PartUpdate

router = APIRouter()


@router.get("/", response_model=List[PartSchema])
def get_parts(
    category: str = None,
    low_stock: bool = False,
    keyword: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(Part).order_by(Part.created_at.desc())
    
    if category:
        query = query.filter(Part.category == category)
    if low_stock:
        query = query.filter(Part.stock <= Part.min_stock)
    if keyword:
        query = query.filter(
            (Part.name.contains(keyword)) |
            (Part.code.contains(keyword))
        )
    
    return query.all()


@router.get("/{part_id}", response_model=PartSchema)
def get_part(part_id: int, db: Session = Depends(get_db)):
    part = db.query(Part).filter(Part.id == part_id).first()
    if not part:
        raise HTTPException(status_code=404, detail="配件不存在")
    return part


@router.post("/", response_model=PartSchema)
def create_part(part: PartCreate, db: Session = Depends(get_db)):
    existing = db.query(Part).filter(Part.code == part.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="配件编码已存在")
    
    db_part = Part(**part.model_dump())
    db.add(db_part)
    db.commit()
    db.refresh(db_part)
    return db_part


@router.put("/{part_id}", response_model=PartSchema)
def update_part(
    part_id: int,
    part_update: PartUpdate,
    db: Session = Depends(get_db)
):
    db_part = db.query(Part).filter(Part.id == part_id).first()
    if not db_part:
        raise HTTPException(status_code=404, detail="配件不存在")
    
    update_data = part_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_part, key, value)
    
    db.commit()
    db.refresh(db_part)
    return db_part


@router.patch("/{part_id}/stock")
def update_stock(
    part_id: int,
    quantity: int,
    operation: str = "add",
    db: Session = Depends(get_db)
):
    db_part = db.query(Part).filter(Part.id == part_id).first()
    if not db_part:
        raise HTTPException(status_code=404, detail="配件不存在")
    
    if operation == "add":
        db_part.stock += quantity
    elif operation == "subtract":
        if db_part.stock < quantity:
            raise HTTPException(status_code=400, detail="库存不足")
        db_part.stock -= quantity
    else:
        raise HTTPException(status_code=400, detail="无效操作类型")
    
    db.commit()
    db.refresh(db_part)
    return db_part


@router.delete("/{part_id}")
def delete_part(part_id: int, db: Session = Depends(get_db)):
    db_part = db.query(Part).filter(Part.id == part_id).first()
    if not db_part:
        raise HTTPException(status_code=404, detail="配件不存在")
    
    used_in_orders = db.query(WorkOrderPart).filter(WorkOrderPart.part_id == part_id).first()
    if used_in_orders:
        raise HTTPException(status_code=400, detail="该配件已在工单中使用，无法删除")
    
    db.delete(db_part)
    db.commit()
    return {"message": "删除成功"}


@router.get("/categories/list")
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Part.category).distinct().all()
    return [cat[0] for cat in categories]


@router.get("/statistics/inventory")
def get_inventory_stats(db: Session = Depends(get_db)):
    total_parts = db.query(Part).count()
    low_stock = db.query(Part).filter(Part.stock <= Part.min_stock).count()
    out_of_stock = db.query(Part).filter(Part.stock == 0).count()
    
    total_value = db.query(func.sum(Part.price * Part.stock)).scalar() or 0
    
    category_stats = db.query(
        Part.category,
        func.count(Part.id).label("count"),
        func.sum(Part.stock).label("total_stock"),
        func.sum(Part.price * Part.stock).label("total_value")
    ).group_by(Part.category).all()
    
    return {
        "total_parts": total_parts,
        "low_stock": low_stock,
        "out_of_stock": out_of_stock,
        "total_value": float(total_value),
        "by_category": [
            {
                "category": stat.category,
                "count": stat.count,
                "total_stock": stat.total_stock,
                "total_value": float(stat.total_value or 0)
            }
            for stat in category_stats
        ]
    }


@router.get("/{part_id}/usage-history")
def get_part_usage_history(
    part_id: int,
    start_date: datetime = None,
    end_date: datetime = None,
    db: Session = Depends(get_db)
):
    db_part = db.query(Part).filter(Part.id == part_id).first()
    if not db_part:
        raise HTTPException(status_code=404, detail="配件不存在")
    
    query = db.query(WorkOrderPart).filter(WorkOrderPart.part_id == part_id)
    
    if start_date:
        query = query.filter(WorkOrderPart.created_at >= start_date)
    if end_date:
        query = query.filter(WorkOrderPart.created_at <= end_date)
    
    usage_records = query.order_by(WorkOrderPart.created_at.desc()).all()
    
    total_used = sum(record.quantity for record in usage_records)
    total_cost = sum(record.subtotal for record in usage_records)
    
    return {
        "part": db_part,
        "total_used": total_used,
        "total_cost": float(total_cost),
        "records": usage_records
    }
