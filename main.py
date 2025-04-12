import asyncio
from src.logger import logger
from fastapi import FastAPI, HTTPException, Query
import uvicorn
from src.schemas import AddressRequest, AddressInfoResponse
from tronpy.providers import AsyncHTTPProvider
from tronpy import AsyncTron
from src.config import TRON_NODE, API_KEY_TRON
from src.database import async_session_factory, insert_address_info, get_address_info_from_db
from typing import List


app = FastAPI(title="Микросервис предоставления информации по адресам в блокчейне TRON")


async def run_uvicorn():
    """ Запуск Uvicorn-сервера в отдельной задаче """
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

# Конфигурация подключения к TRON
TRON_NODE = TRON_NODE  # Основная сеть TRON
API_KEY = API_KEY_TRON  # Ключ API для сети TRON


# Инициализация асинхронного клиента с API-ключом
async def get_tron_client():
    provider = AsyncHTTPProvider(TRON_NODE, api_key=API_KEY)
    return AsyncTron(provider)


@app.post("/address-info")
async def get_address_info(request: AddressRequest):
    """Метод получения информации об адресе TRON: баланс TRX, bandwidth и energy."""
    address = request.address.strip()

    try:
        # Проверка формата адреса
        if not address.startswith("T") or len(address) != 34:
            raise HTTPException(
                status_code=400,
                detail="Неверный формат TRON-адреса. Адрес должен начинаться с буквы 'Т' и содержать 34 символа."
            )

        # Инициализация асинхронного клиента
        async with await get_tron_client() as tron:
            # Проверка валидности адреса
            if not tron.is_address(address):
                raise HTTPException(status_code=400, detail="Неверный TRON-адрес")

            # Получение баланса TRX
            balance = await tron.get_account_balance(address)
            bandwidth = await tron.get_bandwidth(address)
            logger.info(f"get_bandwidth: {bandwidth}")

            # Получение информации о energy
            account_resources = await tron.get_account_resource(address)
            logger.info(f"account_resources: {account_resources}")

            # Извлечение данных об energy
            energy_limit = account_resources.get("EnergyLimit", 0)  # Общий лимит energy
            energy_used = account_resources.get("EnergyUsed", 0)  # Использованная energy
            energy_remaining = energy_limit - energy_used if energy_limit > 0 else 0  # Оставшаяся energy

            # Запись в БД
            async with async_session_factory() as session:
                await insert_address_info(address, float(balance), session)

            # Формируем ответ
            response = {
                "address": address,
                "balance_trx": float(balance),
                "bandwidth": bandwidth,
                "energy": {
                    "limit": energy_limit,
                    "used": energy_used,
                    "remaining": energy_remaining
                }
            }

            logger.info(f"Successfully retrieved info for address: {address}")
            return response

    except HTTPException as error:
        raise error
    except Exception as e:
        logger.error(f"Error processing address {address}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@app.get("/address-info", response_model=List[AddressInfoResponse])
async def get_address_info_list(
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(10, ge=1, le=100, description="Количество записей на странице")
):
    """Получает список последних записей из таблицы AddressInfo с пагинацией."""
    try:
        # Вычисляем смещение для пагинации
        offset = (page - 1) * page_size

        # Запрос в БД на получение записей, отсортированных по убыванию времени
        records = await get_address_info_from_db(offset, page_size)

        # Логирование
        logger.info(f"Retrieved {len(records)} records for page {page} with page_size {page_size}")

        return records

    except Exception as e:
        logger.error(f"Error retrieving address info list: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving records: {str(e)}")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_uvicorn())