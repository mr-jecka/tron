from pydantic import BaseModel
from datetime import datetime


# Модель для входных данных
class AddressRequest(BaseModel):
    address: str = "THUE6WTLaEGytFyuGJQUcKc3r245UKypoi"  # Адрес по умолчанию


# Модель для ответа GET
class AddressInfoResponse(BaseModel):
    id: int
    date: datetime
    address: str
    balance: float

    class Config:
        from_attributes = True