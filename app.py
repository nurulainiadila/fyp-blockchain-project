
import os
import re
import hashlib
from datetime import datetime
from urllib.parse import urlparse

import streamlit as st
from report_generator import generate_evidence_report

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
