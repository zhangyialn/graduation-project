# 公务用车在线申请与审批系统（毕业设计）

本项目是一个基于 Vue 3 + Flask 的公务用车管理系统，覆盖申请、审批、调度、行程执行、费用归档与报表分析的完整闭环。

## 1. 项目简介

### 1.1 建设目标
- 将传统线下用车流转流程线上化，提升审批效率与可追踪性。
- 打通申请、审批、调度、行程、费用、统计的全链路数据。
- 提供角色化权限控制，满足普通用户、司机、审批员、管理员的差异化操作。

### 1.2 角色说明
- user：普通用户，发起申请、查看本人申请与行程。
- driver：司机，查看任务、确认接客、填报里程油耗、更新状态。
- approver：审批员，审批申请、查看审批记录、参与调度与统计。
- admin：管理员，拥有用户/部门/车辆管理与系统初始化能力。

## 2. 技术栈

### 2.1 前端（frontend/vue-project）
- Vue 3
- Vue Router
- Pinia
- Element Plus + @element-plus/icons-vue
- Axios
- ECharts
- Vite

Node.js 版本要求：^20.19.0 || >=22.12.0

### 2.2 后端（backend）
- Flask
- Flask-Cors
- Flask-JWT-Extended
- Flask-Bcrypt
- Flask-SQLAlchemy + SQLAlchemy
- PyMySQL
- pandas / openpyxl / xlrd（用于 Excel 导入）
- python-dotenv

### 2.3 数据库
- MySQL 8.x
- 初始化脚本：database/database.sql
- 增量脚本：database/migrations/*.sql

## 3. 目录结构

```text
graduation-project/
├─ backend/
│  ├─ app.py
│  ├─ config/config.py
│  ├─ controllers/
│  ├─ middleware/
│  ├─ models/index.py
│  └─ routes/
├─ frontend/vue-project/
│  ├─ index.html
│  ├─ vite.config.js
│  └─ src/
│     ├─ main.js
│     ├─ router/
│     ├─ stores/
│     ├─ components/
│     └─ views/
└─ database/
	 ├─ database.sql
	 └─ migrations/
```

## 4. 核心业务流程

1. 用户发起申请（pending）。
2. 审批员或管理员审批（approved / rejected）。
3. 调度创建并启动（scheduled -> in_progress）。
4. 司机确认接客、填报里程油耗。
5. 乘客结束行程，系统计算费用并归档（completed）。
6. 报表按部门、车辆、司机、用户维度进行统计展示。

## 5. 当前实现要点

### 5.1 分页策略
申请、审批、行程的列表接口支持可选分页。

- 未传 page/limit：保持历史行为，返回全量 data。
- 传入 page/limit：返回 data + pagination。

pagination 字段示例：

```json
{
	"total": 100,
	"page": 1,
	"limit": 10,
	"pages": 10,
	"has_next": true,
	"has_prev": false
}
```

### 5.2 安全与鉴权
- JWT 登录态鉴权，前端统一通过 Axios 拦截器附带 Bearer Token。
- 路由守卫控制未登录访问与角色访问范围。
- must_change_password 用户会被强制跳转修改密码页面。
- 首个管理员初始化仅在系统无管理员时开放。

### 5.3 数据模型说明
- 司机信息已并入 users 表（role=driver），并通过 vehicle_id 关联车辆。
- 主要业务表包括：users、departments、vehicles、car_applications、approvals、dispatches、trips、expenses、fuel_prices、user_import_batches。

## 6. API 总览（与当前 routes 一致）

### 6.1 认证（/api/auth）
- POST /register
- POST /login
- POST /refresh
- GET /me
- POST /change-password
- POST /account-settings
- POST /verify-phone
- POST /reset-password
- GET /bootstrap-status
- POST /bootstrap-key
- POST /bootstrap-admin
- GET /dev-users
- POST /dev-switch-user

### 6.2 用户（/api/users）
- GET /
- GET /:id
- POST /
- POST /import
- POST /admins
- PUT /:id
- DELETE /:id
- GET /departments
- POST /departments
- GET /departments/admin-options
- PUT /departments/:department_id/leader

### 6.3 车辆与司机（/api/vehicles）
- GET /
- GET /:id
- POST /
- PUT /:id
- DELETE /:id
- GET /available
- GET /drivers
- POST /drivers
- PUT /drivers/:id
- DELETE /drivers/:id
- GET /drivers/available

### 6.4 申请（/api/applications）
- GET /
- GET /:id
- POST /
- PUT /:id
- POST /:id/cancel
- GET /my/:user_id
- GET /pending/:department_id
- POST /normalize-address
- GET /recommend-drivers

### 6.5 审批（/api/approvals）
- GET /
- GET /:id
- GET /application/:application_id
- GET /approver/:approver_id
- GET /statistics
- POST /application/:application_id/submit

### 6.6 调度（/api/dispatches）
- GET /
- GET /:id
- POST /
- POST /:id/start
- POST /:id/cancel
- GET /pending
- GET /recommend/:application_id

### 6.7 行程（/api/trips）
- GET /
- GET /management
- GET /my
- GET /:id
- POST /
- POST /:id/pickup
- POST /:id/driver-report
- POST /:id/end
- POST /:id/rate
- GET /:id/expense
- PUT /:id/expense
- GET /fuel-prices
- POST /fuel-prices

### 6.8 司机工作台（/api/drivers）
- GET /me/dashboard
- PUT /me/status
- PUT /me/vehicle-status
- PUT /me/bind-vehicle

### 6.9 报表（/api/reports）
- GET /department-usage
- GET /department-expenses
- GET /vehicle-usage
- GET /monthly-stats
- GET /driver-workload
- GET /user-application-stats

## 7. 本地运行

### 7.1 环境准备
- Python 3.10+
- Node.js 20+
- MySQL 8+

### 7.2 初始化数据库
1. 创建数据库 graduation-project。
2. 执行 database/database.sql。
3. 如需升级到新结构，按需执行 database/migrations 下增量脚本。

### 7.3 启动后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

默认地址：http://localhost:5000

### 7.4 启动前端

```bash
cd frontend/vue-project
npm install
npm run dev
```

默认地址：通常为 http://localhost:5173

## 8. 后端环境变量

backend/.env 示例：

```env
DATABASE_URL=mysql+pymysql://root:123456@localhost:3306/graduation-project
JWT_SECRET_KEY=your-secret-key-change-this-in-production
BOOTSTRAP_ADMIN_KEY=
BOOTSTRAP_TOKEN_EXPIRES=600
BOOTSTRAP_LOCAL_ONLY=true
```

## 9. 常见问题

### 9.1 401 未授权
- 检查是否登录过期。
- 清理本地会话后重新登录。

### 9.2 首个管理员无法初始化
- 系统已有管理员时入口会关闭，这是正常行为。

### 9.3 导入失败
- Excel 需包含 name、phone 等必需列。
- role 仅允许 user 或 approver。

## 10. 后续优化建议

- 引入 Alembic 做数据库版本管理。
- 增加 pytest 单元测试和接口回归测试。
- 增加审计日志页面与操作追踪。
- 增加 Docker 与 CI/CD 流程。
