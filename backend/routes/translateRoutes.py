"""翻译相关路由定义。"""

from flask import Blueprint

from controllers.translateController import translate_text, reverse_geocode_free, detect_login_location_free
from middleware.validationMiddleware import validate_request


translateBlueprint = Blueprint('translate', __name__, url_prefix='/api/tools')

translateBlueprint.route('/translate', methods=['POST'])(
    validate_request(
        required_fields=['source_text'],
        optional_fields=['source', 'target', 'project_id']
    )(translate_text)
)

translateBlueprint.route('/reverse-geocode', methods=['GET'])(reverse_geocode_free)
translateBlueprint.route('/login-location', methods=['GET'])(detect_login_location_free)
