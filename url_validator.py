
from urllib.parse import urlsplit


def validate_carousell_url(url):
    try:
        parsed = urlsplit(url.strip())

        if parsed.scheme != "https":
            return False

        if parsed.username or parsed.password:
            return False

        if parsed.port is not None:
            return False

        hostname = (parsed.hostname or "").lower().rstrip(".")

        allowed_domains = {
            "carousell.sg",
            "www.carousell.sg",
            "carousell.com.my",
            "www.carousell.com.my",
        }

        if hostname not in allowed_domains:
            return False

        if not parsed.path or parsed.path == "/":
            return False

        return True

    except ValueError:
        return False
