import streamlit as st

DESIGN_TOKENS = {
    "bg": "#03091b", "panel": "#07142d", "panel2": "#0a1937",
    "line": "rgba(63,137,255,.34)", "text": "#f5f8ff", "muted": "#a6b7d8",
    "cyan": "#16d9ff", "blue": "#2583ff", "violet": "#8b3dff",
    "magenta": "#d92cff", "green": "#28f2a4",
    "error": "#F43F8C", "warning": "#FBBF24",
}


def load_css():
    # Official viewer mode removes developer/deploy controls, not sidebar controls.
    st.set_option("client.toolbarMode", "viewer")
    st.html(
        "<style>:root{" + "".join(f"--{key}:{value};" for key, value in DESIGN_TOKENS.items())
        + "}</style>"
    )
    st.html(
        """
<style>
html, body, .stApp { font-family: Inter, "Segoe UI", sans-serif; color:var(--text); }
.stApp {
  background:
    radial-gradient(ellipse at 70% -12%, rgba(25,94,255,.28), transparent 32%),
    radial-gradient(ellipse at 105% 58%, rgba(124,28,255,.18), transparent 30%),
    linear-gradient(rgba(13,45,91,.09) 1px, transparent 1px),
    linear-gradient(90deg, rgba(13,45,91,.08) 1px, transparent 1px), var(--bg);
  background-size:auto,auto,40px 40px,40px 40px,auto;
  isolation:isolate;
}
.stApp:before{content:"";position:fixed;z-index:-1;pointer-events:none;width:620px;height:620px;right:-210px;top:-330px;
  border-radius:50%;background:radial-gradient(circle at 32% 68%,rgba(53,214,255,.28),rgba(30,78,255,.2) 28%,rgba(74,31,190,.12) 48%,transparent 70%);
  box-shadow:inset 48px -50px 90px rgba(0,8,35,.8),0 0 90px rgba(33,104,255,.18);opacity:.8}
.stApp:after{content:"";position:fixed;z-index:-1;pointer-events:none;width:520px;height:520px;left:-350px;bottom:-330px;
  border-radius:50%;background:radial-gradient(circle at 65% 30%,rgba(21,219,255,.32),rgba(60,47,255,.23) 26%,rgba(124,36,255,.12) 48%,transparent 70%);
  box-shadow:0 0 100px rgba(49,57,255,.18);opacity:.72}
.block-container { max-width:none !important; padding:.65rem 1rem 1.8rem !important; }
[data-testid="stToolbar"] { background:transparent!important; }
[data-testid="stHeader"] { background:transparent!important; }
[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapseButton"] {
  visibility:visible!important;
  opacity:1!important;
  pointer-events:auto!important;
  position:relative!important;
  z-index:1001!important;
}
[data-testid="stExpandSidebarButton"],
[data-testid="stExpandSidebarButton"] button,
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapseButton"] button {
  cursor:pointer!important;
}
[data-testid="stExpandSidebarButton"]:focus-visible,
[data-testid="stExpandSidebarButton"] button:focus-visible,
[data-testid="stSidebarCollapseButton"]:focus-visible,
[data-testid="stSidebarCollapseButton"] button:focus-visible {
  outline:2px solid #67E8FF!important;
  outline-offset:3px!important;
}
[data-testid="stSidebar"] {
  background:linear-gradient(180deg,rgba(2,8,25,.99),rgba(3,13,35,.98));
  border-right:1px solid rgba(41,111,229,.3); }
[data-testid="stSidebar"] .block-container { padding:1.15rem .72rem !important; }
.brand-lockup { display:flex; align-items:center; gap:.72rem; padding:.15rem .42rem .8rem; }
.brand-mark { width:43px;height:43px;display:grid;place-items:center;border-radius:13px;font-weight:950;
  background:conic-gradient(from 210deg,var(--cyan),var(--blue),var(--magenta),var(--violet),var(--cyan));
  color:white;box-shadow:0 0 28px rgba(113,55,255,.55);clip-path:polygon(25% 3%,75% 3%,100% 50%,75% 97%,25% 97%,0 50%); }
.brand-name {font-size:1.05rem;font-weight:900;letter-spacing:-.03em}.brand-version{font-size:.56rem;
  letter-spacing:.22em;color:var(--cyan);font-weight:800;margin-top:.2rem}
[data-testid="stSidebar"] [role="radiogroup"] {gap:.16rem}
[data-testid="stSidebar"] [role="radiogroup"] label {padding:.46rem .65rem;border-radius:9px;
  color:#b9c8e8;transition:.15s ease;border:1px solid transparent}
[data-testid="stSidebar"] [role="radiogroup"] label>div:first-child{display:none!important}
[data-testid="stSidebar"] [role="radiogroup"] label p{font-size:.79rem!important;letter-spacing:-.01em;white-space:nowrap!important;line-height:1.2!important}
[data-testid="stSidebar"] [role="radiogroup"] label:hover{color:#fff;background:rgba(30,78,156,.18);border-color:rgba(61,126,229,.22)}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {color:white;
  background:linear-gradient(90deg,rgba(110,37,255,.65),rgba(20,100,255,.22));
  border-color:#7447ff;box-shadow:0 0 18px rgba(101,48,255,.35)}
[data-testid="stSidebar"] hr {border-color:rgba(86,122,188,.25)}
h1,h2,h3,h4{letter-spacing:-.035em!important;color:var(--text)!important} h1{font-size:2.1rem!important}
.fusion-topbar {height:23px;display:flex;align-items:center;padding:0 .2rem;margin-bottom:.08rem}
.fusion-eyebrow {font-size:.65rem;color:var(--cyan);font-weight:850;letter-spacing:.17em;text-transform:uppercase}
.fusion-eyebrow:before{content:"◆";font-size:.55rem;margin-right:.45rem;color:#8ba8ff;text-shadow:0 0 10px #3c8cff}
.fusion-hero {display:flex;align-items:flex-end;justify-content:space-between;gap:1rem;margin:.25rem 0 .55rem}
.fusion-greeting {font-size:1.8rem;font-weight:900;letter-spacing:-.04em;line-height:1.05}
.fusion-subtitle {color:#a4b6d9;font-size:.86rem;margin-top:.32rem}
.source-chip {font-size:.68rem;color:#a9bce4;padding:.38rem .62rem;border:1px solid rgba(62,132,240,.28);
  background:rgba(6,20,48,.75);border-radius:9px;white-space:nowrap}
.fusion-hero-meta{display:flex;align-items:flex-end;flex-direction:column;gap:.3rem}.fusion-anomaly{font-size:.62rem;color:#ffe9a5;
  padding:.27rem .55rem;border:1px solid rgba(236,190,48,.32);background:rgba(136,105,11,.18);border-radius:8px;white-space:nowrap}
[data-testid="stFileUploader"],[data-testid="stSelectbox"]>div>div {background:rgba(7,21,49,.88)!important}
[data-testid="stFileUploader"] {padding:.35rem .55rem;border-radius:10px;border:1px solid rgba(54,121,226,.32)}
.fusion-kpi {position:relative;min-height:102px;padding:.78rem .9rem;border-radius:14px;overflow:hidden;
  background:linear-gradient(145deg,rgba(7,25,57,.97),rgba(4,14,35,.97));border:1px solid var(--line);
  box-shadow:inset 0 1px rgba(255,255,255,.05),0 0 24px rgba(24,112,255,.08),0 12px 30px rgba(0,0,0,.24)}
.fusion-kpi:after {content:"";position:absolute;inset:auto -20% -65% 25%;height:100px;filter:blur(24px);opacity:.22}
.fusion-kpi{transition:transform .16s ease,border-color .16s ease,box-shadow .16s ease}.fusion-kpi:hover{transform:translateY(-2px);
  border-color:rgba(85,164,255,.62);box-shadow:inset 0 1px rgba(255,255,255,.07),0 0 28px rgba(41,110,255,.15),0 16px 34px rgba(0,0,0,.3)}
.fusion-kpi-cyan:after{background:var(--cyan)}.fusion-kpi-blue:after{background:var(--blue)}
.fusion-kpi-green:after{background:var(--green)}.fusion-kpi-violet:after{background:var(--magenta)}
.fusion-kpi-head{display:flex;justify-content:space-between;gap:.5rem;align-items:center;color:#e5edff;font-size:.79rem;font-weight:780}
.fusion-kpi-label{display:flex;align-items:center;gap:.45rem}.fusion-kpi-icon{display:grid;place-items:center;width:24px;height:24px;
  border-radius:7px;color:#dffaff;background:linear-gradient(145deg,rgba(20,180,255,.35),rgba(100,45,255,.35));
  border:1px solid rgba(87,164,255,.5);box-shadow:0 0 14px rgba(43,131,255,.28)}
.fusion-delta{font-size:.68rem;padding:.22rem .4rem;border-radius:999px;white-space:nowrap}
.fusion-delta-positive{color:var(--green);background:rgba(16,185,129,.11)}
.fusion-delta-negative{color:#ff8b9d;background:rgba(244,63,94,.11)}.fusion-delta-neutral{color:#a9b7d4;background:rgba(148,163,184,.1)}
.fusion-kpi-value{font-size:clamp(1.25rem,1.7vw,1.8rem);font-weight:900;margin-top:.62rem;white-space:nowrap;
  overflow:hidden;text-overflow:ellipsis;letter-spacing:-.045em;position:relative;z-index:1}
.fusion-kpi-detail{font-size:.64rem;color:#91a6cf;margin-top:.35rem}
[data-testid="stVerticalBlockBorderWrapper"] {border:1px solid rgba(45,115,224,.36)!important;border-radius:14px!important;
  background:linear-gradient(145deg,rgba(7,21,49,.94),rgba(4,13,32,.96));box-shadow:inset 0 1px rgba(255,255,255,.04),0 0 28px rgba(36,94,220,.06)}
[data-testid="stPlotlyChart"] {border:0!important;border-radius:12px;background:transparent!important;padding:0!important}
.panel-title{font-size:1rem;font-weight:850;color:#f3f7ff;margin-bottom:.3rem;letter-spacing:-.02em}.panel-copy{font-size:.77rem;color:#afbfdb;line-height:1.5}
.ai-panel-head{display:flex;gap:.65rem;align-items:center}.ai-orb{width:38px;height:38px;display:grid;place-items:center;border-radius:11px;
  background:linear-gradient(135deg,#7b2cff,#266cff);box-shadow:0 0 20px rgba(118,51,255,.48);font-size:1.15rem}
.ai-status{font-size:.66rem;margin-top:.15rem}.ai-status-online{color:var(--green)}.ai-status-offline{color:#91a4ca}
.ai-guardrails{display:flex;flex-wrap:wrap;gap:.3rem;margin:.55rem 0 .7rem}.ai-guardrails span{font-size:.57rem;color:#9db2db;
  border:1px solid rgba(67,125,221,.28);background:rgba(11,34,76,.58);padding:.22rem .38rem;border-radius:999px}
.fusion-insight{height:142px;padding:.95rem 1rem;border-radius:13px;border:1px solid rgba(57,123,221,.33);
  background:linear-gradient(145deg,rgba(8,25,55,.95),rgba(5,16,39,.97));overflow:hidden}
.fusion-insight-tag{font-size:.58rem;letter-spacing:.12em;color:var(--cyan);font-weight:850}
.fusion-insight-title{font-size:.86rem;font-weight:850;margin:.38rem 0}.fusion-insight-copy{font-size:.71rem;line-height:1.45;color:#aab9d7}
[data-testid="stDataFrame"]{border:0;border-radius:10px;overflow:hidden}
[data-testid="stDataFrame"] [role="columnheader"]{background:rgba(18,38,79,.82)!important;color:#aecaef!important}
.stButton>button,.stDownloadButton>button{border-radius:9px;min-height:2.5rem;font-weight:750;border:1px solid rgba(79,133,255,.55)}
.stButton>button[kind="primary"],.stDownloadButton>button[kind="primary"]{background:linear-gradient(95deg,#7b24ff,#147dff)!important;
  box-shadow:0 0 18px rgba(96,49,255,.4);border-color:#975cff!important}
.stButton>button:focus-visible,.stDownloadButton>button:focus-visible,input:focus-visible,[role="radio"]:focus-visible{outline:3px solid var(--cyan)!important;outline-offset:2px}
[data-testid="stAlert"]{border-radius:11px;font-size:.78rem}.method-card{padding:1rem;border:1px solid var(--line);border-radius:12px;background:var(--panel);line-height:1.55}
[data-testid="stAlert"]>div{padding:.55rem .75rem!important}
[data-testid="stExpander"]{border-color:rgba(53,111,208,.26)!important;background:rgba(5,17,42,.7)!important}
.verified-data,.verified-row{display:flex;justify-content:space-between;gap:.6rem;align-items:center;padding:.34rem .15rem;
  font-size:.67rem;color:#91a4ca;border-bottom:1px solid rgba(79,117,182,.13)}
.verified-data strong{color:var(--green)}.verified-row strong{color:#d7e4ff;font-weight:700}
[data-testid="stSidebar"] [data-testid="stAlert"]{padding:.25rem!important;margin:.35rem 0!important}
[data-testid="stSidebar"] [data-testid="stAlert"] p{font-size:.62rem!important;line-height:1.35!important}
[data-testid="stSegmentedControl"] button{font-size:.67rem!important;min-height:2rem!important;border-color:rgba(67,125,221,.35)!important}
.sales-hero{display:flex;align-items:flex-end;justify-content:space-between;gap:1.25rem;padding:.35rem .1rem .8rem}
.sales-eyebrow{font-size:.62rem;letter-spacing:.18em;color:var(--cyan);font-weight:850;margin-bottom:.45rem}
.sales-title{font-size:2rem;font-weight:920;letter-spacing:-.045em;line-height:1;color:#f7f9ff;text-shadow:0 0 30px rgba(62,126,255,.22)}
.sales-subtitle{font-size:.82rem;color:var(--muted);margin-top:.45rem}
.sales-meta{display:flex;justify-content:flex-end;flex-wrap:wrap;gap:.35rem;max-width:610px}
.sales-meta span{font-size:.63rem;color:#aec1e8;padding:.34rem .52rem;border-radius:8px;border:1px solid rgba(65,128,232,.3);background:rgba(7,23,53,.8)}
.sales-meta .sales-meta-warning{color:#ffe7a0;border-color:rgba(227,178,48,.38);background:rgba(123,92,10,.18)}
.sales-kpi{position:relative;min-height:116px;padding:.82rem .88rem;border-radius:14px;overflow:hidden;background:linear-gradient(145deg,rgba(8,27,61,.98),rgba(4,14,35,.98));border:1px solid rgba(57,131,246,.4);box-shadow:inset 0 1px rgba(255,255,255,.06),0 12px 28px rgba(0,0,0,.25),0 0 22px rgba(33,107,255,.08)}
.sales-kpi:after{content:"";position:absolute;width:140px;height:80px;right:-38px;bottom:-48px;background:var(--cyan);filter:blur(32px);opacity:.14;pointer-events:none}
.sales-kpi-head{display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:.42rem;font-size:.74rem;color:#e8efff;font-weight:800}
.sales-kpi-icon{display:grid;place-items:center;width:25px;height:25px;border-radius:7px;color:#e9fbff;background:linear-gradient(145deg,rgba(15,173,255,.42),rgba(111,42,255,.38));border:1px solid rgba(86,162,255,.55);box-shadow:0 0 14px rgba(44,132,255,.3)}
.sales-kpi-value{font-size:clamp(1.3rem,1.7vw,1.8rem);font-weight:920;letter-spacing:-.04em;margin-top:.68rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;position:relative;z-index:1}
.sales-kpi-foot{font-size:.59rem;color:#8da2cb;margin-top:.4rem}.sales-method{font-size:.66rem;color:#94a9d1;margin:.35rem .2rem .7rem}
.sales-section-head{display:flex;align-items:flex-end;justify-content:space-between;flex-wrap:wrap;gap:.22rem 1rem;margin:1rem .15rem .5rem;border-left:3px solid var(--cyan);padding-left:.62rem;overflow:visible}
.sales-section-head span{font-size:1.02rem;font-weight:870;color:#f1f5ff;white-space:normal;overflow:visible;text-overflow:clip}.sales-section-head small{font-size:.68rem;color:#a0b4d8;white-space:normal}
.st-key-sales-timeline [data-testid="stVerticalBlockBorderWrapper"],.st-key-sales-rankings [data-testid="stVerticalBlockBorderWrapper"]{background:linear-gradient(145deg,rgba(7,23,53,.96),rgba(4,13,32,.97));border-color:rgba(56,126,236,.4)!important}
.comparison-card{min-height:158px;padding:.82rem .88rem;border-radius:13px;border:1px solid rgba(63,132,238,.34);background:linear-gradient(145deg,rgba(8,25,56,.96),rgba(5,15,37,.98));box-shadow:inset 0 1px rgba(255,255,255,.04)}
.comparison-label{font-size:.7rem;color:#a9bde2;font-weight:780}.comparison-current{font-size:1.25rem;font-weight:900;margin:.45rem 0;color:#f4f8ff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.comparison-row{display:flex;justify-content:space-between;gap:.5rem;font-size:.62rem;color:#8499c3;padding:.16rem 0}.comparison-row strong{color:#c9d7f1;font-weight:750;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.comparison-rate{display:inline-block;font-size:.61rem;color:var(--cyan);padding:.2rem .38rem;border-radius:999px;background:rgba(22,217,255,.08);margin-top:.42rem}
.sales-comparison-note{margin:.2rem 0 .65rem;padding:.58rem .72rem;border-left:3px solid #FBBF24;border-radius:0 9px 9px 0;background:rgba(120,83,8,.16);color:#F8E5A9;font-size:.69rem;line-height:1.45}
.sales-insight{min-height:132px;padding:.82rem .88rem;border-radius:13px;border:1px solid rgba(63,130,232,.32);background:linear-gradient(145deg,rgba(8,25,55,.96),rgba(5,15,37,.98))}
.sales-insight-badge{font-size:.55rem;letter-spacing:.13em;color:var(--cyan);font-weight:900}.sales-insight-title{font-size:.79rem;font-weight:850;margin:.38rem 0;color:#f0f5ff}.sales-insight-copy{font-size:.67rem;line-height:1.45;color:#a8b8d7}
.sales-ranking-basis{margin:.05rem 0 .3rem;color:#A9BCE0;font-size:.66rem;font-weight:700}
.sales-ranking-wrap{width:100%;overflow-x:auto;border:1px solid rgba(63,121,211,.25);border-radius:10px;background:rgba(3,11,29,.72);margin:.15rem 0 .55rem}
.sales-ranking-table{width:100%;min-width:390px;border-collapse:collapse;table-layout:fixed;font-size:.7rem}.sales-ranking-table th{padding:.5rem .44rem;text-align:left;color:#AFC3E8;background:rgba(19,38,78,.82);font-weight:750;white-space:normal;line-height:1.2}.sales-ranking-table td{padding:.46rem .44rem;border-top:1px solid rgba(75,110,174,.2);color:#E8EFFC;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.sales-ranking-table th:first-child,.sales-ranking-table td:first-child{width:7%;text-align:center}.sales-ranking-table th:nth-child(2),.sales-ranking-table td:nth-child(2){width:37%}.sales-ranking-table th:nth-child(3),.sales-ranking-table td:nth-child(3){width:28%;text-align:right}.sales-ranking-table th:last-child,.sales-ranking-table td:last-child{width:28%;text-align:right}
.product-hero{display:flex;align-items:flex-end;justify-content:space-between;gap:1rem;padding:.28rem .08rem .58rem}.product-eyebrow{font-size:.57rem;letter-spacing:.18em;color:var(--cyan);font-weight:900}.product-title{font-size:clamp(1.75rem,2.7vw,2.45rem);line-height:1.05;font-weight:950;letter-spacing:-.045em;color:#F7FAFF;margin:.38rem 0}.product-subtitle{font-size:.78rem;color:#A8B9D8}.product-meta{display:flex;justify-content:flex-end;flex-wrap:wrap;gap:.36rem;max-width:58%}.product-meta span{font-size:.62rem;color:#B6C7E7;padding:.33rem .48rem;border:1px solid rgba(68,129,230,.32);border-radius:8px;background:rgba(6,22,52,.82)}.product-meta .product-warning{color:#FFE8A5;border-color:rgba(233,186,50,.4);background:rgba(118,83,8,.17)}
.product-kpi{min-height:118px;padding:.82rem .86rem;border-radius:14px;border:1px solid rgba(55,132,244,.42);background:linear-gradient(145deg,rgba(8,28,62,.98),rgba(4,15,37,.98));box-shadow:inset 0 1px rgba(255,255,255,.06),0 12px 26px rgba(0,0,0,.22),0 0 22px rgba(34,115,255,.08)}.product-kpi-head{display:grid;grid-template-columns:auto 1fr auto;gap:.42rem;align-items:center;color:#EAF1FF;font-size:.69rem}.product-kpi-head>span{display:grid;place-items:center;width:25px;height:25px;border-radius:7px;background:linear-gradient(145deg,rgba(22,193,255,.35),rgba(116,45,255,.4));border:1px solid rgba(74,155,255,.5)}.product-kpi-head strong{line-height:1.2}.product-kpi-head em{font-style:normal;white-space:nowrap}.product-kpi-value{font-size:clamp(1.22rem,1.7vw,1.75rem);font-weight:930;letter-spacing:-.04em;margin-top:.68rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.product-kpi-foot{font-size:.58rem;color:#8FA5CE;margin-top:.4rem}
.product-section{display:flex;align-items:flex-end;justify-content:space-between;flex-wrap:wrap;gap:.25rem 1rem;margin:1rem .12rem .5rem;padding-left:.62rem;border-left:3px solid var(--cyan)}.product-section span{font-size:1.02rem;font-weight:880;color:#F2F6FF}.product-section small{font-size:.68rem;color:#9DB2D8}.concentration-strip{display:grid;grid-template-columns:repeat(3,1fr);gap:.35rem;margin:.1rem 0 .35rem}.concentration-strip span{padding:.48rem;border-radius:8px;background:rgba(17,39,80,.65);border:1px solid rgba(67,129,226,.25);font-size:.64rem;color:#AFC0DD;text-align:center}.concentration-strip strong{display:block;color:#F2F7FF;font-size:.83rem;margin-top:.16rem}.product-insight{min-height:126px;padding:.8rem .84rem;border-radius:13px;border:1px solid rgba(62,130,235,.33);background:linear-gradient(145deg,rgba(8,25,56,.97),rgba(5,15,37,.98))}.product-insight em{display:block;font-size:.54rem;letter-spacing:.12em;color:var(--cyan);font-style:normal;font-weight:900}.product-insight strong{display:block;font-size:.78rem;color:#F0F5FF;margin:.38rem 0}.product-insight p{font-size:.65rem;line-height:1.45;color:#A9BAD8;margin:0}
.store-hero{display:flex;align-items:flex-end;justify-content:space-between;gap:1rem;padding:.28rem .08rem .58rem}.store-eyebrow{font-size:.57rem;letter-spacing:.18em;color:var(--cyan);font-weight:900}.store-title{font-size:clamp(1.75rem,2.7vw,2.45rem);line-height:1.05;font-weight:950;letter-spacing:-.045em;color:#F7FAFF;margin:.38rem 0}.store-subtitle{font-size:.78rem;color:#A8B9D8}.store-meta{display:flex;justify-content:flex-end;flex-wrap:wrap;gap:.36rem;max-width:58%}.store-meta span{font-size:.62rem;color:#B6C7E7;padding:.33rem .48rem;border:1px solid rgba(68,129,230,.32);border-radius:8px;background:rgba(6,22,52,.82)}.store-meta .store-warning{color:#FFE8A5;border-color:rgba(233,186,50,.4);background:rgba(118,83,8,.17)}
.store-kpi{min-height:118px;padding:.82rem .86rem;border-radius:14px;border:1px solid rgba(55,132,244,.42);background:linear-gradient(145deg,rgba(8,28,62,.98),rgba(4,15,37,.98));box-shadow:inset 0 1px rgba(255,255,255,.06),0 12px 26px rgba(0,0,0,.22),0 0 22px rgba(34,115,255,.08)}.store-kpi-head{display:grid;grid-template-columns:auto 1fr auto;gap:.42rem;align-items:center;color:#EAF1FF;font-size:.69rem}.store-kpi-head>span{display:grid;place-items:center;width:25px;height:25px;border-radius:7px;background:linear-gradient(145deg,rgba(22,193,255,.35),rgba(116,45,255,.4));border:1px solid rgba(74,155,255,.5)}.store-kpi-head strong{line-height:1.2}.store-kpi-head em{font-style:normal;white-space:nowrap}.store-kpi-value{font-size:clamp(1.22rem,1.7vw,1.75rem);font-weight:930;letter-spacing:-.04em;margin-top:.68rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.store-kpi-foot{font-size:.58rem;color:#8FA5CE;margin-top:.4rem}
.store-section{display:flex;align-items:flex-end;justify-content:space-between;flex-wrap:wrap;gap:.25rem 1rem;margin:1rem .12rem .5rem;padding-left:.62rem;border-left:3px solid var(--cyan)}.store-section span{font-size:1.02rem;font-weight:880;color:#F2F6FF}.store-section small{font-size:.68rem;color:#9DB2D8}.store-concentration,.store-profile-strip{display:grid;grid-template-columns:repeat(3,1fr);gap:.35rem;margin:.1rem 0 .35rem}.store-profile-strip{grid-template-columns:repeat(4,1fr)}.store-concentration span,.store-profile-strip span{padding:.5rem;border-radius:8px;background:rgba(17,39,80,.65);border:1px solid rgba(67,129,226,.25);font-size:.64rem;color:#AFC0DD;text-align:center}.store-concentration strong,.store-profile-strip strong{display:block;color:#F2F7FF;font-size:.84rem;margin-top:.16rem}.store-comparison-note{margin:.15rem 0 .65rem;padding:.56rem .7rem;border-left:3px solid #FBBF24;border-radius:0 9px 9px 0;background:rgba(120,83,8,.16);color:#F8E5A9;font-size:.68rem}.store-insight{min-height:126px;padding:.8rem .84rem;border-radius:13px;border:1px solid rgba(62,130,235,.33);background:linear-gradient(145deg,rgba(8,25,56,.97),rgba(5,15,37,.98))}.store-insight em{display:block;font-size:.54rem;letter-spacing:.12em;color:var(--cyan);font-style:normal;font-weight:900}.store-insight strong{display:block;font-size:.78rem;color:#F0F5FF;margin:.38rem 0}.store-insight p{font-size:.65rem;line-height:1.45;color:#A9BAD8;margin:0}
.st-key-report-native-title{display:none!important}.report-hero{display:flex;align-items:flex-end;justify-content:space-between;gap:1rem;padding:.28rem .08rem .58rem}.report-eyebrow{font-size:.57rem;letter-spacing:.18em;color:var(--cyan);font-weight:900}.report-title{font-size:clamp(1.75rem,2.7vw,2.45rem);line-height:1.05;font-weight:950;letter-spacing:-.045em;color:#F7FAFF;margin:.38rem 0}.report-subtitle{font-size:.78rem;color:#A8B9D8;max-width:720px}.report-meta{display:flex;justify-content:flex-end;flex-wrap:wrap;gap:.36rem;max-width:58%}.report-meta span{font-size:.62rem;color:#B6C7E7;padding:.33rem .48rem;border:1px solid rgba(68,129,230,.32);border-radius:8px;background:rgba(6,22,52,.82)}.report-meta .report-warning{color:#FFE8A5;border-color:rgba(233,186,50,.4);background:rgba(118,83,8,.17)}.report-section{display:flex;align-items:flex-end;justify-content:space-between;flex-wrap:wrap;gap:.25rem 1rem;margin:1rem .12rem .5rem;padding-left:.62rem;border-left:3px solid var(--cyan)}.report-section span{font-size:1.02rem;font-weight:880;color:#F2F6FF}.report-section small{font-size:.68rem;color:#9DB2D8}.report-model{min-height:148px;padding:.76rem;border-radius:13px;border:1px solid rgba(59,130,246,.34);background:linear-gradient(145deg,rgba(8,27,60,.98),rgba(7,14,36,.98));box-shadow:inset 0 1px rgba(255,255,255,.05),0 12px 25px rgba(0,0,0,.2)}.report-model b{display:grid;place-items:center;width:29px;height:29px;border-radius:8px;background:linear-gradient(145deg,#147BEF,#7C2DFF);color:#fff}.report-model strong{display:block;color:#F3F7FF;font-size:.75rem;margin:.62rem 0 .35rem;line-height:1.25}.report-model p{margin:0;color:#96A9CC;font-size:.61rem;line-height:1.45}.report-preview-head{display:flex;align-items:flex-end;justify-content:space-between;gap:1rem;padding:.75rem .85rem;border:1px solid rgba(56,142,246,.32);border-radius:13px;background:linear-gradient(105deg,rgba(8,31,68,.95),rgba(38,13,91,.55))}.report-preview-head em{font-size:.52rem;letter-spacing:.14em;color:var(--cyan);font-style:normal;font-weight:900}.report-preview-head strong{display:block;font-size:1rem;color:#F5F8FF;margin:.26rem 0}.report-preview-head p{margin:0;color:#AFC0DD;font-size:.64rem}.report-preview-head>span{padding:.42rem .58rem;border-radius:8px;border:1px solid rgba(57,150,246,.35);color:#DDECFF;font-size:.65rem}.report-kpi{min-height:92px;padding:.72rem .78rem;border-radius:12px;border:1px solid rgba(55,132,244,.36);background:rgba(5,22,51,.92)}.report-kpi span{display:block;color:#9FB2D4;font-size:.62rem}.report-kpi strong{display:block;color:#F6F9FF;font-size:1.16rem;margin-top:.48rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.st-key-quality-native-title{display:none!important}.quality-hero{display:flex;align-items:flex-end;justify-content:space-between;gap:1rem;padding:.28rem .08rem .52rem}.quality-eyebrow{font-size:.57rem;letter-spacing:.18em;color:var(--cyan);font-weight:900}.quality-title{font-size:clamp(1.75rem,2.7vw,2.45rem);line-height:1.05;font-weight:950;letter-spacing:-.045em;color:#F7FAFF;margin:.38rem 0}.quality-subtitle{font-size:.78rem;color:#A8B9D8}.quality-meta{display:flex;justify-content:flex-end;flex-wrap:wrap;gap:.36rem;max-width:60%}.quality-meta span{font-size:.62rem;color:#B6C7E7;padding:.33rem .48rem;border:1px solid rgba(68,129,230,.32);border-radius:8px;background:rgba(6,22,52,.82)}.quality-meta .quality-status{color:#9DFFCB;border-color:rgba(34,211,154,.38);background:rgba(10,94,70,.18)}.quality-scope{margin:0 0 .62rem;padding:.52rem .68rem;border-left:3px solid var(--cyan);border-radius:0 8px 8px 0;background:rgba(8,31,67,.52);color:#AFC0DD;font-size:.68rem}.quality-scope strong{color:#EAF2FF}
.quality-kpi{min-height:120px;padding:.84rem .88rem;border-radius:14px;border:1px solid rgba(55,132,244,.42);background:linear-gradient(145deg,rgba(8,28,62,.98),rgba(4,15,37,.98));box-shadow:inset 0 1px rgba(255,255,255,.06),0 12px 26px rgba(0,0,0,.22),0 0 24px rgba(31,213,255,.07)}.quality-kpi-head{display:grid;grid-template-columns:auto 1fr;gap:.44rem;align-items:center;color:#EAF1FF;font-size:.69rem}.quality-kpi-head>span{display:grid;place-items:center;width:25px;height:25px;border-radius:7px;background:linear-gradient(145deg,rgba(22,193,255,.35),rgba(116,45,255,.4));border:1px solid rgba(74,155,255,.5)}.quality-kpi-value{font-size:clamp(1.22rem,1.7vw,1.75rem);font-weight:930;letter-spacing:-.04em;margin-top:.68rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.quality-kpi-foot{font-size:.58rem;color:#8FA5CE;margin-top:.4rem}.quality-section{display:flex;align-items:flex-end;justify-content:space-between;flex-wrap:wrap;gap:.25rem 1rem;margin:1rem .12rem .5rem;padding-left:.62rem;border-left:3px solid var(--cyan)}.quality-section span{font-size:1.02rem;font-weight:880;color:#F2F6FF}.quality-section small{font-size:.68rem;color:#9DB2D8}.quality-insight{min-height:132px;padding:.8rem .84rem;border-radius:13px;border:1px solid rgba(62,130,235,.33);background:linear-gradient(145deg,rgba(8,25,56,.97),rgba(5,15,37,.98))}.quality-insight em{display:block;font-size:.54rem;letter-spacing:.12em;color:var(--cyan);font-style:normal;font-weight:900}.quality-insight strong{display:block;font-size:.78rem;color:#F0F5FF;margin:.38rem 0}.quality-insight p{font-size:.65rem;line-height:1.45;color:#A9BAD8;margin:0}
@media(min-width:1101px){[data-testid="stSidebar"] [role="radiogroup"]{gap:.08rem}.fusion-hero{min-height:52px}}
@media(max-width:1100px){.fusion-kpi-value{font-size:1.2rem}}
@media(max-width:900px){
  .st-key-topbar-controls [data-testid="stColumn"],.st-key-overview-kpis [data-testid="stColumn"]{min-width:calc(50% - .5rem)!important;flex:1 1 calc(50% - .5rem)!important}
  .st-key-sales-kpis [data-testid="stColumn"],.st-key-sales-comparison [data-testid="stColumn"],.st-key-sales-insights [data-testid="stColumn"]{min-width:calc(50% - .5rem)!important;flex:1 1 calc(50% - .5rem)!important}
  .st-key-product-kpis [data-testid="stColumn"],.st-key-product-insights [data-testid="stColumn"]{min-width:calc(50% - .5rem)!important;flex:1 1 calc(50% - .5rem)!important}
  .st-key-store-kpis [data-testid="stColumn"],.st-key-store-insights [data-testid="stColumn"]{min-width:calc(50% - .5rem)!important;flex:1 1 calc(50% - .5rem)!important}
  .st-key-quality-kpis [data-testid="stColumn"],.st-key-quality-insights [data-testid="stColumn"]{min-width:calc(50% - .5rem)!important;flex:1 1 calc(50% - .5rem)!important}
  .st-key-report-catalog [data-testid="stColumn"],.st-key-report-preview-kpis [data-testid="stColumn"]{min-width:calc(50% - .5rem)!important;flex:1 1 calc(50% - .5rem)!important}
  .st-key-overview-chart-grid>[data-testid="stLayoutWrapper"]>[data-testid="stHorizontalBlock"]>[data-testid="stColumn"],
  .st-key-overview-lower-grid>[data-testid="stLayoutWrapper"]>[data-testid="stHorizontalBlock"]>[data-testid="stColumn"],
  .st-key-sales-rankings>[data-testid="stLayoutWrapper"]>[data-testid="stHorizontalBlock"]>[data-testid="stColumn"]{min-width:100%!important;flex:1 1 100%!important}
}
@media(max-width:800px){.block-container{padding:.75rem!important}.fusion-hero{align-items:flex-start;flex-direction:column}
  .fusion-hero-meta{align-items:flex-start}.fusion-kpi{min-height:105px}.fusion-insight{height:auto;min-height:120px}
  .sales-hero,.product-hero,.store-hero,.quality-hero,.report-hero{align-items:flex-start;flex-direction:column}.sales-meta,.product-meta,.store-meta,.quality-meta,.report-meta{justify-content:flex-start;max-width:none}}
@media(max-width:640px){.st-key-overview-kpis [data-testid="stColumn"]{min-width:100%!important;flex:1 1 100%!important}
  .st-key-sales-kpis [data-testid="stColumn"],.st-key-sales-comparison [data-testid="stColumn"],.st-key-sales-insights [data-testid="stColumn"]{min-width:100%!important;flex:1 1 100%!important}
  .st-key-product-kpis [data-testid="stColumn"],.st-key-product-insights [data-testid="stColumn"]{min-width:100%!important;flex:1 1 100%!important}
  .st-key-store-kpis [data-testid="stColumn"],.st-key-store-insights [data-testid="stColumn"]{min-width:100%!important;flex:1 1 100%!important}
  .st-key-quality-kpis [data-testid="stColumn"],.st-key-quality-insights [data-testid="stColumn"]{min-width:100%!important;flex:1 1 100%!important}
  .st-key-report-catalog [data-testid="stColumn"],.st-key-report-preview-kpis [data-testid="stColumn"]{min-width:100%!important;flex:1 1 100%!important}
  .st-key-topbar-controls [data-testid="stColumn"]{min-width:100%!important;flex:1 1 100%!important}
  .st-key-topbar-controls [data-testid="stHorizontalBlock"]{gap:.45rem!important}
  .fusion-greeting{font-size:1.55rem}.fusion-kpi-value{font-size:1.45rem}.sales-title,.product-title,.store-title,.quality-title,.report-title{font-size:1.7rem}.sales-kpi-value,.product-kpi-value,.store-kpi-value,.quality-kpi-value{font-size:1.42rem}
  .sales-section-head{align-items:flex-start;flex-direction:column;gap:.15rem}
  .product-section{align-items:flex-start;flex-direction:column;gap:.15rem}.concentration-strip{grid-template-columns:1fr}
  .store-section{align-items:flex-start;flex-direction:column;gap:.15rem}.store-concentration,.store-profile-strip{grid-template-columns:1fr 1fr}
  .sales-ranking-table{min-width:0;font-size:.66rem}.sales-ranking-table th,.sales-ranking-table td{padding:.42rem .3rem}.sales-ranking-table th:nth-child(2),.sales-ranking-table td:nth-child(2){width:34%}.sales-ranking-table th:nth-child(3),.sales-ranking-table td:nth-child(3){width:27%}.sales-ranking-table th:last-child,.sales-ranking-table td:last-child{width:32%}
  .fusion-hero-meta{width:100%}.source-chip,.fusion-anomaly{white-space:normal;max-width:100%}
  [data-testid="stCaptionContainer"] p{white-space:normal!important;overflow-wrap:anywhere!important;line-height:1.35!important}}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
.st-key-settings-status [data-testid="stColumn"]{min-width:0}.settings-hero{display:flex;align-items:flex-end;justify-content:space-between;gap:1rem;padding:.28rem .08rem .7rem}.settings-eyebrow{font-size:.57rem;letter-spacing:.18em;color:var(--cyan);font-weight:900}.settings-title{font-size:clamp(1.75rem,2.7vw,2.45rem);line-height:1.05;font-weight:950;letter-spacing:-.045em;color:#F7FAFF;margin:.38rem 0}.settings-subtitle{font-size:.78rem;color:#A8B9D8;max-width:720px}.settings-meta{display:flex;justify-content:flex-end;flex-wrap:wrap;gap:.36rem;max-width:58%}.settings-meta span{font-size:.62rem;color:#B6C7E7;padding:.33rem .48rem;border:1px solid rgba(68,129,230,.32);border-radius:8px;background:rgba(6,22,52,.82)}.settings-meta .settings-safe{color:#9DFFCB;border-color:rgba(34,211,154,.38);background:rgba(10,94,70,.18)}.settings-status-card{min-height:104px;padding:.72rem .78rem;border-radius:13px;border:1px solid rgba(55,132,244,.36);background:linear-gradient(145deg,rgba(8,28,62,.98),rgba(4,15,37,.98));box-shadow:inset 0 1px rgba(255,255,255,.05),0 10px 24px rgba(0,0,0,.2)}.settings-status-card span,.settings-info-card span,.settings-preview span{display:block;color:#90A8D0;font-size:.6rem}.settings-status-card strong{display:block;color:#F5F8FF;font-size:1.05rem;margin:.34rem 0}.settings-status-card small,.settings-preview small{display:block;color:#849AC2;font-size:.56rem;line-height:1.35}.settings-section{display:flex;align-items:flex-end;justify-content:space-between;flex-wrap:wrap;gap:.25rem 1rem;margin:.75rem .12rem .65rem;padding-left:.62rem;border-left:3px solid var(--cyan)}.settings-section span{font-size:1.02rem;font-weight:880;color:#F2F6FF}.settings-section small{font-size:.68rem;color:#9DB2D8}.settings-preview{padding:.9rem 1rem;border-radius:13px;border:1px solid rgba(70,139,242,.36);background:linear-gradient(105deg,rgba(8,31,68,.9),rgba(44,14,98,.45))}.settings-preview strong{display:block;color:#F5F9FF;font-size:1.15rem;margin:.38rem 0;overflow-wrap:anywhere}.settings-info-card{min-height:82px;padding:.7rem .78rem;margin-bottom:.5rem;border-radius:12px;border:1px solid rgba(55,132,244,.32);background:rgba(5,22,51,.9)}.settings-info-card strong{display:block;color:#F4F8FF;font-size:.72rem;line-height:1.35;margin-top:.45rem}.st-key-settings-status{margin-bottom:.65rem}.stTabs [data-baseweb="tab-list"]{gap:.2rem;overflow-x:auto}.stTabs [data-baseweb="tab"]{border-radius:9px;padding:.42rem .72rem;background:rgba(8,28,61,.65)}.stTabs [aria-selected="true"]{background:linear-gradient(90deg,rgba(108,39,255,.52),rgba(22,104,255,.3))!important;box-shadow:inset 0 -2px var(--cyan)}
@media(max-width:900px){.st-key-settings-status [data-testid="stColumn"]{min-width:calc(50% - .5rem)!important;flex:1 1 calc(50% - .5rem)!important}.settings-hero{align-items:flex-start;flex-direction:column}.settings-meta{justify-content:flex-start;max-width:none}}
@media(max-width:640px){.st-key-settings-status [data-testid="stColumn"]{min-width:100%!important;flex:1 1 100%!important}.settings-title{font-size:1.7rem}.settings-status-card{min-height:88px}.settings-section{align-items:flex-start;flex-direction:column}.settings-meta{width:100%}.settings-meta span{max-width:100%;overflow-wrap:anywhere}}
/* Fase 5.10 — navegação futurista, baseada apenas em componentes interativos nativos. */
[data-testid="stSidebar"]{border-right:1px solid #167cff!important;border-radius:0 24px 24px 0;box-shadow:0 0 28px rgba(15,107,255,.2),inset -1px 0 rgba(130,48,255,.5);overflow:hidden}
[data-testid="stSidebar"] .block-container{padding:.55rem .8rem 1rem!important;overflow-y:auto!important;scrollbar-width:thin;scrollbar-color:#315aa1 transparent}
[data-testid="stSidebar"] [role="radiogroup"]{position:absolute!important;width:1px!important;height:1px!important;clip:rect(0 0 0 0)!important;overflow:hidden!important}
.sidebar-space-brand{position:relative;height:188px;margin:-.55rem -.8rem .55rem;overflow:hidden;border-radius:0 23px 0 0;background:radial-gradient(circle at 26% 35%,rgba(10,218,255,.22),transparent 21%),radial-gradient(circle at 66% 36%,rgba(127,35,255,.2),transparent 28%),linear-gradient(155deg,#031633,#02091c 68%)}
.sidebar-stars{position:absolute;inset:0;opacity:.7;background-image:radial-gradient(circle at 12% 18%,#fff 0 1px,transparent 1.5px),radial-gradient(circle at 76% 12%,#35cfff 0 1px,transparent 1.5px),radial-gradient(circle at 45% 26%,#966cff 0 1px,transparent 1.4px),radial-gradient(circle at 87% 48%,#fff 0 1px,transparent 1.5px),radial-gradient(circle at 17% 67%,#369cff 0 1px,transparent 1.5px);background-size:73px 61px,91px 79px,113px 97px,137px 111px,157px 127px}
.sidebar-planet{position:absolute;width:360px;height:150px;left:-25px;bottom:-108px;border-radius:50%;border-top:3px solid #20CFFF;background:radial-gradient(ellipse at 50% 0,rgba(27,126,255,.38),rgba(13,47,127,.2) 28%,#020819 64%);box-shadow:0 -11px 35px rgba(32,165,255,.45),0 -2px 6px #36DAFF}
.sidebar-brand-row{position:relative;z-index:2;display:flex;align-items:center;gap:1rem;padding:2.8rem 1.05rem 0}.sidebar-df{width:76px;height:76px;display:grid;place-items:center;flex:0 0 auto;color:white;font-size:1.75rem;font-weight:950;clip-path:polygon(25% 3%,75% 3%,100% 50%,75% 97%,25% 97%,0 50%);background:linear-gradient(145deg,#0CD9FF,#194CFF 48%,#8B28FF);filter:drop-shadow(0 0 13px #146fff);border:1px solid #56dcff}.sidebar-brand-copy strong{display:block;font-size:1.22rem;line-height:1.15;color:#F7F9FF;letter-spacing:-.03em}.sidebar-brand-copy span{display:block;margin-top:.55rem;color:#21E6FF;font-size:.63rem;font-weight:900;letter-spacing:.23em}
.sidebar-search-wrap{font-size:0}.st-key-sidebar_menu_search{margin:.25rem 0 .8rem}.st-key-sidebar_menu_search [data-baseweb="input"]{background:rgba(8,20,52,.88)!important;border:1px solid rgba(86,73,239,.68)!important;border-radius:13px!important;min-height:48px;box-shadow:inset 0 0 18px rgba(33,83,190,.12)}.st-key-sidebar_menu_search input{font-size:.76rem!important;color:#DFE9FF!important}.st-key-sidebar_menu_search:focus-within [data-baseweb="input"]{border-color:#29D8FF!important;box-shadow:0 0 0 2px rgba(27,207,255,.15),0 0 18px rgba(98,43,255,.2)}
.sidebar-group{display:flex;align-items:center;gap:.55rem;margin:.9rem .7rem .45rem}.sidebar-group span{font-size:.58rem;font-weight:900;letter-spacing:.23em;color:#1EDCFF;white-space:nowrap}.sidebar-group.violet span{color:#B96CFF}.sidebar-group.ice span{color:#A8C5FF}.sidebar-group i{position:relative;height:1px;flex:1;background:linear-gradient(90deg,currentColor,transparent);color:#20D5FF}.sidebar-group i:before{content:"";position:absolute;left:0;top:-2px;width:5px;height:5px;border-radius:50%;background:currentColor;box-shadow:0 0 9px currentColor}
[data-testid="stSidebar"] [class*="st-key-nav_"]{margin:.12rem 0}[data-testid="stSidebar"] [class*="st-key-nav_"] button{position:relative;min-height:67px!important;padding:.58rem 2rem .58rem .72rem!important;justify-content:flex-start!important;text-align:left!important;border-radius:14px!important;border:1px solid rgba(36,89,171,.17)!important;background:rgba(2,12,34,.48)!important;color:#EAF1FF!important;transition:transform .16s ease,border-color .16s ease,box-shadow .16s ease!important;overflow:hidden}[data-testid="stSidebar"] [class*="st-key-nav_"] button:hover{transform:translateX(2px);border-color:rgba(63,197,255,.55)!important;background:linear-gradient(90deg,rgba(12,49,105,.76),rgba(31,19,93,.62))!important;box-shadow:0 0 18px rgba(35,116,255,.15)}
[data-testid="stSidebar"] [class*="st-key-nav_"] button:focus-visible{outline:2px solid #67E8FF!important;outline-offset:2px!important}[data-testid="stSidebar"] [class*="st-key-nav_"] button:after{content:"›";position:absolute;right:.72rem;top:50%;transform:translateY(-50%);font-size:1.6rem;color:#9DB6FF;text-shadow:0 0 10px rgba(111,109,255,.6)}[data-testid="stSidebar"] [class*="st-key-nav_"] button p{font-size:.75rem!important;line-height:1.45!important;white-space:pre-line!important;font-weight:850!important}[data-testid="stSidebar"] [class*="st-key-nav_"] button p::first-line{font-size:.83rem;color:#F5F8FF}[data-testid="stSidebar"] [class*="st-key-nav_"] [data-testid="stIconMaterial"]{display:grid;place-items:center;width:41px;height:41px;margin-right:.65rem;border-radius:11px;font-size:1.45rem!important;color:#58E5FF!important;background:linear-gradient(145deg,rgba(13,87,179,.75),rgba(57,19,130,.72));border:1px solid rgba(73,134,244,.45);box-shadow:inset 0 1px rgba(255,255,255,.08)}
[data-testid="stSidebar"] [class*="st-key-nav_"] button[kind="primary"]{border-color:#8254FF!important;background:linear-gradient(100deg,rgba(13,104,224,.82),rgba(88,27,224,.76))!important;box-shadow:0 0 24px rgba(63,51,255,.35),inset 0 1px rgba(255,255,255,.12)}[data-testid="stSidebar"] [class*="st-key-nav_"] button[kind="primary"]:before{content:"";position:absolute;left:0;top:8px;bottom:8px;width:4px;border-radius:0 4px 4px 0;background:#72F4FF;box-shadow:0 0 10px #43DEFF}
.sidebar-empty{padding:.85rem;border:1px solid rgba(86,122,205,.35);border-radius:12px;background:rgba(8,24,55,.7)}.sidebar-empty strong,.sidebar-empty span{display:block}.sidebar-empty strong{font-size:.72rem}.sidebar-empty span{font-size:.61rem;color:#91A7CC;margin-top:.35rem;line-height:1.4}.sidebar-status-rule{height:1px;margin:1rem .15rem .7rem;background:linear-gradient(90deg,rgba(64,136,242,.45),transparent)}
.sidebar-system-card{display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:.55rem;margin:.75rem 0 0;padding:.72rem;border-radius:14px;border:1px solid rgba(38,152,205,.35);background:linear-gradient(110deg,rgba(1,67,73,.42),rgba(24,20,102,.55));box-shadow:inset 0 1px rgba(255,255,255,.04)}.sidebar-system-card>b{width:11px;height:11px;border-radius:50%;background:#24E99A;box-shadow:0 0 12px #24E99A}.sidebar-status-copy strong,.sidebar-status-copy span,.sidebar-status-copy small{display:block}.sidebar-status-copy strong{color:#40F0B0;font-size:.67rem}.sidebar-status-copy span{color:#C4D1EB;font-size:.58rem;margin-top:.15rem}.sidebar-status-copy small{color:#7F96BC;font-size:.5rem;margin-top:.2rem}.sidebar-system-card em{font-style:normal;font-size:.56rem;color:#B8C8EE;border:1px solid rgba(94,110,234,.5);border-radius:8px;padding:.3rem}
@media(max-width:800px){[data-testid="stSidebar"]{border-radius:0 20px 20px 0!important}.sidebar-space-brand{height:155px}.sidebar-brand-row{padding-top:2.2rem}[data-testid="stSidebar"] [class*="st-key-nav_"] button{min-height:62px!important}}
@media(prefers-reduced-motion:reduce){[data-testid="stSidebar"] *{animation:none!important;transition:none!important}}
/* Reserve space for the native header at every breakpoint; never hide its controls. */
[data-testid="stMainBlockContainer"]{padding-top:4rem!important}
[data-testid="stChatMessage"]{background:rgba(7,20,45,.82);border:1px solid rgba(63,137,255,.28);border-radius:14px;color:var(--text)}
[data-testid="stChatMessage"] p{line-height:1.6;overflow-wrap:anywhere}
</style>
        """,
    )
