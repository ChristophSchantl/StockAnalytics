"""
STOCK · HAUS — Streamlit Edition
Live Yahoo Finance data via yfinance (server-side, no CORS issues)
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta

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
# DATA LAYER  — yfinance ≥0.2.38 uses curl_cffi internally.
# NEVER pass a custom requests.Session — it breaks the auth flow.
# Security hardening is done via the search endpoint only (requests).
# ═══════════════════════════════════════════════════════════════

def _search_session() -> requests.Session:
    """Hardened requests.Session used ONLY for the Yahoo search endpoint."""
    import random
    _UA_POOL = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    ]
    session = requests.Session()
    session.headers.update({
        "User-Agent"      : random.choice(_UA_POOL),
        "Accept"          : "application/json, text/plain, */*",
        "Accept-Language" : "en-US,en;q=0.9",
        "Accept-Encoding" : "gzip, deflate, br",
        "DNT"             : "1",
    })
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    retry = Retry(total=3, backoff_factor=1.2,
                  status_forcelist=[429, 500, 502, 503, 504],
                  allowed_methods=["GET"])
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session

def _safe(val):
    """Return float or None; never NaN."""
    try:
        v = float(val)
        return None if (np.isnan(v) or np.isinf(v)) else v
    except Exception:
        return None

def _row(df: pd.DataFrame, *keys):
    """Extract first matching row label from a DataFrame, return most-recent value."""
    for k in keys:
        for label in df.index:
            if k.lower() in str(label).lower():
                row = df.loc[label]
                # take the most recent non-null column
                for col in df.columns:
                    v = _safe(row[col])
                    if v is not None:
                        return v
    return None

@st.cache_data(ttl=300, show_spinner=False)
def fetch_ticker_data(symbol: str) -> dict:
    """
    Robust multi-endpoint fetch for yfinance ≥0.2.38.
    tk.info is used ONLY for metadata (name/sector/bio).
    ALL financial ratios are computed from first principles:
      fast_info   → price, mkt_cap, currency, shares
      income_stmt → revenue, net_income, EBITDA, EPS
      balance_sheet → equity, debt, liquidity
      history     → price series, beta (vs SPY), volatility, Sharpe, MDD
    """
    try:
        tk = yf.Ticker(symbol)

        # ── 1. fast_info — price / cap (always reliable) ────────
        fi          = tk.fast_info
        fi_price    = _safe(getattr(fi, "last_price",      None))
        fi_prev     = _safe(getattr(fi, "previous_close",  None))
        fi_mktcap   = _safe(getattr(fi, "market_cap",      None))
        fi_currency = (getattr(fi, "currency", None) or "USD")
        fi_shares   = _safe(getattr(fi, "shares",          None))
        fi_exchange = (getattr(fi, "exchange",  None) or "")

        # ── 2. info — metadata only (name, sector, bio) ─────────
        info = {}
        try:
            info = tk.info or {}
            if len(info) < 5 or list(info.keys()) == ["maxAge"]:
                info = {}
        except Exception:
            info = {}

        # Name: strip generic stubs yfinance returns
        _BAD_NAMES = {"EQUITY", "ETF", "INDEX", "MUTUALFUND", "CURRENCY",
                      "FUTURE", "OPTION", symbol.upper()}
        raw_name = (info.get("longName") or info.get("shortName") or "").strip()
        name = raw_name if raw_name and raw_name.upper() not in _BAD_NAMES else symbol.upper()

        # If info returned a stub, try yf.Search for proper company name
        if name == symbol.upper():
            try:
                results = yf.Search(symbol, max_results=1).quotes
                if results:
                    q = results[0]
                    candidate = q.get("longname") or q.get("shortname") or ""
                    if candidate and candidate.upper() not in _BAD_NAMES:
                        name = candidate
            except Exception:
                pass

        currency   = info.get("currency")  or fi_currency
        sector     = info.get("sector")    or "—"
        industry   = info.get("industry")  or "—"
        country    = info.get("country")   or "—"
        exchange   = info.get("exchange")  or fi_exchange or "—"
        bio        = info.get("longBusinessSummary") or ""
        employees  = info.get("fullTimeEmployees")

        # Price & cap — fast_info wins over info
        price   = fi_price or fi_prev or _safe(info.get("regularMarketPrice"))
        mkt_cap = fi_mktcap or _safe(info.get("marketCap"))
        shares  = fi_shares or _safe(info.get("sharesOutstanding"))

        # ── 3. Income statement ──────────────────────────────────
        revenue = net_income = ebitda_val = gross_profit = None
        interest_exp = None
        try:
            inc = tk.income_stmt
            if inc is not None and not inc.empty:
                revenue      = _row(inc, "Total Revenue")
                net_income   = _row(inc, "Net Income")
                gross_profit = _row(inc, "Gross Profit")
                ebitda_val   = _row(inc, "EBITDA", "Normalized EBITDA")
                interest_exp = _row(inc, "Interest Expense")
                if ebitda_val is None:
                    ebit = _row(inc, "EBIT", "Operating Income")
                    da   = _row(inc, "Depreciation", "Reconciled Depreciation",
                                "Depreciation And Amortization")
                    if ebit is not None and da is not None:
                        ebitda_val = ebit + abs(da)
        except Exception:
            pass

        # ── 4. Balance sheet ─────────────────────────────────────
        total_assets = total_liab = retained = None
        cur_assets = cur_liab = total_debt = equity = None
        try:
            bs = tk.balance_sheet
            if bs is not None and not bs.empty:
                total_assets = _row(bs, "Total Assets")
                total_liab   = _row(bs, "Total Liab", "Total Liabilities Net Minority Interest")
                retained     = _row(bs, "Retained Earnings")
                cur_assets   = _row(bs, "Current Assets", "Total Current Assets")
                cur_liab     = _row(bs, "Current Liabilities", "Total Current Liabilities")
                total_debt   = _row(bs, "Total Debt", "Long Term Debt")
                equity       = _row(bs, "Stockholders Equity", "Total Stockholder Equity",
                                    "Common Stock Equity", "Total Equity Gross Minority Interest")
        except Exception:
            pass

        # ── 5. Price history + beta + risk ───────────────────────
        prices = []
        hist_close    = np.array([])
        hist_dates    = []
        hist_returns  = np.array([])

        try:
            hist = tk.history(period="5y", auto_adjust=True, actions=False, timeout=20)
            if hist is not None and not hist.empty:
                hist = hist[["Close"]].dropna()
                hist.index = pd.to_datetime(hist.index).tz_localize(None)
                hist_close = hist["Close"].values.astype(float)
                hist_dates = hist.index
                if price is None and len(hist_close) > 0:
                    price = float(hist_close[-1])
                prices = [
                    {"date": idx.strftime("%Y-%m-%d"), "price": round(float(v), 2)}
                    for idx, v in zip(hist_dates, hist_close)
                ]
                if len(hist_close) > 1:
                    hist_returns = np.diff(np.log(hist_close[hist_close > 0]))
        except Exception:
            pass

        # Beta: regress stock returns vs SPY over same window
        beta = _safe(info.get("beta"))
        if beta is None and len(hist_returns) > 60:
            try:
                spy = yf.Ticker("^GSPC").history(period="5y", auto_adjust=True,
                                                  actions=False, timeout=15)
                if spy is not None and not spy.empty:
                    spy = spy[["Close"]].dropna()
                    spy.index = pd.to_datetime(spy.index).tz_localize(None)
                    spy_ret = np.diff(np.log(spy["Close"].values.astype(float)))
                    # Align lengths
                    n = min(len(hist_returns), len(spy_ret))
                    if n > 60:
                        x, y = spy_ret[-n:], hist_returns[-n:]
                        cov = np.cov(x, y)[0, 1]
                        var = np.var(x)
                        if var > 0:
                            beta = round(cov / var, 2)
            except Exception:
                pass

        # ── 6. Compute all ratios from first principles ──────────
        # P/E  = market_cap / net_income
        pe = _safe(info.get("trailingPE"))
        if pe is None and mkt_cap and net_income and net_income > 0:
            pe = round(mkt_cap / net_income, 2)

        # P/S  = market_cap / revenue
        ps = _safe(info.get("priceToSalesTrailing12Months"))
        if ps is None and mkt_cap and revenue and revenue > 0:
            ps = round(mkt_cap / revenue, 2)

        # P/B  = market_cap / book_equity
        pb = _safe(info.get("priceToBook"))
        if pb is None and mkt_cap and equity and equity > 0:
            pb = round(mkt_cap / equity, 2)

        # EV   = mkt_cap + total_debt - cash (simplified)
        ev = _safe(info.get("enterpriseValue"))
        if ev is None and mkt_cap and total_debt:
            ev = mkt_cap + (total_debt or 0)

        # EV/Revenue, EV/EBITDA
        ev_rev    = _safe(info.get("enterpriseToRevenue"))
        ev_ebitda = _safe(info.get("enterpriseToEbitda"))
        if ev_rev is None and ev and revenue and revenue > 0:
            ev_rev = round(ev / revenue, 2)
        if ev_ebitda is None and ev and ebitda_val and ebitda_val > 0:
            ev_ebitda = round(ev / ebitda_val, 2)

        # Profit margin
        profit_mg = _safe(info.get("profitMargins"))
        if profit_mg is None and net_income and revenue and revenue > 0:
            profit_mg = net_income / revenue

        # ROE  = net_income / equity
        roe = _safe(info.get("returnOnEquity"))
        if roe is None and net_income and equity and equity > 0:
            roe = net_income / equity

        # ROA  = net_income / total_assets
        roa = _safe(info.get("returnOnAssets"))
        if roa is None and net_income and total_assets and total_assets > 0:
            roa = net_income / total_assets

        # D/E  = total_debt / equity
        debt_eq = _safe(info.get("debtToEquity"))
        if debt_eq is not None:
            debt_eq /= 100   # Yahoo returns ×100
        elif total_debt and equity and equity != 0:
            debt_eq = total_debt / equity

        # Liquidity ratios
        cur_ratio = _safe(info.get("currentRatio"))
        if cur_ratio is None and cur_assets and cur_liab and cur_liab != 0:
            cur_ratio = cur_assets / cur_liab

        quick_r = _safe(info.get("quickRatio"))
        if quick_r is None and cur_assets and cur_liab and cur_liab != 0:
            inv = 0  # conservative — no inventory row needed
            quick_r = (cur_assets - inv) / cur_liab

        # Interest coverage
        ic = None
        if ebitda_val and interest_exp and abs(interest_exp) > 0:
            ic = ebitda_val / abs(interest_exp)

        # Dividends
        div_yield = _safe(info.get("dividendYield")) or 0.0
        payout    = _safe(info.get("payoutRatio"))   or 0.0
        if div_yield == 0.0:
            try:
                divs = tk.dividends
                if divs is not None and not divs.empty and price:
                    annual_div = float(divs.tail(4).sum()) if len(divs) >= 4 else float(divs.sum())
                    div_yield  = annual_div / price
            except Exception:
                pass

        # Altman Z-Score & risk
        zscore = _altman_z_v2(total_assets, retained, ebitda_val, mkt_cap,
                               revenue, cur_assets, cur_liab, total_liab)
        risk   = _compute_risk(hist_close)

        # ── 6b. 52-week high / low distance ──────────────────────
        w52_low = w52_high = dist_52w_low = dist_52w_high = None
        try:
            if len(hist_close) >= 20:
                window = hist_close[-252:] if len(hist_close) >= 252 else hist_close
                w52_low   = float(np.min(window))
                w52_high  = float(np.max(window))
                if price and w52_low > 0:
                    dist_52w_low  = (price - w52_low)  / w52_low   # +X% above low
                if price and w52_high > 0:
                    dist_52w_high = (price - w52_high) / w52_high  # −X% below high (negative)
        except Exception:
            pass

        return {
            "symbol"       : symbol,
            "name"         : name,
            "sector"       : sector,
            "industry"     : industry,
            "country"      : country,
            "exchange"     : exchange,
            "currency"     : currency,
            "employees"    : employees,
            "bio"          : bio,
            "price"        : price,
            "mkt_cap"      : mkt_cap,
            "shares"       : shares,
            "pe"           : pe,
            "ps"           : ps,
            "pb"           : pb,
            "ev"           : ev,
            "ev_rev"       : ev_rev,
            "ev_ebitda"    : ev_ebitda,
            "profit_margin": profit_mg,
            "roa"          : roa,
            "roe"          : roe,
            "revenue"      : revenue,
            "net_income"   : net_income,
            "ebitda"       : ebitda_val,
            "gross_profit" : gross_profit,
            "div_yield"    : div_yield,
            "payout"       : payout,
            "beta"         : beta,
            "ic"           : ic,
            "debt_eq"      : debt_eq,
            "current_ratio": cur_ratio,
            "quick_ratio"  : quick_r,
            "zscore"       : zscore,
            **risk,
            "w52_low"      : w52_low,
            "w52_high"     : w52_high,
            "dist_52w_low" : dist_52w_low,
            "dist_52w_high": dist_52w_high,
            "prices"       : prices,
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

def _altman_z_v2(ta, retained, ebitda_val, mkt_cap, revenue, cur_assets, cur_liab, total_liab):
    """Altman Z-Score from explicit balance sheet / income statement values."""
    try:
        if not ta or ta <= 0 or not mkt_cap or not revenue:
            return None
        wc   = (cur_assets or 0) - (cur_liab or 0)
        ebit = (ebitda_val or 0) * 0.85
        tl   = total_liab or 1
        A = wc / ta
        B = (retained or 0) / ta
        C = ebit / ta
        D = mkt_cap / tl
        E = revenue / ta
        z = 1.2*A + 1.4*B + 3.3*C + 0.6*D + 1.0*E
        return round(z, 2) if 0 < z < 50 else None
    except Exception:
        return None

@st.cache_data(ttl=300, show_spinner=False)
def search_tickers(query: str) -> list[dict]:
    """Live ticker search via Yahoo Finance query endpoint (uses requests, not yfinance)."""
    if len(query) < 1:
        return []
    try:
        session = _search_session()
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
    xaxis=dict(showgrid=False, tickfont=dict(size=10, color=INK_LIGHT),
               zeroline=False, showline=False),
    yaxis=dict(showgrid=True, gridcolor="#DDD8CE", gridwidth=1,
               tickfont=dict(size=10, color=INK_LIGHT),
               zeroline=False, showline=False),
    legend=dict(orientation="h", yanchor="bottom", y=1.02,
                font=dict(size=11, color=INK_MID)),
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
    candidates = [
        ("Revenue",    d.get("revenue"),     GOLD),
        ("EBITDA",     d.get("ebitda"),       DEPTH),
        ("Net Income", d.get("net_income"),   RISE if (d.get("net_income") or 0) >= 0 else FALL),
    ]
    items = [(lbl, val, col) for lbl, val, col in candidates
             if val is not None and not np.isnan(float(val))]

    if not items:
        fig = go.Figure()
        fig.add_annotation(text="Income data unavailable",
                           xref="paper", yref="paper", x=0.5, y=0.5,
                           showarrow=False, font=dict(size=13, color=INK_LIGHT,
                           family="Outfit, sans-serif"))
        fig.update_layout(**_PLOTLY_LAYOUT, height=260)
        return fig

    labels = [i[0] for i in items]
    values = [i[1] / 1e9 for i in items]
    colors = [i[2] for i in items]

    fig = go.Figure(go.Bar(
        x=labels, y=values,
        marker_color=colors,
        text=[f"{cur}{v:.1f}B" for v in values],
        textposition="outside",
        textfont=dict(size=11, family="Outfit, sans-serif", color=INK_MID),
        hovertemplate="%{x}: " + cur + "%{y:.2f}B<extra></extra>",
    ))
    fig.update_traces(marker_line_width=0, width=0.45)

    max_v = max(abs(v) for v in values) * 1.3

    # Build layout without xaxis/yaxis (they conflict with _PLOTLY_LAYOUT)
    base = {k: v for k, v in _PLOTLY_LAYOUT.items() if k not in ("xaxis", "yaxis")}
    fig.update_layout(
        **base,
        height=260,
        showlegend=False,
        xaxis=dict(showgrid=False, tickfont=dict(size=11, color=INK_MID)),
        yaxis=dict(
            range=[-max_v * 0.05, max_v],
            showgrid=True, gridcolor="#DDD8CE",
            tickfont=dict(size=10, color=INK_LIGHT),
            zeroline=True, zerolinecolor="#DDD8CE",
            ticksuffix="B",
        ),
    )
    return fig

def factor_radar(d: dict, symbol: str) -> go.Figure:
    """
    Factor Scorecard Spider Chart — 7 dimensions, each scored 0–100.

    Valuation : low multiples = high score (cheap = good)
    Quality   : high margins + ROE = high score
    Growth    : revenue & income scale (relative to cap)
    Risk      : low vol + low beta + strong Z-score = high score
    Momentum  : price return over window = high score
    Dividend  : yield + payout sustainability
    Liquidity : current ratio + low D/E
    """
    def _clamp(v, lo, hi):
        if v is None: return None
        return max(lo, min(hi, v))

    def _score_val():
        """Cheap = high score. Based on P/E, P/S, P/B."""
        scores = []
        pe = d.get("pe")
        if pe and pe > 0:
            scores.append(_clamp(100 - (pe - 5) * 1.5, 0, 100))
        ps = d.get("ps")
        if ps and ps > 0:
            scores.append(_clamp(100 - (ps - 1) * 8, 0, 100))
        pb = d.get("pb")
        if pb and pb > 0:
            scores.append(_clamp(100 - (pb - 1) * 12, 0, 100))
        ev_e = d.get("ev_ebitda")
        if ev_e and ev_e > 0:
            scores.append(_clamp(100 - (ev_e - 6) * 2.5, 0, 100))
        return round(sum(scores) / len(scores)) if scores else 50

    def _score_quality():
        """Profitability quality."""
        scores = []
        pm = d.get("profit_margin")
        if pm is not None:
            scores.append(_clamp(pm * 300, 0, 100))   # 33% margin → 100
        roe = d.get("roe")
        if roe is not None:
            scores.append(_clamp(roe * 250, 0, 100))  # 40% ROE → 100
        roa = d.get("roa")
        if roa is not None:
            scores.append(_clamp(roa * 500, 0, 100))  # 20% ROA → 100
        return round(sum(scores) / len(scores)) if scores else 50

    def _score_growth():
        """Revenue scale relative to market cap — proxy for capital efficiency."""
        scores = []
        ps = d.get("ps")
        if ps and ps > 0:
            scores.append(_clamp(100 / ps * 15, 0, 100))  # P/S=1 → high, P/S=10 → low
        ev_r = d.get("ev_rev")
        if ev_r and ev_r > 0:
            scores.append(_clamp(100 / ev_r * 12, 0, 100))
        ni = d.get("net_income"); mc = d.get("mkt_cap")
        if ni and mc and mc > 0:
            earn_yield = ni / mc
            scores.append(_clamp(earn_yield * 600, 0, 100))
        return round(sum(scores) / len(scores)) if scores else 50

    def _score_risk():
        """Low risk = high score."""
        scores = []
        vol = d.get("vol")
        if vol is not None:
            scores.append(_clamp(100 - vol * 200, 0, 100))  # 50% vol → 0
        beta = d.get("beta")
        if beta is not None:
            scores.append(_clamp(100 - abs(beta - 1) * 50, 0, 100))
        mdd = d.get("mdd")
        if mdd is not None:
            scores.append(_clamp(100 + mdd * 120, 0, 100))  # mdd is negative
        sharpe = d.get("sharpe")
        if sharpe is not None:
            scores.append(_clamp(sharpe * 50, 0, 100))
        z = d.get("zscore")
        if z is not None:
            scores.append(_clamp((z - 1.8) / (3 - 1.8) * 100, 0, 100))
        return round(sum(scores) / len(scores)) if scores else 50

    def _score_momentum():
        """Price momentum over the available history."""
        prices = d.get("prices", [])
        if len(prices) < 60:
            return 50
        closes = [p["price"] for p in prices]
        # 1Y momentum
        ret_1y = (closes[-1] - closes[max(0, len(closes)-252)]) / closes[max(0, len(closes)-252)] * 100
        # 3M momentum
        ret_3m = (closes[-1] - closes[max(0, len(closes)-63)]) / closes[max(0, len(closes)-63)] * 100
        score = _clamp(50 + ret_1y * 0.5, 0, 100) * 0.6 + _clamp(50 + ret_3m * 1.5, 0, 100) * 0.4
        return round(score)

    def _score_dividend():
        dy = d.get("div_yield") or 0
        po = d.get("payout")    or 0
        if dy == 0:
            return 30   # no dividend — neutral-low
        yield_score = _clamp(dy * 1000, 0, 100)       # 10% yield → 100
        payout_score = _clamp(100 - abs(po - 0.5) * 150, 0, 100)  # 50% payout ideal
        return round(yield_score * 0.6 + payout_score * 0.4)

    def _score_liquidity():
        scores = []
        cr = d.get("current_ratio")
        if cr is not None:
            scores.append(_clamp((cr - 0.5) / 2.5 * 100, 0, 100))  # 3.0 → 100
        deq = d.get("debt_eq")
        if deq is not None:
            scores.append(_clamp(100 - deq * 30, 0, 100))  # D/E=3 → 10
        ic = d.get("ic")
        if ic is not None:
            scores.append(_clamp(ic * 4, 0, 100))   # coverage=25 → 100
        return round(sum(scores) / len(scores)) if scores else 50

    def _score_convexity():
        """
        Convexity = asymmetry of returns: upside capture vs downside capture.
        High convexity → stock gains more on up days than it loses on down days.
        Computed as: mean(positive daily returns) / abs(mean(negative daily returns))
        ratio > 1 = convex (good), ratio < 1 = concave (bad).
        Also incorporates Calmar ratio (ann_return / abs(MDD)).
        """
        prices = d.get("prices", [])
        if len(prices) < 60:
            return 50
        closes = np.array([p["price"] for p in prices], dtype=float)
        rets = np.diff(np.log(closes[closes > 0]))
        if len(rets) < 30:
            return 50

        up_rets   = rets[rets > 0]
        down_rets = rets[rets < 0]
        scores = []

        # Upside/downside capture ratio
        if len(up_rets) > 5 and len(down_rets) > 5:
            up_mean   = np.mean(up_rets)
            down_mean = abs(np.mean(down_rets))
            if down_mean > 0:
                conv_ratio = up_mean / down_mean
                # ratio=1.0 → 50, ratio=1.5 → 80, ratio=2.0 → 100, ratio=0.5 → 0
                scores.append(_clamp((conv_ratio - 0.5) / 1.5 * 100, 0, 100))

        # Calmar ratio: annualised return / abs(max drawdown)
        mdd = d.get("mdd")
        if mdd and abs(mdd) > 0.001:
            ann_return = np.mean(rets) * 252
            calmar = ann_return / abs(mdd)
            # calmar=0 → 40, calmar=0.5 → 65, calmar=1 → 80, calmar=2 → 100
            scores.append(_clamp(40 + calmar * 40, 0, 100))

        # Positive skew of returns (right tail > left tail)
        if len(rets) > 20:
            skew = float(pd.Series(rets).skew())
            scores.append(_clamp(50 + skew * 20, 0, 100))

        return round(sum(scores) / len(scores)) if scores else 50

    # Build scores
    factors = {
        "Valuation" : _score_val(),
        "Quality"   : _score_quality(),
        "Growth"    : _score_growth(),
        "Risk"      : _score_risk(),
        "Momentum"  : _score_momentum(),
        "Convexity" : _score_convexity(),
        "Dividend"  : _score_dividend(),
        "Liquidity" : _score_liquidity(),
    }

    labels = list(factors.keys())
    values = list(factors.values())
    # Close the polygon
    labels_closed = labels + [labels[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=labels_closed,
        fill="toself",
        fillcolor="rgba(182,157,95,0.15)",
        line=dict(color=GOLD, width=2),
        marker=dict(size=5, color=GOLD),
        name=symbol,
        hovertemplate="<b>%{theta}</b><br>Score: %{r:.0f}/100<extra></extra>",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor=STONE,
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickvals=[20, 40, 60, 80, 100],
                tickfont=dict(size=9, color=INK_LIGHT),
                gridcolor="#DDD8CE",
                linecolor="#DDD8CE",
            ),
            angularaxis=dict(
                tickfont=dict(size=12, color=INK, family="Outfit, sans-serif"),
                gridcolor="#DDD8CE",
                linecolor="#DDD8CE",
            ),
        ),
        paper_bgcolor=STONE,
        plot_bgcolor=STONE,
        margin=dict(l=48, r=48, t=48, b=48),
        height=380,
        showlegend=False,
        font=dict(family="Outfit, sans-serif"),
    )
    return fig, factors


def range_52w_chart(d: dict) -> go.Figure | None:
    """
    Vertical 52-week range graphic — Maison aesthetic.
    Thin central stem + fat body (low→current or current→high)
    + floating price label + zone shading.
    """
    low   = d.get("w52_low")
    high  = d.get("w52_high")
    price = d.get("price")
    cur   = cur_sym(d.get("currency", "USD"))
    dist_low  = d.get("dist_52w_low")   # fraction above low
    dist_high = d.get("dist_52w_high")  # fraction below high (negative)

    if not low or not high or not price or high <= low:
        return None

    span  = high - low
    p_pct = (price - low) / span * 100   # 0–100 position within range

    # Colour: green top quarter, red bottom quarter, gold middle
    if p_pct >= 66:
        price_color  = RISE
        zone_label   = "Upper Zone"
        zone_bgcolor = f"rgba(77,124,91,0.06)"
    elif p_pct <= 33:
        price_color  = FALL
        zone_label   = "Lower Zone"
        zone_bgcolor = f"rgba(148,72,72,0.05)"
    else:
        price_color  = GOLD
        zone_label   = "Mid Zone"
        zone_bgcolor = f"rgba(182,157,95,0.06)"

    fig = go.Figure()

    PAD = span * 0.18   # vertical padding

    # ── Zone background rect ──────────────────────────────────────
    fig.add_shape(type="rect",
        x0=0.25, x1=0.75,
        y0=low - PAD * 0.4, y1=high + PAD * 0.4,
        fillcolor=zone_bgcolor,
        line=dict(width=0),
        layer="below",
    )

    # ── Full range stem (thin, gold-pale) ─────────────────────────
    fig.add_shape(type="line",
        x0=0.5, x1=0.5, y0=low, y1=high,
        line=dict(color=GOLD_PALE, width=2),
        layer="below",
    )

    # ── Range body: shaded bar low→price ─────────────────────────
    # Gradient effect via stacked thin bars
    steps = 40
    for i in range(steps):
        y0_s = low  + (price - low) * (i / steps)
        y1_s = low  + (price - low) * ((i + 1) / steps)
        alpha = 0.08 + (i / steps) * 0.22
        r, g, b = (int(price_color.lstrip("#")[j:j+2], 16) for j in (0, 2, 4))
        fig.add_shape(type="rect",
            x0=0.36, x1=0.64,
            y0=y0_s, y1=y1_s,
            fillcolor=f"rgba({r},{g},{b},{alpha:.2f})",
            line=dict(width=0),
            layer="below",
        )

    # ── Tick marks at Low and High ────────────────────────────────
    for yval in [low, high]:
        fig.add_shape(type="line",
            x0=0.36, x1=0.64, y0=yval, y1=yval,
            line=dict(color=INK_LIGHT, width=1.5, dash="solid"),
        )

    # ── Current price thick horizontal bar ───────────────────────
    fig.add_shape(type="line",
        x0=0.28, x1=0.72, y0=price, y1=price,
        line=dict(color=price_color, width=3),
    )

    # ── Current price dot ────────────────────────────────────────
    fig.add_trace(go.Scatter(
        x=[0.5], y=[price],
        mode="markers",
        marker=dict(
            size=16, color=price_color,
            line=dict(color=WHITE, width=2.5),
            symbol="circle",
        ),
        showlegend=False,
        hovertemplate=(
            f"<b>Current</b><br>{cur}{price:,.2f}<br>"
            f"Position: {p_pct:.1f}% of range<extra></extra>"
        ),
    ))

    # ── High marker dot ───────────────────────────────────────────
    fig.add_trace(go.Scatter(
        x=[0.5], y=[high],
        mode="markers",
        marker=dict(size=9, color=RISE,
                    symbol="triangle-up",
                    line=dict(color=WHITE, width=1.5)),
        showlegend=False,
        hovertemplate=f"<b>52w High</b><br>{cur}{high:,.2f}<extra></extra>",
    ))

    # ── Low marker dot ────────────────────────────────────────────
    fig.add_trace(go.Scatter(
        x=[0.5], y=[low],
        mode="markers",
        marker=dict(size=9, color=FALL,
                    symbol="triangle-down",
                    line=dict(color=WHITE, width=1.5)),
        showlegend=False,
        hovertemplate=f"<b>52w Low</b><br>{cur}{low:,.2f}<extra></extra>",
    ))

    # ── RIGHT-SIDE labels: High / Current / Low ───────────────────
    # 52w High
    fig.add_annotation(
        x=0.78, y=high, xref="paper" if False else "x", yref="y",
        text=(f"<span style='font-size:10px;color:{INK_LIGHT};letter-spacing:.1em'>"
              f"52W HIGH</span><br>"
              f"<b style='font-size:15px;font-family:Cormorant Garamond,serif;"
              f"color:{RISE}'>{cur}{high:,.2f}</b>"),
        showarrow=False,
        xanchor="left", yanchor="middle",
        font=dict(family="Outfit, sans-serif", size=11, color=INK_MID),
    )
    # Current
    offset = span * 0.0   # no arrow offset needed
    fig.add_annotation(
        x=0.78, y=price, xref="x", yref="y",
        text=(f"<span style='font-size:10px;color:{INK_LIGHT};letter-spacing:.1em'>"
              f"CURRENT</span><br>"
              f"<b style='font-size:18px;font-family:Cormorant Garamond,serif;"
              f"color:{price_color}'>{cur}{price:,.2f}</b>"
              + (f"<br><span style='font-size:10px;color:{price_color}'>"
                 f"+{dist_low*100:.1f}% above low</span>" if dist_low else "")),
        showarrow=False,
        xanchor="left", yanchor="middle",
        font=dict(family="Outfit, sans-serif", size=11),
    )
    # 52w Low
    fig.add_annotation(
        x=0.78, y=low, xref="x", yref="y",
        text=(f"<span style='font-size:10px;color:{INK_LIGHT};letter-spacing:.1em'>"
              f"52W LOW</span><br>"
              f"<b style='font-size:15px;font-family:Cormorant Garamond,serif;"
              f"color:{FALL}'>{cur}{low:,.2f}</b>"),
        showarrow=False,
        xanchor="left", yanchor="middle",
        font=dict(family="Outfit, sans-serif", size=11, color=INK_MID),
    )

    # ── LEFT-SIDE: percentage position bar label ──────────────────
    fig.add_annotation(
        x=0.22, y=price, xref="x", yref="y",
        text=(f"<b style='font-size:22px;font-family:Cormorant Garamond,serif;"
              f"color:{price_color}'>{p_pct:.0f}%</b><br>"
              f"<span style='font-size:9px;color:{INK_LIGHT};letter-spacing:.12em'>"
              f"OF RANGE</span>"),
        showarrow=False,
        xanchor="right", yanchor="middle",
        font=dict(family="Outfit, sans-serif"),
    )

    # ── Thin percentage ruler on the left ─────────────────────────
    # draw the empty portion (above current)
    fig.add_shape(type="rect",
        x0=0.12, x1=0.17,
        y0=price, y1=high,
        fillcolor="#EDE8DF",
        line=dict(width=0),
    )
    # filled portion (below current)
    r2, g2, b2 = (int(price_color.lstrip("#")[j:j+2], 16) for j in (0, 2, 4))
    fig.add_shape(type="rect",
        x0=0.12, x1=0.17,
        y0=low, y1=price,
        fillcolor=f"rgba({r2},{g2},{b2},0.35)",
        line=dict(width=0),
    )

    fig.update_layout(
        paper_bgcolor=STONE,
        plot_bgcolor=STONE,
        height=340,
        margin=dict(l=10, r=10, t=20, b=20),
        xaxis=dict(
            range=[0, 1.55],
            showgrid=False, showticklabels=False,
            zeroline=False, showline=False, fixedrange=True,
        ),
        yaxis=dict(
            range=[low - PAD, high + PAD],
            showgrid=False, showticklabels=False,
            zeroline=False, showline=False, fixedrange=True,
        ),
        showlegend=False,
        font=dict(family="Outfit, sans-serif"),
    )
    return fig


def comparison_chart(all_data: list[dict], metric: str, label: str) -> go.Figure:
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
        d52l_val = d.get("dist_52w_low")
        st.metric("vs 52w Low",
                  f"+{d52l_val*100:.1f}%" if d52l_val is not None else "—",
                  delta=("Near low ⚠" if d52l_val is not None and d52l_val < 0.05 else
                         "Strong cushion" if d52l_val is not None and d52l_val > 0.3 else None),
                  delta_color=("inverse" if d52l_val is not None and d52l_val < 0.05 else
                               "normal" if d52l_val is not None and d52l_val > 0.3 else "off"))
    with k6:
        beta_note = "High β" if beta and beta > 1.5 else ("Defensive" if beta and beta < 0.8 else None)
        st.metric("Beta (β)", f"{beta:.2f}" if beta else "—",
                  delta=beta_note,
                  delta_color="inverse" if beta_note == "High β" else
                  ("normal" if beta_note == "Defensive" else "off"))
    with k7:
        st.metric("Volatility", fmt_pct(vol), delta_color="off")
    with k8:
        d52h_val = d.get("dist_52w_high")
        st.metric("vs 52w High",
                  f"{d52h_val*100:.1f}%" if d52h_val is not None else "—",
                  delta=("At peak 🔝" if d52h_val is not None and abs(d52h_val) < 0.03 else
                         f"{abs(d52h_val)*100:.0f}% off high" if d52h_val else None),
                  delta_color=("normal" if d52h_val is not None and abs(d52h_val) < 0.03 else "off"))

    st.markdown("&nbsp;", unsafe_allow_html=True)

    # ── Charts ──────────────────────────────────────────────────
    r52_fig = range_52w_chart(d)
    if r52_fig is not None:
        col_chart, col_52w, col_income = st.columns([1.1, 0.45, 0.75])
    else:
        col_chart, col_income = st.columns([1.2, 0.8])
        col_52w = None

    with col_chart:
        st.markdown(f'<div class="section-header">Price History · {years}Y</div>',
                    unsafe_allow_html=True)
        st.plotly_chart(
            price_chart(prices, symbol, d.get("currency", "USD"), years),
            use_container_width=True, config={"displayModeBar": False}
        )

    if col_52w is not None:
        with col_52w:
            st.markdown('<div class="section-header">52-Week Range</div>',
                        unsafe_allow_html=True)
            st.plotly_chart(r52_fig, use_container_width=True,
                            config={"displayModeBar": False})

    with col_income:
        st.markdown('<div class="section-header">Income Statement (TTM)</div>',
                    unsafe_allow_html=True)
        st.plotly_chart(
            income_chart(d), use_container_width=True,
            config={"displayModeBar": False}
        )

    # ── Factor Radar + Risk Gauge ────────────────────────────────
    score, grade, color = risk_score(d)
    mdd  = d.get("mdd")
    zscore_val = d.get("zscore")

    radar_fig, factors = factor_radar(d, symbol)
    col_radar, col_risk = st.columns([1, 1])

    with col_radar:
        st.markdown('<div class="section-header">Factor Scorecard</div>',
                    unsafe_allow_html=True)
        st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)
        st.plotly_chart(radar_fig, use_container_width=True,
                        config={"displayModeBar": False})

    with col_risk:
        st.markdown('<div class="section-header">Factor Scores</div>',
                    unsafe_allow_html=True)
        st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)
        # Score bars for each factor
        for fname, fscore in factors.items():
            bar_color = RISE if fscore >= 65 else (FALL if fscore <= 35 else GOLD)
            st.markdown(f"""
            <div style="margin-bottom:14px;">
              <div style="display:flex;justify-content:space-between;
                   margin-bottom:5px;">
                <span style="font-family:Outfit,sans-serif;font-size:11px;
                      color:{INK_MID};font-weight:500;">{fname}</span>
                <span style="font-family:'Cormorant Garamond',serif;font-size:16px;
                      font-weight:600;color:{bar_color};">{fscore}</span>
              </div>
              <div style="height:5px;background:#EDE8DF;border-radius:3px;overflow:hidden;">
                <div style="width:{fscore}%;height:100%;background:{bar_color};
                     border-radius:3px;transition:width .6s ease;"></div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        # Composite Risk
        st.markdown(f"""
        <div style="margin-top:20px;padding:16px 20px;background:{WHITE};
             border:1px solid #DDD8CE;border-radius:12px;">
          <div style="font-size:9px;color:{INK_LIGHT};letter-spacing:.16em;
               text-transform:uppercase;font-family:Outfit,sans-serif;
               margin-bottom:6px;">Composite Risk Profile</div>
          <div style="font-family:'Cormorant Garamond',serif;font-size:24px;
               font-weight:600;color:{color};">{grade} Risk</div>
          <div style="height:6px;background:#EDE8DF;border-radius:3px;
               overflow:hidden;margin-top:10px;">
            <div style="width:{min(score,100)}%;height:100%;
                 background:linear-gradient(90deg,{RISE},{CAUTION},{FALL});
                 border-radius:3px;"></div>
          </div>
          <div style="font-size:11px;color:{INK_LIGHT};font-family:Outfit,sans-serif;
               margin-top:6px;">Score: <b style="color:{color};">{score}/100</b></div>
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
        mdd_val = d.get("mdd")
        deq = d.get("debt_eq")   # already normalised in fetch (not ×100)
        cr  = d.get("current_ratio")
        qr  = d.get("quick_ratio")
        ic  = d.get("ic")
        d52l  = d.get("dist_52w_low")    # % above 52w low  (positive = good)
        d52h  = d.get("dist_52w_high")   # % below 52w high (negative = bearish)
        w52l  = d.get("w52_low")
        w52h  = d.get("w52_high")
        cur_p = d.get("price")

        # Calmar ratio for convexity context
        calmar = None
        prices_list = d.get("prices", [])
        if len(prices_list) > 60 and mdd_val and abs(mdd_val) > 0.001:
            import math
            closes_arr = np.array([p["price"] for p in prices_list], dtype=float)
            log_rets   = np.diff(np.log(closes_arr[closes_arr > 0]))
            ann_ret    = float(np.mean(log_rets)) * 252
            calmar     = round(ann_ret / abs(mdd_val), 2)

        rows = [
            # ── Price Position ──────────────────────────────────────────
            {"Metric": "52w Low",
             "Value" : f"{cur_sym(d.get('currency','USD'))}{w52l:,.2f}" if w52l else "—",
             "Signal": _sig(None),
             "Comment": "Lowest price in past 52 weeks"},
            {"Metric": "Distance to 52w Low",
             "Value" : f"+{d52l*100:.1f}%" if d52l is not None else "—",
             "Signal": _sig("good" if d52l and d52l>0.2
                            else "warn" if d52l and d52l>0.05
                            else "bad" if d52l is not None else None),
             "Comment": ("Well above low — cushion present" if d52l and d52l>0.2
                         else "Near 52w low — watch closely" if d52l and d52l<0.05
                         else "Moderate distance")},
            {"Metric": "52w High",
             "Value" : f"{cur_sym(d.get('currency','USD'))}{w52h:,.2f}" if w52h else "—",
             "Signal": _sig(None),
             "Comment": "Highest price in past 52 weeks"},
            {"Metric": "Distance from 52w High",
             "Value" : f"{d52h*100:.1f}%" if d52h is not None else "—",
             "Signal": _sig("good" if d52h and abs(d52h)<0.05
                            else "warn" if d52h and abs(d52h)<0.2
                            else None),
             "Comment": ("Near all-time high — strong momentum" if d52h and abs(d52h)<0.05
                         else f"{abs(d52h)*100:.0f}% off the high" if d52h else "")},
            # ── Market Risk ─────────────────────────────────────────────
            {"Metric": "Beta (β)",
             "Value" : fmt_num(beta),
             "Signal": _sig("warn" if beta and beta>1.5 else "good" if beta and beta<0.8 else None),
             "Comment": "High sensitivity" if beta and beta>1.5 else "Defensive" if beta and beta<0.8 else "Near-market"},
            {"Metric": "Annualised Volatility",
             "Value" : fmt_pct(vol),
             "Signal": _sig("bad" if vol and vol>0.35 else "good" if vol and vol<0.2 else None),
             "Comment": "Very high swings" if vol and vol>0.35 else "Low volatility" if vol and vol<0.2 else "Moderate"},
            {"Metric": "Max Drawdown",
             "Value" : fmt_pct(mdd_val),
             "Signal": _sig("bad" if mdd_val and abs(mdd_val)>0.5
                            else "warn" if mdd_val and abs(mdd_val)>0.3 else "good"),
             "Comment": "Worst peak-to-trough"},
            {"Metric": "Sharpe Ratio",
             "Value" : fmt_num(sharpe),
             "Signal": _sig("good" if sharpe and sharpe>1.3 else "bad" if sharpe and sharpe<0.8 else None),
             "Comment": "Excellent risk-adj." if sharpe and sharpe>1.3 else "Poor compensation" if sharpe and sharpe<0.8 else ""},
            {"Metric": "Calmar Ratio",
             "Value" : fmt_num(calmar),
             "Signal": _sig("good" if calmar and calmar>1 else "bad" if calmar and calmar<0.3 else None),
             "Comment": ("Strong return/drawdown" if calmar and calmar>1
                         else "Weak return for drawdown risk" if calmar and calmar<0.3 else "")},
            # ── Balance Sheet Risk ───────────────────────────────────────
            {"Metric": "Debt / Equity",
             "Value" : fmt_num(deq),
             "Signal": _sig("bad" if deq and deq>2 else "good" if deq and deq<0.5 else None),
             "Comment": "High leverage" if deq and deq>2 else "Conservative" if deq and deq<0.5 else ""},
            {"Metric": "Current Ratio",
             "Value" : fmt_num(cr),
             "Signal": _sig("good" if cr and cr>1.5 else "bad" if cr and cr<1 else None),
             "Comment": "Strong liquidity" if cr and cr>2 else "Liquidity concern" if cr and cr<1 else ""},
            {"Metric": "Quick Ratio",
             "Value" : fmt_num(qr),
             "Signal": _sig("good" if qr and qr>1.2 else "bad" if qr and qr<0.8 else None),
             "Comment": ""},
            {"Metric": "Interest Coverage",
             "Value" : f"{ic:.1f}×" if ic else "—",
             "Signal": _sig("good" if ic and ic>10 else "bad" if ic and ic<3 else None),
             "Comment": "Very comfortable" if ic and ic>20 else "Debt strain" if ic and ic<3 else ""},
            {"Metric": "Altman Z-Score",
             "Value" : fmt_num(zscore_val),
             "Signal": _sig("good" if zscore_val and zscore_val>3
                            else "bad" if zscore_val and zscore_val<1.8 else "warn"),
             "Comment": ("Safe zone" if zscore_val and zscore_val>3
                         else "Distress zone" if zscore_val and zscore_val<1.8 else "Grey zone")},
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
