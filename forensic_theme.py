import streamlit as st


def apply_forensic_theme():
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