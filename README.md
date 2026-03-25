# 公务用车在线申请与审批系统（毕业设计）

一个基于 **Vue 3 + Flask** 的公务用车管理系统，覆盖从“申请 → 审批 → 调度 → 出车 → 费用统计”的完整业务闭环，并提供管理员初始化、用户导入、司机工作台、油价管理和报表可视化能力。

---

## 1. 项目概述

### 1.1 目标
- 解决传统公务用车流程线下流转慢、状态不透明、费用难追踪的问题。
- 建立可追踪、可审计、可视化的用车流程系统。

### 1.2 主要能力
- 用户发起用车申请（起点、目的地、时间、人数等）。
- 审批员/管理员审批申请。
- 调度分配车辆与司机。
- 司机执行行程并结束出车。
- 系统自动计算里程与费用（结合油价和油耗）。
- 报表展示部门/车辆/司机/用户维度统计。

### 1.3 角色模型
- `user`：普通用户，发起并查看自己的申请。
- `driver`：司机，查看任务、更新状态、结束行程。
- `approver`：审批员，审批申请、查看审批记录与报表。
- `admin`：管理员，拥有导入、管理员管理、车辆/调度等高级权限。

---

## 2. 技术栈

### 2.1 前端（`frontend/vue-project`）
- Vue 3
- Vue Router
- Pinia
- Element Plus + `@element-plus/icons-vue`
- Axios
- ECharts
- Vite

> Node.js 要求：`^20.19.0 || >=22.12.0`（来自 `package.json`）

### 2.2 后端（`backend`）
- Flask 3.1.3
- Flask-Cors
- Flask-JWT-Extended 4.6.0
- Flask-Bcrypt 1.0.1
- Flask-SQLAlchemy 3.1.1
- SQLAlchemy
- PyMySQL 1.1.1
- pandas 2.2.3
- openpyxl 3.1.5
- xlrd 2.0.1
- python-dotenv 1.0.0

### 2.3 数据库
- MySQL 8.x
- SQL 文件：`database/database.sql`

---

## 3. 项目结构

```text
graduation-project/
├─ backend/                     # Flask 后端
│  ├─ app.py                    # 应用入口
│  ├─ config/config.py          # 配置项（DB、JWT、初始化管理员策略）
│  ├─ controllers/              # 业务控制器
│  ├─ middleware/               # 鉴权、校验、错误处理中间件
│  ├─ models/index.py           # SQLAlchemy 模型与枚举
│  └─ routes/                   # API 路由蓝图
├─ frontend/vue-project/        # Vue 前端
│  ├─ src/main.js               # 前端入口（Axios 拦截器）
│  ├─ src/router/index.js       # 路由与权限守卫
│  ├─ src/stores/               # Pinia 状态管理
│  ├─ src/components/           # 业务组件
│  └─ src/views/                # 页面级视图
└─ database/database.sql        # 初始化表结构
```

---

## 4. 核心业务流程

### 4.1 用车主流程
1. 普通用户创建申请（状态 `pending`）。
2. 审批员/管理员审批（`approved` / `rejected`）。
3. 调度员（当前由具备权限角色）创建调度（`scheduled`）。
4. 调度启动后进入行程阶段（`in_progress` / `started`）。
5. 司机或授权用户结束行程，系统计算费用并归档（`completed`）。

### 4.2 费用计算逻辑（出车结束）
- 里程：`distance_km = end_mileage - start_mileage`
- 单公里成本：
	- 优先使用前端显式传入 `cost_per_km`
	- 否则按 `fuel_consumption_per_100km / 100 * fuel_price`
- 总费用：`fuel_cost + maintenance_cost + other_cost`

### 4.3 首个管理员初始化
- 当系统中无管理员时，`/api/auth/bootstrap-status` 返回可初始化。
- 前端可生成一次性密钥（默认 10 分钟有效）。
- 密钥绑定当前浏览器（UA 哈希）且只可使用一次。
- 初始化成功后入口自动关闭。

