import json
import os
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class AlertContacts(BaseModel):
    accident: List[str] = Field(default_factory=list)
    fire: List[str] = Field(default_factory=list)
    flood: List[str] = Field(default_factory=list)


class AppSettings(BaseSettings):
    app_secret_key: str = Field(env="APP_SECRET_KEY")
    admin_username: str = Field(env="ADMIN_USERNAME")
    admin_password_hash: str = Field(env="ADMIN_PASSWORD_HASH", default="")
    admin_totp_secret: str = Field(env="ADMIN_TOTP_SECRET", default="")

    yolo_model_name: str = Field(env="YOLO_MODEL_NAME", default="yolov8n.pt")
    detection_confidence: float = Field(env="DETECTION_CONFIDENCE", default=0.35)
    incident_alert_cooldown_seconds: int = Field(env="INCIDENT_ALERT_COOLDOWN_SECONDS", default=120)
    max_concurrent_streams: int = Field(env="MAX_CONCURRENT_STREAMS", default=9)

    twilio_account_sid: str = Field(env="TWILIO_ACCOUNT_SID", default="")
    twilio_auth_token: str = Field(env="TWILIO_AUTH_TOKEN", default="")
    twilio_from_number: str = Field(env="TWILIO_FROM_NUMBER", default="")

    smtp_host: str = Field(env="SMTP_HOST", default="")
    smtp_port: int = Field(env="SMTP_PORT", default=587)
    smtp_use_tls: bool = Field(env="SMTP_USE_TLS", default=True)
    smtp_username: str = Field(env="SMTP_USERNAME", default="")
    smtp_password: str = Field(env="SMTP_PASSWORD", default="")
    alert_email_from: str = Field(env="ALERT_EMAIL_FROM", default="no-reply@example.com")

    site_location_label: str = Field(env="SITE_LOCATION_LABEL", default="")

    alert_contacts_json: str = Field(env="ALERT_CONTACTS_JSON", default="{}")

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def alert_contacts(self) -> AlertContacts:
        try:
            data = json.loads(self.alert_contacts_json) if self.alert_contacts_json else {}
            return AlertContacts(**{k: v for k, v in data.items() if k in {"accident", "fire", "flood"}})
        except Exception:
            return AlertContacts()


def load_settings() -> AppSettings:
    return AppSettings()