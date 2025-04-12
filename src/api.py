from tronpy import Tron
from tronpy.providers import HTTPProvider
from pydantic import BaseModel
import logging
from fastapi import FastAPI, HTTPException, Path, Response


# app = FastAPI(title="TRON Address Info Microservice")
app = FastAPI(root_path="/api", openapi_tags=[{"name": "Настройки ботов"}])


# Модель для входных данных
class AddressRequest(BaseModel):
    address: str


# Конфигурация подключения к TRON
TRON_NODE = "https://api.trongrid.io"  # Основная сеть TRON
tron = Tron(HTTPProvider(TRON_NODE))


@app.post("/address-info")
async def get_address_info(request: AddressRequest):
    """
    Получает информацию об адресе TRON: баланс TRX, bandwidth и energy.
    """
    address = request.address.strip()

    try:
        # Проверка валидности адреса
        if not tron.is_address(address):
            raise HTTPException(status_code=400, detail="Invalid TRON address")

        # Получение баланса TRX
        balance = await tron.get_account_balance(address)

        # Получение информации о ресурсах (bandwidth и energy)
        account_resources = await tron.get_account_resources(address)

        # Формирование ответа
        response = {
            "address": address,
            "balance_trx": balance,  # Баланс в TRX
            "bandwidth": {
                "free_net_used": account_resources.get("freeNetUsed", 0),
                "free_net_limit": account_resources.get("freeNetLimit", 0),
                "net_used": account_resources.get("NetUsed", 0),
                "net_limit": account_resources.get("NetLimit", 0)
            },
            "energy": {
                "energy_used": account_resources.get("EnergyUsed", 0),
                "energy_limit": account_resources.get("EnergyLimit", 0)
            }
        }

        logger.info(f"Successfully retrieved info for address: {address}")
        return response

    except Exception as e:
        logger.error(f"Error processing address {address}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@app.get("/health")
async def health_check():
    """Проверка состояния сервиса"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)