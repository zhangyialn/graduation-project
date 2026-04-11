"""文本翻译与免费地理工具控制器。"""

import json
import threading
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import jsonify, request


_REVERSE_GEOCODE_CACHE = {}
_IP_LOCATION_CACHE = {}
_CACHE_LOCK = threading.Lock()
_REVERSE_GEOCODE_TTL_SECONDS = 10 * 60
_IP_LOCATION_TTL_SECONDS = 30 * 60


def _cache_get(container, key, ttl_seconds):
    """读取缓存并做过期判断，命中则返回值。"""
    now = time.time()
    with _CACHE_LOCK:
        item = container.get(key)
        if not item:
            return None
        if now - item['timestamp'] > ttl_seconds:
            container.pop(key, None)
            return None
        return item['value']


def _cache_set(container, key, value):
    """写入缓存，减少外部免费服务请求压力。"""
    with _CACHE_LOCK:
        container[key] = {
            'timestamp': time.time(),
            'value': value
        }


def _http_get_json(url, timeout=4, headers=None):
    """发起 GET 请求并解析 JSON 结果。"""
    req = Request(url, headers=headers or {'User-Agent': 'graduation-project/1.0'})
    with urlopen(req, timeout=timeout) as response:
        body = response.read().decode('utf-8')
        return json.loads(body)


def _build_address_text_nominatim(address=None):
    """将 Nominatim 结构化地址拼为可读中文文本。"""
    payload = address or {}
    province = payload.get('state') or payload.get('province') or ''
    city = payload.get('city') or payload.get('town') or payload.get('county') or payload.get('state_district') or ''
    district = payload.get('city_district') or payload.get('suburb') or payload.get('borough') or payload.get('quarter') or ''
    road = payload.get('road') or payload.get('pedestrian') or payload.get('residential') or payload.get('neighbourhood') or ''
    number = payload.get('house_number') or ''
    return ''.join([part for part in [province, city, district, road, number] if part])


def _build_address_text_bigdatacloud(data=None):
    """将 BigDataCloud 结果整理成短地址文本。"""
    payload = data or {}
    country_name = str(payload.get('countryName') or '').strip()
    principal_subdivision = str(payload.get('principalSubdivision') or '').strip()
    city = str(payload.get('city') or payload.get('locality') or '').strip()
    locality = str(payload.get('locality') or '').strip()

    parts = []
    for part in [country_name, principal_subdivision, city, locality]:
        if part and part not in parts:
            parts.append(part)
    return ''.join(parts)


def _reverse_geocode_nominatim(lat, lng):
    """调用 Nominatim 逆地理解析。"""
    query = urlencode({
        'format': 'jsonv2',
        'lat': str(lat),
        'lon': str(lng),
        'addressdetails': 1,
        'accept-language': 'zh-CN'
    })
    url = f'https://nominatim.openstreetmap.org/reverse?{query}'
    data = _http_get_json(url, timeout=4)
    address_text = _build_address_text_nominatim(data.get('address') if isinstance(data, dict) else None)
    fallback = str((data or {}).get('display_name') or '').strip() if isinstance(data, dict) else ''
    normalized = (address_text or fallback).strip()
    if not normalized:
        raise ValueError('nominatim empty address')
    return {
        'address': normalized,
        'source': 'nominatim'
    }


def _reverse_geocode_bigdatacloud(lat, lng):
    """调用 BigDataCloud 免费逆地理解析。"""
    query = urlencode({
        'latitude': str(lat),
        'longitude': str(lng),
        'localityLanguage': 'zh'
    })
    url = f'https://api-bdc.net/data/reverse-geocode-client?{query}'
    data = _http_get_json(url, timeout=4)
    address_text = _build_address_text_bigdatacloud(data if isinstance(data, dict) else None)
    if not address_text:
        raise ValueError('bigdatacloud empty address')
    return {
        'address': address_text,
        'source': 'bigdatacloud'
    }


def _extract_client_ip():
    """尽量提取真实客户端 IP，兼容反向代理场景。"""
    x_forwarded_for = str(request.headers.get('X-Forwarded-For') or '').strip()
    if x_forwarded_for:
        first = x_forwarded_for.split(',')[0].strip()
        if first and first.lower() != 'unknown':
            return first

    x_real_ip = str(request.headers.get('X-Real-IP') or '').strip()
    if x_real_ip and x_real_ip.lower() != 'unknown':
        return x_real_ip

    return str(request.remote_addr or '').strip()


