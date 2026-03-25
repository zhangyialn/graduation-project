from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from config.config import Config
from models.index import db
from routes import userBlueprint, vehicleBlueprint, applicationBlueprint, approvalBlueprint, dispatchBlueprint, tripBlueprint, driverBlueprint, reportBlueprint, authBlueprint
from middleware.error_middleware import register_error_handlers


app = Flask(__name__)
CORS(app)

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
print('蓝图注册完成')

@app.route('/')
def index():
    print('访问服务器成功')
    return jsonify({'success': True, 'message': '访问服务器成功', 'data': None})



if __name__ == '__main__':
    app.run(debug=True)