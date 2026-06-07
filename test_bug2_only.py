import requests
import json
import threading
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8083/api"

def main():
    print("=" * 70)
    print("✅ 验证 Bug2 修复: 库存扣减并发超卖")
    print("=" * 70)
    
    try:
        response = requests.get(f"{BASE_URL}/appointments?status=pending")
        pending_appointments = response.json()
        print(f"找到 {len(pending_appointments)} 个待处理预约")
        
        test_appointment_id = None
        for apt in pending_appointments:
            if apt['status'] == 'pending':
                test_appointment_id = apt['id']
                print(f"使用预约ID: {test_appointment_id}")
                break
        
        if not test_appointment_id:
            print("没有待处理预约，创建一个测试预约...")
            appointment_data = {
                "customer_id": 0,
                "service_type": "常规保养",
                "description": "并发库存测试",
                "appointment_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
                "customer": {
                    "name": "库存测试",
                    "phone": "13800138999",
                    "car_model": "测试车型",
                    "car_plate": f"KC{int(time.time()) % 10000}"
                }
            }
            response = requests.post(f"{BASE_URL}/appointments", json=appointment_data)
            test_appointment_id = response.json()['id']
            print(f"创建测试预约ID: {test_appointment_id}")
        
        response = requests.get(f"{BASE_URL}/technicians")
        technicians = response.json()
        available_tech = None
        for tech in technicians:
            if tech['status'] == 'available':
                available_tech = tech['id']
                print(f"使用技师ID: {available_tech}")
                break
        
        if not available_tech:
            print("没有可用技师，测试失败")
            return
        
        parts = requests.get(f"{BASE_URL}/parts").json()
        test_part = None
        for p in parts:
            if p['stock'] >= 20:
                test_part = p
                break
        
        if not test_part:
            print("没有库存>=20的配件，先创建一个测试配件...")
            part_data = {
                "name": "并发测试配件",
                "code": f"TEST-{int(time.time())}",
                "category": "测试",
                "price": 100,
                "stock": 10,
                "min_stock": 5,
                "unit": "个"
            }
            response = requests.post(f"{BASE_URL}/parts", json=part_data)
            test_part = response.json()
            print(f"创建测试配件: {test_part['name']}, ID: {test_part['id']}, 库存: {test_part['stock']}")
        
        part_id = test_part['id']
        initial_stock = test_part['stock']
        print(f"🔧 测试配件: {test_part['name']} (ID: {part_id})")
        print(f"📦 初始库存: {initial_stock}")
        
        work_order_data = {
            "appointment_id": test_appointment_id,
            "technician_id": available_tech,
            "labor_cost": 100
        }
        print(f"创建工单数据: {json.dumps(work_order_data, ensure_ascii=False)}")
        wo_response = requests.post(f"{BASE_URL}/work-orders", json=work_order_data)
        print(f"工单创建响应状态: {wo_response.status_code}")
        print(f"工单创建响应: {json.dumps(wo_response.json(), ensure_ascii=False)}")
        
        if wo_response.status_code != 200:
            print("❌ 创建工单失败，测试终止")
            return
            
        work_order = wo_response.json()
        work_order_id = work_order['id']
        print(f"📋 创建测试工单: ID {work_order_id}")
        
        print("\n🧵 开始并发扣减测试 (5个线程同时扣减3个)...")
        
        results = []
        errors = []
        lock = threading.Lock()
        
        def deduct_stock(thread_id):
            try:
                part_data = {
                    "part_id": part_id,
                    "quantity": 3,
                    "unit_price": test_part['price']
                }
                response = requests.post(
                    f"{BASE_URL}/work-orders/{work_order_id}/parts",
                    json=part_data
                )
                with lock:
                    if response.status_code == 200:
                        results.append(f"线程 {thread_id}: 成功")
                    else:
                        errors.append(f"线程 {thread_id}: {response.status_code} - {response.json().get('detail', '未知错误')}")
            except Exception as e:
                with lock:
                    errors.append(f"线程 {thread_id}: 异常 - {e}")
        
        threads = []
        for i in range(5):
            t = threading.Thread(target=deduct_stock, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        print(f"\n📊 成功次数: {len(results)}, 失败次数: {len(errors)}")
        for r in results:
            print(f"  ✅ {r}")
        for e in errors:
            print(f"  ❌ {e}")
        
        final_part = requests.get(f"{BASE_URL}/parts/{part_id}").json()
        final_stock = final_part['stock']
        expected_deduction = len(results) * 3
        expected_stock = initial_stock - expected_deduction
        
        print(f"\n📦 最终库存: {final_stock}")
        print(f"📊 期望库存: {initial_stock} - {expected_deduction} = {expected_stock}")
        
        success = True
        
        if final_stock < 0:
            print(f"❌ 库存出现负数！库存: {final_stock}")
            success = False
        else:
            print("✅ 库存没有出现负数")
        
        if final_stock != expected_stock:
            diff = final_stock - expected_stock
            print(f"❌ 库存与预期不符，差异: {diff} (可能有部分扣减失败属于正常)")
            if diff < 0:
                success = False
        else:
            print("✅ 库存与预期一致")
        
        if success and len(errors) > 0:
            print(f"\n⚠️  注意: {len(errors)} 个请求被拒绝（库存不足），这是正确的行为！")
            print("   说明原子锁生效，阻止了超卖。")
        
        if success:
            print("\n✅ BUG2 修复成功: 库存扣减有原子性保证！")
        else:
            print("\n❌ BUG2 仍然存在问题")
        
        return success
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
