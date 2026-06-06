# 汽车4S店售后保养预约及配件消耗追踪系统

## 技术栈
- **后端**: FastAPI + SQLAlchemy + SQLite
- **前端**: Vue 3 + Vite + Element Plus
- **端口**: 后端 8083, 前端 3083

## 功能模块

### 1. 车主在线预约
- 填写车辆信息（姓名、电话、车型、车牌号）
- 选择服务类型（常规保养、大保养、维修服务等）
- 选择预约时间
- 提交预约申请

### 2. 预约管理
- 查看所有预约列表
- 按状态、日期筛选
- 确认预约
- 创建工单（指派技师）
- 删除预约

### 3. 工单管理
- 查看所有工单
- 按状态、技师筛选
- 查看工单详情

### 4. 技师接单与工单处理
- 开始维修（状态变为进行中）
- 记录工时费
- 添加配件消耗（自动扣减库存）
- 移除配件（自动退回库存）
- 完成维修（状态变为已完成）
- 生成工单结算单

### 5. 技师管理
- 新增技师（姓名、电话、专长）
- 更改技师状态（空闲/工作中/休息）
- 技师状态统计

### 6. 配件库存管理
- 新增配件（编码、名称、分类、价格、库存、预警值）
- 配件入库（增加库存）
- 配件出库（减少库存）
- 库存预警（低于最小值提示）
- 按分类、关键词搜索
- 库存统计（总值、分类统计）

## 项目结构

```
rk-83/
├── backend/                    # 后端项目
│   ├── main.py                # 主入口文件
│   ├── requirements.txt       # Python依赖
│   ├── init_data.py           # 初始化数据脚本
│   ├── database/
│   │   └── __init__.py        # 数据库连接
│   ├── models/
│   │   └── __init__.py        # 数据库模型
│   ├── schemas/
│   │   └── __init__.py        # Pydantic模式
│   └── routers/
│       ├── appointments.py    # 预约API
│       ├── technicians.py    # 技师API
│       ├── parts.py          # 配件API
│       └── work_orders.py    # 工单API
└── frontend/                  # 前端项目
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── main.js
        ├── App.vue
        ├── api/
        │   └── index.js       # API封装
        ├── router/
        │   └── index.js       # 路由配置
        └── views/             # 页面组件
            ├── Dashboard.vue
            ├── AppointmentForm.vue
            ├── Appointments.vue
            ├── WorkOrders.vue
            ├── WorkOrderDetail.vue
            ├── Technicians.vue
            └── Parts.vue
```

## 快速开始

### 1. 启动后端服务
```bash
cd backend
pip install -r requirements.txt
python init_data.py          # 初始化测试数据
python main.py               # 启动服务，端口 8083
```

### 2. 启动前端服务
```bash
cd frontend
npm install
npm run dev                  # 启动服务，端口 3083
```

### 3. 访问系统
- 前端地址: http://localhost:3083
- 后端API文档: http://localhost:8083/docs

## API接口

### 预约管理
- `GET /api/appointments` - 获取预约列表
- `POST /api/appointments` - 创建预约
- `PUT /api/appointments/{id}` - 更新预约
- `DELETE /api/appointments/{id}` - 删除预约

### 技师管理
- `GET /api/technicians` - 获取技师列表
- `POST /api/technicians` - 新增技师
- `PUT /api/technicians/{id}/status` - 更新技师状态

### 配件管理
- `GET /api/parts` - 获取配件列表
- `POST /api/parts` - 新增配件
- `PATCH /api/parts/{id}/stock` - 更新库存
- `GET /api/parts/statistics/inventory` - 库存统计

### 工单管理
- `GET /api/work-orders` - 获取工单列表
- `POST /api/work-orders` - 创建工单
- `PUT /api/work-orders/{id}/status` - 更新工单状态
- `POST /api/work-orders/{id}/parts` - 添加配件消耗
- `DELETE /api/work-orders/{id}/parts/{part_id}` - 移除配件
- `GET /api/work-orders/{id}/invoice` - 获取工单结算单
- `GET /api/work-orders/statistics/dashboard` - 仪表板统计

## 业务流程

1. **车主预约**: 车主通过在线预约页面提交保养/维修申请
2. **确认预约**: 管理员确认预约信息
3. **创建工单**: 为预约指派技师，创建工单
4. **开始维修**: 技师开始维修，工单状态变为"进行中"
5. **配件消耗**: 维修过程中使用的配件自动从库存中扣减
6. **完成维修**: 技师完成维修，记录工时费，生成结算单
7. **库存管理**: 管理员可以随时查看库存，进行入库/出库操作
