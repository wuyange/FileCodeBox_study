# @Time    : 2023/8/14 03:59
# @Author  : Lan
# @File    : views.py
# @Software: PyCharm
# 导入所需的库和模块
from fastapi import APIRouter, Form, UploadFile, File, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Select
from typing import Union, Tuple

from apps.admin.depends import admin_required
from apps.base.models import FileCodes
from apps.base.pydantics import SelectFileModel
from apps.base.utils import get_expire_info, get_file_path_name
from core.response import APIResponse
from core.settings import settings
from core.storage import storages, FileStorageInterface
from core.utils import get_select_token
from .depends import depends_get_db_session

# 创建一个API路由
share_api = APIRouter(
    prefix='/share',  # 路由前缀
    tags=['分享'],  # 标签
)


# 分享文本的API
@share_api.post('/text/')
async def share_text(text: str = Form(...), expire_value: int = Form(default=1, gt=0), 
                     expire_style: str = Form(default='day'), db_session: AsyncSession = Depends(depends_get_db_session)):
    # 获取大小
    text_size = len(text)
    # 限制 222KB
    max_txt_size = settings.textSize
    if text_size > max_txt_size:
        raise HTTPException(status_code=403, detail=f'内容过多，建议采用文件形式')
    # 获取过期信息
    expired_at, expired_count, used_count, code = await get_expire_info(expire_value, expire_style)
    # 创建一个新的FileCodes实例
    db_session.add(FileCodes(
        code=code,
        text=text,
        expired_at=expired_at,
        expired_count=expired_count,
        used_count=used_count,
        size=len(text),
        prefix='文本分享',
    ))

    return APIResponse(detail={
        'code': code,
    })


# 分享文件的API
@share_api.post('/file/')
async def share_file(expire_value: int = Form(default=1, gt=0), expire_style: str = Form(default='day'), 
                     file: UploadFile = File(...), db_session: AsyncSession = Depends(depends_get_db_session)):
    if file.size > settings.uploadSize:
        # 转换为 MB 并格式化输出
        max_size_mb = settings.uploadSize / (1024 * 1024)
        raise HTTPException(status_code=403, detail=f'大小超过限制，最大为{max_size_mb:.2f} MB')
    # 获取过期信息
    if expire_style not in settings.expireStyle:
        raise HTTPException(status_code=400, detail='过期时间类型错误')
    expired_at, expired_count, used_count, code = await get_expire_info(expire_value, expire_style)
    # 获取文件路径和名称
    path, suffix, prefix, uuid_file_name, save_path = await get_file_path_name(file)
    # 保存文件
    file_storage: FileStorageInterface = storages[settings.file_storage]()
    await file_storage.save_file(file, save_path)
    # 创建一个新的FileCodes实例
    db_session.add(FileCodes(
        code=code,
        prefix=prefix,
        suffix=suffix,
        uuid_file_name=uuid_file_name,
        file_path=path,
        size=file.size,
        expired_at=expired_at,
        expired_count=expired_count,
        used_count=used_count,
    ))

    return APIResponse(detail={
        'code': code,
        'name': file.filename,
    })


# 根据code获取文件
async def get_code_file_by_code(code, check=True, db_session: AsyncSession = Depends(depends_get_db_session)) -> Tuple[bool, Union[FileCodes, str]]:
    # 查询文件
    file_code:Union[FileCodes, None] = (await db_session.execute(Select(FileCodes).where(FileCodes.code == code))).scalars().first()
    # 检查文件是否存在
    if not file_code:
        return False, '文件不存在'
    # 检查文件是否过期
    if await file_code.is_expired and check:
        return False, '文件已过期',
    return True, file_code


# 获取文件的API
@share_api.get('/select/')
async def get_code_file(code: str, db_session: AsyncSession = Depends(depends_get_db_session)):
    file_storage: FileStorageInterface = storages[settings.file_storage]()
    # 获取文件
    has, file_code = await get_code_file_by_code(code, db_session=db_session)
    # 检查文件是否存在
    if not has:
        print(APIResponse(code=404, detail=file_code))
        print(type(APIResponse(code=404, detail=file_code)))
        return JSONResponse(content=APIResponse(code=404, detail=file_code).dict(), status_code=404)
    # 更新文件的使用次数和过期次数
    file_code.used_count += 1
    if file_code.expired_count > 0:
        file_code.expired_count -= 1

    # 返回文件响应
    return await file_storage.get_file_response(file_code)


# 选择文件的API
@share_api.post('/select/')
async def select_file(data: SelectFileModel, db_session: AsyncSession = Depends(depends_get_db_session)):
    file_storage: FileStorageInterface = storages[settings.file_storage]()
    # 获取文件
    has, file_code = await get_code_file_by_code(data.code, db_session=db_session)
    # 检查文件是否存在
    if not has:
        print(APIResponse(code=404, detail=file_code).dict())
        print(type(APIResponse(code=404, detail=file_code)))
        return JSONResponse(content=APIResponse(code=404, detail=file_code).dict(), status_code=404)
    # 更新文件的使用次数和过期次数
    file_code.used_count += 1
    if file_code.expired_count > 0:
        file_code.expired_count -= 1
        
    # 返回API响应
    return APIResponse(detail={
        'code': file_code.code,
        'name': file_code.prefix + file_code.suffix,
        'size': file_code.size,
        'text': file_code.text if file_code.text is not None else await file_storage.get_file_url(file_code),
    })


# 下载文件的API
@share_api.get('/download')
async def download_file(key: str, code: str, db_session: AsyncSession = Depends(depends_get_db_session)):
    file_storage: FileStorageInterface = storages[settings.file_storage]()
    # 获取文件
    has, file_code = await get_code_file_by_code(code, False, db_session=db_session)
    # 检查文件是否存在
    if not has:
        # 返回API响应
        return JSONResponse(content=APIResponse(code=404, detail='文件不存在'), status_code=404)
    # 如果文件是文本，返回文本内容，否则返回文件响应
    if file_code.text:
        return APIResponse(detail=file_code.text)
    else:
        return await file_storage.get_file_response(file_code)
