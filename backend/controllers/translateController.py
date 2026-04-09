"""文本翻译控制器。"""

from flask import jsonify, request


def _normalize_language(value, default_value):
    raw = str(value or '').strip().lower()
    if not raw:
        return default_value

    mapping = {
        'en-us': 'en',
        'en': 'en',
        'zh-cn': 'zh-CN',
        'zh': 'zh-CN',
        'zh-tw': 'zh-TW'
    }
    return mapping.get(raw, raw)


def _to_mymemory_code(value, fallback):
    """将通用语言代码映射为 MyMemory 可识别代码。"""
    normalized = _normalize_language(value, fallback)
    mapping = {
        'en': 'en-GB',
        'zh-CN': 'zh-CN',
        'zh-TW': 'zh-TW'
    }
    return mapping.get(normalized, normalized)


def translate_text():
    """调用免费翻译服务，将源语言文本翻译到目标语言。"""
    try:
        data = request.get_json() or {}
        source_text = str(data.get('source_text') or '').strip()
        source = _normalize_language(data.get('source'), 'en')
        target = _normalize_language(data.get('target'), 'zh')

        if not source_text:
            return jsonify({'success': False, 'message': 'source_text 不能为空'}), 400

        try:
            from deep_translator import MyMemoryTranslator
        except ImportError:
            return jsonify({
                'success': False,
                'message': '翻译依赖未安装，请安装 deep-translator'
            }), 500

        try:
            provider_source = _to_mymemory_code(source, 'en')
            provider_target = _to_mymemory_code(target, 'zh-CN')
            translated_text = MyMemoryTranslator(source=provider_source, target=provider_target).translate(source_text)
        except Exception as err:
            return jsonify({
                'success': False,
                'message': f'翻译服务调用失败: {str(err)}'
            }), 502

        translated_text = str(translated_text or '').strip()

        return jsonify({
            'success': True,
            'data': {
                'target_text': translated_text,
                'source': source,
                'target': target,
                'request_id': 'free-mymemory-translator'
            }
        }), 200
    except Exception as err:
        return jsonify({'success': False, 'message': str(err)}), 500
