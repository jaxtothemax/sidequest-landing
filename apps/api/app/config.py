import json
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    supabase_url: str = Field(default="")
    supabase_service_key: str = Field(default="")
    supabase_jwt_jwks_url: str = Field(default="")

    openrouter_api_key: str = Field(default="")
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1")
    openrouter_model_default: str = Field(default="anthropic/claude-sonnet-4-5")
    openrouter_model_cheap: str = Field(default="anthropic/claude-haiku-4-5")

    cors_origins: str = Field(default="http://localhost:5173,http://127.0.0.1:5173")

    # Polar.sh payments
    polar_access_token: str = Field(default="")
    polar_webhook_secret: str = Field(default="")
    polar_server: Literal["sandbox", "production"] = Field(default="sandbox")
    # JSON map: {"token2049": "<polar-product-uuid>", ...}
    polar_product_ids: str = Field(default="{}")
    public_web_base_url: str = Field(default="http://localhost:5173")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def polar_product_id_map(self) -> dict[str, str]:
        try:
            parsed = json.loads(self.polar_product_ids or "{}")
        except json.JSONDecodeError:
            return {}
        return {str(k): str(v) for k, v in parsed.items()} if isinstance(parsed, dict) else {}

    @property
    def jwks_url(self) -> str:
        if self.supabase_jwt_jwks_url:
            return self.supabase_jwt_jwks_url
        if self.supabase_url:
            return f"{self.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
        return ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
