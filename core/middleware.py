from datetime import datetime
import json
from loguru import logger
from fastapi import Request
from starlette.types import ASGIApp, Receive, Scope, Send
from typing import Dict, AnyStr

class LoggingMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        receive_ = await receive()

        while receive_['more_body']:
            message = await receive()
            receive_['body'] += message.get('body', b'')
            receive_['more_body'] = message['more_body']
        async def receive():
            return receive_

        request = Request(scope, receive)
        if not request.url.path.startswith('/assets'):
            logger.info(await self.make_request_log_msg(request))
        response = await self.app(scope, receive, send)
        return response

    async def make_request_log_msg(self, request: Request) -> Dict:
        # 从当前请求中获取到具体的客户端信息
        ip, method, url = request.client.host, request.method, request.url.path
        # 在这里记录下当前提交的body的数据，用于下文的提取
        request_data = await self.get_request_body(request)
        # 从头部里面获取出对应的请求头信息，用户用户机型等信息获取
        user_agent = request.headers["user-agent"]
        log_msg = {
            "useragent": user_agent,
            'url': url,
            'method': method,
            'ip': ip,
            'request_data': {**request_data},
            "ts": f'{datetime.now():%Y-%m-%d %H:%M:%S%z}'
        }
        return log_msg
    
    async def get_request_body(self, request: Request) -> AnyStr:
        request_data = {'query_params': str(request.query_params)}
        content_type = request.headers.get('content-type', '')
        if content_type == 'application/json':
            request_data['json_data'] = await request.json()
        elif 'multipart/form-data' in content_type:
            form = await request.form()
            request_data['from_data'] = {}
            for key, value in form.items():
                if key == 'file':
                    request_data['from_data'][key] = value.filename
                request_data['from_data'][key] = value
        return request_data
