
import json
import hashlib
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# ==========================================
# FORENSICVAULT - IIUM SOUQ FEASIBILITY TEST
# ==========================================

OUTPUT_DIR = Path("souq_test_results")
OUTPUT_DIR.mkdir(exist_ok=True)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
)

def validate_url(url):
    """Allow only HTTP/HTTPS URLs."""
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise ValueError("Only HTTP and HTTPS URLs are allowed.")

    if not parsed.hostname:
        raise ValueError("Invalid URL.")

    # Avoid accidentally testing a different website.
    if parsed.hostname.lower() != "souq.iium.edu.my":
        raise ValueError(
            "For this test, use an approved URL on souq.iium.edu.my."
        )

    return url


def extract_title(html):
    """Extract the HTML page title."""
    match = re.search(
        r"<title[^>]*>(.*?)</title>",
        html,
        re.IGNORECASE | re.DOTALL
    )

    if match:
        return re.sub(r"\s+", " ", match.group(1)).strip()

    return None


def extract_metadata(html, property_name):
    """Extract basic Open Graph metadata."""
    pattern = (
        r'<meta[^>]+property=["\']'
        + re.escape(property_name)
        + r'["\'][^>]+content=["\'](.*?)["\']'
    )

    match = re.search(pattern, html, re.IGNORECASE)

    if match:
        return match.group(1).strip()

    # Also support the reverse attribute order.
    pattern = (
        r'<meta[^>]+content=["\'](.*?)["\'][^>]+property=["\']'
        + re.escape(property_name)
        + r'["\']'
    )

    match = re.search(pattern, html, re.IGNORECASE)

    return match.group(1).strip() if match else None


def run_probe(url):
    """Perform one basic request to the approved public page."""

    result = {
        "project": "ForensicVault",
        "test": "IIUM Souq Feasibility Test",
        "tested_at": datetime.now(timezone.utc).isoformat(),
        "url": url,
        "status": "FAILED",
        "http_status": None,
        "page_title": None,
        "product_name": None,
        "product_image": None,
        "price_metadata": None,
        "content_sha256": None,
        "error": None
    }

    print("\nConnecting to IIUM Souq...")
    print("Target:", url)

    request = Request(
        url,
        headers={"User-Agent": USER_AGENT}
    )

    try:
        with urlopen(request, timeout=15) as response:
            status_code = response.status

            # Read a limited amount of page content.
            html_bytes = response.read(2_000_000)

            content = html_bytes.decode(
                "utf-8",
                errors="replace"
            )

            result["http_status"] = status_code
            result["page_title"] = extract_title(content)

            result["product_name"] = extract_metadata(
                content, "og:title"
            )

            result["product_image"] = extract_metadata(
                content, "og:image"
            )

            result["price_metadata"] = extract_metadata(
                content, "product:price:amount"
            )

            result["content_sha256"] = hashlib.sha256(
                html_bytes
            ).hexdigest()

            result["status"] = (
                "SUCCESS" if status_code == 200 else "CHECK"
            )

            print("\n[+] HTTP Status:", status_code)
            print("[+] Page Title:", result["page_title"])
            print("[+] Product Name:", result["product_name"])
            print("[+] Product Image:", result["product_image"])
            print("[+] Price Metadata:", result["price_metadata"])
            print("[+] SHA-256:", result["content_sha256"])

    except HTTPError as error:
        result["http_status"] = error.code
        result["error"] = str(error)

        print("\n[!] HTTP Error:", error.code)

        if error.code in (401, 403, 429):
            print("[!] Access restricted or rate limited.")
            print("[!] Stop testing. Do not attempt to bypass it.")

    except (URLError, TimeoutError, OSError) as error:
        result["error"] = str(error)
        print("\n[!] Connection Error:", error)

    except Exception as error:
        result["error"] = str(error)
        print("\n[!] Unexpected Error:", error)

    return result


def save_reports(result):
    """Save JSON and HTML reports."""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    json_file = OUTPUT_DIR / f"souq_report_{timestamp}.json"
    html_file = OUTPUT_DIR / f"souq_report_{timestamp}.html"

    with open(json_file, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=4, ensure_ascii=False)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>IIUM Souq Test Report</title>
    </head>
    <body>
        <h1>ForensicVault - IIUM Souq Test Report</h1>
        <p><b>Status:</b> {result['status']}</p>
        <p><b>URL:</b> {result['url']}</p>
        <p><b>HTTP Status:</b> {result['http_status']}</p>
        <p><b>Page Title:</b> {result['page_title']}</p>
        <p><b>Product Name:</b> {result['product_name']}</p>
        <p><b>Product Image:</b> {result['product_image']}</p>
        <p><b>Price Metadata:</b> {result['price_metadata']}</p>
        <p><b>SHA-256:</b> {result['content_sha256']}</p>
        <p><b>Error:</b> {result['error']}</p>
        <p><b>Tested At:</b> {result['tested_at']}</p>
    </body>
    </html>
    """

    with open(html_file, "w", encoding="utf-8") as file:
        file.write(html_content)

    print("\n================================")
    print("TEST REPORTS GENERATED")
    print("================================")
    print("JSON:", json_file)
    print("HTML:", html_file)


def main():
    print("========================================")
    print(" FORENSICVAULT - IIUM SOUQ PROBE")
    print("========================================")

    url = input(
        "\nEnter approved public IIUM Souq product URL: "
    ).strip()

    try:
        url = validate_url(url)
    except ValueError as error:
        print("\n[!] Invalid URL:", error)
        sys.exit(1)

    result = run_probe(url)

    save_reports(result)

    print("\nTest completed.")
    print("Final status:", result["status"])


if __name__ == "__main__":
    main()
