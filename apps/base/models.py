# @Time    : 2023/8/13 20:43
# @Author  : Lan
# @File    : models.py
# @Software: PyCharm
from datetime import datetime
from typing import Optional

from tortoise import fields
from tortoise.models import Model
from tortoise.contrib.pydantic import pydantic_model_creator

from core.utils import get_now


class FileCodes(Model):
    id: Optional[int] = fields.IntField(pk=True)
    code: Optional[int] = fields.CharField(description='分享码', max_length=255, index=True, unique=True)
    prefix: Optional[str] = fields.CharField(max_length=255, description='前缀', default='')
    suffix: Optional[str] = fields.CharField(max_length=255, description='后缀', default='')
    uuid_file_name: Optional[str] = fields.CharField(max_length=255, description='uuid文件名', null=True)
    file_path: Optional[str] = fields.CharField(max_length=255, description='文件路径', null=True)
    size: Optional[int] = fields.IntField(description='文件大小', default=0)
    text: Optional[str] = fields.TextField(description='文本内容', null=True)
    expired_at: Optional[datetime] = fields.DatetimeField(null=True, description='过期时间')
    expired_count: Optional[int] = fields.IntField(description='可用次数', default=0)
    used_count: Optional[int] = fields.IntField(description='已用次数', default=0)
    created_at: Optional[datetime] = fields.DatetimeField(auto_now_add=True, description='创建时间')

    async def is_expired(self):
        # 按时间
        if self.expired_at is None:
            return False
        if self.expired_at and self.expired_count < 0:
            return self.expired_at < await get_now()
        # 按次数
        else:
            return self.expired_count <= 0

    async def get_file_path(self):
        return f"{self.file_path}/{self.uuid_file_name}"


class KeyValue(Model):
    id: Optional[int] = fields.IntField(pk=True)
    key: Optional[str] = fields.CharField(max_length=255, description='键', index=True, unique=True)
    value: Optional[str] = fields.JSONField(description='值', null=True)
    created_at: Optional[datetime] = fields.DatetimeField(auto_now_add=True, description='创建时间')


file_codes_pydantic = pydantic_model_creator(FileCodes, name='FileCodes')



from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator

from contextlib import asynccontextmanager
from sqlalchemy import MetaData
from sqlalchemy.engine.url import URL
from core.settings import settings

# 创建异步引擎对象
async_engine = create_async_engine(url=URL.create(settings.mysql_driver,
                                                  settings.mysql_user,
                                                  settings.mysql_password,
                                                  settings.mysql_host,
                                                  settings.mysql_port,
                                                  settings.mysql_database),
                                   echo=settings.mysql_echo,
                                   pool_size=settings.mysql_pool_size,
                                   max_overflow=settings.mysql_max_overflow,
                                   future=True)

metadata = MetaData()
# 创建异步的会话管理对象
AsyncSessionLocal = sessionmaker(bind=async_engine, expire_on_commit=False, class_=AsyncSession, 
                                 autocommit=False, autoflush=False, future=False)

# 创建ORM模型基类
class Base(DeclarativeBase):
    pass


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


# 需要使用这个来装饰一下，才可以使用with
@asynccontextmanager
async def async_context_get_db() -> AsyncGenerator:
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



from sqlalchemy import DateTime, Integer, Text, String
from sqlalchemy.orm import mapped_column, Mapped, relationship
from datetime import datetime
metadata = Base.metadata


class FileCodes(Base):
    __tablename__ = 'file_codes'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='主键Id', autoincrement=True)
    code: Mapped[int] = mapped_column(Integer, description='分享码', index=True, unique=True)
    prefix: Mapped[str] = mapped_column(String(255), comment='前缀', default='')
    suffix: Mapped[str] = mapped_column(String(255), comment='后缀', default='')
    uuid_file_name: Mapped[str] = mapped_column(String(255), comment='uuid文件名', null=True)
    file_path: Mapped[str] = mapped_column(String(255), comment='文件路径', null=True)
    size: Mapped[int] = mapped_column(Integer, comment='文件大小', default=0)
    text: Mapped[str] = mapped_column(Text, comment='文本内容', null=True)
    expired_at: Mapped[datetime] = mapped_column(DateTime, null=True, comment='过期时间')
    expired_count: Mapped[int] = mapped_column(Integer, comment='可用次数', default=0)
    used_count: Mapped[int] = mapped_column(Integer, comment='已用次数', default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, comment='创建时间', default_factory=datetime.now)

    @property
    async def is_expired(self):
        # 按时间
        if self.expired_at is None:
            return False
        if self.expired_at and self.expired_count < 0:
            return self.expired_at < await get_now()
        # 按次数
        else:
            return self.expired_count <= 0

    @property
    async def get_file_path(self):
        return f"{self.file_path}/{self.uuid_file_name}"
