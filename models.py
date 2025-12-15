from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.sql import func
from database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True)
    plate_number = Column(String, unique=True, nullable=False)
    is_allowed = Column(Boolean, default=True)


class ParkingLog(Base):
    __tablename__ = "parking_logs"

    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"))
    entered_at = Column(DateTime, default=func.now())
    exited_at = Column(DateTime, nullable=True)
