"""行程与油价领域服务。"""

from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import requests
from models.index import db, Expense, FuelPrice


GUI_GUI_YA_OIL_API_URL = 'http://api.guiguiya.com/api/youjia'
GUI_GUI_YA_REGION_MAP = {
    'n92': '92',
    'n95': '95',
    'n98': '98',
    'n0': 'chaiyou'
}

_FUEL_TYPE_COMPAT_GROUPS = {
    '汽油': ['汽油', '92号汽油', '95号汽油', '98号汽油'],
    '92号汽油': ['汽油', '92号汽油', '95号汽油', '98号汽油'],
    '95号汽油': ['汽油', '92号汽油', '95号汽油', '98号汽油'],
    '98号汽油': ['汽油', '92号汽油', '95号汽油', '98号汽油'],
    '柴油': ['柴油', '0号柴油'],
    '0号柴油': ['柴油', '0号柴油']
}


class ExternalOilCache:
    """第三方油价短缓存。"""

    def __init__(self, ttl_seconds=600):
        self.ttl_seconds = ttl_seconds
        self._data = None
        self._expires_at = 0
        self._fetched_at = None

    def get_if_valid(self, now_ts, force_refresh=False):
        if force_refresh:
            return None
        if self._data and self._expires_at > now_ts:
            return {
                'success': True,
                'data': self._data,
                'cached': True,
                'cached_at': self._fetched_at
            }
        return None

    def store(self, raw_by_fuel, now_ts):
        fetched_at = datetime.utcnow().isoformat()
        self._data = raw_by_fuel
        self._expires_at = now_ts + self.ttl_seconds
        self._fetched_at = fetched_at
        return fetched_at


external_oil_cache = ExternalOilCache(ttl_seconds=600)


def is_force_refresh(value):
    return str(value or '').strip() in ['1', 'true', 'True']


def find_latest_fuel_price(vehicle_fuel_type):
    # 先精确油号查询，查不到再走油品族兜底，保持历史口径。
    normalized_fuel_type = str(vehicle_fuel_type or '汽油').strip() or '汽油'
    latest_price = FuelPrice.query.filter_by(
        fuel_type=normalized_fuel_type
    ).order_by(FuelPrice.effective_date.desc()).first()
    if latest_price:
        return latest_price

    compat_group = _FUEL_TYPE_COMPAT_GROUPS.get(normalized_fuel_type)
    if not compat_group:
        return None

    return FuelPrice.query.filter(
        FuelPrice.fuel_type.in_(compat_group)
    ).order_by(FuelPrice.effective_date.desc()).first()


def calculate_trip_expense(mileage, fuel_used_value, vehicle, request_fuel_price=None, request_cost_per_km=None):
    latest_price = find_latest_fuel_price(vehicle.fuel_type if vehicle else '汽油')
    fuel_price_value = float(request_fuel_price) if request_fuel_price is not None else float(latest_price.price) if latest_price else 0.0

    if request_cost_per_km is not None:
        cost_per_km = float(request_cost_per_km)
        fuel_cost = mileage * cost_per_km
    elif vehicle and vehicle.fuel_consumption_per_100km is not None:
        cost_per_km = float(vehicle.fuel_consumption_per_100km) / 100 * fuel_price_value
        fuel_cost = mileage * cost_per_km
    else:
        fuel_used = max(float(fuel_used_value), 0)
        fuel_cost = fuel_used * fuel_price_value if fuel_price_value > 0 else 0.0
        cost_per_km = (fuel_cost / mileage) if mileage > 0 else 0.0

    return {
        'fuel_price_value': fuel_price_value,
        'cost_per_km': cost_per_km,
        'fuel_cost': fuel_cost,
        'total_cost': fuel_cost
    }


def upsert_trip_expense(trip_id, mileage, cost_per_km, fuel_cost, total_cost, fuel_price_value):
    expense = Expense.query.filter_by(trip_id=trip_id).first()
    if not expense:
        expense = Expense(
            trip_id=trip_id,
            mileage_km=mileage,
            cost_per_km=cost_per_km,
            fuel_cost=fuel_cost,
            total_cost=total_cost,
            fuel_price=fuel_price_value
        )
        db.session.add(expense)
        return expense

    expense.mileage_km = mileage
    expense.cost_per_km = cost_per_km
    expense.fuel_cost = fuel_cost
    expense.total_cost = total_cost
    expense.fuel_price = fuel_price_value
    return expense


def fetch_external_oil_prices(api_url=GUI_GUI_YA_OIL_API_URL, region_map=None, timeout=8):
    region_map = region_map or GUI_GUI_YA_REGION_MAP

    def _fetch_single(fuel_field, region_code):
        response = requests.get(
            api_url,
            params={'region': region_code},
            timeout=timeout
        )
        response.raise_for_status()
        payload = response.json() if response.content else {}
        if int(payload.get('code', 0)) != 200:
            raise ValueError(f'油价接口返回异常: {fuel_field}')
        return fuel_field, payload

    raw_by_fuel = {}
    with ThreadPoolExecutor(max_workers=len(region_map)) as executor:
        futures = [
            executor.submit(_fetch_single, fuel_field, region_code)
            for fuel_field, region_code in region_map.items()
        ]

        for future in futures:
            fuel_field, payload = future.result()
            raw_by_fuel[fuel_field] = payload

    return raw_by_fuel


def prepare_fuel_price_batch_items(raw_items, default_effective_date=None, default_source=None):
    items = []
    for raw in raw_items:
        region_name = str(raw.get('region_name') or '').strip() or '未知省份'
        fuel_type = raw.get('fuel_type')
        price_value = raw.get('price')
        effective_date = raw.get('effective_date') or default_effective_date
        source = raw.get('source') or default_source

        if not fuel_type or price_value is None or not effective_date:
            return None

        items.append({
            'region_name': region_name,
            'fuel_type': fuel_type,
            'price': price_value,
            'effective_date': effective_date,
            'source': source
        })
    return items


def upsert_fuel_prices_batch(items):
    region_set = {item['region_name'] for item in items}
    fuel_set = {item['fuel_type'] for item in items}
    date_set = {item['effective_date'] for item in items}

    existing_rows = FuelPrice.query.filter(
        FuelPrice.region_name.in_(list(region_set)),
        FuelPrice.fuel_type.in_(list(fuel_set)),
        FuelPrice.effective_date.in_(list(date_set))
    ).all()
    existing_map = {
        (row.region_name, row.fuel_type, row.effective_date.isoformat() if row.effective_date else None): row
        for row in existing_rows
    }

    created_count = 0
    updated_count = 0
    affected = []

    for item in items:
        key = (item['region_name'], item['fuel_type'], str(item['effective_date']))
        current = existing_map.get(key)
        if current:
            current.price = item['price']
            if item['source']:
                current.source = item['source']
            updated_count += 1
            affected.append(current)
        else:
            row = FuelPrice(
                region_name=item['region_name'],
                fuel_type=item['fuel_type'],
                price=item['price'],
                effective_date=item['effective_date'],
                source=item['source']
            )
            db.session.add(row)
            created_count += 1
            affected.append(row)

    return {
        'created': created_count,
        'updated': updated_count,
        'total': created_count + updated_count,
        'affected': affected
    }
