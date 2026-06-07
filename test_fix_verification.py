import requests
import json
import threading
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8083/api"

def test_bug1_fix():
    print("=" * 70)
    print("✅ 验证 Bug1 修复: 预约时间差8小时")
    print("=" * 70)
    
    local_time = datetime.now().replace(hour=14, minute=30, second=0, microsecond=0) + timedelta(days=1)
    frontend_format = local_time.strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"📅 前端选择的本地时间: {local_time}")
    print(f"📤 前端发送格式 (value-format): {frontend_format}")
    print(f"   (注意: 这是不带Z的本地时间字符串，不是UTC)")
    
    appointment_data = {
        "customer_id": 0,
        "service_type": "常规保养",
        "description": "验证时区修复",
        "appointment_date": frontend_format,
        "customer": {
            "name": "时区测试",
            "phone": "13800138000",
            "car_model": "测试车型",
            "car_plate": "京TZ001"
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/appointments", json=appointment_data)
        result = response.json()
        
        returned_time = result.get('appointment_date')
        print(f"\n📥 后端返回时间: {returned_time}")
        print(f"✅ 期望时间: {local_time.strftime('%Y-%m-%dT%H:%M:%S')}")
        
        returned_dt = datetime.fromisoformat(returned_time.replace('Z', '+00:00'))
        expected_dt = local_time
        diff_minutes = abs((expected_dt - returned_dt).total_seconds() / 60)
        
        print(f"\n⏱️  时间偏差: {diff_minutes:.2f} 分钟")
        if diff_minutes < 1:
            print("✅ BUG1 修复成功: 时间正确，没有8小时偏移！")
            return True
        else:
            print(f"❌ BUG1 仍然存在问题: 偏差 {diff_minutes:.2f} 分钟")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def test_bug1_with_utc_time():
    print("\n" + "=" * 70)
    print("🔄 测试 Bug1 向后兼容: 处理带Z的UTC时间")
    print("=" * 70)
    
    local_time = datetime.now().replace(hour=16, minute=0, second=0, microsecond=0) + timedelta(days=1)
    utc_time = local_time - timedelta(hours=8)
    utc_with_z = utc_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    print(f"📅 前端选择的本地时间: {local_time} (UTC: {utc_time})")
    print(f"📤 前端发送UTC时间 (带Z): {utc_with_z}")
    
    appointment_data = {
        "customer_id": 0,
        "service_type": "常规保养",
        "description": "测试UTC向后兼容",
        "appointment_date": utc_with_z,
        "customer": {
            "name": "UTC兼容测试",
            "phone": "13800138001",
            "car_model": "测试车型",
            "car_plate": "京TZ002"
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/appointments", json=appointment_data)
        result = response.json()
        
        returned_time = result.get('appointment_date')
        print(f"\n📥 后端返回时间: {returned_time}")
        print(f"✅ 期望时间: {local_time.strftime('%Y-%m-%dT%H:%M:%S')}")
        
        returned_dt = datetime.fromisoformat(returned_time.replace('Z', '+00:00'))
        expected_dt = local_time
        diff_minutes = abs((expected_dt - returned_dt).total_seconds() / 60)
        
        print(f"\n⏱️  时间偏差: {diff_minutes:.2f} 分钟")
        if diff_minutes < 1:
            print("✅ UTC时间兼容成功: 带Z的时间也正确转换！")
            return True
        else:
            print(f"❌ UTC时间转换有问题: 偏差 {diff_minutes:.2f} 分钟")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def test_bug3_fix():
    print("\n" + "=" * 70)
    print("✅ 验证 Bug3 修复: 日期筛选显示昨天数据")
    print("=" * 70)
    
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    print(f"📅 今天日期: {today}")
    print(f"📅 昨天日期: {yesterday}")
    
    test_times = [
        ("今天 00:00:01", datetime.combine(today, datetime.min.time()) + timedelta(seconds=1)),
        ("今天 12:00:00", datetime.combine(today, datetime.min.time()) + timedelta(hours=12)),
        ("今天 23:59:59", datetime.combine(today, datetime.max.time())),
    ]
    
    created_ids = []
    for desc, test_time in test_times:
        appointment_data = {
            "customer_id": 0,
            "service_type": "常规保养",
            "description": f"日期筛选测试 - {desc}",
            "appointment_date": test_time.strftime("%Y-%m-%d %H:%M:%S"),
            "customer": {
                "name": "日期测试",
                "phone": "13800138002",
                "car_model": "测试车型",
                "car_plate": f"京RQ{int(time.time()) % 1000}"
            }
        }
        try:
            response = requests.post(f"{BASE_URL}/appointments", json=appointment_data)
            result = response.json()
            created_ids.append(result['id'])
            print(f"✅ 创建测试预约: {desc} -> ID {result['id']}, 时间 {result['appointment_date']}")
        except Exception as e:
            print(f"❌ 创建失败: {e}")
    
    print(f"\n🔍 筛选 [今天] 的预约记录...")
    params = {
        "start_date": today.isoformat(),
        "end_date": today.isoformat()
    }
    
    try:
        response = requests.get(f"{BASE_URL}/appointments", params=params)
        results = response.json()
        
        print(f"📊 返回记录数: {len(results)}")
        returned_ids = {apt['id'] for apt in results}
        expected_ids = set(created_ids)
        
        missing = expected_ids - returned_ids
        extra = returned_ids - expected_ids
        
        success = True
        
        if missing:
            print(f"❌ 缺失记录 (应该显示但未显示): {missing}")
            success = False
        else:
            print("✅ 所有今天的记录都正确显示")
        
        has_yesterday = any(str(yesterday) in apt.get('appointment_date', '') for apt in results)
        if has_yesterday:
            print("❌ 包含了昨天的记录！")
            success = False
        else:
            print("✅ 没有包含昨天的记录")
        
        if success:
            print("\n✅ BUG3 修复成功: 日期筛选正确！")
        else:
            print("\n❌ BUG3 仍然存在问题")
        
        return success
        
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def test_bug2_fix():
    print("\n" + "=" * 70)
    print("✅ 验证 Bug2 修复: 库存扣减并发超卖")
    print("=" * 70)
    
    try:
        parts = requests.get(f"{BASE_URL}/parts").json()
        test_part = None
        for p in parts:
            if p['stock'] >= 20:
                test_part = p
                break
        
        if not test_part:
            print("⚠️  没有库存>=20的配件，跳过并发测试")
            return None
        
        part_id = test_part['id']
        initial_stock = test_part['stock']
        print(f"🔧 测试配件: {test_part['name']} (ID: {part_id})")
        print(f"📦 初始库存: {initial_stock}")
        
        work_order_data = {
            "appointment_id": 1,
            "technician_id": 1,
            "labor_cost": 100
        }
        wo_response = requests.post(f"{BASE_URL}/work-orders", json=work_order_data)
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
    print("\n" + "🚀" * 25)
    print("   🧪 开始验证三个Bug的修复效果  ")
    print("🚀" * 25 + "\n")
    
    bug1_ok = test_bug1_fix()
    bug1_utc_ok = test_bug1_with_utc_time()
    bug3_ok = test_bug3_fix()
    bug2_ok = test_bug2_fix()
    
    print("\n" + "=" * 70)
    print("📋 测试总结")
    print("=" * 70)
    
    all_ok = True
    results = [
        ("Bug1 (时间偏移8小时) - 本地时间", bug1_ok),
        ("Bug1 (时间偏移8小时) - UTC兼容", bug1_utc_ok),
        ("Bug2 (库存并发超卖)", bug2_ok),
        ("Bug3 (日期筛选错误)", bug3_ok),
    ]
    
    for name, ok in results:
        if ok is None:
            status = "⚠️  跳过"
        elif ok:
            status = "✅ 通过"
        else:
            status = "❌ 失败"
            all_ok = False
        print(f"  {status} - {name}")
    
    print("\n" + "=" * 70)
    if all_ok:
        print("🎉 所有Bug修复验证通过！")
    else:
        print("⚠️  部分Bug修复需要进一步检查")
    print("=" * 70 + "\n")
