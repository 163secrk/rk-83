from database import SessionLocal, engine, Base
from models import Technician, Part, Customer, Vehicle, Appointment, WorkOrder, WorkOrderPart, MaintenancePackage, MaintenancePackageService, MaintenancePackagePart
from datetime import datetime, timedelta

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
                Part(name="机油", code="OIL001", specification="5W-30 全合成", category="油品", price=198.0, stock=50, min_stock=20, unit="升", description="全合成5W-30机油"),
                Part(name="机油滤清器", code="FIL001", specification="适配大众EA211", category="滤清器", price=35.0, stock=100, min_stock=30, unit="个", description="机油格"),
                Part(name="空气滤清器", code="FIL002", specification="适配丰田卡罗拉", category="滤清器", price=45.0, stock=80, min_stock=20, unit="个", description="空气格"),
                Part(name="空调滤清器", code="FIL003", specification="活性炭 PM2.5", category="滤清器", price=55.0, stock=60, min_stock=20, unit="个", description="空调格"),
                Part(name="火花塞", code="SPA001", specification="双铂金 1.4T", category="点火系统", price=85.0, stock=40, min_stock=15, unit="个", description="铂金火花塞"),
                Part(name="刹车片", code="BRA001", specification="前刹车片 陶瓷配方", category="制动系统", price=280.0, stock=30, min_stock=10, unit="套", description="前刹车片"),
                Part(name="刹车油", code="BRA002", specification="DOT4 1L装", category="油品", price=120.0, stock=25, min_stock=10, unit="升", description="DOT4刹车油"),
                Part(name="防冻液", code="COO001", specification="-35℃ 红色", category="油品", price=95.0, stock=40, min_stock=15, unit="升", description="-35℃防冻液"),
                Part(name="变速箱油", code="TRA001", specification="ATF 6速自动", category="油品", price=180.0, stock=20, min_stock=8, unit="升", description="自动变速箱油"),
                Part(name="轮胎", code="TYR001", specification="195/65 R15 91V", category="轮胎", price=650.0, stock=16, min_stock=4, unit="条", description="195/65 R15"),
                Part(name="雨刮片", code="WIP001", specification="24/16寸 无骨", category="外观", price=65.0, stock=50, min_stock=20, unit="对", description="无骨雨刮"),
                Part(name="蓄电池", code="BAT001", specification="12V 60Ah 550CCA", category="电气", price=480.0, stock=10, min_stock=3, unit="个", description="12V 60Ah蓄电池")
            ]
            db.add_all(parts)
            db.flush()
            print("已初始化配件数据")
        
        if db.query(MaintenancePackage).count() == 0:
            parts_dict = {p.code: p for p in parts}
            
            packages_data = [
                {
                    "name": "常规保养套餐A",
                    "description": "适合5000-10000公里常规保养，更换机油机滤，车辆安全检查",
                    "package_price": 899.0,
                    "services": ["常规保养"],
                    "parts": [
                        {"code": "OIL001", "qty": 4},
                        {"code": "FIL001", "qty": 1}
                    ]
                },
                {
                    "name": "标准保养套餐B",
                    "description": "适合15000-20000公里保养，更换机油三滤，空调系统检查",
                    "package_price": 1299.0,
                    "services": ["常规保养"],
                    "parts": [
                        {"code": "OIL001", "qty": 4},
                        {"code": "FIL001", "qty": 1},
                        {"code": "FIL002", "qty": 1},
                        {"code": "FIL003", "qty": 1}
                    ]
                },
                {
                    "name": "全面大保养套餐C",
                    "description": "适合30000-40000公里大保养，全车油水更换，深度检测",
                    "package_price": 2999.0,
                    "services": ["大保养"],
                    "parts": [
                        {"code": "OIL001", "qty": 5},
                        {"code": "FIL001", "qty": 1},
                        {"code": "FIL002", "qty": 1},
                        {"code": "FIL003", "qty": 1},
                        {"code": "BRA002", "qty": 2},
                        {"code": "TRA001", "qty": 6},
                        {"code": "SPA001", "qty": 4}
                    ]
                },
                {
                    "name": "刹车系统保养套餐",
                    "description": "刹车片更换+刹车油更换，保障行车安全",
                    "package_price": 1599.0,
                    "services": ["维修服务"],
                    "parts": [
                        {"code": "BRA001", "qty": 1},
                        {"code": "BRA002", "qty": 2}
                    ]
                }
            ]
            
            for pkg_data in packages_data:
                package = MaintenancePackage(
                    name=pkg_data["name"],
                    description=pkg_data["description"],
                    package_price=pkg_data["package_price"],
                    is_active=1
                )
                db.add(package)
                db.flush()
                
                for service_type in pkg_data["services"]:
                    pkg_service = MaintenancePackageService(
                        package_id=package.id,
                        service_type=service_type
                    )
                    db.add(pkg_service)
                
                for part_item in pkg_data["parts"]:
                    part = parts_dict.get(part_item["code"])
                    if part:
                        pkg_part = MaintenancePackagePart(
                            package_id=package.id,
                            part_id=part.id,
                            quantity=part_item["qty"]
                        )
                        db.add(pkg_part)
            
            print("已初始化保养套餐数据")
        
        if db.query(Customer).count() == 0:
            customers = [
                Customer(name="张三", phone="13900139001"),
                Customer(name="李四", phone="13900139002"),
                Customer(name="王五", phone="13900139003"),
            ]
            db.add_all(customers)
            db.flush()
            
            vehicles = [
                Vehicle(
                    customer_id=customers[0].id,
                    car_model="大众帕萨特 2023款",
                    car_plate="京A12345",
                    vin="WVWZZZ3CZWE123456",
                    mileage=25000,
                    color="黑色",
                    purchase_date=datetime(2023, 3, 15),
                    remarks="客户日常上下班使用"
                ),
                Vehicle(
                    customer_id=customers[0].id,
                    car_model="丰田凯美瑞 2022款",
                    car_plate="京A67890",
                    vin="LFV3A24F4C3123456",
                    mileage=18000,
                    color="白色",
                    purchase_date=datetime(2022, 8, 20),
                    remarks="家庭用车"
                ),
                Vehicle(
                    customer_id=customers[1].id,
                    car_model="本田雅阁 2024款",
                    car_plate="京B11111",
                    vin="LHGCV2F41K1234567",
                    mileage=5000,
                    color="银色",
                    purchase_date=datetime(2024, 1, 10),
                    remarks="新车"
                ),
                Vehicle(
                    customer_id=customers[2].id,
                    car_model="奥迪A4L 2023款",
                    car_plate="京C22222",
                    vin="WAUZZZF4XPN123456",
                    mileage=35000,
                    color="黑色",
                    purchase_date=datetime(2022, 11, 5),
                    remarks="商务用车"
                ),
            ]
            db.add_all(vehicles)
            db.flush()
            print("已初始化客户和车辆数据")
            
            if db.query(Appointment).count() == 0:
                technicians = db.query(Technician).all()
                parts = db.query(Part).all()
                parts_dict = {p.code: p for p in parts}
                
                appointments_data = [
                    {
                        "vehicle_idx": 0,
                        "service_type": "首次保养",
                        "description": "5000公里首保，更换机油机滤",
                        "date": datetime(2023, 8, 20, 9, 30),
                        "status": "completed",
                        "technician": technicians[0],
                        "labor_cost": 120.0,
                        "parts": [
                            {"code": "OIL001", "qty": 4},
                            {"code": "FIL001", "qty": 1}
                        ],
                        "notes": "首保完成，车况良好"
                    },
                    {
                        "vehicle_idx": 0,
                        "service_type": "常规保养",
                        "description": "15000公里二保，更换机油三滤",
                        "date": datetime(2024, 1, 15, 10, 0),
                        "status": "completed",
                        "technician": technicians[0],
                        "labor_cost": 180.0,
                        "parts": [
                            {"code": "OIL001", "qty": 4},
                            {"code": "FIL001", "qty": 1},
                            {"code": "FIL002", "qty": 1},
                            {"code": "FIL003", "qty": 1}
                        ],
                        "notes": "常规保养完成，建议下次更换火花塞"
                    },
                    {
                        "vehicle_idx": 0,
                        "service_type": "常规保养",
                        "description": "25000公里保养，更换机油机滤、火花塞",
                        "date": datetime(2024, 6, 10, 14, 0),
                        "status": "completed",
                        "technician": technicians[0],
                        "labor_cost": 280.0,
                        "parts": [
                            {"code": "OIL001", "qty": 4},
                            {"code": "FIL001", "qty": 1},
                            {"code": "SPA001", "qty": 4}
                        ],
                        "notes": "保养完成，刹车片还剩60%"
                    },
                    {
                        "vehicle_idx": 0,
                        "service_type": "常规保养",
                        "description": "35000公里保养预约",
                        "date": datetime.now() + timedelta(days=7),
                        "status": "pending",
                        "technician": None,
                        "labor_cost": 0,
                        "parts": [],
                        "notes": ""
                    },
                    {
                        "vehicle_idx": 1,
                        "service_type": "首次保养",
                        "description": "5000公里首保",
                        "date": datetime(2023, 1, 20, 9, 0),
                        "status": "completed",
                        "technician": technicians[1],
                        "labor_cost": 100.0,
                        "parts": [
                            {"code": "OIL001", "qty": 4},
                            {"code": "FIL001", "qty": 1}
                        ],
                        "notes": "首保完成"
                    },
                    {
                        "vehicle_idx": 1,
                        "service_type": "常规保养",
                        "description": "15000公里保养，更换机油机滤、空调滤",
                        "date": datetime(2023, 7, 15, 10, 30),
                        "status": "completed",
                        "technician": technicians[1],
                        "labor_cost": 150.0,
                        "parts": [
                            {"code": "OIL001", "qty": 4},
                            {"code": "FIL001", "qty": 1},
                            {"code": "FIL003", "qty": 1}
                        ],
                        "notes": "保养完成"
                    },
                    {
                        "vehicle_idx": 3,
                        "service_type": "常规保养",
                        "description": "30000公里大保养",
                        "date": datetime(2024, 5, 20, 9, 0),
                        "status": "completed",
                        "technician": technicians[4],
                        "labor_cost": 580.0,
                        "parts": [
                            {"code": "OIL001", "qty": 5},
                            {"code": "FIL001", "qty": 1},
                            {"code": "FIL002", "qty": 1},
                            {"code": "FIL003", "qty": 1},
                            {"code": "BRA002", "qty": 2},
                            {"code": "TRA001", "qty": 6}
                        ],
                        "notes": "大保养完成，更换变速箱油、刹车油"
                    },
                    {
                        "vehicle_idx": 2,
                        "service_type": "首次保养",
                        "description": "新车首保预约",
                        "date": datetime.now() + timedelta(days=3),
                        "status": "confirmed",
                        "technician": None,
                        "labor_cost": 0,
                        "parts": [],
                        "notes": "客户要求周末上午"
                    }
                ]
                
                for appt_data in appointments_data:
                    vehicle = vehicles[appt_data["vehicle_idx"]]
                    customer = customers[0] if appt_data["vehicle_idx"] < 2 else (customers[1] if appt_data["vehicle_idx"] == 2 else customers[2])
                    
                    appointment = Appointment(
                        customer_id=customer.id,
                        vehicle_id=vehicle.id,
                        service_type=appt_data["service_type"],
                        description=appt_data["description"],
                        appointment_date=appt_data["date"],
                        status=appt_data["status"]
                    )
                    db.add(appointment)
                    db.flush()
                    
                    if appt_data["status"] == "completed" and appt_data["technician"]:
                        parts_total = 0
                        work_order_parts = []
                        
                        for p in appt_data["parts"]:
                            part = parts_dict.get(p["code"])
                            if part:
                                subtotal = part.price * p["qty"]
                                parts_total += subtotal
                                work_order_parts.append(WorkOrderPart(
                                    part_id=part.id,
                                    quantity=p["qty"],
                                    unit_price=part.price,
                                    subtotal=subtotal
                                ))
                        
                        total_amount = appt_data["labor_cost"] + parts_total
                        
                        work_order = WorkOrder(
                            appointment_id=appointment.id,
                            technician_id=appt_data["technician"].id,
                            status="completed",
                            actual_start=appt_data["date"],
                            actual_end=appt_data["date"] + timedelta(hours=2),
                            labor_cost=appt_data["labor_cost"],
                            total_amount=total_amount,
                            notes=appt_data["notes"]
                        )
                        db.add(work_order)
                        db.flush()
                        
                        for wop in work_order_parts:
                            wop.work_order_id = work_order.id
                            db.add(wop)
                
                print("已初始化预约和工单数据")
        
        db.commit()
        print("数据初始化完成")
        
    except Exception as e:
        db.rollback()
        print(f"初始化失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    init_data()
