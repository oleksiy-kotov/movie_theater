import re
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict


class BaseEmailPasswordSchema(BaseModel):
    email: EmailStr
    password: str

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        str_strip_whitespace=True,
    )

    @field_validator("password", mode="before")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must contain at least 8 characters.")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain at least one lower letter.")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one digit.")
        if not re.search(r"[@$!%*?&#]", value):
            raise ValueError(
                "Password must contain at least one special character: @, $, !, %, *, ?, #, &."
            )
        return value

# Registration
class UserRegistrationRequestSchema(BaseEmailPasswordSchema):
    pass

# Login
class UserLoginRequestSchema(BaseEmailPasswordSchema):
    pass


# Activation
class UserActivationRequestSchema(BaseModel):
    email: EmailStr
    token: str

    model_config = ConfigDict(extra="forbid")

# Password reset
class PasswordResetRequestSchema(BaseModel):
    email: EmailStr

    model_config = ConfigDict(extra="forbid")

# Complete reset password
class PasswordResetCompleteRequestSchema(BaseEmailPasswordSchema):
    token: str

# Response
class MessageResponseSchema(BaseModel):
    message: str


class UserRegistrationResponseSchema(BaseModel):
    id: int
    email: EmailStr

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class UserLoginResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefreshRequestSchema(BaseModel):
    refresh_token: str


class TokenRefreshResponseSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"
