"""
STOCK · HAUS — Streamlit Edition
Live Yahoo Finance data via yfinance (server-side, no CORS issues)
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import time
import requests
from datetime import datetime, timedelta
from functools import lru_cache

# ═══════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="STOCK · HAUS",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════
# DESIGN TOKENS  (Warm stone + gold leaf)
# ═══════════════════════════════════════════════════════════════

GOLD       = "#B69D5F"
GOLD_DEEP  = "#9A8243"
GOLD_PALE  = "#EDE4CC"
STONE      = "#F5F1EB"
INK        = "#1E1E1E"
INK_MID    = "#6E6E6E"
INK_LIGHT  = "#9C9C9C"
RISE       = "#4D7C5B"
FALL       = "#944848"
CAUTION    = "#A08030"
DEPTH      = "#5B6B8A"
WHITE      = "#FFFFFF"

# ═══════════════════════════════════════════════════════════════
# GLOBAL CSS  — matches the Maison aesthetic
# ═══════════════════════════════════════════════════════════════

st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300&family=Outfit:wght@300;400;500;600&display=swap');

  /* Root */
  .stApp {{ background: {STONE}; }}
  [data-testid="stSidebar"] {{ background: {WHITE}; border-right: 1px solid #DDD8CE; }}
  [data-testid="stSidebar"] * {{ font-family: 'Outfit', sans-serif; }}

  /* Typography overrides */
  h1, h2, h3 {{ font-family: 'Cormorant Garamond', Georgia, serif !important; color: {INK}; }}
  p, span, div {{ font-family: 'Outfit', sans-serif; }}

  /* Metric cards */
  [data-testid="metric-container"] {{
    background: {WHITE};
    border: 1px solid #DDD8CE;
    border-radius: 12px;
    padding: 16px 20px;
    transition: box-shadow .2s;
  }}
  [data-testid="metric-container"]:hover {{
    box-shadow: 0 4px 24px rgba(182,157,95,0.12);
  }}
  [data-testid="stMetricLabel"] {{
    font-family: 'Outfit', sans-serif !important;
    font-size: 10px !important;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: {INK_LIGHT} !important;
  }}
  [data-testid="stMetricValue"] {{
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 26px !important;
    color: {INK} !important;
    font-weight: 400;
  }}

  /* Tabs */
  .stTabs [data-baseweb="tab-list"] {{
    gap: 0;
    border-bottom: 2px solid {GOLD};
    background: transparent;
  }}
  .stTabs [data-baseweb="tab"] {{
    font-family: 'Outfit', sans-serif;
    font-size: 10px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    font-weight: 600;
    color: {INK_LIGHT};
    padding: 10px 24px;
    background: transparent;
    border: none;
  }}
  .stTabs [aria-selected="true"] {{
    color: {GOLD} !important;
    border-bottom: 2px solid {GOLD};
    background: transparent !important;
  }}

  /* Buttons */
  .stButton > button {{
    font-family: 'Outfit', sans-serif;
    font-weight: 600;
    font-size: 11px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    background: linear-gradient(135deg, {GOLD}, #D4B96A);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
    transition: all .2s;
  }}
  .stButton > button:hover {{
    transform: translateY(-1px);
    box-shadow: 0 4px 20px rgba(182,157,95,0.25);
  }}

  /* Data table */
  [data-testid="stDataFrame"] {{ border-radius: 12px; overflow: hidden; }}

  /* Divider with gold gradient */
  .gold-rule {{
    height: 1px;
    background: linear-gradient(90deg, {GOLD}, {GOLD_PALE}, transparent);
    margin: 12px 0 24px 0;
  }}

  /* Section headers */
  .section-header {{
    font-family: 'Outfit', sans-serif;
    font-size: 10px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    font-weight: 600;
    color: {GOLD};
    margin-bottom: 8px;
  }}

  /* KPI badge */
  .kpi-badge {{
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-family: 'Outfit', sans-serif;
    font-weight: 600;
  }}

  /* Risk gauge */
  .risk-card {{
    background: {WHITE};
    border: 1px solid #DDD8CE;
    border-radius: 14px;
    padding: 20px 28px;
    display: flex;
    align-items: center;
    gap: 16px;
  }}

  /* Company name hero */
  .hero-name {{
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-size: 38px;
    font-weight: 400;
    color: {INK};
    letter-spacing: -0.03em;
    line-height: 1.05;
  }}
  .hero-ticker {{
    font-family: 'Outfit', sans-serif;
    font-size: 14px;
    font-weight: 600;
    color: {GOLD};
    letter-spacing: 0.1em;
    margin-top: 4px;
  }}
  .hero-price {{
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-size: 48px;
    font-weight: 300;
    color: {INK};
    letter-spacing: -0.04em;
    line-height: 1;
  }}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# DATA LAYER  — yfinance with caching & security headers
# ═══════════════════════════════════════════════════════════════

# Randomised user-agent pool → avoids fingerprinting
_UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

def _make_session() -> requests.Session:
    """
    Create a hardened requests.Session that mimics a real browser.
    yfinance accepts a custom session, so all requests inherit these headers.
    This significantly reduces the chance of Yahoo returning 429 / 401.
    """
    import random
    session = requests.Session()
    session.headers.update({
        "User-Agent"      : random.choice(_UA_POOL),
        "Accept"          : "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language" : "en-US,en;q=0.9",
        "Accept-Encoding" : "gzip, deflate, br",
        "DNT"             : "1",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest"  : "document",
        "Sec-Fetch-Mode"  : "navigate",
        "Sec-Fetch-Site"  : "none",
        "Cache-Control"   : "max-age=0",
    })
    # Mount a retry adapter: 3 retries with exponential back-off
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    retry = Retry(
        total=3,
        backoff_factor=1.2,          # 1.2s, 2.4s, 4.8s
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session

@st.cache_resource(ttl=300)          # 5-min server-side cache
def _get_session():
    return _make_session()

@st.cache_data(ttl=300, show_spinner=False)
def fetch_ticker_data(symbol: str) -> dict:
    """
    Fetch all fundamentals + price history in one call.
    Returns a normalised dict; never raises — returns {'error': str} on failure.
    """
    try:
        session = _get_session()
        tk = yf.Ticker(symbol, session=session)

        info = tk.info or {}
        if not info or info.get("trailingPegRatio") is None and "shortName" not in info:
            # Fallback: fast_info is lighter and often succeeds when full info throttles
            fi = tk.fast_info
            info = {
                "shortName"          : getattr(fi, "quote_type", symbol),
                "regularMarketPrice" : getattr(fi, "last_price", None),
                "marketCap"          : getattr(fi, "market_cap", None),
                "currency"           : getattr(fi, "currency", "USD"),
            }

        # Price history
        hist = tk.history(period="5y", auto_adjust=True, timeout=15)
        prices = []
        if hist is not None and not hist.empty:
            hist = hist[["Close"]].dropna()
            hist.index = pd.to_datetime(hist.index).tz_localize(None)
            prices = [
                {"date": idx.strftime("%Y-%m-%d"), "price": round(float(row["Close"]), 2)}
                for idx, row in hist.iterrows()
            ]

        # Risk metrics from price history
        risk = _compute_risk(hist["Close"].values if prices else np.array([]))

        return {
            "symbol"  : symbol,
            "name"    : info.get("longName") or info.get("shortName") or symbol,
            "sector"  : info.get("sector", "—"),
            "industry": info.get("industry", "—"),
            "country" : info.get("country", "—"),
            "exchange": info.get("exchange", "—"),
            "currency": info.get("currency", "USD"),
            "employees": info.get("fullTimeEmployees"),
            "bio"     : info.get("longBusinessSummary", ""),
            "website" : info.get("website", ""),
            # Price
            "price"   : info.get("regularMarketPrice") or info.get("previousClose"),
            "mkt_cap" : info.get("marketCap"),
            "shares"  : info.get("sharesOutstanding"),
            # Valuation
            "pe"      : info.get("trailingPE"),
            "ps"      : info.get("priceToSalesTrailing12Months"),
            "pb"      : info.get("priceToBook"),
            "ev"      : info.get("enterpriseValue"),
            "ev_rev"  : info.get("enterpriseToRevenue"),
            "ev_ebitda": info.get("enterpriseToEbitda"),
            # Profitability
            "profit_margin": info.get("profitMargins"),
            "roa"     : info.get("returnOnAssets"),
            "roe"     : info.get("returnOnEquity"),
            "revenue" : info.get("totalRevenue"),
            "net_income": info.get("netIncomeToCommon"),
            "ebitda"  : info.get("ebitda"),
            # Dividends
            "div_yield": info.get("dividendYield", 0) or 0,
            "payout"  : info.get("payoutRatio", 0) or 0,
            # Risk / balance sheet
            "beta"    : info.get("beta"),
            "debt_eq" : info.get("debtToEquity"),  # Yahoo gives ×100 here
            "current_ratio": info.get("currentRatio"),
            "quick_ratio"  : info.get("quickRatio"),
            "zscore"  : _altman_z(info),
            # Computed risk
            **risk,
            # Raw history list
            "prices"  : prices,
        }
    except Exception as e:
        return {"symbol": symbol, "error": str(e), "prices": []}

def _compute_risk(closes: np.ndarray) -> dict:
    if len(closes) < 30:
        return {"vol": None, "mdd": None, "sharpe": None}
    log_ret = np.diff(np.log(closes[closes > 0]))
    if len(log_ret) < 20:
        return {"vol": None, "mdd": None, "sharpe": None}
    daily_vol  = np.std(log_ret)
    ann_vol    = daily_vol * np.sqrt(252)
    ann_return = np.mean(log_ret) * 252
    sharpe     = (ann_return - 0.04) / ann_vol if ann_vol > 0 else None
    # Max drawdown
    peak = np.maximum.accumulate(closes)
    mdd  = float(np.min((closes - peak) / peak))
    return {"vol": float(ann_vol), "mdd": mdd, "sharpe": float(sharpe) if sharpe else None}

def _altman_z(info: dict):
    """Simplified Altman Z-Score from yfinance info fields."""
    try:
        ta   = info.get("totalAssets")
        re   = info.get("retainedEarningsquity") or info.get("retainedEarnings")
        ebit = (info.get("ebitda") or 0) * 0.85
        mc   = info.get("marketCap")
        rev  = info.get("totalRevenue")
        ca   = info.get("totalCurrentAssets")
        cl   = info.get("totalCurrentLiabilities")
        tl   = info.get("totalDebt") or 0
        if not ta or ta <= 0 or not mc or not rev:
            return None
        wc = (ca or 0) - (cl or 0)
        A  = wc / ta
        B  = (re or 0) / ta
        C  = ebit / ta
        D  = mc / max(tl, 1)
        E  = rev / ta
        z  = 1.2*A + 1.4*B + 3.3*C + 0.6*D + 1.0*E
        return round(z, 2) if 0 < z < 50 else None
    except Exception:
        return None

@st.cache_data(ttl=300, show_spinner=False)
def search_tickers(query: str) -> list[dict]:
    """Live ticker search via Yahoo Finance query endpoint."""
    if len(query) < 1:
        return []
    try:
        session = _get_session()
        url = (
            f"https://query2.finance.yahoo.com/v1/finance/search"
            f"?q={query}&quotesCount=8&newsCount=0&listsCount=0"
        )
        r = session.get(url, timeout=8)
        r.raise_for_status()
        return [
            {
                "sym": q["symbol"],
                "name": q.get("shortname") or q.get("longname") or q["symbol"],
                "exchange": q.get("exchDisp", ""),
            }
            for q in r.json().get("quotes", [])
            if q.get("symbol") and q.get("shortname")
        ][:8]
    except Exception:
        return []

# ═══════════════════════════════════════════════════════════════
# FORMATTING HELPERS
# ═══════════════════════════════════════════════════════════════

def fmt_num(v, digits=2):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    return f"{v:,.{digits}f}"

def fmt_pct(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    return f"{v*100:.2f}%"

def fmt_big(v, cur="$"):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    a = abs(v)
    if a >= 1e12: return f"{cur}{v/1e12:.2f}T"
    if a >= 1e9:  return f"{cur}{v/1e9:.2f}B"
    if a >= 1e6:  return f"{cur}{v/1e6:.2f}M"
    return f"{cur}{v:,.0f}"

def cur_sym(c: str) -> str:
    return {"USD":"$","EUR":"€","GBP":"£","JPY":"¥","CHF":"Fr.",
            "HKD":"HK$","CAD":"C$","AUD":"A$","INR":"₹","CNY":"¥"}.get(c, c)

def delta_color(v, good_above=None, bad_above=None):
    """Return Streamlit delta_color string."""
    if v is None: return "off"
    if good_above is not None and v > good_above: return "normal"
    if bad_above  is not None and v > bad_above:  return "inverse"
    return "off"

# ═══════════════════════════════════════════════════════════════
# CHART BUILDERS  (Plotly — Maison palette)
# ═══════════════════════════════════════════════════════════════

_PLOTLY_LAYOUT = dict(
    font_family="Outfit, sans-serif",
    paper_bgcolor=STONE,
    plot_bgcolor=STONE,
    margin=dict(l=0, r=0, t=24, b=0),
    xaxis=dict(showgrid=False, tickfont_size=10, tickfont_color=INK_LIGHT,
               zeroline=False, showline=False),
    yaxis=dict(showgrid=True, gridcolor="#DDD8CE", gridwidth=1,
               tickfont_size=10, tickfont_color=INK_LIGHT,
               zeroline=False, showline=False),
    legend=dict(orientation="h", yanchor="bottom", y=1.02,
                font_size=11, font_color=INK_MID),
)

def price_chart(prices: list[dict], symbol: str, cur: str, years: int = 3) -> go.Figure:
    if not prices:
        return go.Figure()

    df = pd.DataFrame(prices)
    df["date"] = pd.to_datetime(df["date"])
    cutoff = datetime.now() - timedelta(days=years * 365)
    df = df[df["date"] >= cutoff]
    if df.empty:
        return go.Figure()

    first, last = df["price"].iloc[0], df["price"].iloc[-1]
    chg_pct = (last - first) / first * 100
    color = RISE if chg_pct >= 0 else FALL

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["price"],
        mode="lines",
        line=dict(color=color, width=1.5),
        fill="tozeroy",
        fillcolor=f"rgba({','.join(str(int(color.lstrip('#')[i:i+2], 16)) for i in (0,2,4))}, 0.07)",
        name=symbol,
        hovertemplate=f"%{{x|%b %d, %Y}}<br>{cur_sym(cur)}%{{y:.2f}}<extra></extra>",
    ))
    fig.update_layout(
        **_PLOTLY_LAYOUT,
        height=260,
        xaxis_rangeslider_visible=False,
        showlegend=False,
    )
    return fig

def income_chart(d: dict) -> go.Figure:
    cur = cur_sym(d.get("currency", "USD"))
    items = [
        ("Revenue",     d.get("revenue"),    GOLD),
        ("EBITDA",      d.get("ebitda"),      DEPTH),
        ("Net Income",  d.get("net_income"),  RISE if (d.get("net_income") or 0) > 0 else FALL),
    ]
    labels = [i[0] for i in items if i[1]]
    values = [i[1] / 1e9 for i in items if i[1]]
    colors = [i[2] for i in items if i[1]]

    if not labels:
        return go.Figure()

    fig = go.Figure(go.Bar(
        x=labels, y=values,
        marker_color=colors,
        text=[f"{cur}{v:.1f}B" for v in values],
        textposition="outside",
        textfont=dict(size=11, family="Outfit", color=INK_MID),
        hovertemplate="%{x}: " + cur + "%{y:.2f}B<extra></extra>",
    ))
    fig.update_traces(marker_line_width=0, width=0.45)
    fig.update_layout(**_PLOTLY_LAYOUT, height=260, showlegend=False,
                      yaxis_title=f"({cur}B)")
    return fig

def comparison_chart(all_data: list[dict], metric: str, label: str) -> go.Figure:
    symbols = [d["symbol"] for d in all_data]
    values  = [d.get(metric) for d in all_data]
    colors  = [GOLD if v is not None else "#DDD8CE" for v in values]
    clean_v = [v if v is not None else 0 for v in values]

    fig = go.Figure(go.Bar(
        x=symbols, y=clean_v,
        marker_color=colors,
        text=[f"{v:.2f}" if v is not None else "N/A" for v in values],
        textposition="outside",
        textfont=dict(size=11, family="Outfit", color=INK_MID),
        hovertemplate="%{x}: %{y:.2f}<extra></extra>",
    ))
    fig.update_traces(marker_line_width=0, width=0.45)
    fig.update_layout(**_PLOTLY_LAYOUT, height=240, title=dict(
        text=label, font=dict(size=11, color=INK_LIGHT, family="Outfit"),
        x=0, xanchor="left",
    ), showlegend=False)
    return fig

def portfolio_returns_chart(all_data: list[dict], years: int = 3) -> go.Figure:
    """Normalised price chart (100 = start) for all tickers."""
    fig = go.Figure()
    palette = [GOLD, RISE, FALL, DEPTH, CAUTION, "#7C6D9F", "#5B8FA8", "#B5715A"]

    for i, d in enumerate(all_data):
        prices = d.get("prices", [])
        if not prices:
            continue
        df = pd.DataFrame(prices)
        df["date"] = pd.to_datetime(df["date"])
        cutoff = datetime.now() - timedelta(days=years * 365)
        df = df[df["date"] >= cutoff]
        if df.empty or len(df) < 5:
            continue
        df["norm"] = df["price"] / df["price"].iloc[0] * 100
        sym = d["symbol"]
        color = palette[i % len(palette)]
        fig.add_trace(go.Scatter(
            x=df["date"], y=df["norm"],
            mode="lines", name=sym,
            line=dict(color=color, width=1.8),
            hovertemplate=f"<b>{sym}</b><br>%{{x|%b %Y}}<br>%{{y:.1f}}<extra></extra>",
        ))

    fig.update_layout(
        **_PLOTLY_LAYOUT,
        height=320,
        yaxis_title="Indexed (base = 100)",
        xaxis_rangeslider_visible=False,
    )
    return fig

# ═══════════════════════════════════════════════════════════════
# RISK GAUGE
# ═══════════════════════════════════════════════════════════════

def risk_score(d: dict) -> tuple[int, str, str]:
    score = 0
    beta = d.get("beta")
    if beta and beta > 1.5:   score += 25
    elif beta and beta > 1.1: score += 12
    vol = d.get("vol")
    if vol and vol > 0.35:    score += 20
    elif vol and vol > 0.25:  score += 10
    mdd = d.get("mdd")
    if mdd and abs(mdd) > 0.5:  score += 20
    elif mdd and abs(mdd) > 0.3: score += 10
    sharpe = d.get("sharpe")
    if sharpe is not None:
        if sharpe < 0.8:  score += 15
        elif sharpe < 1.2: score += 5
    zscore = d.get("zscore")
    if zscore is not None:
        if zscore < 1.8:  score += 20
        elif zscore < 3:  score += 10
    if score <= 20:   return score, "Low",      RISE
    if score <= 40:   return score, "Moderate", GOLD
    if score <= 60:   return score, "Elevated", CAUTION
    return score, "High", FALL

# ═══════════════════════════════════════════════════════════════
# SECTION: SINGLE TICKER DETAIL
# ═══════════════════════════════════════════════════════════════

def render_ticker_detail(symbol: str, years: int):
    with st.spinner(f"Loading {symbol}…"):
        d = fetch_ticker_data(symbol)

    if "error" in d and not d.get("name"):
        st.error(f"⚠️  Could not load **{symbol}**: {d['error']}")
        st.info("Try refreshing, or check the ticker symbol (e.g. BMW.DE for BMW on XETRA).")
        return

    cur  = cur_sym(d.get("currency", "USD"))
    prices = d.get("prices", [])

    # ── Hero ────────────────────────────────────────────────────
    st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)
    col_name, col_price = st.columns([2, 1])

    with col_name:
        exchange_label = d.get("exchange","") or ""
        sector_label   = d.get("sector","") or ""
        industry_label = d.get("industry","") or ""
        meta = " · ".join(filter(None, [exchange_label, sector_label, industry_label]))
        if meta:
            st.markdown(
                f'<div style="font-size:11px;color:{GOLD};letter-spacing:.2em;'
                f'text-transform:uppercase;font-family:Outfit,sans-serif;margin-bottom:4px;">'
                f'{meta}</div>', unsafe_allow_html=True
            )
        st.markdown(
            f'<div class="hero-name">{d.get("name", symbol)}</div>'
            f'<div class="hero-ticker">{symbol}</div>',
            unsafe_allow_html=True
        )
        if d.get("bio"):
            st.markdown(
                f'<p style="font-size:13px;color:{INK_MID};line-height:1.75;'
                f'max-width:560px;margin-top:12px;font-weight:300;'
                f'display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;'
                f'overflow:hidden;">{d["bio"]}</p>',
                unsafe_allow_html=True
            )

    with col_price:
        price = d.get("price")
        mc    = d.get("mkt_cap")
        if price:
            st.markdown(
                f'<div style="text-align:right;">'
                f'<div style="font-size:9px;color:{GOLD};letter-spacing:.2em;'
                f'text-transform:uppercase;font-family:Outfit,sans-serif;">Current Price</div>'
                f'<div class="hero-price">{cur}{price:,.2f}</div>'
                f'<div style="font-size:11px;color:{INK_LIGHT};margin-top:6px;">'
                f'Cap {fmt_big(mc, cur)} · {d.get("currency","USD")}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)

    # ── KPI Row ─────────────────────────────────────────────────
    k1, k2, k3, k4, k5, k6, k7, k8 = st.columns(8)
    pe  = d.get("pe")
    ps  = d.get("ps")
    pb  = d.get("pb")
    dy  = d.get("div_yield") or 0
    po  = d.get("payout") or 0
    beta = d.get("beta")
    vol  = d.get("vol")
    sharpe = d.get("sharpe")

    with k1:
        delta_pe = "Undervalued" if pe and pe < 10 else ("Premium" if pe and pe > 50 else None)
        st.metric("P/E", f"{pe:.1f}×" if pe else "—", delta=delta_pe,
                  delta_color="normal" if delta_pe == "Undervalued" else
                  ("inverse" if delta_pe == "Premium" else "off"))
    with k2:
        st.metric("P/S", f"{ps:.1f}×" if ps else "—")
    with k3:
        below_book = "Below book" if pb and pb < 1 else None
        st.metric("P/B", f"{pb:.1f}×" if pb else "—",
                  delta=below_book, delta_color="normal" if below_book else "off")
    with k4:
        st.metric("Div. Yield", fmt_pct(dy) if dy else "—")
    with k5:
        st.metric("Payout", fmt_pct(po) if po else "—")
    with k6:
        beta_note = "High β" if beta and beta > 1.5 else ("Defensive" if beta and beta < 0.8 else None)
        st.metric("Beta (β)", f"{beta:.2f}" if beta else "—",
                  delta=beta_note,
                  delta_color="inverse" if beta_note == "High β" else
                  ("normal" if beta_note == "Defensive" else "off"))
    with k7:
        st.metric("Volatility", fmt_pct(vol), delta_color="off")
    with k8:
        st.metric("Sharpe", f"{sharpe:.2f}" if sharpe else "—",
                  delta="Good" if sharpe and sharpe > 1.3 else
                  ("Poor" if sharpe and sharpe < 0.8 else None),
                  delta_color="normal" if sharpe and sharpe > 1.3 else
                  ("inverse" if sharpe and sharpe < 0.8 else "off"))

    st.markdown("&nbsp;", unsafe_allow_html=True)

    # ── Charts ──────────────────────────────────────────────────
    col_chart, col_income = st.columns([1.2, 0.8])
    with col_chart:
        st.markdown(f'<div class="section-header">Price History · {years}Y</div>',
                    unsafe_allow_html=True)
        st.plotly_chart(
            price_chart(prices, symbol, d.get("currency", "USD"), years),
            use_container_width=True, config={"displayModeBar": False}
        )
    with col_income:
        st.markdown('<div class="section-header">Income Statement (TTM)</div>',
                    unsafe_allow_html=True)
        st.plotly_chart(
            income_chart(d), use_container_width=True,
            config={"displayModeBar": False}
        )

    # ── Risk Gauge ───────────────────────────────────────────────
    score, grade, color = risk_score(d)
    mdd  = d.get("mdd")
    zscore_val = d.get("zscore")

    st.markdown(f"""
    <div class="risk-card" style="margin: 24px 0 8px; background: {WHITE}; border: 1px solid #DDD8CE;
         border-radius: 14px; padding: 20px 28px; gap: 16px;">
      <div style="flex:1;">
        <div style="font-size:9px;color:{INK_LIGHT};letter-spacing:.16em;
             text-transform:uppercase;font-family:Outfit,sans-serif;">Composite Risk Profile</div>
        <div style="font-family:'Cormorant Garamond',serif;font-size:26px;
             font-weight:600;color:{color};margin-top:4px;">{grade} Risk</div>
      </div>
      <div style="flex:2;">
        <div style="height:8px;background:#EDE8DF;border-radius:4px;overflow:hidden;margin-bottom:6px;">
          <div style="width:{min(score,100)}%;height:100%;
               background:linear-gradient(90deg,{RISE},{CAUTION},{FALL});border-radius:4px;"></div>
        </div>
        <div style="font-size:11px;color:{INK_LIGHT};font-family:Outfit,sans-serif;">
          Score: <b style="color:{color};">{score}/100</b>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Detailed Tables ─────────────────────────────────────────
    tabs = st.tabs(["📐 Valuation", "📊 Profitability", "🛡  Risk Metrics"])

    with tabs[0]:
        ev = d.get("ev"); evr = d.get("ev_rev"); eve = d.get("ev_ebitda")
        rows = [
            {"Metric": "Enterprise Value",  "Value": fmt_big(ev, cur),    "Signal": _sig(None),    "Comment": "Total firm value incl. debt"},
            {"Metric": "Trailing P/E",       "Value": f"{pe:.1f}×" if pe else "—",
             "Signal": _sig("good" if pe and pe<10 else "warn" if pe and pe>50 else None),
             "Comment": "Attractive" if pe and pe<10 else "Premium" if pe and pe>50 else "Fair range"},
            {"Metric": "EV / Revenue",       "Value": f"{evr:.1f}×" if evr else "—", "Signal": _sig(None), "Comment": ""},
            {"Metric": "EV / EBITDA",        "Value": f"{eve:.1f}×" if eve else "—",
             "Signal": _sig("good" if eve and eve<10 else "warn" if eve and eve>40 else None),
             "Comment": "Undervalued" if eve and eve<10 else "Growth priced in" if eve and eve>40 else ""},
            {"Metric": "Price / Book",       "Value": f"{pb:.1f}×" if pb else "—",
             "Signal": _sig("good" if pb and pb<1 else None),
             "Comment": "Below book value" if pb and pb<1 else ""},
            {"Metric": "Price / Sales",      "Value": f"{ps:.1f}×" if ps else "—", "Signal": _sig(None), "Comment": ""},
            {"Metric": "Dividend Yield",     "Value": fmt_pct(dy),
             "Signal": _sig("good" if dy and dy>0.05 else None),
             "Comment": "High yield" if dy and dy>0.05 else ""},
        ]
        _render_table(rows)

    with tabs[1]:
        pm  = d.get("profit_margin")
        roa = d.get("roa")
        roe = d.get("roe")
        rev = d.get("revenue"); ni = d.get("net_income"); ebitda = d.get("ebitda")
        rows = [
            {"Metric": "Profit Margin",    "Value": fmt_pct(pm),
             "Signal": _sig("good" if pm and pm>0.2 else "bad" if pm and pm<0.05 else None),
             "Comment": "Exceptional" if pm and pm>0.25 else ""},
            {"Metric": "Return on Assets", "Value": fmt_pct(roa),
             "Signal": _sig("good" if roa and roa>0.1 else None), "Comment": ""},
            {"Metric": "Return on Equity", "Value": fmt_pct(roe),
             "Signal": _sig("good" if roe and roe>0.25 else None), "Comment": ""},
            {"Metric": "Revenue (TTM)",    "Value": fmt_big(rev, cur), "Signal": _sig(None), "Comment": ""},
            {"Metric": "Net Income (TTM)", "Value": fmt_big(ni, cur),
             "Signal": _sig("good" if ni and ni>0 else "bad" if ni and ni<0 else None),
             "Comment": "Profitable" if ni and ni>0 else "Loss-making" if ni and ni<0 else ""},
            {"Metric": "EBITDA",           "Value": fmt_big(ebitda, cur), "Signal": _sig(None), "Comment": ""},
        ]
        _render_table(rows)

    with tabs[2]:
        mdd_val = d.get("mdd"); deq = d.get("debt_eq")
        if deq: deq = deq / 100   # Yahoo returns ×100
        cr = d.get("current_ratio"); qr = d.get("quick_ratio")
        rows = [
            {"Metric": "Beta (β)",            "Value": fmt_num(beta),
             "Signal": _sig("warn" if beta and beta>1.5 else "good" if beta and beta<0.8 else None),
             "Comment": "High sensitivity" if beta and beta>1.5 else "Defensive" if beta and beta<0.8 else "Near-market"},
            {"Metric": "Annualised Volatility","Value": fmt_pct(vol),
             "Signal": _sig("bad" if vol and vol>0.35 else "good" if vol and vol<0.2 else None),
             "Comment": "Very high swings" if vol and vol>0.35 else "Low volatility" if vol and vol<0.2 else "Moderate"},
            {"Metric": "Max Drawdown",         "Value": fmt_pct(mdd_val),
             "Signal": _sig("bad" if mdd_val and abs(mdd_val)>0.5 else "warn" if mdd_val and abs(mdd_val)>0.3 else "good"),
             "Comment": "Worst peak-to-trough"},
            {"Metric": "Sharpe Ratio",         "Value": fmt_num(sharpe),
             "Signal": _sig("good" if sharpe and sharpe>1.3 else "bad" if sharpe and sharpe<0.8 else None),
             "Comment": "Excellent risk-adj." if sharpe and sharpe>1.3 else "Poor compensation" if sharpe and sharpe<0.8 else ""},
            {"Metric": "Debt / Equity",        "Value": fmt_num(deq),
             "Signal": _sig("bad" if deq and deq>2 else "good" if deq and deq<0.5 else None),
             "Comment": "High leverage" if deq and deq>2 else "Conservative" if deq and deq<0.5 else ""},
            {"Metric": "Current Ratio",        "Value": fmt_num(cr),
             "Signal": _sig("good" if cr and cr>1.5 else "bad" if cr and cr<1 else None),
             "Comment": "Strong liquidity" if cr and cr>2 else "Liquidity concern" if cr and cr<1 else ""},
            {"Metric": "Quick Ratio",          "Value": fmt_num(qr),
             "Signal": _sig("good" if qr and qr>1.2 else "bad" if qr and qr<0.8 else None), "Comment": ""},
            {"Metric": "Altman Z-Score",       "Value": fmt_num(zscore_val),
             "Signal": _sig("good" if zscore_val and zscore_val>3 else "bad" if zscore_val and zscore_val<1.8 else "warn"),
             "Comment": "Safe zone" if zscore_val and zscore_val>3 else "Distress zone" if zscore_val and zscore_val<1.8 else "Grey zone"},
        ]
        _render_table(rows)

