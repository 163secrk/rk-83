from database import SessionLocal, engine
from models import Customer, Vehicle, Appointment, Base
from sqlalchemy import text
import sys

def migrate_existing_data():
    db = SessionLocal()
    
    try:
        print("开始迁移客户车辆数据...")
        
        with engine.connect() as conn:
            try:
                result = conn.execute(text("SELECT id, car_model, car_plate FROM customers"))
                old_customers = result.fetchall()
            except Exception as e:
                print(f"查询旧数据失败: {e}")
                old_customers = []
        
        migrated_count = 0
        for old_customer in old_customers:
            customer_id = old_customer[0]
            car_model = old_customer[1]
            car_plate = old_customer[2]
            
            existing_vehicle = db.query(Vehicle).filter(
                Vehicle.customer_id == customer_id,
                Vehicle.car_plate == car_plate
            ).first()
            
            if not existing_vehicle:
                vehicle = Vehicle(
                    customer_id=customer_id,
                    car_model=car_model,
                    car_plate=car_plate
                )
                db.add(vehicle)
                db.flush()
                
                appointments = db.query(Appointment).filter(
                    Appointment.customer_id == customer_id,
                    Appointment.vehicle_id.is_(None)
                ).all()
                
                for apt in appointments:
                    apt.vehicle_id = vehicle.id
                
                migrated_count += 1
                print(f"已迁移客户 {customer_id} 的车辆: {car_model} ({car_plate})")
        
        db.commit()
        
        with engine.connect() as conn:
            try:
                conn.execute(text("ALTER TABLE customers DROP COLUMN car_model"))
                conn.execute(text("ALTER TABLE customers DROP COLUMN car_plate"))
                conn.commit()
                print("已删除 customers 表中的旧车辆字段")
            except Exception as e:
                print(f"删除旧字段失败（可能已不存在）: {e}")
        
        print(f"数据迁移完成，共迁移 {migrated_count} 辆车的数据")
        
    except Exception as e:
        db.rollback()
        print(f"迁移失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    migrate_existing_data()
