import os
import re
import hashlib
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
import streamlit as st
from report_generator import generate_evidence_report
from report_database import get_all_reports, get_report_evidence, update_report_status
from scraper import (
    setup_driver,
    extract_evidence,
    generate_file_hash,
)
from blockchain import (
    w3,
    CONTRACT_ADDRESS,
    store_on_blockchain,
    verify_hash,
    get_all_evidence,
)
# ==================================================
# PAGE SETTINGS
# ==================================================
st.set_page_config(
    page_title="ForensicVault | Investigator",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)
# ==================================================
# DARK NAVY + ELECTRIC BLUE THEME
# ==================================================
st.markdown("""
<style>
.stApp {
    background:
        radial-gradient(
            ellipse at 85% 5%,
            rgba(50, 78, 220, 0.22),
            transparent 40%
        ),
        #080D1B;
    color: #EAF0FF;
}
.block-container {
    max-width: 1180px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}
[data-testid="stHeader"] {
    background: transparent;
}
[data-testid="stSidebar"] {
    background: #0C1428;
    border-right: 1px solid #1D2B49;
}
[data-testid="stSidebar"] * {
    color: #EAF0FF;
}
[data-testid="stSidebar"] [role="radiogroup"] {
    gap: 0.5rem;
}
[data-testid="stSidebar"] [role="radiogroup"] label {
    padding: 9px 12px;
    border-radius: 10px;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: #182746;
}
[data-testid="stSidebar"]
[role="radiogroup"] label:has(input:checked) {
    background: #1C3261;
}
h1, h2, h3 {
    color: #F5F8FF !important;
    letter-spacing: -0.6px;
}
p, label {
    color: #CFD9EE;
}
[data-testid="stMetric"] {
    background: rgba(18, 30, 55, 0.94);
    border: 1px solid #263A61;
    border-radius: 15px;
    padding: 22px;
}
[data-testid="stMetricLabel"] {
    color: #A6B8D8;
}
[data-testid="stMetricValue"] {
    color: #F6F9FF;
}
div.stButton > button[kind="primary"],
div.stFormSubmitButton > button[kind="primary"] {
    background: linear-gradient(
        110deg, #528BFF, #3152EA
    );
    color: #FFFFFF;
    border: none;
    border-radius: 10px;
    min-height: 44px;
    font-weight: 600;
}
div.stButton > button[kind="primary"]:hover,
div.stFormSubmitButton > button[kind="primary"]:hover {
    background: #4169F1;
    color: white;
}
div.stButton > button[kind="secondary"] {
    background: #111C34;
    border: 1px solid #41639E;
    border-radius: 10px;
    color: #EAF0FF;
    min-height: 44px;
}
div.stButton > button[kind="secondary"]:hover {
    background: #1C3158;
    color: white;
}
[data-testid="stExpander"] {
    background: #101A30;
    border: 1px solid #263958;
    border-radius: 12px;
}
[data-testid="stForm"] {
    background: rgba(17, 27, 49, 0.85);
    border: 1px solid #263958;
    border-radius: 15px;
    padding: 24px;
}
[data-baseweb="input"] > div,
[data-baseweb="select"] > div,
[data-baseweb="textarea"] > div {
    background-color: #121E36;
    color: #EAF0FF;
    border-color: #304567;
}
[data-testid="stDataFrame"] {
    border: 1px solid #263958;
    border-radius: 12px;
}
/* Main hero banner */
.fv-hero {
    position: relative;
    overflow: hidden;
    padding: 48px 42px;
    border-radius: 22px;
    border: 1px solid #294477;
    background:
        radial-gradient(
            circle at 88% 45%,
            rgba(70, 111, 255, 0.48),
            transparent 40%
        ),
        linear-gradient(
            115deg,
            #0C1427 5%,
            #102253 70%,
            #1C3F9B
        );
    margin-bottom: 22px;
}
.fv-tag {
    display: inline-block;
    padding: 7px 13px;
    background: #152A4B;
    border: 1px solid #294E81;
    border-radius: 100px;
    color: #A3C4FF;
    font-size: 12px;
    letter-spacing: 0.5px;
    margin-bottom: 24px;
}
.fv-hero-title {
    font-size: clamp(34px, 4vw, 56px);
    line-height: 1.15;
    letter-spacing: -1.8px;
    font-weight: 750;
    color: #FFFFFF;
    max-width: 780px;
}
.fv-hero-title span {
    color: #8CB7FF;
}
.fv-hero-description {
    margin-top: 20px;
    color: #C3D3F4;
    font-size: 16px;
    max-width: 560px;
    line-height: 1.7;
}
.fv-brand {
    font-size: 24px;
    font-weight: 750;
    color: #FFFFFF;
    letter-spacing: -0.7px;
}
.fv-brand span {
    color: #78A7FF;
}
.fv-section-label {
    color: #8EA4C8;
    font-size: 12px;
    letter-spacing: 1.5px;
    font-weight: 600;
    margin-bottom: 8px;
}
@media (max-width: 768px) {
    .fv-hero {
        padding: 30px 22px;
    }
    .block-container {
        padding-top: 1.5rem;
    }
}
</style>
""", unsafe_allow_html=True)
# ==================================================
# HELPER FUNCTIONS
# ==================================================
PAGES = [
    "Dashboard",
    "Victim Reports",
    "Case Management",
    "Collect Evidence",
    "Evidence Records",
    "Verify Evidence",
]
if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"
def go_to_page(page_name):
    st.session_state.current_page = page_name
