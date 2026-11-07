import hashlib
from pathlib import Path
import streamlit as st
from url_validator import validate_carousell_url
from report_database import save_report, save_report_evidence, get_reports_for_user, get_report_evidence
from victim_evidence import save_victim_evidence, save_captured_evidence
from auto_capture import capture_test_evidence

def render_victim_portal(user):
    if not user or user.get('role') != 'victim':
        st.error('Victim login required.')
        st.stop()
    st.title('🛡️ Victim Portal')
    st.caption('Report suspected Carousell or Telegram fraud and track your own reports.')
    tab_submit, tab_reports = st.tabs(['Submit Fraud Report', 'My Reports'])
    with tab_submit:
        with st.form('fraud_report_form'):
            platform = st.selectbox('Platform', ['Carousell', 'Telegram'])
            scam_url = st.text_input('Scam Listing or Channel URL (optional)')
            description = st.text_area('Describe What Happened')
            evidence_file = st.file_uploader('Supporting Evidence', type=['png','jpg','jpeg','pdf','txt'])
            consent = st.checkbox('I confirm this report is accurate to the best of my knowledge.')
            submitted = st.form_submit_button('Submit Fraud Report', type='primary')
        if submitted:
            if not description.strip():
                st.error('Please describe the incident.')
            elif not consent:
                st.error('Please confirm the declaration.')
            elif platform == 'Carousell' and scam_url.strip() and not validate_carousell_url(scam_url):
                st.error('Please enter a valid HTTPS Carousell listing URL.')
            elif evidence_file is not None and evidence_file.size > 10 * 1024 * 1024:
                st.error('Evidence file must be 10 MB or smaller.')
            else:
                try:
                    report_id = save_report(user['name'], user['email'], platform,
                                            scam_url.strip(), description.strip(), user_id=user['id'])
                    st.success(f'Report REPORT-{report_id:04d} submitted.')
                    if evidence_file is not None:
                        try:
                            data = save_victim_evidence(evidence_file)
                            save_report_evidence(report_id, data)
                            st.success('Supporting evidence saved with SHA-256 hash.')
                        except (ValueError, OSError) as exc:
                            st.warning(f'Report saved, but evidence upload failed: {exc}')
                    # Local demonstration only. Never claim this is a live capture.
                    try:
                        test_path = capture_test_evidence(report_id, platform, scam_url.strip())
                        test_data = save_captured_evidence(test_path)
                        save_report_evidence(report_id, test_data)
                        st.info('Simulated test screenshot saved (NOT a capture of the reported site).')
                    except Exception:
                        st.info('Report saved; simulated screenshot unavailable.')
                except Exception:
                    st.error('Unable to save report. Please try again.')
    with tab_reports:
        reports = get_reports_for_user(user['id'])
        if not reports:
            st.info('You have not submitted any reports with this account.')
        for report in reports:
            with st.expander(f"REPORT-{report['id']:04d} · {report['platform']} · {report['status']}"):
                st.write('**Submitted:**', report['submitted_at'])
                st.write('**Status:**', report['status'])
                st.write('**Description:**', report['description'])
                for evidence in get_report_evidence(report['id']):
                    st.write('**File:**', evidence['original_filename'])
                    is_test = evidence['original_filename'].startswith(f"report_{report['id']}_")
                    if is_test:
                        st.warning('SIMULATED TEST EVIDENCE — not a real website capture.')
                    path = Path(evidence['file_path'])
                    if not path.is_file():
                        st.error('Evidence file is missing.')
                        continue
                    data = path.read_bytes()
                    if hashlib.sha256(data).hexdigest() != evidence['sha256']:
                        st.error('Evidence integrity mismatch. File cannot be trusted.')
                        continue
                    st.caption('Local SHA-256 integrity check passed.')
                    if path.suffix.lower() in ('.png', '.jpg', '.jpeg'):
                        st.image(data, width=400)
                    st.download_button('Download Evidence', data, file_name=evidence['original_filename'],
                                       key=f"victim_download_{evidence['id']}")

if __name__ == '__main__':
    st.set_page_config(page_title='ForensicVault | Victim Portal', page_icon='🛡️')
    st.warning('For secure role-based login, launch the unified portal with: python -m streamlit run app.py')
