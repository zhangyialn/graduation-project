"""控制器公共工具函数。"""

from flask import request


def enum_value(value):
    """兼容 Enum/字符串状态读取。"""
    return value.value if hasattr(value, 'value') else value


def normalize_identity(identity):
    """将 JWT identity 统一转换为整数，避免字符串/整数比较误差。"""
    if identity is None:
        return None
    try:
        return int(identity)
    except Exception:
        return identity


def parse_optional_pagination(default_limit=20, max_limit=100):
    """解析可选分页参数：有参数走分页，无参数保持历史全量返回。"""
    has_pagination = ('page' in request.args) or ('limit' in request.args)
    if not has_pagination:
        return None, None, False

    page = request.args.get('page', default=1, type=int) or 1
    limit = request.args.get('limit', default=default_limit, type=int) or default_limit
    page = max(page, 1)
    limit = min(max(limit, 1), max_limit)
    return page, limit, True


def pagination_meta(total, page, limit):
    """组装统一分页响应结构。"""
    pages = (total + limit - 1) // limit if limit else 0
    return {
        'total': total,
        'page': page,
        'limit': limit,
        'pages': pages,
        'has_next': page < pages,
        'has_prev': page > 1
    }
