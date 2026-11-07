
import streamlit as st
from url_validator import validate_carousell_url
from forensic_theme import apply_forensic_theme
from report_database import save_report, save_report_evidence
from victim_evidence import save_victim_evidence


st.set_page_config(
    page_title="ForensicVault | Victim Portal",
    page_icon="🛡️",
    layout="wide",
)

apply_forensic_theme()

st.markdown(
    """
<div class="fv-hero">
    <div class="fv-tag">● VICTIM REPORTING PORTAL</div>
    <div class="fv-hero-title">
        Report. <span>Protect. Preserve.</span>
    </div>
    <div class="fv-hero-description">
        Report suspected e-commerce fraud and submit
        supporting information for investigator review.
    </div>
</div>
    """,
    unsafe_allow_html=True,
)

st.divider()

st.header("📝 Submit a Fraud Report")

with st.form("fraud_report_form"):

    victim_name = st.text_input("Your Name")

    victim_email = st.text_input("Email Address")

    platform = st.selectbox(
        "Platform Where Fraud Occurred",
        ["Carousell", "Telegram"]
    )

    scam_url = st.text_input(
        "Scam Listing or Channel URL"
    )

    incident_description = st.text_area(
        "Describe What Happened",
        placeholder="Explain how the scam happened..."
    )

    evidence_file = st.file_uploader(
        "Upload Supporting Evidence",
        type=["png", "jpg", "jpeg", "pdf", "txt"]
    )

    consent = st.checkbox(
        "I confirm that the information provided is accurate "
        "to the best of my knowledge."
    )

    submitted = st.form_submit_button(
        "Submit Fraud Report",
        type="primary"
    )

    if submitted:

        if not victim_name.strip():
            st.error("Please enter your name.")

        elif not victim_email.strip():
            st.error("Please enter your email address.")

        elif not incident_description.strip():
            st.error("Please describe the incident.")

        elif not consent:
            st.error("Please confirm the declaration.")

        elif platform == "Carousell" and scam_url.strip() and not validate_carousell_url(scam_url):
            st.error(
                "Please enter a valid Carousell HTTPS listing URL."
            )

        else:
            try:
                # Save the victim report
                report_id = save_report(
                    victim_name=victim_name.strip(),
                    victim_email=victim_email.strip(),
                    platform=platform,
                    scam_url=scam_url.strip(),
                    description=incident_description.strip()
                )

                st.success(
                    "Fraud report submitted successfully!"
                )

                st.write(
                    "**Your Report ID:**",
                    f"REPORT-{report_id:04d}"
                )

                # Save uploaded supporting evidence
                if evidence_file is not None:

                    try:
                        evidence_data = save_victim_evidence(
                            evidence_file
                        )

                        save_report_evidence(
                            report_id,
                            evidence_data
                        )

                        st.success(
                            "Supporting evidence saved and linked to your report!"
)

                        st.write(
                            "**Evidence SHA-256:**",
                            evidence_data["sha256"]
                        )

                    except (ValueError, OSError) as exc:
                        st.error(
                            "Report saved, but the supporting "
                            "evidence could not be preserved."
                        )
                        st.warning(str(exc))

                st.info(
                    "Your report has been saved locally "
                    "and is awaiting investigator review."
                )

            except Exception as exc:
                st.error(
                    "Unable to save your fraud report."
                )

                with st.expander("Technical details"):
                    st.text(str(exc))
