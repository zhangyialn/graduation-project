"""翻译相关路由定义。"""

from flask import Blueprint

from controllers.translateController import translate_text
from middleware.validation_middleware import validate_request


translateBlueprint = Blueprint('translate', __name__, url_prefix='/api/tools')

translateBlueprint.route('/translate', methods=['POST'])(
    validate_request(
        required_fields=['source_text'],
        optional_fields=['source', 'target', 'project_id']
    )(translate_text)
)
