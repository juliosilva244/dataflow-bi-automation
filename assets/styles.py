import streamlit as st

def load_css():
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: 
        radial-gradient(circle at top left, rgba(0,153,255,0.10), transparent 30%),
        radial-gradient(circle at bottom right, rgba(0,255,200,0.07), transparent 30%),
        #020617;
    color: #ffffff;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #06111f 0%, #020617 100%);
    border-right: 1px solid rgba(255,255,255,0.08);
}

/* Titles */
.main-title {
    font-size: 2.8rem;
    font-weight: 800;
    line-height: 1.1;
    margin-bottom: 0.5rem;
    background: linear-gradient(to right, #ffffff, #94a3b8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.main-subtitle {
    font-size: 1.1rem;
    color: #94a3b8;
    margin-bottom: 1.5rem;
    max-width: 700px;
}

.section-header {
    margin-top: 2rem;
    margin-bottom: 1.5rem;
}

.section-title {
    font-size: 1.6rem;
    font-weight: 700;
    color: #ffffff;
}

.section-subtitle {
    font-size: 0.95rem;
    color: #64748b;
}

/* KPI Cards */
.kpi-card {
    background: linear-gradient(135deg, rgba(15,23,42,0.96), rgba(2,6,23,0.96));
    border: 1px solid rgba(14,165,233,0.20);
    border-radius: 20px;
    padding: 1.5rem;
    box-shadow: 0 0 24px rgba(14,165,233,0.08);
    transition: 0.3s ease;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.kpi-card:hover {
    transform: translateY(-4px);
    border-color: rgba(14,165,233,0.45);
    box-shadow: 0 8px 32px rgba(14,165,233,0.15);
}

.kpi-icon {
    font-size: 1.8rem;
    margin-bottom: 0.8rem;
}

.kpi-title {
    font-size: 0.9rem;
    font-weight: 600;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.kpi-value {
    font-size: 2rem;
    font-weight: 800;
    color: #ffffff;
    margin: 0.5rem 0;
}

.kpi-badge {
    font-size: 0.75rem;
    padding: 0.2rem 0.6rem;
    border-radius: 99px;
    background: rgba(14,165,233,0.15);
    color: #38bdf8;
    width: fit-content;
    margin-bottom: 0.5rem;
}

.kpi-growth-positive {
    color: #4ade80;
    font-weight: 600;
    font-size: 0.9rem;
}

.kpi-growth-negative {
    color: #f87171;
    font-weight: 600;
    font-size: 0.9rem;
}

.kpi-growth-neutral {
    color: #94a3b8;
    font-weight: 600;
    font-size: 0.9rem;
}

/* Chart Cards */
.chart-card {
    background: rgba(15,23,42,0.6);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 24px;
    padding: 1rem;
    margin-bottom: 1.5rem;
}

/* Insight Cards */
.insight-card {
    background: rgba(15,23,42,0.8);
    border-left: 4px solid #38bdf8;
    border-radius: 12px;
    padding: 1.2rem;
    margin-bottom: 1rem;
}

.insight-title {
    font-weight: 700;
    font-size: 1rem;
    color: #ffffff;
    margin-bottom: 0.5rem;
}

.insight-text {
    font-size: 0.95rem;
    color: #94a3b8;
    line-height: 1.5;
}

.insight-highlight {
    color: #38bdf8;
    font-weight: 600;
}

/* Smart Insights */
.smart-insight-card {
    background: linear-gradient(90deg, rgba(14,165,233,0.05), transparent);
    border: 1px solid rgba(14,165,233,0.1);
    border-radius: 16px;
    padding: 1.2rem;
    margin-bottom: 1rem;
    display: flex;
    gap: 1.2rem;
}

.smart-insight-icon {
    font-size: 1.5rem;
    background: rgba(14,165,233,0.1);
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 12px;
}

.smart-insight-title {
    font-weight: 700;
    color: #ffffff;
}

.smart-insight-badge {
    font-size: 0.7rem;
    text-transform: uppercase;
    background: #0ea5e9;
    color: white;
    padding: 2px 8px;
    border-radius: 4px;
    font-weight: 800;
}

/* Forms and Buttons */
.stButton > button {
    background: linear-gradient(135deg, #0ea5e9, #0284c7) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.6rem 1.5rem !important;
    font-weight: 600 !important;
    transition: 0.3s ease !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(14,165,233,0.3) !important;
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: #020617;
}

::-webkit-scrollbar-thumb {
    background: #1e293b;
    border-radius: 99px;
}

::-webkit-scrollbar-thumb:hover {
    background: #334155;
}

/* DataFlow Fusion Design System: midnight + aurora + glass + AI */
:root {
 --df-bg:#080d1b; --df-surface:#111b31; --df-line:rgba(156,181,240,.17);
 --df-text:#f5f8ff; --df-muted:#a3b3d2; --df-blue:#4b93ff;
 --df-violet:#a37bff; --df-cyan:#4de1e3;
}
html {scroll-behavior:smooth}
.stApp {
 background:radial-gradient(ellipse 55% 38% at 85% 0%,rgba(111,72,230,.18),transparent 85%),
 radial-gradient(ellipse 45% 42% at 0% 30%,rgba(23,131,218,.11),transparent 90%),
 linear-gradient(145deg,#080d1b,#0b1225 55%,#090d1a)!important;
 color:var(--df-text);
}
[data-testid="stAppViewContainer"]>.main .block-container {
 max-width:1600px;padding-top:2rem;padding-bottom:5rem;
}
[data-testid="stHeader"]{background:rgba(8,13,27,.78);backdrop-filter:blur(18px);border-bottom:1px solid rgba(148,163,184,.08)}
section[data-testid="stSidebar"]{
 background:linear-gradient(170deg,rgba(19,29,54,.98),rgba(8,13,27,.99))!important;
 border-right:1px solid var(--df-line)!important;
}
section[data-testid="stSidebar"] [data-testid="stButton"] button[kind="secondary"] {
 background:transparent!important;box-shadow:none!important;border:1px solid transparent!important;
 color:#b9c6df!important;text-align:left;justify-content:flex-start;
}
section[data-testid="stSidebar"] [data-testid="stButton"] button[kind="secondary"]:hover {
 background:rgba(103,129,215,.12)!important;border-color:var(--df-line)!important;color:white!important;
}
section[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"]{
 background:linear-gradient(100deg,rgba(65,126,248,.3),rgba(141,89,250,.18))!important;
 border:1px solid rgba(117,151,255,.4)!important;box-shadow:inset 3px 0 0 #76aaff!important;
 text-align:left;justify-content:flex-start;
}
.hero-block{position:relative;overflow:hidden;padding:2rem 2.25rem;margin:0 0 1.25rem;
 border:1px solid rgba(134,155,234,.25);border-radius:24px;
 background:linear-gradient(115deg,rgba(29,45,82,.85),rgba(17,25,48,.7) 65%,rgba(77,44,127,.33));
 box-shadow:0 18px 70px rgba(0,0,0,.15),inset 0 1px 0 rgba(255,255,255,.07)}
.hero-block:after{content:"";position:absolute;width:250px;height:250px;right:-75px;top:-150px;
 background:radial-gradient(circle,rgba(129,92,255,.3),transparent 70%);pointer-events:none}
.hero-eyebrow{font-size:.73rem;letter-spacing:.18em;text-transform:uppercase;color:#8dc9ff;font-weight:800;margin-bottom:.8rem}
.main-title{font-size:clamp(2rem,4vw,3.1rem)!important;letter-spacing:-.045em;
 background:linear-gradient(105deg,#fff 25%,#b7c9ff 67%,#a48bff)!important;
 -webkit-background-clip:text!important;background-clip:text!important}
.main-subtitle{color:#b2c1dc!important;line-height:1.75;max-width:900px}
.source-card{display:inline-block;padding:.65rem 1rem;border-radius:12px;
 background:rgba(77,115,202,.12);border:1px solid var(--df-line);font-size:.85rem;color:#c6d8ff}
.section-title{letter-spacing:-.03em}.section-subtitle{color:var(--df-muted)!important}
.kpi-card,.chart-card,.insight-card,.smart-insight-card{
 background:linear-gradient(150deg,rgba(28,41,70,.87),rgba(15,23,44,.9))!important;
 border:1px solid var(--df-line)!important;border-radius:20px!important;
 box-shadow:0 12px 40px rgba(0,0,0,.14),inset 0 1px 0 rgba(255,255,255,.035)!important;
 backdrop-filter:blur(16px);transition:transform .2s ease,border-color .2s ease,box-shadow .2s ease;
}
.kpi-card:hover,.chart-card:hover,.insight-card:hover{transform:translateY(-3px);
 border-color:rgba(122,160,255,.4)!important;box-shadow:0 16px 45px rgba(30,73,174,.13)!important}
.kpi-value{font-variant-numeric:tabular-nums;letter-spacing:-.04em}
.kpi-badge{background:rgba(100,128,255,.16)!important;color:#a8bfff!important}
[data-testid="stMetric"]{padding:1.05rem 1.2rem;border:1px solid var(--df-line);
 border-radius:16px;background:linear-gradient(150deg,rgba(31,44,77,.73),rgba(17,25,47,.73));
 min-height:110px}
[data-testid="stMetricLabel"]{color:#b1bfd9}[data-testid="stMetricValue"]{letter-spacing:-.04em;font-variant-numeric:tabular-nums}
[data-testid="stVerticalBlockBorderWrapper"]>div{border-color:var(--df-line)}
[data-testid="stDataFrame"],[data-testid="stPlotlyChart"]{border-radius:16px;overflow:hidden}
div[data-baseweb="select"]>div,div[data-baseweb="input"]>div,[data-testid="stDateInput"] input{
 background:#17223b!important;border-color:rgba(143,166,223,.25)!important;border-radius:12px!important}
.stButton>button[kind="primary"],.stDownloadButton>button{
 background:linear-gradient(110deg,#397dff,#7955ec)!important;border:1px solid rgba(183,186,255,.22)!important;
 box-shadow:0 7px 22px rgba(80,94,240,.19)!important;
}
.stButton>button:focus-visible,.stDownloadButton>button:focus-visible{outline:2px solid #8ad6ff;outline-offset:3px}
@media(max-width:768px){
 [data-testid="stAppViewContainer"]>.main .block-container{padding:1.2rem .8rem 3rem}
 .hero-block{padding:1.25rem;border-radius:17px}.main-title{font-size:2rem!important}
 .main-subtitle{font-size:.92rem}.kpi-card{padding:1rem}.section-title{font-size:1.3rem}
}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation-duration:.01ms!important;transition-duration:.01ms!important;scroll-behavior:auto!important}}

</style>
""",
        unsafe_allow_html=True,
    )

def load_global_styles():
    load_css()
