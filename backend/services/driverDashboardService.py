"""司机工作台聚合服务。"""

from models.index import db, Dispatch, Trip, Vehicle, CarApplication, User
from controllers.commonHelpers import enum_value


def _build_active_task_row(dispatch, application, applicant, trip):
    return {
        'dispatch_id': dispatch.id,
        'dispatch_status': enum_value(dispatch.status),
        'application_id': application.id if application else None,
        'start_time': application.start_time.isoformat() if application and application.start_time else None,
        'end_time': application.end_time.isoformat() if application and application.end_time else None,
        'start_point': application.start_point if application else None,
        'destination': application.destination if application else None,
        'passenger_name': applicant.name if applicant else None,
        'passenger_phone': applicant.phone if applicant else None,
        'trip_id': trip.id if trip else None,
        'trip_status': enum_value(trip.status) if trip else None,
        'passenger_picked_up': (bool(trip.passenger_picked_up) or bool(trip.actual_start_time)) if trip else False,
        'driver_report_distance_km': float(trip.driver_report_distance_km) if trip and trip.driver_report_distance_km is not None else None,
        'driver_report_fuel_used_l': float(trip.driver_report_fuel_used_l) if trip and trip.driver_report_fuel_used_l is not None else None,
        'driver_reported_at': trip.driver_reported_at.isoformat() if trip and trip.driver_reported_at else None,
        'user_rating': float(trip.user_rating) if trip and trip.user_rating is not None else None,
        'actual_start_time': trip.actual_start_time.isoformat() if trip and trip.actual_start_time else None,
        'actual_end_time': trip.actual_end_time.isoformat() if trip and trip.actual_end_time else None
    }


def _build_completed_trip_row(dispatch, application, applicant, trip, trip_rating):
    return {
        'dispatch_id': dispatch.id,
        'application_id': application.id if application else None,
        'passenger_name': applicant.name if applicant else None,
        'destination': application.destination if application else None,
        'trip_id': trip.id,
        'distance_km': float(trip.distance_km) if trip.distance_km is not None else None,
        'fuel_used_l': float(trip.fuel_used_l) if trip.fuel_used_l is not None else None,
        'user_rating': trip_rating,
        'actual_start_time': trip.actual_start_time.isoformat() if trip.actual_start_time else None,
        'actual_end_time': trip.actual_end_time.isoformat() if trip.actual_end_time else None
    }


def build_driver_dashboard(driver):
    """聚合司机工作台数据；如存在进行中调度且未建 trip，会补建并 flush。"""
    vehicle = Vehicle.query.get(driver.vehicle_id) if driver.vehicle_id else None

    active_dispatches = Dispatch.query.filter(
        Dispatch.driver_id == driver.id,
        Dispatch.status.in_(['scheduled', 'in_progress'])
    ).order_by(Dispatch.dispatch_time.desc()).all()

    task_rows = []
    for dispatch in active_dispatches:
        application = CarApplication.query.get(dispatch.application_id)
        applicant = User.query.get(application.applicant_id) if application else None
        trip = Trip.query.filter_by(dispatch_id=dispatch.id).first()
        if not trip and enum_value(dispatch.status) == 'in_progress':
            trip = Trip(
                dispatch_id=dispatch.id,
                passenger_picked_up=False,
                status='started'
            )
            db.session.add(trip)
            db.session.flush()

        task_rows.append(_build_active_task_row(dispatch, application, applicant, trip))

    completed_dispatches = Dispatch.query.filter(
        Dispatch.driver_id == driver.id,
        Dispatch.status == 'completed'
    ).order_by(Dispatch.updated_at.desc(), Dispatch.id.desc()).limit(30).all()

    completed_rows = []
    ratings = []
    for dispatch in completed_dispatches:
        application = CarApplication.query.get(dispatch.application_id)
        applicant = User.query.get(application.applicant_id) if application else None
        trip = Trip.query.filter_by(dispatch_id=dispatch.id).first()
        if not trip:
            continue

        trip_rating = float(trip.user_rating) if trip.user_rating is not None else None
        if trip_rating is not None:
            ratings.append(trip_rating)

        completed_rows.append(_build_completed_trip_row(dispatch, application, applicant, trip, trip_rating))

    driver_rating_avg = round(sum(ratings) / len(ratings), 2) if ratings else None

    return {
        'driver': {
            'id': driver.id,
            'name': driver.name,
            'status': enum_value(driver.driver_status),
            'vehicle_id': driver.vehicle_id
        },
        'vehicle': {
            'id': vehicle.id if vehicle else None,
            'plate_number': vehicle.plate_number if vehicle else None,
            'status': enum_value(vehicle.status) if vehicle else None
        },
        'tasks': task_rows,
        'completed_trips': completed_rows,
        'driver_rating_avg': driver_rating_avg
    }
