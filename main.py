# @Time    : 2023/8/9 23:23
# @Author  : Lan
# @File    : main.py
# @Software: PyCharm
import asyncio
import os
import aioredis
from urllib.parse import quote
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import Select
from typing import Union

from apps.base.models import KeyValue, Base, async_engine
from apps.base.views import share_api
from apps.admin.views import admin_api
from apps.base.depends import async_context_get_db
from core.response import APIResponse
from core.settings import data_root, settings, BASE_DIR
from core.tasks import delete_expire_files
from core.utils import setup_ext_loguru
from core.middleware import LoggingMiddleware, IPLimitMIddleware
from core.exceptions import ApiExceptionHandler
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)

app = FastAPI(docs_url=None, redoc_url=None)

# 注册异常
ApiExceptionHandler(app=app)

# 注册中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)

app.add_middleware(IPLimitMIddleware, 
                   max_requests=settings.request_count, request_time_window=settings.request_time_window,
                   max_update=settings.update_count, update_time_window=settings.update_time_window,
                   max_error_requests=settings.error_count, error_time_window=settings.error_time_window
)

app.mount('/assets', StaticFiles(directory='./fcb-fronted/dist/assets'), name="assets")
static_dir = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=f"{static_dir}/static"), name="static")

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Custom API",
        version="3.0.1",
        description="This is a very custom OpenAPI schema",
        routes=app.routes,
    )
    # Here we override the OpenAPI version
    openapi_schema["openapi"] = "3.1.0"
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui/swagger-ui.css",
    )


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="/static/redoc/bundles/redoc.standalone.js",
)


app.include_router(share_api)
app.include_router(admin_api)


@app.on_event("startup")
async def startup_event():
    # 创建数据库
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_context_get_db() as db_session:
        # 读取用户配置
        key:Union[KeyValue, None] = (await db_session.execute(Select(KeyValue).where(KeyValue.key == 'settings'))).scalars().first()
        if key: 
            key.value = settings.model_dump()
        else:
            key = KeyValue(key='settings', value=settings.model_dump())
            db_session.add(key)
    # 生成日志文件夹
    setup_ext_loguru()
    # 初始化redis
    redis_url = f'redis://{settings.redis_username}:{quote(settings.redis_password)}@{settings.redis_host}:{settings.redis_port}/{settings.redis_db}'
    app.state.redis_client = aioredis.from_url(redis_url, encoding='utf-8', max_connections=10, decode_responses=True)
    # 启动后台任务，不定时删除过期文件
    asyncio.create_task(delete_expire_files())

@app.on_event('shutdown')
async def shutdown_event():
    await app.state.redis_client.close()


@app.get('/')
async def index():
    return HTMLResponse(
        content=open(BASE_DIR / 'fcb-fronted/dist/index.html', 'r', encoding='utf-8').read()
        .replace('{{title}}', str(settings.name))
        .replace('{{description}}', str(settings.description))
        .replace('{{keywords}}', str(settings.keywords))
        .replace('{{opacity}}', str(settings.opacity))
        .replace('{{background}}', str(settings.background))
        , media_type='text/html', headers={'Cache-Control': 'no-cache'})


@app.get('/robots.txt')
async def robots():
    return HTMLResponse(content=settings.robotsText, media_type='text/plain')


@app.post('/')
async def get_config():
    return APIResponse(detail={
        'explain': settings.page_explain,
        'uploadSize': settings.uploadSize,
        'expireStyle': settings.expireStyle,
        'openUpload': settings.openUpload,
        'notify_title': settings.notify_title,
        'notify_content': settings.notify_content,
        'show_admin_address': settings.showAdminAddr,
    })


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app='main:app', host="0.0.0.0", port=settings.port, reload=True, workers=4)
