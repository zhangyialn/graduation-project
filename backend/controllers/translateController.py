"""文本翻译控制器。"""

import datetime
import hashlib
import hmac
import json
import time
from urllib import error as urllib_error
from urllib import request as urllib_request

from flask import current_app, jsonify, request


def _normalize_language(value, default_value):
    raw = str(value or '').strip().lower()
    if not raw:
        return default_value

    mapping = {
        'en-us': 'en',
        'en': 'en',
        'zh-cn': 'zh',
        'zh': 'zh'
    }
    return mapping.get(raw, raw)


def _sha256_hex(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _hmac_sha256(key_bytes, message_text):
    return hmac.new(key_bytes, message_text.encode('utf-8'), hashlib.sha256).digest()


def _build_tencent_headers(payload_json, secret_id, secret_key, region):
    service = 'tmt'
    host = 'tmt.tencentcloudapi.com'
    action = 'TextTranslate'
    version = '2018-03-21'
    algorithm = 'TC3-HMAC-SHA256'

    timestamp = int(time.time())
    date_text = datetime.datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d')

    canonical_headers = f'content-type:application/json; charset=utf-8\nhost:{host}\n'
    signed_headers = 'content-type;host'
    hashed_payload = _sha256_hex(payload_json)
    canonical_request = f'POST\n/\n\n{canonical_headers}\n{signed_headers}\n{hashed_payload}'

    credential_scope = f'{date_text}/{service}/tc3_request'
    string_to_sign = f'{algorithm}\n{timestamp}\n{credential_scope}\n{_sha256_hex(canonical_request)}'

    secret_date = _hmac_sha256(('TC3' + secret_key).encode('utf-8'), date_text)
    secret_service = hmac.new(secret_date, service.encode('utf-8'), hashlib.sha256).digest()
    secret_signing = hmac.new(secret_service, b'tc3_request', hashlib.sha256).digest()
    signature = hmac.new(secret_signing, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

    authorization = (
        f'{algorithm} '
        f'Credential={secret_id}/{credential_scope}, '
        f'SignedHeaders={signed_headers}, '
        f'Signature={signature}'
    )

    return {
        'Authorization': authorization,
        'Content-Type': 'application/json; charset=utf-8',
        'Host': host,
        'X-TC-Action': action,
        'X-TC-Version': version,
        'X-TC-Region': region,
        'X-TC-Timestamp': str(timestamp)
    }


def translate_text():
    """调用腾讯云 TMT，将英文翻译为中文。"""
    try:
        data = request.get_json() or {}
        source_text = str(data.get('source_text') or '').strip()
        source = _normalize_language(data.get('source'), 'en')
        target = _normalize_language(data.get('target'), 'zh')
        project_id = data.get('project_id', 0)

        if not source_text:
            return jsonify({'success': False, 'message': 'source_text 不能为空'}), 400

        try:
            project_id = int(project_id)
        except Exception:
            project_id = 0

        secret_id = current_app.config.get('TENCENT_SECRET_ID', '')
        secret_key = current_app.config.get('TENCENT_SECRET_KEY', '')
        region = current_app.config.get('TENCENT_TMT_REGION', 'ap-beijing')
        timeout_seconds = int(current_app.config.get('TENCENT_TMT_TIMEOUT', 5))

        if not secret_id or not secret_key:
            return jsonify({
                'success': False,
                'message': '翻译服务未配置，请设置 TENCENT_SECRET_ID 与 TENCENT_SECRET_KEY'
            }), 500

        payload = {
            'SourceText': source_text,
            'Source': source,
            'Target': target,
            'ProjectId': project_id
        }
        payload_json = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
        headers = _build_tencent_headers(payload_json, secret_id, secret_key, region)

        req = urllib_request.Request(
            url='https://tmt.tencentcloudapi.com/',
            data=payload_json.encode('utf-8'),
            headers=headers,
            method='POST'
        )

        try:
            with urllib_request.urlopen(req, timeout=timeout_seconds) as response:
                body_text = response.read().decode('utf-8')
        except urllib_error.HTTPError as http_err:
            body_text = http_err.read().decode('utf-8', errors='ignore')
            try:
                upstream = json.loads(body_text)
                upstream_error = (upstream.get('Response') or {}).get('Error') or {}
                return jsonify({
                    'success': False,
                    'message': upstream_error.get('Message') or '翻译服务调用失败',
                    'error_code': upstream_error.get('Code'),
                    'request_id': (upstream.get('Response') or {}).get('RequestId')
                }), 502
            except Exception:
                return jsonify({'success': False, 'message': '翻译服务调用失败'}), 502

        result = json.loads(body_text)
        response_data = result.get('Response') or {}
        upstream_error = response_data.get('Error')
        if upstream_error:
            return jsonify({
                'success': False,
                'message': upstream_error.get('Message') or '翻译失败',
                'error_code': upstream_error.get('Code'),
                'request_id': response_data.get('RequestId')
            }), 502

        return jsonify({
            'success': True,
            'data': {
                'target_text': response_data.get('TargetText') or '',
                'source': response_data.get('Source') or source,
                'target': response_data.get('Target') or target,
                'request_id': response_data.get('RequestId')
            }
        }), 200
    except Exception as err:
        return jsonify({'success': False, 'message': str(err)}), 500
