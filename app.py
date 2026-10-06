import streamlit as st
import os
import hashlib
from scraper import setup_driver, login_to_facebook, extract_evidence, generate_file_hash
from blockchain import store_on_blockchain, verify_hash, get_all_evidence

# Set up the dashboard interface
st.set_page_config(page_title="Digital Forensic Preservation System", layout="wide")

st.sidebar.title("🔍 Investigator Menu")
page = st.sidebar.radio("Navigation", ["Dashboard Overview", "Collect Evidence", "Verify Evidence"])

if page == "Dashboard Overview":
    st.header("🛡️ Digital Forensic Preservation System")
    st.write("E-Commerce Fraud Investigation using Blockchain Technology")
    
    st.subheader("System Status")
    st.success("Blockchain Ledger: Connected to Ganache Local Testnet")
    
    st.subheader("Recent Evidence Log")
    records = get_all_evidence()
    if records:
        for record in reversed(records):
            st.info(f"**Case ID:** {record['case_id']} | **Timestamp:** {record['timestamp']} | **Hash:** {record['hash']}")
    else:
        st.write("No evidence records found on the blockchain.")

elif page == "Collect Evidence":
    st.header("Collect Evidence from Carousell")
    st.write("Extract volatile artifacts, generate a cryptographic hash, and anchor it to the ledger.")
    
    with st.form("collection_form"):
        st.subheader("Target Information")
        target_url = st.text_input("Target URL (e.g., Carousell Listing)")
        case_id = st.text_input("Case ID (e.g., EVD-2026-001)")
        
        submit_button = st.form_submit_button("Initiate Evidence Extraction")
        
    if submit_button:
        if not target_url or not case_id:
            st.error("Please provide both a Target URL and a Case ID.")
        else:
            with st.spinner("Executing Web Navigation Request & Extracting Artifacts..."):
                driver = setup_driver()
                try:
                    # Notice we removed the login function completely
                    evidence = extract_evidence(driver, target_url, case_id)
                    
                    st.info("Computing SHA-256 Hash from saved physical file...")
                    file_hash = generate_file_hash(evidence["screenshot_path"])
                    
                    st.info("Anchoring Hash and Case ID to the Blockchain Ledger...")
                    store_on_blockchain(file_hash, case_id)
                    
                    st.success("✅ Evidence Successfully Preserved on the Blockchain!")
                    st.write(f"**Case ID:** {evidence['case_id']}")
                    st.write(f"**Page Title:** {evidence['title']}")
                    st.write(f"**SHA-256 Hash:** `{file_hash}`")
                    
                    st.image(evidence["screenshot_path"], caption="Visual Artifact Captured from Target Platform")
                    
                except Exception as e:
                    st.error(f"An error occurred during extraction: {e}")
                finally:
                    driver.quit() # Reactivated so the browser closes cleanly

elif page == "Verify Evidence":
    st.header("Verify Evidence Integrity")
    st.write("Upload a local evidence artifact to compute its new hash and compare it against the immutable Ganache ledger to detect tampering.")
    
    uploaded_file = st.file_uploader("Upload Evidence File (e.g., Screenshot PNG)", type=['png', 'html'])
    
    if uploaded_file is not None:
        # Read the uploaded file to compute its current SHA-256 hash
        bytes_data = uploaded_file.getvalue()
        current_hash = hashlib.sha256(bytes_data).hexdigest()
        
        st.write(f"**Current Hash of Uploaded File:** `{current_hash}`")
        
        if st.button("Query Smart Contract"):
            with st.spinner("Verifying against Blockchain Ledger..."):
                # Check if this exact hash exists on the blockchain
                is_authentic, linked_case_id = verify_hash(current_hash)
                
                if is_authentic:
                    st.success("✅ INTEGRITY VERIFIED: Evidence Authentic")
                    st.write(f"This file has not been tampered with. It matches the immutable record for Case ID: **{linked_case_id}**")
                else:
                    st.error("❌ TAMPERING DETECTED: Evidence Invalid")
                    st.write("The cryptographic hash of this file does not exist on the blockchain ledger. The evidence may have been modified.")