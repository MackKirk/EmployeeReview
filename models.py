from sqlalchemy import Column, Integer, String, Text
from db import Base

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    employee_name = Column(String, index=True)
    role = Column(String)
    question = Column(String)
    answer = Column(Text)
