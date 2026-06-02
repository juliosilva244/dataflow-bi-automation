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
</style>
""",
        unsafe_allow_html=True,
    )

def load_global_styles():
    load_css()
