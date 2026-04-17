"""Password reset via SMS + email OTP (same code to both). No reset links."""

import logging
import random

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail

from representatives.otp import normalize_phone_digits, send_transactional_sms

logger = logging.getLogger(__name__)

CACHE_PREFIX = "app_pwd_reset_otp:"
RATE_PREFIX = "app_pwd_reset_send:"


def generate_otp() -> str:
    return f"{random.randint(0, 10**6 - 1):06d}"


def _otp_key(user_id: int) -> str:
    return f"{CACHE_PREFIX}{user_id}"


def _rate_key(user_id: int) -> str:
    return f"{RATE_PREFIX}{user_id}"


def otp_ttl_seconds() -> int:
    return int(getattr(settings, "PASSWORD_RESET_OTP_TTL", 600))


def can_send_password_reset_otp(user_id: int) -> bool:
    limit = int(getattr(settings, "PASSWORD_RESET_OTP_MAX_SENDS_PER_HOUR", 10))
    n = cache.get(_rate_key(user_id), 0)
    return n < limit


def increment_password_reset_send_count(user_id: int) -> None:
    key = _rate_key(user_id)
    try:
        cache.incr(key)
    except ValueError:
        cache.set(key, 1, 3600)


def store_password_reset_otp(user_id: int, otp: str) -> None:
    cache.set(_otp_key(user_id), otp, otp_ttl_seconds())


def verify_and_consume_password_reset_otp(user_id: int, otp: str) -> bool:
    key = _otp_key(user_id)
    expected = cache.get(key)
    if not expected:
        return False
    entered = (otp or "").strip()
    if not entered.isdigit():
        return False
    if entered != expected:
        return False
    cache.delete(key)
    return True


def send_password_reset_sms(phone_digits: str, otp: str) -> None:
    body = (
        f"Your password reset OTP is {otp}. It expires in {otp_ttl_seconds() // 60} minutes. "
        "If you did not request this, ignore this SMS."
    )
    send_transactional_sms(phone_digits, body)


def send_password_reset_email(email: str, otp: str) -> None:
    if not (email or "").strip():
        return
    subject = "Your password reset OTP"
    body = (
        f"Your password reset OTP is {otp}. It expires in {otp_ttl_seconds() // 60} minutes.\n"
        "If you did not request this, ignore this email."
    )
    try:
        send_mail(
            subject,
            body,
            getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@localhost"),
            [email.strip()],
            fail_silently=False,
        )
    except Exception:
        logger.exception("Password reset email failed for %s", email)
