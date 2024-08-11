from fastapi import FastAPI, Request
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .response import APIResponse


class ApiExceptionHandler:
    def __init__(self, app=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if app is not None:
            self.init_app(app)

    def init_app(self, app: FastAPI):
        app.add_exception_handler(Exception, handler=self.all_exception_handler)
        app.add_exception_handler(StarletteHTTPException, handler=self.http_exception_handler)
        app.add_exception_handler(RequestValidationError, handler=self.validation_exception_handler)

    async def validation_exception_handler(self, request: Request, exc: RequestValidationError):
        return JSONResponse(content=APIResponse(code=400, message='参数校验错误', result={
            "detail": exc.errors(),
            "body": exc.body
        }).dict(), status_code=400)

    async def all_exception_handler(self, request: Request, exc: Exception):
        request._receive
        return JSONResponse(content=APIResponse(code=500, message='Internal Server Error', detail='服务器内部错误').dict(), status_code=500)

    async def http_exception_handler(self, request: Request, exc: StarletteHTTPException):
        return JSONResponse(content=APIResponse(code=exc.status_code, message=exc.detail, detail=exc.details).dict(), status_code=exc.status_code)