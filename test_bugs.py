import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8083/api"

def test_bug1_timezone():
    print("=" * 60)
    print("测试 Bug1: 预约时间差8小时")
    print("=" * 60)
    
    local_time = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0) + timedelta(days=1)
    print(f"前端选择的本地时间: {local_time}")
    print(f"前端发送的ISO格式: {local_time.isoformat()}")
    print(f"前端时区偏移: {local_time.utcoffset()}")
    
    js_iso = local_time.isoformat() + "Z"
    print(f"模拟JavaScript JSON序列化后的时间: {js_iso}")
    
    appointment_data = {
        "customer_id": 0,
        "service_type": "常规保养",
        "description": "测试时区问题",
        "appointment_date": js_iso,
        "customer": {
            "name": "测试用户",
            "phone": "13900139000",
            "car_model": "测试车型",
            "car_plate": "京TEST001"
        }
    }
    
    print(f"\n发送请求数据: {json.dumps(appointment_data, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(f"{BASE_URL}/appointments", json=appointment_data)
        print(f"\n响应状态码: {response.status_code}")
        result = response.json()
        print(f"响应数据: {json.dumps(result, indent=2, ensure_ascii=False)}")
        print(f"\n返回的预约时间: {result.get('appointment_date')}")
        print(f"期望的预约时间: {local_time.isoformat()}")
        
        returned_time = result.get('appointment_date')
        if returned_time:
            returned_dt = datetime.fromisoformat(returned_time.replace('Z', '+00:00'))
            expected_dt = local_time
            diff_hours = (expected_dt - returned_dt).total_seconds() / 3600
            print(f"时间差: {diff_hours:.2f} 小时")
            if abs(diff_hours) > 7.5 and abs(diff_hours) < 8.5:
                print("❌ 确认Bug存在: 时间差了约8小时！")
            else:
                print("✅ 时间差在正常范围内")
        return result
    except Exception as e:
        print(f"请求失败: {e}")
        return None

def test_bug3_date_filter():
    print("\n" + "=" * 60)
    print("测试 Bug3: 日期筛选显示昨天数据")
    print("=" * 60)
    
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    print(f"今天日期: {today}")
    print(f"昨天日期: {yesterday}")
    
    params = {
        "start_date": today.isoformat(),
        "end_date": today.isoformat()
    }
    
    print(f"\n筛选参数: {params}")
    
    try:
        response = requests.get(f"{BASE_URL}/appointments", params=params)
        print(f"响应状态码: {response.status_code}")
        results = response.json()
        print(f"返回记录数: {len(results)}")
        
        has_yesterday = False
        for apt in results:
            apt_date = apt.get('appointment_date', '')
            print(f"  预约ID: {apt['id']}, 时间: {apt_date}")
            if str(yesterday) in apt_date:
                has_yesterday = True
                print(f"    ❗ 发现昨天的记录！")
        
        if has_yesterday:
            print("❌ 确认Bug存在: 筛选今天但显示了昨天的数据！")
        else:
            print("✅ 没有发现昨天的数据")
            
        return results
    except Exception as e:
        print(f"请求失败: {e}")
        return None

def test_bug2_concurrent_stock():
    print("\n" + "=" * 60)
    print("测试 Bug2: 库存扣减负数（并发问题）")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/parts")
        parts = response.json()
        
        if not parts:
            print("没有配件数据，跳过测试")
            return None
            
        test_part = parts[0]
        print(f"测试配件: {test_part['name']}, 当前库存: {test_part['stock']}")
        
        if test_part['stock'] < 10:
            print("库存不足10，先补充库存")
            requests.patch(f"{BASE_URL}/parts/{test_part['id']}/stock?quantity=20&operation=add")
            response = requests.get(f"{BASE_URL}/parts/{test_part['id']}")
            test_part = response.json()
            print(f"补充后库存: {test_part['stock']}")
        
        print("\n⚠️  并发库存扣减测试需要同时发起多个请求")
        print("当前代码逻辑分析:")
        print("  1. 先查询库存: SELECT stock FROM parts WHERE id = ?")
        print("  2. 再判断库存是否足够: if stock < quantity: raise error")
        print("  3. 最后扣减库存: UPDATE parts SET stock = stock - ? WHERE id = ?")
        print("\n❌ 问题: 步骤1和3之间没有原子性保证，并发时会出现超卖")
        print("✅ 修复方案: 使用原子更新 UPDATE parts SET stock = stock - ? WHERE id = ? AND stock >= ?")
        
        return test_part
    except Exception as e:
        print(f"请求失败: {e}")
        return None

if __name__ == "__main__":
    print("\n🚀 开始测试三个Bug...\n")
    
    test_bug1_timezone()
    test_bug3_date_filter()
    test_bug2_concurrent_stock()
    
    print("\n" + "=" * 60)
    print("测试完成！查看调试日志获取更多细节")
    print("=" * 60)
