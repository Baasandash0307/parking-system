from sqlalchemy.orm import Session
from datetime import datetime
from models import Vehicle, ParkingLog
import math


def get_vehicle_by_plate(db: Session, plate: str):
    return db.query(Vehicle).filter(Vehicle.plate_number == plate).first()


def create_vehicle(db: Session, plate: str):
    vehicle = Vehicle(plate_number=plate)
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


def vehicle_enter(db: Session, vehicle: Vehicle):
    active_log = (
        db.query(ParkingLog)
        .filter(ParkingLog.vehicle_id == vehicle.id)
        .filter(ParkingLog.exited_at == None)
        .first()
    )

    if active_log:
        return None

    # Python datetime.now() ашиглах
    log = ParkingLog(vehicle_id=vehicle.id, entered_at=datetime.now())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def vehicle_exit(db: Session, vehicle: Vehicle):
    log = (
        db.query(ParkingLog)
        .filter(ParkingLog.vehicle_id == vehicle.id)
        .filter(ParkingLog.exited_at == None)
        .first()
    )

    if not log:
        return None

    # Python datetime.now() ашиглах
    log.exited_at = datetime.now()
    db.commit()
    db.refresh(log)
    return log


def calculate_minutes(log):
    delta = log.exited_at - log.entered_at
    return int(delta.total_seconds() / 60)


def calculate_fee(minutes: int):
    hours = math.ceil(minutes / 60)
    return hours * 2000


def get_all_parked_vehicles(db: Session):
    return (
        db.query(Vehicle, ParkingLog)
        .join(ParkingLog, ParkingLog.vehicle_id == Vehicle.id)
        .filter(ParkingLog.exited_at == None)
        .all()
    )


def get_all_vehicles(db: Session):
    return db.query(Vehicle).all()


def get_vehicle_by_id(db: Session, vehicle_id: int):
    return db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()


def get_all_logs(db: Session, limit: int = 50):
    return (
        db.query(ParkingLog).order_by(ParkingLog.entered_at.desc()).limit(limit).all()
    )


def get_vehicle_logs(db: Session, vehicle_id: int):
    return (
        db.query(ParkingLog)
        .filter(ParkingLog.vehicle_id == vehicle_id)
        .order_by(ParkingLog.entered_at.desc())
        .all()
    )
