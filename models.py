from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class Customer(Base):
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100))
    phone = Column(String(20))
    company = Column(String(100))
    status = Column(String(20), default='lead')
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    deals = relationship("Deal", back_populates="customer", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="customer", cascade="all, delete-orphan")

class Deal(Base):
    __tablename__ = 'deals'
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    value = Column(Float, default=0.0)
    stage = Column(String(20), default='prospecting')
    probability = Column(Integer, default=10)
    expected_close = Column(Date)
    closed_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    customer_id = Column(Integer, ForeignKey('customers.id'))
    customer = relationship("Customer", back_populates="deals")

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    due_date = Column(Date)
    priority = Column(String(20), default='medium')
    status = Column(String(20), default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    customer_id = Column(Integer, ForeignKey('customers.id'))
    customer = relationship("Customer", back_populates="tasks")