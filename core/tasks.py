# @Time    : 2023/8/15 22:00
# @Author  : Lan
# @File    : tasks.py
# @Software: PyCharm
import asyncio

from sqlalchemy import Select, or_

from apps.base.models import FileCodes
from apps.base.depends import async_context_get_db
from core.settings import settings
from core.storage import FileStorageInterface, storages
from core.utils import get_now


async def delete_expire_files():
    file_storage: FileStorageInterface = storages[settings.file_storage]()
    while True:
        try:
            # expire_data = await FileCodes.filter(Q(expired_at__lt=await get_now()) | Q(expired_count=0)).all()
            async with async_context_get_db() as db:
                expire_data = await db.execute(Select(FileCodes).where(or_(FileCodes.expired_at < await get_now(), 
                                                                           FileCodes.expired_count == 0)))
            for exp in expire_data:
                await file_storage.delete_file(exp)
                await exp.delete()
        except Exception as e:
            print(e)
        finally:
            await asyncio.sleep(600)
