import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from main import app, get_tron_client
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
from src.database import AddressInfo, insert_address_info, async_session_factory
from sqlalchemy import select, delete
from datetime import datetime
from httpx import AsyncClient
from httpx import ASGITransport

# Создаем клиент для тестов
client = TestClient(app)


# Переопределяем get_tron_client для мока
async def override_get_tron_client():
    tron = AsyncMock()
    tron.is_address.return_value = True
    tron.get_account_balance.return_value = 123.456
    tron.get_bandwidth.return_value = 600
    tron.get_account_resource.return_value = {
        "EnergyLimit": 1000,
        "EnergyUsed": 200
    }
    return tron


# Переопределяем зависимости
app.dependency_overrides[get_tron_client] = override_get_tron_client


@pytest.mark.asyncio
async def test_insert_address_info():
    """Unit-тест функции insert_address_info."""
    test_address = "TTestAddress1234567890abcdef"
    test_balance = 789.012

    # Очищаем таблицу перед тестом
    async with async_session_factory() as session:
        await session.execute(delete(AddressInfo).where(AddressInfo.address == test_address))
        await session.commit()

    # Выполняем вставку
    async with async_session_factory() as session:
        await insert_address_info(test_address, test_balance, session)
        await session.commit()

    # Проверяем, что запись появилась в БД
    async with async_session_factory() as session:
        stmt = select(AddressInfo).where(AddressInfo.address == test_address)
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()
        assert record is not None
        assert record.address == test_address
        assert record.balance == test_balance
        assert isinstance(record.date, datetime)

        # Очищаем запись после теста
        await session.execute(delete(AddressInfo).where(AddressInfo.address == test_address))
        await session.commit()


@pytest.mark.asyncio
async def test_insert_address_info_failure():
    """Unit-тест для обработки ошибок в insert_address_info."""
    # Мокаем сессию, чтобы симулировать ошибку
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.execute.side_effect = Exception("Database error")

    # Проверяем, что функция вызывает исключение
    with pytest.raises(Exception, match="Database error"):
        await insert_address_info("TTestAddress1234567890abcdef", 789.012, mock_session)


@pytest.mark.asyncio
async def test_get_address_info_endpoint_invalid_address():
    """Интеграционный тест для POST /address-info с невалидным адресом."""
    response = client.post("/address-info", json={"address": "InvalidAddress"})

    assert response.status_code == 400
    assert "Неверный формат TRON-адреса" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_address_info_list_endpoint():
    """Интеграционный тест для GET /address-info."""
    # Предварительно добавляем тестовую запись
    test_address = "TTestAddress1234567890abcdef"

    async with async_session_factory() as session:
        await insert_address_info(test_address, 789.012, session)

        # response = client.get("/address-info?page=1&page_size=10")

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/address-info?page=1&page_size=10")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Очищаем тестовую запись
        await session.execute(delete(AddressInfo).where(AddressInfo.address == test_address))
        await session.commit()