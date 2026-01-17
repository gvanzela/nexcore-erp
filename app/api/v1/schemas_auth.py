# app/api/v1/schemas_auth.py

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """
    Payload used when creating a new user.

    - email: unique user identifier (login)
    - password: raw password sent by the client
      (will be hashed before being stored)
    """
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """
    Payload used during authentication (login).

    The password received here is never stored.
    It is only used to verify the hash in the database.
    """
    email: EmailStr
    password: str


class Token(BaseModel):
    """
    Authentication response returned after a successful login.

    - access_token: signed JWT token
    - token_type: usually 'bearer' (Authorization header standard)
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessToken(BaseModel):
    """
    Authentication response returned after a token refresh.

    - access_token: new signed JWT token
    - token_type: usually 'bearer' (Authorization header standard)

    Note:
    This response does NOT include a refresh token.
    The existing refresh token remains valid until it expires.
    """
    access_token: str
    token_type: str = "bearer"


class LogoutRequest(BaseModel):
    """
    Request body for logout.

    - refresh_token: refresh token to be revoked
    """
    refresh_token: str


class LogoutResponse(BaseModel):
    """
    Response returned after a successful logout.

    - message: confirmation message
    """
    message: str


