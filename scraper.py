import os
import time
import hashlib
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

STORAGE_VAULT = "local_vault"

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver

def extract_evidence(driver, target_url, case_id):
    """Extracts evidence from public listings without needing an account."""
    if not os.path.exists(STORAGE_VAULT):
        os.makedirs(STORAGE_VAULT)

    driver.get(target_url)
    time.sleep(8) # Wait for images and text to load completely

    # Generic extraction that won't crash if the UI changes
    try:
        page_title = driver.title
    except Exception:
        page_title = "Title extraction failed - refer to screenshot"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = os.path.join(STORAGE_VAULT, f"{case_id}_{timestamp}_screenshot.png")
    html_path = os.path.join(STORAGE_VAULT, f"{case_id}_{timestamp}_source.html")

    driver.save_screenshot(screenshot_path)
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(driver.page_source)

    return {
        "case_id": case_id,
        "target_url": target_url,
        "title": page_title,
        "screenshot_path": screenshot_path,
        "html_path": html_path,
        "extraction_date": timestamp
    }

def generate_file_hash(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()