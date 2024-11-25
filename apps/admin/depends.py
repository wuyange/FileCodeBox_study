from fastapi import Depends, HTTPException, status, Request, Header
from fastapi.security import OAuth2AuthorizationCodeBearer
from typing import Dict, Union
import httpx

from core.settings import settings

# oauth2_scheme = OAuth2AuthorizationCodeBearer(
#     authorizationUrl="https://github.com/login/oauth/authorize",
#     tokenUrl="https://github.com/login/oauth/access_token"
# )

# async def admin_required(token: str = Depends(oauth2_scheme)):
#     async with httpx.AsyncClient() as client:
#         user_response = await client.get(
#             "https://api.github.com/user",
#             # headers={"Authorization": f"Bearer {token['detail']['access_token']}"}
#             headers={"Authorization": f"Bearer {token}"}
#         )
#         if user_response.status_code != 200:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Invalid authentication credentials",
#             )
#         return user_response.json()

async def admin_required(authorization: Union[str, None] = Header(default=None), request: Request = None):
    is_admin = authorization == str(settings.admin_token)
    if request.url.path.startswith('/share/'):
        if not settings.openUpload and not is_admin:
            raise HTTPException(status_code=403, detail='本站未开启游客上传，如需上传请先登录后台')
    else:
        if not is_admin:
            raise HTTPException(status_code=401, detail='未授权或授权校验失败')