from flask import Flask, jsonify
from flask_cors import CORS
from models.index import db
from routes import userBlueprint, vehicleBlueprint, applicationBlueprint, approvalBlueprint, dispatchBlueprint, tripBlueprint, reportBlueprint

app = Flask(__name__)
CORS(app)

# 配置JSON返回中文
app.json.ensure_ascii = False

# 配置数据库
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost:3306/graduation-project'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db.init_app(app)

# 注册蓝图
app.register_blueprint(userBlueprint)
app.register_blueprint(vehicleBlueprint)
app.register_blueprint(applicationBlueprint)
app.register_blueprint(approvalBlueprint)
app.register_blueprint(dispatchBlueprint)
app.register_blueprint(tripBlueprint)
app.register_blueprint(reportBlueprint)

# 根路由
@app.route('/')
def index():
    return jsonify({
        'message': '公务用车管理系统API',
        'version': '1.0.0',
        'endpoints': {
            'users': '/api/users',
            'vehicles': '/api/vehicles',
            'applications': '/api/applications',
            'approvals': '/api/approvals',
            'dispatches': '/api/dispatches',
            'trips': '/api/trips',
            'reports': '/api/reports'
        }
    })

if __name__ == '__main__':
    app.run(debug=True)