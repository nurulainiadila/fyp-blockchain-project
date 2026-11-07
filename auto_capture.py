import ipaddress
import socket
from urllib.parse import urlsplit
from url_validator import validate_carousell_url
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def prepare_capture_url(url):
    url = url.strip()

    if not validate_carousell_url(url):
        raise ValueError("Invalid Carousell URL.")

    parsed = urlsplit(url)

    if parsed.hostname not in {
        "carousell.com.my",
        "www.carousell.com.my",
        "carousell.sg",
        "www.carousell.sg",
    }:
        raise ValueError("Unsupported website.")

    return url


def capture_carousell_evidence(url, report_id):
    safe_url = prepare_capture_url(url)

    # Screenshot capture will be connected after
    # browser destination and redirect safeguards.
    return {
        "report_id": report_id,
        "url": safe_url,
        "status": "Pending capture",
    }

def check_public_destination(hostname):
    addresses = socket.getaddrinfo(
        hostname,
        443,
        type=socket.SOCK_STREAM
    )

    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])

        if not ip.is_global:
            raise ValueError(
                "Blocked unsafe or private network destination."
            )

    return True

def setup_capture_driver():
    options = Options()

    options.add_argument("--headless=new")
    options.add_argument("--window-size=1365,900")
    options.add_argument("--disable-notifications")
    options.add_argument("--no-first-run")

    # Block common local-network destinations in Chrome.
    options.add_argument(
        "--host-resolver-rules="
        "MAP localhost ~NOTFOUND,"
        "MAP 127.0.0.1 ~NOTFOUND,"
        "MAP 169.254.169.254 ~NOTFOUND,"
        "MAP 10.0.0.0 ~NOTFOUND,"
        "MAP 192.168.0.0 ~NOTFOUND"
    )

    return webdriver.Chrome(options=options)