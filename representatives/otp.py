import logging
import random
import re
import time
from pathlib import Path

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail

logger = logging.getLogger(__name__)

CACHE_OTP_PREFIX = "sarpanch_otp:"
CACHE_RATE_PREFIX = "sarpanch_otp_sends:"


def normalize_phone_digits(value) -> str:
    if value is None:
        return ""
    digits = re.sub(r"\D", "", str(value).strip())
    if len(digits) >= 10:
        return digits[-10:]
    return digits


def find_representative_by_phone(digits: str):
    from .models import Representative

    if not digits or len(digits) != 10:
        return None
    matches = []
    for rep in Representative.objects.filter(status="ACTIVE").select_related("local_body"):
        if normalize_phone_digits(rep.mobile_number) == digits:
            matches.append(rep)
    if not matches:
        return None
    if len(matches) > 1:
        logger.warning(
            "Multiple ACTIVE representatives share the same normalized phone; using first id=%s",
            matches[0].pk,
        )
    return matches[0]


def generate_otp() -> str:
    return f"{random.randint(0, 10**6 - 1):06d}"


def _otp_cache_key(digits: str) -> str:
    return f"{CACHE_OTP_PREFIX}{digits}"


def _rate_cache_key(digits: str) -> str:
    return f"{CACHE_RATE_PREFIX}{digits}"


def can_send_otp(digits: str) -> bool:
    limit = getattr(settings, "SARPANCH_OTP_MAX_SENDS_PER_HOUR", 10)
    key = _rate_cache_key(digits)
    n = cache.get(key, 0)
    return n < limit


def increment_send_count(digits: str) -> None:
    key = _rate_cache_key(digits)
    try:
        cache.incr(key)
    except ValueError:
        cache.set(key, 1, 3600)


def store_otp(digits: str, otp: str) -> None:
    ttl = getattr(settings, "SARPANCH_OTP_TTL", 600)
    cache.set(_otp_cache_key(digits), otp, ttl)


def verify_and_consume_otp(digits: str, otp: str) -> bool:
    key = _otp_cache_key(digits)
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


def send_transactional_sms(phone_digits: str, body: str) -> None:
    """Deliver arbitrary SMS text. Without Twilio, logs and writes to sms_outbox/."""
    logger.info("SMS to ***%s: %s", phone_digits[-4:], body[:80])

    if getattr(settings, "SMS_LOG_TO_FILE", True):
        out = Path(settings.BASE_DIR) / "sms_outbox"
        out.mkdir(exist_ok=True)
        fname = f"sms_{phone_digits}_{int(time.time() * 1000)}.txt"
        path = out / fname
        path.write_text(
            f"To: +91{phone_digits}\n{body}\n",
            encoding="utf-8",
        )

    account_sid = (getattr(settings, "TWILIO_ACCOUNT_SID", "") or "").strip()
    auth_token = (getattr(settings, "TWILIO_AUTH_TOKEN", "") or "").strip()
    from_num = (getattr(settings, "TWILIO_FROM_NUMBER", "") or "").strip()
    if account_sid and auth_token and from_num:
        try:
            from twilio.rest import Client  # type: ignore
        except ImportError:
            logger.warning("Twilio not installed; configure pip install twilio for SMS.")
        else:
            try:
                client = Client(account_sid, auth_token)
                to = f"+91{phone_digits}" if len(phone_digits) == 10 else phone_digits
                client.messages.create(body=body, from_=from_num, to=to)
            except Exception:
                logger.exception("Twilio SMS failed; OTP still in sms_outbox / logs")


def send_sms_otp(phone_digits: str, otp: str) -> None:
    """Deliver SMS OTP. Without Twilio, logs and writes to sms_outbox/."""
    msg = f"Your Sarpanch login OTP is {otp}. It expires in {getattr(settings, 'SARPANCH_OTP_TTL', 600) // 60} minutes."
    send_transactional_sms(phone_digits, msg)


def send_email_otp(email: str, otp: str) -> None:
    if not (email or "").strip():
        return
    subject = "Your Sarpanch login OTP"
    body = (
        f"Your OTP is {otp}. It expires in {getattr(settings, 'SARPANCH_OTP_TTL', 600) // 60} minutes.\n"
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
        logger.exception("Sarpanch OTP email failed for %s", email)
