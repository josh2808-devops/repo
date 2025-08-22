from dataclasses import dataclass
from typing import Optional
import time

import pyotp
from passlib.hash import argon2


ARGON2_PARAMS = {
    "time_cost": 3,
    "memory_cost": 102400,  # ~100MB
    "parallelism": 8,
}


@dataclass
class AuthState:
    failed_attempts: int = 0
    locked_until_ts: float = 0.0


def hash_password(plain_password: str) -> str:
    return argon2.using(**ARGON2_PARAMS).hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return argon2.verify(plain_password, password_hash)
    except Exception:
        return False


def verify_totp(totp_secret: str, totp_code: str) -> bool:
    try:
        totp = pyotp.TOTP(totp_secret)
        return totp.verify(totp_code, valid_window=1)
    except Exception:
        return False


def get_totp_uri(issuer: str, username: str, secret: str) -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name=issuer)


def lockout_check(auth_state: AuthState) -> Optional[int]:
    now = time.time()
    if now < auth_state.locked_until_ts:
        return int(auth_state.locked_until_ts - now)
    return None


def register_failure(auth_state: AuthState) -> None:
    auth_state.failed_attempts += 1
    # Exponential backoff lockout
    if auth_state.failed_attempts >= 5:
        lock_seconds = min(600, 2 ** (auth_state.failed_attempts - 4))
        auth_state.locked_until_ts = time.time() + lock_seconds


def register_success(auth_state: AuthState) -> None:
    auth_state.failed_attempts = 0
    auth_state.locked_until_ts = 0.0