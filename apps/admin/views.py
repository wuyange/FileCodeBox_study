# @Time    : 2023/8/14 14:38
# @Author  : Lan
# @File    : views.py
# @Software: PyCharm
import math
import httpx

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Select, Delete, func

from apps.admin.depends import admin_required
from apps.admin.pydantics import IDData
from apps.base.models import FileCodes, KeyValue
from apps.base.depends import depends_get_db_session
from core.response import APIResponse
from core.settings import settings
from core.storage import FileStorageInterface, storages

admin_api = APIRouter(
    prefix='/admin',
    tags=['管理'],
)

@admin_api.get("/login")
async def login():
    return RedirectResponse(
        f"https://github.com/login/oauth/authorize?client_id={settings.client_id}&redirect_uri={settings.redirect_uri}"
    )

@admin_api.get("/callback")
async def callback(code: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.client_id,
                "client_secret": settings.client_secrets,
                "code": code,
                "redirect_uri": settings.redirect_uri,
            },
        )
        token_data = response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            raise JSONResponse(status_code=400, content=APIResponse(code=400, detail='获取access_token失败'))

    # return APIResponse(detail={"access_token": access_token}, code=200)
    return {"access_token": access_token}


@admin_api.delete('/file/delete', dependencies=[Depends(admin_required)])
async def file_delete(data: IDData, db_session: AsyncSession = Depends(depends_get_db_session)):
    file_storage: FileStorageInterface = storages[settings.file_storage]()
    file_code = await db_session.execute(Delete(Select(FileCodes).where(FileCodes.id == data.id)))
    await file_storage.delete_file(file_code)
    return APIResponse()


@admin_api.get('/file/list')
async def file_list(page: float = 1, size: int = 10, db_session: AsyncSession = Depends(depends_get_db_session)):
    data = (await db_session.execute(Select(FileCodes).limit(size).offset((math.ceil(page) - 1) * size))).scalars().all()
    data = [{key: value for key, value in vars(file).items() if not key.startswith('_')} for file in data]
    return APIResponse(detail={
        'page': page,
        'size': size,
        'data': data,
        'total': (await db_session.execute(Select(func.count(FileCodes.id)))).scalar_one(),
    })


@admin_api.get('/config/get', dependencies=[Depends(admin_required)])
async def get_config():
    return APIResponse(detail=settings.model_dump())


@admin_api.patch('/config/update', dependencies=[Depends(admin_required)])
async def update_config(data: dict, db_session: AsyncSession = Depends(depends_get_db_session)):
    admin_token = data.get('admin_token')
    for key, value in data.items():
        if key not in settings.model_dump().keys():
            continue
        if key in ['errorCount', 'errorMinute', 'max_save_seconds', 'onedrive_proxy', 'openUpload', 'port', 's3_proxy', 'uploadCount', 'uploadMinute', 'uploadSize']:
            data[key] = int(value)
        elif key in ['opacity']:
            data[key] = float(value)
        else:
            data[key] = value
    if admin_token is None or admin_token == '':
        return JSONResponse(content=APIResponse(code=400, detail='管理员密码不能为空'), status_code=400)
    key:KeyValue = (await db_session.execute(Select(KeyValue).where(KeyValue.key == 'settings'))).scalars().first()
    key.value = data
    for k, v in data.items():
        settings.__setattr__(k, v)
    return APIResponse()


# 根据code获取文件
async def get_file_by_id(id, db_session: AsyncSession = Depends(depends_get_db_session)):
    # 查询文件
    file_code = (await db_session.execute(Select(FileCodes).where(FileCodes.id == id))).scalars().first()
    # 检查文件是否存在
    if not file_code:
        return False, '文件不存在'
    return True, file_code


@admin_api.get('/file/download', dependencies=[Depends(admin_required)])
async def file_download(id: int):
    file_storage: FileStorageInterface = storages[settings.file_storage]()
    has, file_code = await get_file_by_id(id)
    # 检查文件是否存在
    if not has:
        # 返回API响应
        return JSONResponse(content=APIResponse(code=404, detail='文件不存在'), status_code=404)
    # 如果文件是文本，返回文本内容，否则返回文件响应
    if file_code.text:
        return APIResponse(detail=file_code.text)
    else:
        return await file_storage.get_file_response(file_code)

