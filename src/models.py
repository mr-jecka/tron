from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime

Base = declarative_base()


class AddressInfo(Base):
    __tablename__ = 'address_info'

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, default=datetime.utcnow)  # Время запроса
    address = Column(String, nullable=False)          # Адрес кошелька
    balance = Column(Float, nullable=False)           # Баланс в TRX