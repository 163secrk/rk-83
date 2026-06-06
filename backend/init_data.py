from database import SessionLocal, engine, Base
from models import Technician, Part

Base.metadata.create_all(bind=engine)

def init_data():
    db = SessionLocal()
    
    try:
        if db.query(Technician).count() == 0:
            technicians = [
                Technician(name="张工", phone="13800138001", specialty="机修", status="available"),
                Technician(name="李工", phone="13800138002", specialty="钣金", status="available"),
                Technician(name="王工", phone="13800138003", specialty="喷漆", status="available"),
                Technician(name="赵工", phone="13800138004", specialty="电器", status="available"),
                Technician(name="刘工", phone="13800138005", specialty="综合维修", status="available")
            ]
            db.add_all(technicians)
            print("已初始化技师数据")
        
        if db.query(Part).count() == 0:
            parts = [
                Part(name="机油", code="OIL001", category="油品", price=198.0, stock=50, min_stock=20, unit="升", description="全合成5W-30机油"),
                Part(name="机油滤清器", code="FIL001", category="滤清器", price=35.0, stock=100, min_stock=30, unit="个", description="机油格"),
                Part(name="空气滤清器", code="FIL002", category="滤清器", price=45.0, stock=80, min_stock=20, unit="个", description="空气格"),
                Part(name="空调滤清器", code="FIL003", category="滤清器", price=55.0, stock=60, min_stock=20, unit="个", description="空调格"),
                Part(name="火花塞", code="SPA001", category="点火系统", price=85.0, stock=40, min_stock=15, unit="个", description="铂金火花塞"),
                Part(name="刹车片", code="BRA001", category="制动系统", price=280.0, stock=30, min_stock=10, unit="套", description="前刹车片"),
                Part(name="刹车油", code="BRA002", category="油品", price=120.0, stock=25, min_stock=10, unit="升", description="DOT4刹车油"),
                Part(name="防冻液", code="COO001", category="油品", price=95.0, stock=40, min_stock=15, unit="升", description="-35℃防冻液"),
                Part(name="变速箱油", code="TRA001", category="油品", price=180.0, stock=20, min_stock=8, unit="升", description="自动变速箱油"),
                Part(name="轮胎", code="TYR001", category="轮胎", price=650.0, stock=16, min_stock=4, unit="条", description="195/65 R15"),
                Part(name="雨刮片", code="WIP001", category="外观", price=65.0, stock=50, min_stock=20, unit="对", description="无骨雨刮"),
                Part(name="蓄电池", code="BAT001", category="电气", price=480.0, stock=10, min_stock=3, unit="个", description="12V 60Ah蓄电池")
            ]
            db.add_all(parts)
            print("已初始化配件数据")
        
        db.commit()
        print("数据初始化完成")
        
    except Exception as e:
        db.rollback()
        print(f"初始化失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_data()
