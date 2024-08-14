from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2AuthorizationCodeBearer
from typing import Dict
import httpx

from core.settings import settings

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://github.com/login/oauth/authorize",
    tokenUrl="https://github.com/login/oauth/access_token"
)

async def admin_required(token: str = Depends(oauth2_scheme)):
    async with httpx.AsyncClient() as client:
        user_response = await client.get(
            "https://api.github.com/user",
            # headers={"Authorization": f"Bearer {token['detail']['access_token']}"}
            headers={"Authorization": f"Bearer {token}"}
        )
        if user_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        return user_response.json()