def blockchain_ready():
    try:
        return (
            w3.is_connected()
            and len(w3.eth.get_code(CONTRACT_ADDRESS)) > 0
        )
    except Exception:
        return False
def load_records():
    try:
        return get_all_evidence(), None
    except Exception as exc:
        return [], str(exc)
def readable_date(timestamp):
    try:
        return datetime.fromtimestamp(
            int(timestamp)
        ).strftime("%d %b %Y, %I:%M %p")
    except (ValueError, TypeError, OverflowError, OSError):
        return "Unknown date"
def valid_case_id(case_id):
    return bool(
        re.fullmatch(
            r"[A-Za-z0-9_-]{1,50}",
            case_id
        )
    )
def normalize_carousell_url(value):
    value = value.strip()
    if not value.startswith(("https://", "http://")):
        value = "https://" + value
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    allowed_domains = (
        "carousell.com",
        "carousell.com.my",
        "carousell.sg",
        "carousell.ph",
        "carousell.hk",
        "carousell.tw",
        "carousell.id",
    )
    allowed = any(
        host == domain or host.endswith("." + domain)
        for domain in allowed_domains
    )
    if (
        parsed.scheme != "https"
        or not allowed
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise ValueError(
            "Please enter a valid HTTPS Carousell URL."
        )
    try:
        if parsed.port not in (None, 443):
            raise ValueError("Unexpected URL port.")
    except ValueError:
        raise ValueError("Invalid Carousell URL port.")
    return value
def normalize_telegram_target(value):
    value = value.strip()
    if value.startswith("@"):
        value = value[1:]
    if value.startswith(("https://", "http://")):
        parsed = urlparse(value)
        if (
            parsed.scheme != "https"
            or (parsed.hostname or "").lower()
            not in ("t.me", "www.t.me")
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError(
                "Use a public Telegram channel link."
            )
        value = parsed.path.strip("/")
    if not re.fullmatch(
        r"[A-Za-z0-9_]{5,32}",
        value
    ):
        raise ValueError(
            "Enter a valid public Telegram channel username."
        )
    return value
def page_heading(title, description):
    st.title(title)
    st.caption(description)
    st.write("")
def show_record(record):
    case_id = str(record.get("case_id", "Unknown"))
    timestamp = readable_date(record.get("timestamp"))
    evidence_hash = str(record.get("hash", ""))
    with st.expander(
        f"📄 {case_id}  ·  {timestamp}"
    ):
        st.write("**Case ID**")
        st.write(case_id)
        st.write("**Blockchain Timestamp**")
        st.write(timestamp)
        st.write("**SHA-256 Hash**")
        st.code(evidence_hash, language=None)
# ==================================================
# AUTHENTICATION AND ROLE ROUTING
# ==================================================
from auth import create_user, authenticate, get_user
from victim_portal import render_victim_portal
if 'auth_user_id' not in st.session_state:
    st.session_state.auth_user_id = None
current_user = get_user(st.session_state.auth_user_id) if st.session_state.auth_user_id else None
if current_user is None:
    st.title('🛡️ ForensicVault')
    st.caption('Secure local research prototype · Carousell & Telegram fraud reporting')
    login_tab, register_tab = st.tabs(['Login', 'Register as Victim'])
    with login_tab:
        # Keep role selector outside the form so the identifier label updates immediately.
        login_role = st.radio('Login as', ['Victim', 'Investigator'], horizontal=True)
        with st.form('login_form'):
            login_identifier = st.text_input('Email Address' if login_role == 'Victim' else 'Staff ID')
            login_password = st.text_input('Password', type='password')
            login_clicked = st.form_submit_button('Login', type='primary')
        if login_clicked:
            import time
            # Session-level throttle for accidental rapid retries; not an internet-grade rate limiter.
            failures = st.session_state.get('login_failures', 0)
            last_attempt = st.session_state.get('last_login_attempt', 0)
            if failures >= 5 and time.monotonic() - last_attempt < 60:
                st.error('Too many attempts. Please wait one minute.')
            else:
                st.session_state.last_login_attempt = time.monotonic()
                account = authenticate(login_identifier, login_password, role=login_role.lower())
                if account:
                    st.session_state.auth_user_id = account['id']
                    st.session_state.login_failures = 0
                    st.rerun()
                else:
                    st.session_state.login_failures = failures + 1
                    st.error('Invalid login credentials.')
    with register_tab:
        with st.form('registration_form'):
            name = st.text_input('Full Name')
            email = st.text_input('Email Address')
            password = st.text_input('Password (at least 12 characters)', type='password')
            confirm = st.text_input('Confirm Password', type='password')
            register_clicked = st.form_submit_button('Create Victim Account')
        if register_clicked:
            if password != confirm:
                st.error('Passwords do not match.')
            else:
                try:
                    create_user(name, email, password)
                    st.success('Victim account created. You can log in now.')
                except ValueError as exc:
                    st.error(str(exc))
    st.stop()
with st.sidebar:
    st.caption(f"Signed in: {current_user['name']} ({current_user['role']})")
    if st.button('Log out', key='logout_button'):
        st.session_state.auth_user_id = None
        st.session_state.current_page = 'Dashboard'
        st.rerun()
if current_user['role'] == 'victim':
    render_victim_portal(current_user)
else:
    # ==================================================
    # SIDEBAR
    # ==================================================
    with st.sidebar:
        st.markdown(
            '<div class="fv-brand">🛡️ Forensic<span>Vault</span></div>',
            unsafe_allow_html=True,
        )
        st.caption("DIGITAL FORENSIC PRESERVATION")
        st.write("")
        st.divider()
        st.radio(
            "Navigation",
            PAGES,
            key="current_page",
            label_visibility="collapsed",
        )
        st.divider()
        st.caption("INVESTIGATOR WORKSPACE")
        st.caption("FYP Research Prototype")
    page = st.session_state.current_page
    # ==================================================
    # DASHBOARD
    # ==================================================
    if page == "Dashboard":
        # IMPORTANT:
        # HTML starts at the beginning of the line
        # to prevent Markdown from rendering it as code.
        st.markdown(
            """
<div class="fv-hero">
    <div class="fv-tag">● INVESTIGATOR WORKSPACE</div>
    <div class="fv-hero-title">
        Investigate.<br>
        Collect. <span>Preserve.</span>
    </div>
    <div class="fv-hero-description">
        Capture digital evidence, preserve its integrity,
        and verify blockchain records in one workspace.
    </div>
</div>
        """,
            unsafe_allow_html=True,
        )
        action1, action2, space = st.columns(
            [1.3, 1.3, 2.5]
        )
        with action1:
            st.button(
                "＋ Collect Evidence",
                type="primary",
                use_container_width=True,
                on_click=go_to_page,
                args=("Collect Evidence",),
            )
        with action2:
            st.button(
                "♢ Verify Evidence",
                use_container_width=True,
                on_click=go_to_page,
                args=("Verify Evidence",),
            )
        st.write("")
        st.write("")
        connected = blockchain_ready()
        if connected:
            records, error = load_records()
        else:
            records = []
            error = "Ganache or contract unavailable."
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "Evidence Records",
                len(records) if not error else "—",
            )
        with col2:
            st.metric(
                "Blockchain Status",
                "Connected" if connected and not error
                else "Unavailable",
            )
        if error:
            st.warning(
                "Blockchain records are unavailable. "
                "Check Ganache and your contract address."
            )
        st.write("")
        st.write("")
        title_col, button_col = st.columns([4, 1.3])
        with title_col:
            st.subheader("Recent Evidence")
            st.caption(
                "Latest evidence hashes registered on the blockchain."
            )
        with button_col:
            st.button(
                "View All Records",
                use_container_width=True,
                on_click=go_to_page,
                args=("Evidence Records",),
            )
        if not error and records:
            recent = list(reversed(records))[:5]
            table_data = []
            for record in recent:
                evidence_hash = str(record.get("hash", ""))
                table_data.append({
                    "Case ID": record.get("case_id", ""),
                    "Timestamp": readable_date(
                        record.get("timestamp")
                    ),
                    "SHA-256": (
                        evidence_hash[:18] + "..."
                        if len(evidence_hash) > 18
                        else evidence_hash
                    ),
                })
            st.dataframe(
                table_data,
                use_container_width=True,
                hide_index=True,
            )
            with st.expander("View full evidence details"):
                for record in recent:
                    show_record(record)
        elif not error:
            st.info("No evidence records found.")
        st.write("")
        st.caption(
            "ForensicVault · Local research prototype · "
            "Blockchain integrity verification"
        )
    # ==================================================
    # VICTIM REPORTS
    # ==================================================
    elif page == "Victim Reports":
        page_heading(
            "Victim Reports",
            "Review fraud reports submitted through the Victim Portal.",
        )
        try:
            reports = get_all_reports()
            total_reports = len(reports)
            pending_reports = sum(
                1 for report in reports
                if report["status"] == "Pending"
            )
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Reports", total_reports)
            with col2:
                st.metric("Pending Reports", pending_reports)
            st.write("")
            if not reports:
                st.info("No victim reports have been submitted yet.")
            else:
                search = st.text_input(
                    "Search Reports",
                    placeholder="Search by Report ID or platform...",
                )
                for report in reports:
                    report_id = f"REPORT-{report['id']:04d}"
                    if (
                        search.lower() not in report_id.lower()
                        and search.lower() not in report["platform"].lower()
                    ):
                        continue
                    with st.expander(
                        f"📋 {report_id} — {report['platform']} — {report['status']}"
                    ):
                        st.write("**Report ID:**", report_id)
                        st.write("**Status:**", report["status"])
                        st.write("**Platform:**", report["platform"])
                        st.write("**Victim Name:**", report["victim_name"])
                        st.write("**Victim Email:**", report["victim_email"])
                        st.write("**Scam URL:**", report["scam_url"])
                        st.write("**Incident Description:**")
                        st.write(report["description"])
                        st.write("**Submitted At:**", report["submitted_at"])
                        # Only the investigator role can reach this page.
                        status_options = ["Pending", "Under Investigation", "Resolved"]
                        with st.form(key=f"status_form_{report['id']}"):
                            new_status = st.selectbox(
                                "Investigation Status",
                                status_options,
                                index=(status_options.index(report["status"])
                                       if report["status"] in status_options else 0),
                                key=f"status_select_{report['id']}",
                            )
                            save_status = st.form_submit_button("Save Status")
                        if save_status:
                            if new_status == report["status"]:
                                st.info("Status is already up to date.")
                            else:
                                try:
                                    if update_report_status(report["id"], new_status):
                                        st.success(f"Status updated to {new_status}.")
                                        st.rerun()
                                    else:
                                        st.error("Report no longer exists.")
                                except Exception:
                                    st.error("Unable to update report status.")
                        st.divider()
                        st.subheader("📁 Preserved Evidence")
                        evidence_list = get_report_evidence(report["id"])
                        if not evidence_list:
                            st.info(
                                "No uploaded evidence linked to this report."
                            )
                        for evidence in evidence_list:
                            file_path = Path(evidence["file_path"])
                            # Temporary identification of locally generated test captures.
                            # Filename-based detection is not forensic provenance.
                            # Test captures are generated under local_vault/test_captures,
                            # then copied to victim_uploads. This filename convention
                            # is temporary, not a trusted provenance field.
                            is_simulated = bool(re.fullmatch(
                                r"report_\d+_\d{8}_\d{6}\.png",
                                str(evidence["original_filename"]),
                            ))
                            if is_simulated:
                                st.warning(
                                    "🧪 SIMULATED TEST EVIDENCE — generated locally, "
                                    "NOT a capture of the reported website. "
                                    "Blockchain registration is disabled."
                                )
                            st.write(
                                "**Original Filename:**",
                                evidence["original_filename"]
                            )
                            st.write(
                                "**SHA-256:**",
                                evidence["sha256"]
                            )
                            st.write(
                                "**Received At:**",
                                evidence["captured_at"]
                            )
                            if not file_path.is_file():
                                st.error("Preserved evidence file is missing.")
                                continue
                            file_bytes = file_path.read_bytes()
                            current_hash = hashlib.sha256(
                                file_bytes
                            ).hexdigest()
                            if current_hash != evidence["sha256"]:
                                st.error(
                                    "Evidence integrity check failed! "
                                    "The file does not match its recorded hash."
                                )
                                continue
                            st.success(
                                "Local evidence integrity check passed."
                            )
                            # Blockchain registration is restricted to investigators
                            # by the role routing above. Do not register synthetic
                            # test screenshots as real-world evidence.
                            evidence_case_id = report_id
                            if is_simulated:
                                st.info("Test capture: blockchain registration unavailable.")
                            elif not blockchain_ready():
                                st.info("Blockchain registration pending — start Ganache.")
                            else:
                                try:
                                    blockchain_records = get_all_evidence()
                                    matching_records = [
                                        record for record in blockchain_records
                                        if str(record.get("hash", "")).lower() == current_hash.lower()
                                        and str(record.get("case_id", "")) == evidence_case_id
                                    ]
                                    if matching_records:
                                        st.success("Blockchain registered and hash verified for this report.")
                                    else:
                                        st.warning("Pending blockchain registration.")
                                        confirmation = st.checkbox(
                                            "I reviewed this file and understand that hash "
                                            "registration does not prove the reported scam is genuine.",
                                            key=f"confirm_register_{evidence['id']}",
                                        )
                                        if st.button(
                                            "Register SHA-256 on Blockchain",
                                            key=f"register_evidence_{evidence['id']}",
                                            disabled=not confirmation,
                                        ):
                                            # Recheck before sending, to avoid duplicates
                                            # on ordinary repeated clicks.
                                            latest = get_all_evidence()
                                            already_registered = any(
                                                str(r.get("hash", "")).lower() == current_hash.lower()
                                                and str(r.get("case_id", "")) == evidence_case_id
                                                for r in latest
                                            )
                                            if already_registered:
                                                st.info("This hash is already registered for the report.")
                                            else:
                                                store_on_blockchain(current_hash, evidence_case_id)
                                                verified = any(
                                                    str(r.get("hash", "")).lower() == current_hash.lower()
                                                    and str(r.get("case_id", "")) == evidence_case_id
                                                    for r in get_all_evidence()
                                                )
                                                if not verified:
                                                    raise RuntimeError(
                                                        "Blockchain transaction did not produce a verified record."
                                                    )
                                                st.success("Evidence hash registered on Ganache.")
                                                st.rerun()
                                except Exception as blockchain_error:
                                    st.error("Unable to verify or register blockchain evidence.")
                                    with st.expander("Blockchain technical details"):
                                        st.text(str(blockchain_error))
                            if file_path.suffix.lower() in [
                                ".png", ".jpg", ".jpeg"
                            ]:
                                st.image(
                                    file_bytes,
                                    caption=evidence["original_filename"],
                                    width=500
                                )
                            st.download_button(
                                "⬇️ Download Evidence",
                                data=file_bytes,
                                file_name=evidence["original_filename"],
                                key=f"download_{evidence['id']}"
                            )
        except Exception as exc:
            st.error("Unable to load victim reports.")
            with st.expander("Technical details"):
                st.text(str(exc))
    # ==================================================
    # COLLECT EVIDENCE
    # ==================================================
    elif page == "Collect Evidence":
        page_heading(
            "Collect Evidence",
            "Capture digital evidence from supported platforms.",
        )
        st.markdown(
            '<div class="fv-section-label">NEW COLLECTION</div>',
            unsafe_allow_html=True,
        )
        platform = st.selectbox(
            "Evidence Source",
            ["Carousell", "Telegram"],
        )
        with st.form("collection_form"):
            case_id = st.text_input(
                "Case ID",
                placeholder="CASE-2026-001",
            )
            target = st.text_input(
                "Target URL or Channel",
                placeholder=(
                    "https://www.carousell.com.my/..."
                    if platform == "Carousell"
                    else "https://t.me/channelname"
                ),
            )
            submitted = st.form_submit_button(
                "Collect & Preserve Evidence",
                type="primary",
                use_container_width=True,
            )
        st.caption(
            "Evidence artifacts are stored locally. "
            "Their SHA-256 hashes are registered on Ganache."
        )
        if submitted:
            case_id = case_id.strip()
            target = target.strip()
            if not valid_case_id(case_id):
                st.error(
                    "Case ID must contain 1–50 letters, "
                    "numbers, hyphens, or underscores."
                )
            elif not target:
                st.error("Please enter a target.")
            elif not blockchain_ready():
                st.error(
                    "Blockchain unavailable. "
                    "Start Ganache before collecting."
                )
            else:
                try:
                    if platform == "Carousell":
                        target = normalize_carousell_url(target)
                    else:
                        target = normalize_telegram_target(target)
                    with st.spinner(
                        "Collecting and preserving evidence..."
                    ):
                        if platform == "Carousell":
                            driver = setup_driver()
                            try:
                                evidence = extract_evidence(
                                    driver,
                                    target,
                                    case_id,
                                )
                            finally:
                                driver.quit()
                        else:
                            from telegram_scraper import (
                                extract_telegram_evidence,
                            )
                            evidence = extract_telegram_evidence(
                                target,
                                case_id,
                            )
                        artifact_path = evidence["screenshot_path"]
                        if not os.path.isfile(artifact_path):
                            raise FileNotFoundError(
                                "The collected artifact was not found."
                            )
                        file_hash = generate_file_hash(
                            artifact_path
                        )
                        store_on_blockchain(
                            file_hash,
                            case_id,
                        )
                    st.success(
                        "Evidence hash registered on the blockchain."
                    )
                    st.write("**Case ID**")
                    st.write(case_id)
                    st.write("**SHA-256 Hash**")
                    st.code(file_hash, language=None)
                    with st.expander("View Collected Artifact"):
                        if platform == "Carousell":
                            st.image(artifact_path)
                        else:
                            with open(
                                artifact_path,
                                "r",
                                encoding="utf-8",
                            ) as file:
                                chat_log = file.read()
                            st.text_area(
                                "Telegram Chat Log",
                                value=chat_log,
                                height=280,
                            )
                    if platform == "Carousell":
                        st.caption(
                            "The screenshot hash was registered. "
                            "The HTML source is also saved locally, "
                            "but is not yet registered separately."
                        )
                except Exception as exc:
                    st.error(
                        "Evidence collection or preservation failed."
                    )
                    with st.expander("Technical details"):
                        st.text(str(exc))
    # ==================================================
    # CASE MANAGEMENT
    # ==================================================
    elif page == "Case Management":
        page_heading(
            "Case Management",
            "View fraud investigation cases and their linked evidence.",
        )
        if not blockchain_ready():
            st.warning(
                "Ganache or the deployed contract is unavailable."
            )
        else:
            records, error = load_records()
            if error:
                st.error("Unable to retrieve case records.")
                with st.expander("Technical details"):
                    st.text(error)
            elif not records:
                st.info(
                    "No cases found. Collect evidence to create your first case."
                )
            else:
                cases = {}
                for record in records:
                    case_id = str(record.get("case_id", "Unknown"))
                    if case_id not in cases:
                        cases[case_id] = []
                    cases[case_id].append(record)
                st.metric("Total Cases", len(cases))
                st.write("")
                search_case = st.text_input(
                    "Search Cases",
                    placeholder="Enter Case ID...",
                )
                for case_id, evidence_list in cases.items():
                    if search_case.lower() not in case_id.lower():
                        continue
                    with st.expander(
                        f"📁 {case_id} — {len(evidence_list)} Evidence Record(s)"
                    ):
                        st.write("**Case ID:**", case_id)
                        st.write(
                            "**Total Evidence:**",
                            len(evidence_list),
                        )
                        st.divider()
                        for record in evidence_list:
                            show_record(record)
    # ==================================================
    # EVIDENCE RECORDS
    # ==================================================
    elif page == "Evidence Records":
        page_heading(
            "Evidence Records",
            "Explore evidence hashes stored on the blockchain.",
        )
        if not blockchain_ready():
            st.warning(
                "Ganache or the deployed contract is unavailable."
            )
        else:
            records, error = load_records()
            if error:
                st.error(
                    "Unable to retrieve blockchain records."
                )
                with st.expander("Technical details"):
                    st.text(error)
            elif not records:
                st.info("No evidence records found.")
            else:
                st.metric(
                    "Total Blockchain Records",
                    len(records),
                )
                st.write("")
                search = st.text_input(
                    "Search by Case ID",
                    placeholder="Search case...",
                )
                filtered = [
                    record
                    for record in reversed(records)
                    if search.lower()
                    in str(record.get("case_id", "")).lower()
                ]
                if not filtered:
                    st.info("No matching evidence records.")
                for record in filtered:
                    show_record(record)
                    # Generate a PDF using available blockchain metadata
                    case_id = str(record.get("case_id", "Unknown"))
                    evidence_hash = str(record.get("hash", ""))
                    # The current blockchain records do not necessarily
                    # contain the original URL, source or transaction hash.
                    # Do not invent these forensic details.
                    source = record.get("source") or "Not recorded"
                    target_url = record.get("target_url") or "Not recorded"
                    collection_time = record.get("timestamp") or "Not recorded"
                    transaction_hash = record.get("transaction_hash")
                    pdf_bytes = generate_evidence_report(
                        case_id=case_id,
                        source=source,
                        target_url=target_url,
                        evidence_hash=evidence_hash,
                        collection_time=collection_time,
                        verification_status="Not independently verified",
                        transaction_hash=transaction_hash,
                    )
                    st.download_button(
                        label=f"Download PDF Report — {case_id}",
                        data=pdf_bytes,
                        file_name=f"forensic_report_{record.get('index', 'record')}.pdf",
                        mime="application/pdf",
                        key=f"pdf_report_{record.get('index', evidence_hash)}",
                    )
                    st.write("")
    # ==================================================
    # VERIFY EVIDENCE
    # ==================================================
    elif page == "Verify Evidence":
        page_heading(
            "Verify Evidence",
            "Check whether a file's SHA-256 hash "
            "matches a blockchain record.",
        )
        uploaded_file = st.file_uploader(
            "Upload Evidence File",
            type=["png", "html", "txt"],
        )
        if uploaded_file is not None:
            current_hash = hashlib.sha256(
                uploaded_file.getvalue()
            ).hexdigest()
            st.write("**Calculated SHA-256 Hash**")
            st.code(current_hash, language=None)
            st.write("")
            if st.button(
                "Verify Integrity",
                type="primary",
            ):
                if not blockchain_ready():
                    st.error(
                        "Blockchain unavailable. "
                        "Please check Ganache."
                    )
                else:
                    try:
                        verified, linked_case = verify_hash(
                            current_hash
                        )
                        if verified:
                            st.success(
                                "Integrity verified: the file hash "
                                "matches a blockchain record."
                            )
                            st.write(
                                "**Linked Case ID:**",
                                linked_case,
                            )
                        else:
                            st.warning(
                                "No matching hash was found on "
                                "the blockchain. This alone does "
                                "not prove the file was tampered with."
                            )
                    except Exception as exc:
                        st.error(
                            "Verification could not be completed."
                        )
                        with st.expander("Technical details"):
                            st.text(str(exc))
        else:
            st.info(
                "Upload an evidence file to begin verification."
            )
