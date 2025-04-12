from sqlalchemy.engine.url import URL
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.config import db_database, db_host, db_user, db_port, db_password
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select
from datetime import datetime
from logger import logger
from models import AddressInfo

asyncpg_introspection_issue = dict(connect_args={"server_settings": {"jit": "off"}})

DATABASE_CONNECTION_URL = URL.create(
    drivername="postgresql+asyncpg",
    username=db_user,
    password=db_password,
    host=db_host,
    port=db_port,
    database=db_database)

async_engine = create_async_engine(
    DATABASE_CONNECTION_URL,
    **asyncpg_introspection_issue,
    echo=False,
    pool_size=144,)

async_session_factory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autoflush=True,
    expire_on_commit=False)


async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session


async def insert_address_info(address: str, balance_trx: float, session: AsyncSession):
    """Вставляем запись об адресе и балансе в таблицу AddressInfo."""
    try:
        stmt = insert(AddressInfo).values(
            address=address,
            balance=balance_trx,
            date=datetime.utcnow()
        )
        await session.execute(stmt)
        await session.commit()
        logger.info(f"Successfully inserted address {address} into DB")
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to insert address {address} into DB: {str(e)}")
        raise


async def get_address_info_from_db(offset: int, page_size: int) -> list:
    """Получаем список записей из таблицы AddressInfo с пагинацией."""
    try:
        async with async_session_factory() as session:
            stmt = select(AddressInfo).order_by(
                AddressInfo.date.desc()).offset(offset).limit(page_size)
            result = await session.execute(stmt)
            records = result.scalars().all()
            logger.info(f"Retrieved {len(records)} records from DB with offset {offset} and page_size {page_size}")
            return records
    except Exception as e:
        logger.error(f"Failed to retrieve records from DB: {str(e)}")
        raise