def _build_ip_location_text(payload):
    """将 IP 归属地信息拼接为地点文本。"""
    country = str(payload.get('country') or payload.get('country_name') or '').strip()
    region = str(payload.get('region') or payload.get('regionName') or '').strip()
    city = str(payload.get('city') or '').strip()
    parts = [part for part in [country, region, city] if part]
    return ' '.join(parts).strip()


def _detect_ip_location_from_ipapi(ip_text):
    """通过 ipapi 获取 IP 地点。"""
    safe_ip = str(ip_text or '').strip()
    if safe_ip:
        url = f'https://ipapi.co/{safe_ip}/json/?lang=zh-CN'
    else:
        url = 'https://ipapi.co/json/?lang=zh-CN'
    data = _http_get_json(url, timeout=4)
    location_text = _build_ip_location_text(data if isinstance(data, dict) else {})
    if not location_text:
        raise ValueError('ipapi empty location')
    return {
        'location': location_text,
        'source': 'ipapi'
    }


def _detect_ip_location_from_ipwho(ip_text):
    """通过 ipwho.is 获取 IP 地点。"""
    safe_ip = str(ip_text or '').strip()
    if safe_ip:
        url = f'https://ipwho.is/{safe_ip}?lang=zh'
    else:
        url = 'https://ipwho.is/?lang=zh'
    data = _http_get_json(url, timeout=4)
    if isinstance(data, dict) and data.get('success') is False:
        raise ValueError('ipwho failed')
    location_text = _build_ip_location_text(data if isinstance(data, dict) else {})
    if not location_text:
        raise ValueError('ipwho empty location')
    return {
        'location': location_text,
        'source': 'ipwho'
    }


def reverse_geocode_free():
    """免费逆地理接口：双服务兜底并带缓存。"""
    try:
        lat = float(request.args.get('lat', '').strip())
        lng = float(request.args.get('lng', '').strip())
    except Exception:
        return jsonify({'success': False, 'message': 'lat/lng 参数格式不正确'}), 400

    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return jsonify({'success': False, 'message': 'lat/lng 超出有效范围'}), 400

    cache_key = f"{round(lat, 4)},{round(lng, 4)}"
    cached = _cache_get(_REVERSE_GEOCODE_CACHE, cache_key, _REVERSE_GEOCODE_TTL_SECONDS)
    if cached:
        return jsonify({
            'success': True,
            'data': {
                'address': cached['address'],
                'latitude': lat,
                'longitude': lng,
                'source': cached['source'],
                'cached': True
            }
        })

    providers = [_reverse_geocode_nominatim, _reverse_geocode_bigdatacloud]
    for provider in providers:
        try:
            result = provider(lat, lng)
            _cache_set(_REVERSE_GEOCODE_CACHE, cache_key, result)
            return jsonify({
                'success': True,
                'data': {
                    'address': result['address'],
                    'latitude': lat,
                    'longitude': lng,
                    'source': result['source'],
                    'cached': False
                }
            })
        except Exception:
            continue

    fallback_address = f'当前位置附近（纬度:{lat:.6f}，经度:{lng:.6f}）'
    return jsonify({
        'success': True,
        'data': {
            'address': fallback_address,
            'latitude': lat,
            'longitude': lng,
            'source': 'coordinate-fallback',
            'cached': False
        }
    })


def detect_login_location_free():
    """免费登录地点识别：优先读取客户端 IP，双服务兜底。"""
    ip_text = str(request.args.get('ip') or '').strip() or _extract_client_ip()
    cache_key = ip_text or 'auto'

    cached = _cache_get(_IP_LOCATION_CACHE, cache_key, _IP_LOCATION_TTL_SECONDS)
    if cached:
        return jsonify({
            'success': True,
            'data': {
                'location': cached['location'],
                'source': cached['source'],
                'cached': True,
                'ip': ip_text
            }
        })

    providers = [_detect_ip_location_from_ipapi, _detect_ip_location_from_ipwho]
    for provider in providers:
        try:
            result = provider(ip_text)
            _cache_set(_IP_LOCATION_CACHE, cache_key, result)
            return jsonify({
                'success': True,
                'data': {
                    'location': result['location'],
                    'source': result['source'],
                    'cached': False,
                    'ip': ip_text
                }
            })
        except Exception:
            continue

    return jsonify({
        'success': True,
        'data': {
            'location': '未知地点',
            'source': 'fallback',
            'cached': False,
            'ip': ip_text
        }
    })


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
