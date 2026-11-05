"""Basic text cleanup shared by the keyword baselines."""
import re

_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_EMAIL_RE = re.compile(r"\S+@\S+")
_PHONE_RE = re.compile(r"\+?\d[\d\-\s()]{7,}\d")
_BULLET_RE = re.compile(r"^[\s•\-\*●]+", re.MULTILINE)
_WS_RE = re.compile(r"\s+")


def clean_text(text: str) -> str:
    text = _URL_RE.sub(" ", text)
    text = _EMAIL_RE.sub(" ", text)
    text = _PHONE_RE.sub(" ", text)
    text = _BULLET_RE.sub(" ", text)
    text = _WS_RE.sub(" ", text)
    return text.strip().lower()