---

## 5. 权限与安全机制

### 5.1 登录态与鉴权
- 使用 JWT（访问令牌 + 刷新令牌）。
- 前端 Axios 请求拦截器自动附加 `Authorization: Bearer <token>`。
- 路由守卫会在无 token 时跳转登录页。

### 5.2 强制改密机制
- 由管理员创建/导入的用户默认密码为手机号。
- 此类用户 `must_change_password = true`。
- 前端路由守卫会强制跳转到修改密码页。

### 5.3 参数校验与错误标准化
- 后端 `validate_request` 中间件统一校验必填、白名单字段、邮箱/手机号格式。
- 返回结构化错误 `errors[]`，前端统一拼接并友好展示。

---

## 6. 主要功能模块

### 6.1 认证与账户
- 登录、注册、刷新 token。
- 获取当前用户。
- 修改密码。
- 手机号找回密码（用户名 + 手机号双因子校验）。

### 6.2 用户与组织
- 用户增删改查（软删除）。
- Excel 批量导入（仅支持 `user/approver`）。
- 管理员创建管理员（需输入当前管理员密码二次确认）。
- 部门管理。

### 6.3 车辆与司机
- 车辆 CRUD、可用车辆查询。
- 司机 CRUD、可用司机查询。
- 司机与用户、车辆绑定。

### 6.4 申请、审批、调度
- 申请创建、查看、取消。
- 审批提交与统计。
- 调度创建、启动、取消、推荐调度。

### 6.5 行程与费用
- 行程创建、结束。
- 费用明细查询与更新。
- 油价查询/写入、与油耗联动计算燃油成本。

### 6.6 报表可视化
- 部门用车频率
- 部门费用统计
- 车辆使用与费用
- 月度趋势
- 司机工作量
- 用户申请统计

---

## 7. 数据库设计（摘要）

核心表：
- `users`：用户（含角色、软删除、强制改密标记）
- `departments`：部门
- `vehicles`：车辆
- `drivers`：司机
- `car_applications`：用车申请
- `approvals`：审批记录
- `dispatches`：调度单
- `trips`：行程
- `expenses`：费用
- `fuel_prices`：油价
- `user_import_batches`：导入批次审计

完整建表语句见 `database/database.sql`。

---

## 8. API 分组总览（后端）

### 8.1 认证（`/api/auth`）
- `POST /register`
- `POST /login`
- `POST /refresh`
- `GET /me`
- `POST /change-password`
- `POST /verify-phone`
- `POST /reset-password`
- `GET /bootstrap-status`
- `POST /bootstrap-key`
- `POST /bootstrap-admin`

### 8.2 用户（`/api/users`）
- `GET /`
- `GET /:id`
- `POST /`
- `POST /import`
- `POST /admins`
- `PUT /:id`
- `DELETE /:id`
- `GET /departments`
- `POST /departments`

### 8.3 车辆/司机（`/api/vehicles`）
- `GET /`
- `GET /:id`
- `POST /`
- `PUT /:id`
- `DELETE /:id`
- `GET /available`
- `GET /drivers`
- `POST /drivers`
- `PUT /drivers/:id`
- `DELETE /drivers/:id`
- `GET /drivers/available`

### 8.4 申请（`/api/applications`）
- `GET /`
- `GET /:id`
- `POST /`
- `PUT /:id`
- `POST /:id/cancel`
- `GET /my/:user_id`
- `GET /pending/:department_id`
- `POST /normalize-address`

### 8.5 审批（`/api/approvals`）
- `GET /`
- `GET /:id`
- `GET /application/:application_id`
- `GET /approver/:approver_id`
- `GET /statistics`
- `POST /application/:application_id/submit`

### 8.6 调度（`/api/dispatches`）
- `GET /`
- `GET /:id`
- `POST /`
- `POST /:id/start`
- `POST /:id/cancel`
- `GET /pending`
- `GET /recommend/:application_id`