# ─── Table render helper ─────────────────────────────────────────────────────

def _sig(tone):
    return {"good": "🟢", "bad": "🔴", "warn": "🟡", None: ""}[tone]

def _render_table(rows: list[dict]):
    df = pd.DataFrame(rows)
    df = df[df["Value"] != "—"]
    st.dataframe(
        df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Signal" : st.column_config.TextColumn("", width="small"),
            "Metric" : st.column_config.TextColumn("Metric", width="medium"),
            "Value"  : st.column_config.TextColumn("Value",  width="small"),
            "Comment": st.column_config.TextColumn("Assessment"),
        },
    )

# ═══════════════════════════════════════════════════════════════
# SECTION: COMPARISON VIEW
# ═══════════════════════════════════════════════════════════════

def render_comparison(symbols: list[str], years: int):
    st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-header">Cross-Comparison · {len(symbols)} Securities · Live</div>',
                unsafe_allow_html=True)

    with st.spinner("Loading comparison data…"):
        all_data = []
        progress = st.progress(0)
        for i, sym in enumerate(symbols):
            d = fetch_ticker_data(sym)
            all_data.append(d)
            progress.progress((i + 1) / len(symbols))
        progress.empty()

    valid = [d for d in all_data if "error" not in d or d.get("price")]

    if len(valid) < 2:
        st.warning("Need at least 2 valid tickers for comparison.")
        return

    # Normalised returns chart
    st.markdown(f'<div class="section-header">Indexed Returns (Base = 100, {years}Y)</div>',
                unsafe_allow_html=True)
    st.plotly_chart(portfolio_returns_chart(valid, years),
                    use_container_width=True, config={"displayModeBar": False})

    # Bar-chart grid
    col_charts = st.columns(3)
    metrics_viz = [
        ("pe",   "P/E Ratio"),
        ("profit_margin", "Profit Margin"),
        ("roe",  "Return on Equity"),
        ("vol",  "Annualised Volatility"),
        ("beta", "Beta (β)"),
        ("div_yield", "Dividend Yield"),
    ]
    for i, (key, label) in enumerate(metrics_viz):
        with col_charts[i % 3]:
            st.plotly_chart(comparison_chart(valid, key, label),
                            use_container_width=True, config={"displayModeBar": False})

    # Summary table
    st.markdown('<div class="section-header">Summary Table</div>',
                unsafe_allow_html=True)
    rows = []
    for d in valid:
        cur = cur_sym(d.get("currency", "USD"))
        deq = d.get("debt_eq")
        if deq: deq /= 100
        sc, grade, _ = risk_score(d)
        rows.append({
            "Ticker"    : d["symbol"],
            "Name"      : (d.get("name") or d["symbol"])[:28],
            "Price"     : f'{cur}{d["price"]:,.2f}' if d.get("price") else "—",
            "Mkt Cap"   : fmt_big(d.get("mkt_cap"), cur),
            "P/E"       : f'{d["pe"]:.1f}×' if d.get("pe") else "—",
            "P/B"       : f'{d["pb"]:.1f}×' if d.get("pb") else "—",
            "Div Yield" : fmt_pct(d.get("div_yield")),
            "Profit Mg.": fmt_pct(d.get("profit_margin")),
            "ROE"       : fmt_pct(d.get("roe")),
            "EV/EBITDA" : f'{d["ev_ebitda"]:.1f}×' if d.get("ev_ebitda") else "—",
            "Beta"      : fmt_num(d.get("beta")),
            "D/E"       : fmt_num(deq),
            "Volatility": fmt_pct(d.get("vol")),
            "Sharpe"    : fmt_num(d.get("sharpe")),
            "Risk Score": f'{grade} ({sc})',
        })

    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    # Export
    csv_buf = pd.DataFrame(rows).to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇  Export Comparison CSV",
        data=csv_buf,
        file_name="stock_haus_comparison.csv",
        mime="text/csv",
    )

