import time
from datetime import datetime
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
        user_agent = request.headers.get('user-agent', None)
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


class IPLimitMIddleware:
    def __init__(self, app: ASGIApp, max_requests: int, request_time_window: int, 
                 max_update:int = 10, update_time_window: int = 60,
                 max_error_requests: int = 10, error_time_window: int = 60):
        self.app = app
        self.max_requests = max_requests
        self.request_time_window = request_time_window
        self.max_update = max_update
        self.update_time_window = update_time_window
        self.max_error_requests = max_error_requests
        self.error_time_window = error_time_window

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope['type'] != 'http':
            # 调用下一个中间件或应用
            await self.app(scope, receive, send)
            return
        
        client_ip = scope['client'][0] if 'client' in scope else 'unknown'
        current_time = int(time.time())
        
        # 判断是否因为错误次数过多而被锁定
        count = await self.app.state.redis_client.get(f'IP:{client_ip}:error')
        if count and count > self.max_error_requests:
            logger.error(f'{client_ip} is locked due to too many errors')
            raise Exception(f'{client_ip} is locked due to too many errors')

        # 限制IP请求频率
        count = await self.app.state.redis_client.incr(f'IP:{client_ip}')
        await self.app.state.redis_client.expire(f'IP:{client_ip}', self.request_time_window)
        if count > self.max_requests:
            logger.error(f'{client_ip} exceed the maximum request limit')
            raise Exception('Too Many Requests')
        
        # 限制IP上传文件频率
        count = await self.app.state.redis_client.incr(f'IP:{client_ip}:upload')
        await self.app.state.redis_client.expire(f'IP:{client_ip}:upload', self.update_time_window)
        if count > self.max_update:
            logger.error(f'{client_ip} 上传次数过多')
            raise Exception('Too Many uploads')
        
        # 统计错误次数
        response = await self.app(scope, receive, send)
        if response.status_code != 400:
            count = await self.app.state.redis_client.incr(f'IP:{client_ip}:error')
            await self.app.state.redis_client.expire(f'IP:{client_ip}:error', self.error_time_window)
        
        return response


class ErrorHandlingMiddleware:
    pass