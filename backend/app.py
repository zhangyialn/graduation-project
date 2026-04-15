"""Flask 应用入口。"""

import logging
import time
from flask import Flask, jsonify, g, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from config.appConfig import Config
from models.index import db
from routes import userBlueprint, vehicleBlueprint, applicationBlueprint, approvalBlueprint, dispatchBlueprint, tripBlueprint, driverBlueprint, reportBlueprint, authBlueprint, translateBlueprint
from middleware.errorMiddleware import register_error_handlers


app = Flask(__name__)
CORS(app)

# 中文日志格式化器：将默认英文级别映射为中文，便于排查问题。
class ChineseLevelFormatter(logging.Formatter):
    LEVEL_NAME_MAP = {
        'DEBUG': '调试',
        'INFO': '信息',
        'WARNING': '警告',
        'ERROR': '错误',
        'CRITICAL': '严重'
    }

    def format(self, record):
        original_level_name = record.levelname
        record.levelname = self.LEVEL_NAME_MAP.get(original_level_name, original_level_name)
        try:
            return super().format(record)
        finally:
            record.levelname = original_level_name


def configure_chinese_logging():
    """统一后端日志为中文输出，降低默认英文噪声。"""
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(
        ChineseLevelFormatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s')
    )

    root_logger.addHandler(stream_handler)
    root_logger.setLevel(logging.INFO)

    # werkzeug 默认访问日志信息量较大，这里只保留错误级别，减少英文输出。
    logging.getLogger('werkzeug').setLevel(logging.ERROR)


# 统一日志输出等级，便于在开发/联调阶段追踪请求链路。
configure_chinese_logging()
logger = logging.getLogger(__name__)

# 配置
app.config.from_object(Config)
app.json.ensure_ascii = False
print('配置加载完成')

# 初始化扩展
jwt = JWTManager(app)
bcrypt = Bcrypt(app)
print('扩展初始化完成')



# 初始化数据库
db.init_app(app)
print('数据库初始化完成')


# 注册中间件
register_error_handlers(app)
print('中间件注册完成')


# 注册蓝图
app.register_blueprint(authBlueprint)
app.register_blueprint(userBlueprint)
app.register_blueprint(vehicleBlueprint)
app.register_blueprint(applicationBlueprint)
app.register_blueprint(approvalBlueprint)
app.register_blueprint(dispatchBlueprint)
app.register_blueprint(tripBlueprint)
app.register_blueprint(driverBlueprint)
app.register_blueprint(reportBlueprint)
app.register_blueprint(translateBlueprint)
print('蓝图注册完成')


# 请求进入时打时间戳，供响应阶段统一计算耗时。
@app.before_request
def mark_request_start():
    # 记录请求开始时间，供 after_request 统计耗时
    g.request_start_at = time.time()


# 请求结束后输出访问日志，并对慢请求单独告警。
@app.after_request
def log_request_latency(response):
    # 某些极早返回的请求可能未进入 before_request，这里做兜底。
    start = getattr(g, 'request_start_at', None)
    if start is None:
        return response

    elapsed_ms = (time.time() - start) * 1000
    message = f"请求={request.method} {request.path} | 状态码={response.status_code} | 耗时={elapsed_ms:.1f}ms"
    # 1s 以上请求按慢请求告警，便于定位 SQL/外部接口瓶颈。
    if elapsed_ms >= 1000:
        logger.warning(f"慢请求告警 | {message}")
    else:
        logger.info(f"请求完成 | {message}")
    return response

@app.route('/')
# 健康检查与基础连通性验证接口
def index():
    print('访问服务器成功')
    return jsonify({'success': True, 'message': '访问服务器成功', 'data': None})



if __name__ == '__main__':
    app.run(debug=True)