# ═══════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════

def render_sidebar() -> tuple[list[str], int, str]:
    with st.sidebar:
        # Logo
        st.markdown(f"""
        <div style="padding: 16px 0 24px;">
          <div style="font-family:'Cormorant Garamond',serif;font-size:22px;
               font-weight:600;color:{INK};letter-spacing:.12em;">STOCK · HAUS</div>
          <div style="font-family:Outfit,sans-serif;font-size:8px;color:{INK_LIGHT};
               letter-spacing:.28em;text-transform:uppercase;margin-top:2px;">
            Intelligence &amp; Analytics · Live</div>
          <div style="height:1px;background:linear-gradient(90deg,{GOLD},{GOLD_PALE},transparent);
               margin-top:12px;"></div>
        </div>
        """, unsafe_allow_html=True)

        # Ticker search
        st.markdown(f'<div class="section-header">Search Ticker</div>',
                    unsafe_allow_html=True)
        query = st.text_input("", placeholder="AAPL, BMW.DE, 7203.T…",
                              label_visibility="collapsed", key="search_q")

        if query and len(query) >= 1:
            with st.spinner("Searching…"):
                found = search_tickers(query)
            if found:
                for r in found:
                    label = f"**{r['sym']}**  {r['name'][:30]}  _{r['exchange']}_"
                    if st.button(label, key=f"add_{r['sym']}", use_container_width=True):
                        if r["sym"] not in st.session_state.get("tickers", []):
                            st.session_state.tickers = st.session_state.get("tickers", ["AAPL"]) + [r["sym"]]
                        st.session_state.active = r["sym"]
                        st.rerun()

        # Bulk add
        st.markdown(f'<div class="section-header" style="margin-top:20px;">Watchlist</div>',
                    unsafe_allow_html=True)
        bulk = st.text_area("Add tickers (comma/space separated)",
                            placeholder="MSFT, TSLA, LVMH.PA…",
                            height=80, label_visibility="visible")
        if st.button("＋ Add to Watchlist", use_container_width=True):
            news = [t.strip().upper() for t in bulk.replace(",", " ").split() if t.strip()]
            current = st.session_state.get("tickers", ["AAPL"])
            st.session_state.tickers = list(dict.fromkeys(current + news))
            if news:
                st.session_state.active = news[0]
            st.rerun()

        # Current watchlist
        tickers = st.session_state.get("tickers", ["AAPL"])
        if tickers:
            st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
            to_remove = None
            for sym in tickers:
                col_sym, col_rm = st.columns([3, 1])
                with col_sym:
                    active = st.session_state.get("active", tickers[0])
                    style = f"color:{GOLD};font-weight:600;" if sym == active else f"color:{INK_MID};"
                    if st.button(sym, key=f"sel_{sym}", use_container_width=True):
                        st.session_state.active = sym
                        st.session_state.view_mode = "detail"
                        st.rerun()
                with col_rm:
                    if st.button("✕", key=f"rm_{sym}"):
                        to_remove = sym
            if to_remove:
                st.session_state.tickers = [t for t in tickers if t != to_remove]
                if st.session_state.get("active") == to_remove and st.session_state.tickers:
                    st.session_state.active = st.session_state.tickers[0]
                st.rerun()

        # Compare toggle
        st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
        if len(tickers) >= 2:
            if st.button("⇄  Compare All", use_container_width=True):
                st.session_state.view_mode = "compare"
                st.rerun()

        # Year selector
        st.markdown(f'<div class="section-header" style="margin-top:24px;">Time Window</div>',
                    unsafe_allow_html=True)
        yr = st.select_slider("", options=[1, 2, 3, 5, 10],
                              value=st.session_state.get("years", 3),
                              format_func=lambda x: f"{x}Y",
                              label_visibility="collapsed")
        st.session_state.years = yr

        # Data note
        st.markdown(f"""
        <div style="margin-top:32px;padding:12px 16px;background:{STONE};
             border-radius:8px;border:1px solid #DDD8CE;">
          <div style="font-size:9px;color:{INK_LIGHT};font-family:Outfit,sans-serif;
               letter-spacing:.1em;text-transform:uppercase;line-height:1.8;">
            Data: Yahoo Finance<br>Cache: 5 min (server-side)<br>
            Transport: yfinance (server-to-server)<br>
            No CORS proxy required
          </div>
        </div>
        """, unsafe_allow_html=True)

        return (
            st.session_state.get("tickers", ["AAPL"]),
            int(yr),
            st.session_state.get("view_mode", "detail"),
        )

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    # Init session state
    if "tickers"   not in st.session_state: st.session_state.tickers   = ["AAPL"]
    if "active"    not in st.session_state: st.session_state.active    = "AAPL"
    if "view_mode" not in st.session_state: st.session_state.view_mode = "detail"
    if "years"     not in st.session_state: st.session_state.years     = 3

    tickers, years, mode = render_sidebar()

    # Ensure active is in tickers
    if st.session_state.active not in tickers and tickers:
        st.session_state.active = tickers[0]

    active = st.session_state.active

    if not tickers:
        st.markdown(f"""
        <div style="text-align:center;padding:100px 20px;">
          <div style="font-family:'Cormorant Garamond',serif;font-size:28px;
               color:{INK_MID};font-weight:400;margin-bottom:10px;">
            Begin your analysis</div>
          <div style="font-size:13px;font-family:Outfit,sans-serif;color:{INK_LIGHT};">
            Search any ticker in the sidebar — US, EU, Asia, all exchanges.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    if mode == "compare" and len(tickers) >= 2:
        render_comparison(tickers, years)
    else:
        render_ticker_detail(active, years)

    # Footer
    st.markdown(f"""
    <div style="margin-top:60px;border-top:1px solid #DDD8CE;padding:20px 0;
         display:flex;justify-content:space-between;">
      <span style="font-size:10px;font-family:Outfit,sans-serif;color:#C5BFB5;
            letter-spacing:.14em;">STOCK · HAUS</span>
      <span style="font-size:9px;font-family:Outfit,sans-serif;color:#DDD8CE;">
        Live data via Yahoo Finance · 5 min cache · No CORS proxies</span>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
