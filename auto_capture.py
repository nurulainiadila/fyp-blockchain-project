import ipaddress
import socket
from urllib.parse import urlsplit
from url_validator import validate_carousell_url
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from pathlib import Path
from datetime import datetime, timezone
from html import escape
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


def capture_test_evidence(report_id, platform, reported_url):
    """
    Generate a local test screenshot for a victim report.
    Does not visit any external website.
    """

    capture_folder = Path("local_vault") / "test_captures"
    capture_folder.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%d_%H%M%S"
    )

    screenshot_path = capture_folder / (
        f"report_{report_id}_{timestamp}.png"
    )

    safe_platform = escape(platform)
    safe_url = escape(reported_url or "No URL provided")

    html_content = f"""
    <html>
    <body style="font-family:Arial; padding:40px;">
        <h1>ForensicVault - Test Evidence</h1>
        <p>Report ID: REPORT-{report_id:04d}</p>
        <p>Platform: {safe_platform}</p>
        <p>Reported URL: {safe_url}</p>
        <p>Capture Type: LOCAL TEST ONLY</p>
        <p>This is not a screenshot of the reported website.</p>
    </body>
    </html>
    """

    driver = None

    try:
        driver = setup_capture_driver()

        driver.get("data:text/html;charset=utf-8,")

        driver.execute_script(
            "document.open();"
            "document.write(arguments[0]);"
            "document.close();",
            html_content
        )

        if not driver.save_screenshot(str(screenshot_path.resolve())):
            raise RuntimeError("Screenshot capture failed.")

        return screenshot_path

    finally:
        if driver is not None:
            driver.quit()
