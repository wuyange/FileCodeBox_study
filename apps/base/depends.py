# @Time    : 2023/8/14 12:20
# @Author  : Lan
# @File    : depends.py
# @Software: PyCharm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from apps.base.models import AsyncSessionLocal



async def depends_get_db_session() -> AsyncGenerator[AsyncSession, None]:
    db_session = None
    try:
        db_session = AsyncSessionLocal()
        yield db_session
        await db_session.commit()
    except SQLAlchemyError as ex:
        await db_session.rollback()
        raise ex
    finally:
        await db_session.close()


@asynccontextmanager
async def async_context_get_db() -> AsyncGenerator[AsyncSession, None]:
    '''
        async def init() -> None:
        pass
        async with get_db() as session:
            result = await session.execute(select(Hospital))
            listsd = result.scalars().fetchall()
            print([itm.name for itm in listsd])
            # import asyncio
            # # asyncio.run(init())
            # loop = asyncio.get_event_loop()
            # loop.run_until_complete(init())
    :return:
    '''
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except SQLAlchemyError as ex:
        await session.rollback()
        raise ex
    finally:
        await session.close()
