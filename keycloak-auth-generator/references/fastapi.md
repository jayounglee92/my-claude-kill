# FastAPI + Keycloak

## Overview

FastAPI + `PyJWT` (JWT verification) or `fastapi-keycloak` library combination.
FastAPI acts as an API server that **verifies** JWT tokens received from the frontend.

> **⚠️ Do NOT use `python-jose`.** It has been abandoned since 2021 and causes import errors on Python 3.10+. FastAPI official docs have also migrated to PyJWT.

**Two approaches:**
1. **PyJWT** (recommended) — Lightweight, actively maintained. FastAPI's official recommendation.
2. **fastapi-keycloak library** — Includes user management and Swagger OIDC integration. Feature-rich.

Default to Option 1. If the user wants admin features or Swagger OIDC, use Option 2.

## Required Packages

### Option 1 (PyJWT — recommended)
```bash
pip install fastapi uvicorn "pyjwt[crypto]" httpx
```

> `pyjwt[crypto]` includes the `cryptography` dependency needed for RS256 verification.

### Option 2 (fastapi-keycloak)
```bash
pip install fastapi uvicorn fastapi-keycloak
```

## Environment Variables (.env)

```env
KEYCLOAK_URL=https://auth.company.com
KEYCLOAK_REALM=my-realm
KEYCLOAK_CLIENT_ID=my-api
KEYCLOAK_CLIENT_SECRET=your-client-secret
```

## Option 1: PyJWT (recommended)

### Generated Files

#### 1. `app/core/config.py` — Config

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    KEYCLOAK_URL: str = "https://auth.company.com"
    KEYCLOAK_REALM: str = "my-realm"
    KEYCLOAK_CLIENT_ID: str = "my-api"
    KEYCLOAK_CLIENT_SECRET: str = ""

    @property
    def keycloak_issuer(self) -> str:
        return f"{self.KEYCLOAK_URL}/realms/{self.KEYCLOAK_REALM}"

    @property
    def keycloak_jwks_url(self) -> str:
        return f"{self.keycloak_issuer}/protocol/openid-connect/certs"

    @property
    def keycloak_token_url(self) -> str:
        return f"{self.keycloak_issuer}/protocol/openid-connect/token"

    class Config:
        env_file = ".env"


settings = Settings()
```

#### 2. `app/core/auth.py` — Auth Dependency

```python
from typing import Annotated

import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer

from app.core.config import settings

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{settings.keycloak_issuer}/protocol/openid-connect/auth",
    tokenUrl=settings.keycloak_token_url,
)

# JWKS client (caches public keys automatically)
jwks_client = PyJWKClient(settings.keycloak_jwks_url)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> dict:
    """Verify JWT token and return user info"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication failed",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.KEYCLOAK_CLIENT_ID,
            issuer=settings.keycloak_issuer,
            options={"verify_exp": True},
        )
        return payload
    except jwt.exceptions.InvalidTokenError:
        raise credentials_exception


def require_role(required_roles: list[str]):
    """RBAC dependency factory"""

    async def _check_roles(
        user: Annotated[dict, Depends(get_current_user)],
    ) -> dict:
        user_roles = user.get("realm_access", {}).get("roles", [])
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )
        return user

    return _check_roles
```

#### 3. `app/main.py` — FastAPI App

```python
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.auth import get_current_user, require_role

app = FastAPI(title="My API", version="1.0.0")

# CORS settings (allow frontend domain)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/protected")
async def protected_route(
    user: Annotated[dict, Depends(get_current_user)],
):
    return {
        "message": "Authenticated users only",
        "user": user.get("preferred_username"),
        "email": user.get("email"),
    }


@app.get("/admin")
async def admin_route(
    user: Annotated[dict, Depends(require_role(["admin"]))],
):
    return {
        "message": "Admin only",
        "user": user.get("preferred_username"),
    }


@app.get("/me")
async def get_me(
    user: Annotated[dict, Depends(get_current_user)],
):
    return {
        "sub": user.get("sub"),
        "username": user.get("preferred_username"),
        "email": user.get("email"),
        "name": user.get("name"),
        "roles": user.get("realm_access", {}).get("roles", []),
    }
```

## Option 2: fastapi-keycloak Library

```python
from fastapi import FastAPI, Depends
from fastapi_keycloak import FastAPIKeycloak, OIDCUser

app = FastAPI()

idp = FastAPIKeycloak(
    server_url=f"{settings.KEYCLOAK_URL}",
    client_id=settings.KEYCLOAK_CLIENT_ID,
    client_secret=settings.KEYCLOAK_CLIENT_SECRET,
    realm=settings.KEYCLOAK_REALM,
    callback_uri="http://localhost:8000/callback",
)

# Add OIDC login button to Swagger UI
idp.add_swagger_config(app)


@app.get("/protected")
async def protected(user: OIDCUser = Depends(idp.get_current_user())):
    return {"message": f"Hello {user.preferred_username}"}


@app.get("/admin")
async def admin(
    user: OIDCUser = Depends(idp.get_current_user(required_roles=["admin"])),
):
    return {"message": f"Admin: {user.preferred_username}"}
```

## Keycloak Client Configuration

| Setting | Value |
|---------|-------|
| Client type | OpenID Connect |
| Client authentication | ON (confidential) |
| Standard flow | ON |
| Direct access grants | ON (dev/testing) |
| Valid redirect URIs | `http://localhost:8000/*` |
| Web origins | `http://localhost:3000` (frontend) |

## Troubleshooting

**"Could not deserialize key data" error**
→ Verify `pyjwt[crypto]` is installed (`pip install "pyjwt[crypto]"`)

**"audience doesn't match" error**
→ Verify Keycloak Client audience mapping. Client Scopes → dedicated scope → Mappers → add Audience

**Swagger UI auth not working**
→ Use Option 2's `idp.add_swagger_config(app)`, or create a separate public client for Swagger

**CORS error**
→ Add frontend origin to `CORSMiddleware`

**ImportError with `python-jose`**
→ Do NOT use `python-jose`. It is abandoned and broken on Python 3.10+. Switch to `PyJWT`.
