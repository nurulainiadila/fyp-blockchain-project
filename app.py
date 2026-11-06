import streamlit as st
import os
import hashlib
from scraper import setup_driver, extract_evidence, generate_file_hash
from blockchain import store_on_blockchain, verify_hash, get_all_evidence

st.set_page_config(page_title="Digital Forensic Preservation System", layout="wide")
st.sidebar.title("🔍 Investigator Menu")
page = st.sidebar.radio("Navigation", ["Dashboard Overview", "Collect Evidence", "Verify Evidence"])

if page == "Dashboard Overview":
    st.header("🛡️ Digital Forensic Preservation System")
    st.success("Blockchain Ledger: Connected to Ganache Local Testnet")
    records = get_all_evidence()
    if records:
        for record in reversed(records):
            st.info(f"**Case ID:** {record['case_id']} | **Timestamp:** {record['timestamp']} | **Hash:** {record['hash']}")
    else:
        st.write("No evidence records found on the blockchain.")

elif page == "Collect Evidence":
    st.header("Collect Evidence")
    
    # Platform Selection Option
    platform = st.radio("Select Target Platform:", ["Carousell (Web Scraping)", "Telegram (API Extraction)"])
    
    with st.form("collection_form"):
        target_url = st.text_input("Target URL / Telegram Channel (e.g., Carousell URL or t.me/channel)")
        case_id = st.text_input("Case ID (e.g., EVD-2026-001)")
        submit_button = st.form_submit_button("Initiate Evidence Extraction")
        
    if submit_button and target_url and case_id:
        with st.spinner(f"Executing Extraction & Capturing Artifacts from {platform}..."):
            try:
                if platform == "Carousell (Web Scraping)":
                    # Auto-fix missing protocol schema to prevent Selenium InvalidArgumentException
                    formatted_url = target_url.strip()
                    if not formatted_url.startswith(("http://", "https://")):
                        formatted_url = "https://" + formatted_url
                    
                    driver = setup_driver()
                    try:
                        evidence = extract_evidence(driver, formatted_url, case_id)
                    finally:
                        driver.quit()
                        
                else:  # Telegram API Extraction
                    from telegram_scraper import extract_telegram_evidence
                    evidence = extract_telegram_evidence(target_url, case_id)

                # Unified Blockchain & Hashing Pipeline
                file_hash = generate_file_hash(evidence["screenshot_path"])
                store_on_blockchain(file_hash, case_id)
                
                st.success("✅ Evidence Successfully Preserved on the Blockchain!")
                st.write(f"**Case ID:** {evidence['case_id']}\n**SHA-256 Hash:** `{file_hash}`")
                
                # Display platform artifact output
                if platform == "Carousell (Web Scraping)" and os.path.exists(evidence["screenshot_path"]):
                    st.image(evidence["screenshot_path"])
                elif platform == "Telegram (API Extraction)" and os.path.exists(evidence["screenshot_path"]):
                    with open(evidence["screenshot_path"], "r", encoding="utf-8") as f:
                        chat_log = f.read()
                    st.text_area("Extracted Telegram Chat Log Artifact:", chat_log, height=300)

            except Exception as e:
                st.error(f"❌ Extraction failed: {e}")

elif page == "Verify Evidence":
    st.header("Verify Evidence Integrity")
    uploaded_file = st.file_uploader("Upload Evidence File", type=['png', 'html', 'txt'])
    if uploaded_file:
        current_hash = hashlib.sha256(uploaded_file.getvalue()).hexdigest()
        st.write(f"**Current Hash:** `{current_hash}`")
        if st.button("Query Smart Contract"):
            is_authentic, linked_case_id = verify_hash(current_hash)
            if is_authentic:
                st.success(f"✅ INTEGRITY VERIFIED: Matches Case ID: {linked_case_id}")
            else:
                st.error("❌ TAMPERING DETECTED: Hash not found on blockchain.")