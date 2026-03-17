from flask import Flask, jsonify, Response
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from models.index import db
from routes import userBlueprint, vehicleBlueprint, applicationBlueprint, approvalBlueprint, dispatchBlueprint, tripBlueprint, reportBlueprint, authBlueprint
from middleware import auth_middleware, error_middleware, validation_middleware

app = Flask(__name__)
CORS(app)

# 配置JSON返回中文
app.config['JSON_AS_ASCII'] = False
app.config['RESTFUL_JSON'] = {'ensure_ascii': False}

# 配置JWT
app.config['JWT_SECRET_KEY'] = 'your-secret-key-change-this-in-production'  # 生产环境请更换为随机密钥
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600  # 访问令牌有效期：1小时
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = 604800  # 刷新令牌有效期：7天

# 初始化扩展
jwt = JWTManager(app)
bcrypt = Bcrypt(app)

# 配置数据库
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost:3306/graduation-project'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# 初始化数据库
db.init_app(app)

# 注册中间件
app.before_request(auth_middleware.validate_request)
app.errorhandler(400)(error_middleware.error_handler)
app.errorhandler(401)(error_middleware.error_handler)
app.errorhandler(403)(error_middleware.error_handler)
app.errorhandler(404)(error_middleware.error_handler)
app.errorhandler(500)(error_middleware.error_handler)
validation_middleware.register_error_handlers(app)


# 注册蓝图
app.register_blueprint(authBlueprint)
app.register_blueprint(userBlueprint)
app.register_blueprint(vehicleBlueprint)
app.register_blueprint(applicationBlueprint)
app.register_blueprint(approvalBlueprint)
app.register_blueprint(dispatchBlueprint)
app.register_blueprint(tripBlueprint)
app.register_blueprint(reportBlueprint)

# 路由映射


if __name__ == '__main__':
    app.run(debug=True)