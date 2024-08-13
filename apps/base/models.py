# @Time    : 2023/8/13 20:43
# @Author  : Lan
# @File    : models.py
# @Software: PyCharm
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import mapped_column, Mapped, sessionmaker, DeclarativeBase
from sqlalchemy import DateTime, Integer, Text, String, JSON, MetaData
from datetime import datetime

from sqlalchemy.engine.url import URL
from core.settings import settings
from core.utils import get_now

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
                                 autocommit=False, autoflush=False)

# 创建ORM模型基类
class Base(DeclarativeBase):
    pass


class FileCodes(Base):
    __tablename__ = 'file_codes'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='主键Id', autoincrement=True)
    code: Mapped[int] = mapped_column(Integer, comment='分享码', index=True, unique=True)
    prefix: Mapped[str] = mapped_column(String(255), comment='前缀', default='')
    suffix: Mapped[str] = mapped_column(String(255), comment='后缀', default='')
    uuid_file_name: Mapped[str] = mapped_column(String(255), comment='uuid文件名', nullable=True)
    file_path: Mapped[str] = mapped_column(String(255), comment='文件路径', nullable=True)
    size: Mapped[int] = mapped_column(Integer, comment='文件大小', default=0)
    text: Mapped[str] = mapped_column(Text, comment='文本内容', nullable=True)
    expired_at: Mapped[datetime] = mapped_column(DateTime, nullable=True, comment='过期时间')
    expired_count: Mapped[int] = mapped_column(Integer, comment='可用次数', default=0)
    used_count: Mapped[int] = mapped_column(Integer, comment='已用次数', default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, comment='创建时间', default=datetime.now)

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

class KeyValue(Base):
    __tablename__ = 'key_value'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(255), comment='键', index=True, unique=True)
    value: Mapped[dict] = mapped_column(JSON, comment='值', nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, comment='创建时间', default=datetime.now)
