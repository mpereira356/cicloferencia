import re
import unicodedata


def slugify(value):
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    sanitized = re.sub(r"[^a-zA-Z0-9]+", "-", normalized).strip("-").lower()
    return sanitized or "item"