### 8.7 行程（`/api/trips`）
- `GET /`
- `GET /:id`
- `POST /`
- `POST /:id/end`
- `GET /:id/expense`
- `PUT /:id/expense`
- `GET /fuel-prices`
- `POST /fuel-prices`

### 8.8 司机工作台（`/api/drivers`）
- `GET /me/dashboard`
- `PUT /me/status`
- `PUT /me/vehicle-status`
- `PUT /me/bind-vehicle`

### 8.9 报表（`/api/reports`）
- `GET /department-usage`
- `GET /department-expenses`
- `GET /vehicle-usage`
- `GET /monthly-stats`
- `GET /driver-workload`
- `GET /user-application-stats`

---

## 9. 本地部署指南（Windows 示例）

### 9.1 前置条件
- Python 3.10+
- Node.js 20+
- MySQL 8+

### 9.2 初始化数据库
1. 创建数据库：`graduation-project`
2. 执行 SQL：`database/database.sql`

### 9.3 启动后端
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

默认后端地址：`http://localhost:5000`

### 9.4 启动前端
```bash
cd frontend/vue-project
npm install
npm run dev
```

默认前端地址：Vite 控制台输出地址（通常 `http://localhost:5173`）

---

## 10. 环境变量说明（后端）

`backend/.env` 常用配置：

```env
DATABASE_URL=mysql+pymysql://root:123456@localhost:3306/graduation-project
JWT_SECRET_KEY=your-secret-key-change-this-in-production

# 可选：首个管理员初始化主密钥（不为空时前端需填写）
BOOTSTRAP_ADMIN_KEY=

# 可选：初始化密钥有效期（秒）
BOOTSTRAP_TOKEN_EXPIRES=600

# 可选：是否仅允许本机/内网初始化
BOOTSTRAP_LOCAL_ONLY=true
```

---

## 11. 前端路由与页面

核心页面：
- 登录 / 找回密码 / 首个管理员初始化
- 仪表盘首页
- 用车申请创建与列表
- 审批列表与审批详情
- 车辆与司机管理
- 调度管理
- 导入中心（管理员）
- 管理员管理（管理员）
- 油价管理
- 报表可视化
- 审批记录
- 司机面板
- 修改密码

路由守卫规则：
- 未登录禁止访问 `/dashboard/**`
- `must_change_password=true` 时强制进入 `/dashboard/change-password`
- 管理员专属路由由 `meta.roles=['admin']` 控制

---

## 12. 常见问题与排查

### 12.1 后端依赖安装失败
- 确认使用了虚拟环境。
- 确认 `pip` 与 Python 版本匹配。

### 12.2 前端请求 401
- 令牌失效会被前端拦截器自动清理并跳回登录。
- 重新登录后重试。

### 12.3 初始化管理员入口不可用
- 若系统已有管理员，入口会自动关闭（这是预期行为）。
- 若仅测试环境需重开入口，请清理管理员数据后再访问。

### 12.4 导入失败
- Excel 必须包含 `name`、`phone` 列。
- `role` 仅支持 `user` 或 `approver`。
- 手机号/用户名/邮箱重复会被跳过并记录失败原因。

---

## 13. 后续可扩展方向
- 接入迁移工具（Alembic）统一数据库版本管理。
- 增加单元测试与接口测试（pytest）。
- 增加审计日志与操作追踪页面。
- 完善 Docker 化部署与 CI/CD。

---

## 14. 英文简介（English Summary）

This is an official vehicle management system built with **Vue 3 + Flask**.
It supports the full workflow of **application, approval, dispatch, trip execution, and expense calculation**, along with **bootstrap admin initialization**, **Excel user import**, **driver dashboard**, **fuel price management**, and **visual reports**.

For setup, see sections **9 (Local Deployment)** and **10 (Environment Variables)** above.
