from sqlalchemy import Column, String, Date, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

Base = declarative_base()

class Employee(Base):
    __tablename__ = "employees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    birth_date = Column(Date, nullable=False)
    password = Column(String, nullable=True)
    supervisor_email = Column(String, nullable=True)
    is_supervisor = Column(Boolean, default=False)
    role = Column(String, default="employee")  # 'employee', 'supervisor', 'director'

    # Extended profile fields
    department = Column(String, nullable=True)
    position = Column(String, nullable=True)
    years_months_with_mk = Column(String, nullable=True)
    pay_hr_last_3_years = Column(Text, nullable=True)
    loan_amount = Column(String, nullable=True)
    lmia = Column(String, nullable=True)  # SKILLED / UNSKILLED
    company_phone = Column(String, nullable=True)  # Allowance or iPhone
    company_laptop_ipad = Column(String, nullable=True)
    drive_company_vehicle = Column(String, nullable=True)  # Y/N
    company_gas_card = Column(String, nullable=True)  # Y/N
    skills_trade_completed = Column(String, nullable=True)  # lvl 1, 2, 3 Red Seal
    safety_infraction_description = Column(Text, nullable=True)

class Review(Base):
    __tablename__ = "reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"))
    supervisor_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"))
    employee_answers = Column(JSONB, nullable=True)
    supervisor_answers = Column(JSONB, nullable=True)
    director_comments = Column(JSONB, nullable=True)
    director_section_comments = Column(JSONB, nullable=True)
    status = Column(String, default="draft")
    employee_scheduled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    employee = relationship("Employee", foreign_keys=[employee_id])

class EmailEvent(Base):
    __tablename__ = "email_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"))
    event_type = Column(String)  # 'sent' | 'clicked'
    created_at = Column(DateTime, default=datetime.utcnow)