"""
STOCK · HAUS — Streamlit Edition
Live Yahoo Finance data via yfinance (server-side, no CORS issues)
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
GRID       = "#E8E3DA"
CAUTION    = "#A08030"
DEPTH      = "#5B6B8A"
WHITE      = "#FFFFFF"

# ═══════════════════════════════════════════════════════════════
# GLOBAL CSS  — matches the Maison aesthetic
# ═══════════════════════════════════════════════════════════════

st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300&family=Outfit:wght@300;400;500;600&display=swap');
  @import url('https://fonts.googleapis.com/icon?family=Material+Icons');

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

  /* ── Sidebar toggle button ── */
  [data-testid="collapsedControl"] {{
    background: {STONE} !important;
    border-radius: 0 8px 8px 0 !important;
    border: 1px solid #DDD8CE !important;
    border-left: none !important;
  }}
  [data-testid="collapsedControl"]:hover {{
    background: {GOLD_PALE} !important;
  }}
  /* Hide the raw ligature text, show nothing — JS injects SVG below */
  [data-testid="collapsedControl"] span {{
    font-size: 0 !important;
    visibility: hidden;
  }}
  /* The injected SVG arrow sits as ::before pseudo via data-attr */
  [data-testid="collapsedControl"]::after {{
    content: "◀◀";
    font-size: 13px;
    color: {GOLD};
    font-family: system-ui, sans-serif;
    letter-spacing: -3px;
    padding-left: 4px;
  }}
</style>
""", unsafe_allow_html=True)

# JS: also watch for sidebar open/closed state and flip the arrow
st.markdown("""
<script>
(function() {{
  function fixToggle() {{
    const btn = document.querySelector('[data-testid="collapsedControl"]');
    if (!btn) return;
    // If sidebar is expanded the button is on the left edge pointing left (close)
    // If collapsed it points right (open) — toggle arrow direction
    const observer = new MutationObserver(() => {{
      const expanded = document.querySelector('[data-testid="stSidebar"]');
      btn.setAttribute('data-open', expanded ? '1' : '0');
    }});
    observer.observe(document.body, {{ childList: true, subtree: true }});
  }}
  if (document.readyState === 'complete') fixToggle();
  else window.addEventListener('load', fixToggle);
}})();
</script>
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
        # No fallback: Quick Ratio needs inventory data (Current Assets - Inventory).
        # Without inventory, computing it yields the same as Current Ratio → misleading.

        # Interest coverage
        ic = None
        if ebitda_val and interest_exp and abs(interest_exp) > 0:
            ic = ebitda_val / abs(interest_exp)

        # Dividends
        div_yield = _safe(info.get("dividendYield")) or 0.0

        # Validate info yield — Yahoo sometimes gives raw value needing /100
        if div_yield and div_yield > 1.0:
            div_yield = div_yield / 100

        # Fallback: compute from actual dividend history (last 12 months only)
        if div_yield == 0.0:
            try:
                divs = tk.dividends
                if divs is not None and not divs.empty and price and price > 0:
                    divs.index = pd.to_datetime(divs.index).tz_localize(None)
                    cutoff = datetime.now() - timedelta(days=366)
                    last_year = divs[divs.index >= cutoff]
                    if not last_year.empty:
                        annual_div = float(last_year.sum())
                        div_yield  = annual_div / price
            except Exception:
                pass

        # Final sanity cap — yield >25% is almost certainly a data error
        if div_yield and div_yield > 0.25:
            div_yield = 0.0

        payout = _safe(info.get("payoutRatio")) or 0.0

        # Altman Z-Score & risk
        zscore = _altman_z_v2(total_assets, retained, ebitda_val, mkt_cap,
                               revenue, cur_assets, cur_liab, total_liab)
        risk   = _compute_risk(hist_close, hist_dates if len(hist_dates) == len(hist_close) else None)

        # ── 6b. 52-week high / low distance ──────────────────────
        w52_low = w52_high = dist_52w_low = dist_52w_high = None
        w52_low_date = w52_high_date = None
        w52_low_days = w52_high_days = None
        try:
            if len(hist_close) >= 20:
                window_closes = hist_close[-252:] if len(hist_close) >= 252 else hist_close
                window_dates  = hist_dates[-252:]  if len(hist_dates)  >= 252 else hist_dates

                low_idx  = int(np.argmin(window_closes))
                high_idx = int(np.argmax(window_closes))

                w52_low  = float(window_closes[low_idx])
                w52_high = float(window_closes[high_idx])

                w52_low_date  = window_dates[low_idx]
                w52_high_date = window_dates[high_idx]

                today = pd.Timestamp.now().normalize()
                w52_low_days  = int((today - pd.Timestamp(w52_low_date)).days)
                w52_high_days = int((today - pd.Timestamp(w52_high_date)).days)

                if price and w52_low > 0:
                    dist_52w_low  = (price - w52_low)  / w52_low
                if price and w52_high > 0:
                    dist_52w_high = (price - w52_high) / w52_high
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
            "zscore"            : zscore,
            **risk,   # includes vol, downside_vol, mdd, sharpe, ulcer_index,
                      # pct_time_under_water, avg/max/median_recovery_days,
                      # avg_tuw_days, recovery_success_ratio, recovery_efficiency, calmar
            "w52_low"       : w52_low,
            "w52_high"      : w52_high,
            "w52_low_date"  : w52_low_date.strftime("%Y-%m-%d")  if w52_low_date  else None,
            "w52_high_date" : w52_high_date.strftime("%Y-%m-%d") if w52_high_date else None,
            "w52_low_days"  : w52_low_days,
            "w52_high_days" : w52_high_days,
            "dist_52w_low"  : dist_52w_low,
            "dist_52w_high" : dist_52w_high,
            "prices"       : prices,
        }
    except Exception as e:
        return {"symbol": symbol, "error": str(e), "prices": []}

def _compute_risk(closes: np.ndarray, dates=None) -> dict:
    """
    Full risk model: vol, MDD, Sharpe + recovery-path metrics.
    Recovery metrics require dates (pd.DatetimeIndex same length as closes).
    """
    empty = {
        "vol": None, "downside_vol": None, "mdd": None, "sharpe": None,
        "ulcer_index": None, "martin_ratio": None, "pct_time_under_water": None,
        "avg_recovery_days": None, "max_recovery_days": None,
        "median_recovery_days": None, "avg_tuw_days": None,
        "recovery_success_ratio": None, "recovery_efficiency": None,
        "calmar": None,
    }
    if closes is None or len(closes) < 60:
        return empty
    closes = np.asarray(closes, dtype=float)
    closes = closes[np.isfinite(closes) & (closes > 0)]
    if len(closes) < 60:
        return empty

    log_ret    = np.diff(np.log(closes))
    daily_vol  = float(np.std(log_ret))
    ann_vol    = daily_vol * np.sqrt(252)
    ann_return = float(np.mean(log_ret)) * 252
    sharpe     = (ann_return - 0.04) / ann_vol if ann_vol > 0 else None

    # Downside vol
    down_rets   = log_ret[log_ret < 0]
    downside_vol = float(np.std(down_rets) * np.sqrt(252)) if len(down_rets) > 5 else None

    # MDD + Ulcer Index + Time Under Water
    peaks      = np.maximum.accumulate(closes)
    dds        = (closes - peaks) / peaks          # drawdown series (≤0)
    mdd        = float(np.min(dds))
    ulcer      = float(np.sqrt(np.mean((dds * 100) ** 2)))
    tuw        = float(np.mean(dds < 0))

    # Calmar
    calmar = round(ann_return / abs(mdd), 2) if mdd and abs(mdd) > 0.001 else None

    # Recovery cycles (only if dates provided)
    avg_rec = max_rec = median_rec = avg_tuw = rec_success = rec_eff = None
    if dates is not None and len(dates) == len(closes):
        try:
            dates_ts = pd.to_datetime(pd.Index(dates)).tz_localize(None)
            underwater = dds < 0
            cycles, in_seg, start = [], False, None
            for i, uw in enumerate(underwater):
                if uw and not in_seg:
                    in_seg, start = True, i
                elif not uw and in_seg:
                    cycles.append((start, i - 1, i))
                    in_seg, start = False, None
            if in_seg and start is not None:
                cycles.append((start, len(closes) - 1, None))

            rows = []
            for seg_s, seg_e, rec_i in cycles:
                pk_i = max(seg_s - 1, 0)
                seg  = closes[seg_s:seg_e + 1]
                if not len(seg):
                    continue
                tr_i  = seg_s + int(np.argmin(seg))
                depth = float(dds[tr_i])
                pk_dt = pd.Timestamp(dates_ts[pk_i])
                tr_dt = pd.Timestamp(dates_ts[tr_i])
                if rec_i is not None:
                    rc_dt   = pd.Timestamp(dates_ts[rec_i])
                    d2rec   = int((rc_dt - tr_dt).days)
                    tuw_tot = int((rc_dt - pk_dt).days)
                    recovered = True
                    eff = abs(depth) / d2rec if d2rec > 0 else None
                else:
                    d2rec = tuw_tot = None
                    recovered = False
                    eff = None
                rows.append({"d2rec": d2rec, "tuw": tuw_tot,
                             "recovered": recovered, "eff": eff})

            if rows:
                df_c = pd.DataFrame(rows)
                rec  = df_c[df_c["recovered"]]
                avg_rec    = float(rec["d2rec"].mean())      if not rec.empty else None
                max_rec    = int(rec["d2rec"].max())         if not rec.empty else None
                median_rec = float(rec["d2rec"].median())    if not rec.empty else None
                avg_tuw    = float(df_c["tuw"].dropna().mean()) if not df_c.empty else None
                rec_success = float(len(rec) / len(df_c))   if len(df_c) > 0 else None
                eff_vals   = rec["eff"].dropna()
                rec_eff    = float(eff_vals.mean()) if not eff_vals.empty else None
        except Exception:
            pass

    # Martin Ratio = Annualised Return / Ulcer Index (like Sharpe but uses Ulcer as risk denominator)
    martin = round(ann_return / (ulcer / 100), 2) if ulcer and ulcer > 0 else None

    return {
        "vol": float(ann_vol),
        "downside_vol": downside_vol,
        "mdd": mdd,
        "sharpe": float(sharpe) if sharpe is not None else None,
        "ulcer_index": ulcer,
        "martin_ratio": martin,
        "pct_time_under_water": tuw,
        "avg_recovery_days": avg_rec,
        "max_recovery_days": max_rec,
        "median_recovery_days": median_rec,
        "avg_tuw_days": avg_tuw,
        "recovery_success_ratio": rec_success,
        "recovery_efficiency": rec_eff,
        "calmar": calmar,
    }

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
        """
        Recovery-path risk model:
        MDD depth + Ulcer Index + Time Under Water + Recovery Success Rate.
        Volatility is secondary — high vol with fast recovery is acceptable.
        """
        scores = []
        mdd = d.get("mdd")
        if mdd is not None:
            scores.append(_clamp(100 + mdd * 120, 0, 100))   # mdd<0; -40% → 52, -80% → 4
        ulcer = d.get("ulcer_index")
        if ulcer is not None:
            scores.append(_clamp(100 - ulcer * 3.5, 0, 100))  # ulcer=20 → 30, ulcer=8 → 72
        tuw = d.get("pct_time_under_water")
        if tuw is not None:
            scores.append(_clamp(100 - tuw * 120, 0, 100))   # 80% TUW → 4
        rec_success = d.get("recovery_success_ratio")
        if rec_success is not None:
            scores.append(_clamp(rec_success * 100, 0, 100))
        avg_rec = d.get("avg_recovery_days")
        if avg_rec is not None:
            scores.append(_clamp(100 - avg_rec / 3, 0, 100))  # 300d → 0, 30d → 90
        # Volatility as secondary tiebreaker
        vol = d.get("vol")
        if vol is not None:
            scores.append(_clamp(100 - vol * 150, 0, 100))   # 65% vol → 2
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
    Smart label placement prevents overlapping when price is near low or high.
    """
    low   = d.get("w52_low")
    high  = d.get("w52_high")
    price = d.get("price")
    cur   = cur_sym(d.get("currency", "USD"))
    dist_low  = d.get("dist_52w_low")
    dist_high = d.get("dist_52w_high")

    if not low or not high or not price or high <= low:
        return None

    span  = high - low
    p_pct = (price - low) / span * 100   # 0–100 position within range

    if p_pct >= 66:
        price_color = RISE
    elif p_pct <= 33:
        price_color = FALL
    else:
        price_color = GOLD

    fig = go.Figure()
    PAD = span * 0.22

    # ── Zone background ───────────────────────────────────────────
    fig.add_shape(type="rect",
        x0=0.25, x1=0.75,
        y0=low - PAD * 0.3, y1=high + PAD * 0.3,
        fillcolor="rgba(182,157,95,0.04)",
        line=dict(width=0), layer="below",
    )

    # ── Full stem ─────────────────────────────────────────────────
    fig.add_shape(type="line",
        x0=0.5, x1=0.5, y0=low, y1=high,
        line=dict(color="#DDD8CE", width=2), layer="below",
    )

    # ── Gradient body low → price ─────────────────────────────────
    steps = 40
    r2, g2, b2 = (int(price_color.lstrip("#")[j:j+2], 16) for j in (0, 2, 4))
    for i in range(steps):
        y0_s = low + (price - low) * (i / steps)
        y1_s = low + (price - low) * ((i + 1) / steps)
        alpha = 0.06 + (i / steps) * 0.24
        fig.add_shape(type="rect",
            x0=0.38, x1=0.62, y0=y0_s, y1=y1_s,
            fillcolor=f"rgba({r2},{g2},{b2},{alpha:.2f})",
            line=dict(width=0), layer="below",
        )

    # ── Tick lines at Low and High ────────────────────────────────
    for yval in [low, high]:
        fig.add_shape(type="line",
            x0=0.38, x1=0.62, y0=yval, y1=yval,
            line=dict(color=INK_LIGHT, width=1.5),
        )

    # ── Current price bar + dot ───────────────────────────────────
    fig.add_shape(type="line",
        x0=0.3, x1=0.7, y0=price, y1=price,
        line=dict(color=price_color, width=3),
    )
    fig.add_trace(go.Scatter(
        x=[0.5], y=[price], mode="markers",
        marker=dict(size=16, color=price_color,
                    line=dict(color=WHITE, width=2.5)),
        showlegend=False,
        hovertemplate=f"<b>Current</b><br>{cur}{price:,.2f}<br>{p_pct:.0f}% of range<extra></extra>",
    ))

    # ── High / Low marker triangles ───────────────────────────────
    fig.add_trace(go.Scatter(
        x=[0.5], y=[high], mode="markers",
        marker=dict(size=9, color=RISE, symbol="triangle-up",
                    line=dict(color=WHITE, width=1.5)),
        showlegend=False,
        hovertemplate=f"<b>52w High</b><br>{cur}{high:,.2f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=[0.5], y=[low], mode="markers",
        marker=dict(size=9, color=FALL, symbol="triangle-down",
                    line=dict(color=WHITE, width=1.5)),
        showlegend=False,
        hovertemplate=f"<b>52w Low</b><br>{cur}{low:,.2f}<extra></extra>",
    ))

    # ── LEFT mini ruler ───────────────────────────────────────────
    fig.add_shape(type="rect", x0=0.12, x1=0.17, y0=price, y1=high,
        fillcolor="#EDE8DF", line=dict(width=0))
    fig.add_shape(type="rect", x0=0.12, x1=0.17, y0=low, y1=price,
        fillcolor=f"rgba({r2},{g2},{b2},0.3)", line=dict(width=0))

    # ── LEFT label: % of range ────────────────────────────────────
    fig.add_annotation(
        x=0.09, y=(low + high) / 2, xref="x", yref="y",
        text=(f"<b style='font-size:22px;font-family:Cormorant Garamond,serif;"
              f"color:{price_color}'>{p_pct:.0f}%</b><br>"
              f"<span style='font-size:9px;color:{INK_LIGHT};letter-spacing:.1em'>OF RANGE</span>"),
        showarrow=False, xanchor="center", yanchor="middle",
    )

    # ── SMART RIGHT-SIDE LABELS ───────────────────────────────────
    # Compute normalised positions (0–1) for collision detection
    norm_high  = 1.0
    norm_price = p_pct / 100
    norm_low   = 0.0

    # Minimum visual gap in normalised units before we push labels apart
    MIN_GAP = 0.18

    # Start with natural y positions, then push apart if too close
    y_high_n  = norm_high
    y_price_n = norm_price
    y_low_n   = norm_low

    if y_high_n - y_price_n < MIN_GAP:
        # price near high → push price label down
        y_high_n  = norm_high
        y_price_n = norm_high - MIN_GAP
    if y_price_n - y_low_n < MIN_GAP:
        # price near low → push price label up
        y_price_n = norm_low + MIN_GAP
        # re-check high collision after pushing up
        if y_high_n - y_price_n < MIN_GAP:
            y_high_n = y_price_n + MIN_GAP

    # Convert back to price space
    def n2p(n): return low + n * span

    y_high_lbl  = n2p(y_high_n)
    y_price_lbl = n2p(y_price_n)
    y_low_lbl   = n2p(y_low_n)

    # Draw connector lines if label moved significantly from actual price
    CONNECTOR_THRESH = span * 0.04
    for actual, label_y, color in [
        (high,  y_high_lbl,  RISE),
        (price, y_price_lbl, price_color),
        (low,   y_low_lbl,   FALL),
    ]:
        if abs(actual - label_y) > CONNECTOR_THRESH:
            fig.add_shape(type="line",
                x0=0.72, x1=0.76, y0=actual, y1=label_y,
                line=dict(color=color, width=1, dash="dot"),
            )

    dist_label = f"+{dist_low*100:.1f}% above low" if dist_low else ""

    annotations = [
        # 52w High
        dict(x=0.79, y=y_high_lbl,
             text=(f"<span style='font-size:9px;color:{INK_LIGHT};letter-spacing:.1em'>"
                   f"52W HIGH</span><br>"
                   f"<b style='font-size:15px;font-family:Cormorant Garamond,serif;"
                   f"color:{RISE}'>{cur}{high:,.2f}</b>"),
             xanchor="left", yanchor="middle"),
        # Current
        dict(x=0.79, y=y_price_lbl,
             text=(f"<span style='font-size:9px;color:{INK_LIGHT};letter-spacing:.1em'>"
                   f"CURRENT</span><br>"
                   f"<b style='font-size:17px;font-family:Cormorant Garamond,serif;"
                   f"color:{price_color}'>{cur}{price:,.2f}</b>"
                   + (f"<br><span style='font-size:9px;color:{price_color}'>{dist_label}</span>"
                      if dist_label else "")),
             xanchor="left", yanchor="middle"),
        # 52w Low
        dict(x=0.79, y=y_low_lbl,
             text=(f"<span style='font-size:9px;color:{INK_LIGHT};letter-spacing:.1em'>"
                   f"52W LOW</span><br>"
                   f"<b style='font-size:15px;font-family:Cormorant Garamond,serif;"
                   f"color:{FALL}'>{cur}{low:,.2f}</b>"),
             xanchor="left", yanchor="middle"),
    ]
    for ann in annotations:
        fig.add_annotation(
            x=ann["x"], y=ann["y"], xref="x", yref="y",
            text=ann["text"], showarrow=False,
            xanchor=ann["xanchor"], yanchor=ann["yanchor"],
            font=dict(family="Outfit, sans-serif", size=11),
        )

    fig.update_layout(
        paper_bgcolor=STONE,
        plot_bgcolor=STONE,
        height=340,
        margin=dict(l=10, r=10, t=20, b=20),
        xaxis=dict(range=[0, 1.62], showgrid=False, showticklabels=False,
                   zeroline=False, showline=False, fixedrange=True),
        yaxis=dict(range=[low - PAD, high + PAD], showgrid=False,
                   showticklabels=False, zeroline=False, showline=False,
                   fixedrange=True),
        showlegend=False,
        font=dict(family="Outfit, sans-serif"),
    )
    return fig


def recovery_dashboard_chart(prices: list[dict], symbol: str, years: int = 5) -> go.Figure:
    """
    Combined subplot:
      Row 1 (60%): Price line + Running Peak (dashed gold)
      Row 2 (40%): Drawdown-from-Peak area chart
    Shared X-axis — eliminates two separate charts.
    """
    from plotly.subplots import make_subplots

    if not prices:
        return go.Figure()

    df = pd.DataFrame(prices)
    df["date"]  = pd.to_datetime(df["date"])
    cutoff = datetime.now() - timedelta(days=years * 365)
    df = df[df["date"] >= cutoff].sort_values("date").reset_index(drop=True)
    if df.empty:
        return go.Figure()

    df["peak"] = df["price"].cummax()
    df["dd"]   = (df["price"] - df["peak"]) / df["peak"] * 100

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.60, 0.40],
        vertical_spacing=0.04,
    )

    # ── Row 1: Price + Running Peak ───────────────────────────────
    first, last = df["price"].iloc[0], df["price"].iloc[-1]
    price_color = RISE if last >= first else FALL
    rgb = ",".join(str(int(price_color.lstrip("#")[i:i+2], 16)) for i in (0, 2, 4))

    fig.add_trace(go.Scatter(
        x=df["date"], y=df["price"],
        mode="lines", name="Price",
        line=dict(color=price_color, width=1.8),
        fill="tozeroy",
        fillcolor=f"rgba({rgb},0.05)",
        hovertemplate=f"<b>{symbol}</b><br>%{{x|%b %d, %Y}}<br>Price: %{{y:,.2f}}<extra></extra>",
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=df["date"], y=df["peak"],
        mode="lines", name="Running Peak",
        line=dict(color=GOLD, width=1.4, dash="dash"),
        hovertemplate="%{x|%b %d}<br>Peak: %{y:,.2f}<extra></extra>",
    ), row=1, col=1)

    # ── Row 2: Drawdown area ──────────────────────────────────────
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["dd"],
        mode="lines", name="Drawdown",
        line=dict(color=FALL, width=1.5),
        fill="tozeroy",
        fillcolor=f"rgba(148,72,72,0.15)",
        hovertemplate="%{x|%b %d}<br>DD: %{y:.1f}%<extra></extra>",
        showlegend=False,
    ), row=2, col=1)

    # Zero line on drawdown
    fig.add_hline(y=0, line=dict(color=GRID, width=1), row=2, col=1)

    fig.update_layout(
        paper_bgcolor=STONE,
        plot_bgcolor=STONE,
        height=420,
        margin=dict(l=10, r=10, t=10, b=20),
        legend=dict(
            orientation="h", x=0, y=1.04,
            font=dict(size=11, color=INK_MID, family="Outfit, sans-serif"),
        ),
        font=dict(family="Outfit, sans-serif"),
        hovermode="x unified",
    )
    # Row 1 axes
    fig.update_xaxes(showgrid=False, showticklabels=False,
                     zeroline=False, row=1, col=1)
    fig.update_yaxes(showgrid=True, gridcolor=GRID, gridwidth=1,
                     tickfont=dict(size=10, color=INK_LIGHT),
                     zeroline=False, row=1, col=1)
    # Row 2 axes
    fig.update_xaxes(showgrid=False, tickfont=dict(size=10, color=INK_LIGHT),
                     zeroline=False, row=2, col=1)
    fig.update_yaxes(showgrid=True, gridcolor=GRID, gridwidth=1,
                     tickfont=dict(size=10, color=INK_LIGHT),
                     ticksuffix="%", zeroline=True, zerolinecolor=GRID,
                     row=2, col=1)
    return fig


def recovery_metrics_html(d: dict, symbol: str) -> str:
    """Summary card with all recovery KPIs — used in Tab 4.
    Hover tooltips via HTML title= attribute on each row label.
    """
    def _fmt_eff(v):
        if v is None: return "—"
        return f"{v*100:.3f}%/day"

    def _fmt_days(v):
        if v is None: return "—"
        if v < 30: return f"{v:.0f}d"
        return f"{v/30:.1f}mo  ({v:.0f}d)"

    # (key, label, formatted_value, tooltip_text)
    rows_data = [
        ("mdd",
         "Max Drawdown",
         fmt_pct(d.get("mdd")),
         "Größter kumulierter Kursverlust vom Hochpunkt bis zum Tiefpunkt — misst das schlimmste Szenario für einen Investor."),
        ("ulcer_index",
         "Ulcer Index",
         fmt_num(d.get("ulcer_index")),
         "Ulcer Index (Peter Martin, 1987): Misst Tiefe UND Dauer von Drawdowns — je länger und tiefer ein Portfolio unter Wasser liegt, desto höher der Wert. Besser als reine Volatilität, da nur Verluste bestraft werden. Werte <5 sind gut, >20 signalisieren anhaltenden Stress."),
        ("martin_ratio",
         "Martin Ratio",
         fmt_num(d.get("martin_ratio")),
         "Martin Ratio = Annualisierte Rendite / Ulcer Index — analoges Konzept zur Sharpe Ratio, jedoch wird statt Volatilität der Ulcer Index als Risikomaß verwendet. Bewertet, wie gut die Rendite den erlebten Drawdown-Stress kompensiert. Höher ist besser; >1.0 gilt als solide."),
        ("pct_time_under_water",
         "Time Under Water",
         fmt_pct(d.get("pct_time_under_water")),
         "Anteil der Handelstage, an denen der Kurs unter seinem letzten Allzeithoch lag. 40%+ bedeutet, der Investor wartete häufig auf Erholung."),
        ("avg_recovery_days",
         "Avg Recovery",
         _fmt_days(d.get("avg_recovery_days")),
         "Durchschnittliche Anzahl Tage vom Tiefpunkt bis zur vollständigen Erholung auf den vorherigen Hochpunkt."),
        ("median_recovery_days",
         "Median Recovery",
         _fmt_days(d.get("median_recovery_days")),
         "Typische Heilungszeit — weniger von Ausreißern beeinflusst als der Durchschnitt."),
        ("max_recovery_days",
         "Max Recovery",
         _fmt_days(d.get("max_recovery_days")),
         "Längste beobachtete Erholungsphase — misst das Worst-Case-Szenario für Geduld."),
        ("avg_tuw_days",
         "Avg TUW Period",
         _fmt_days(d.get("avg_tuw_days")),
         "Durchschnittliche Gesamtdauer einer Drawdown-Episode (vom Hochpunkt bis zur vollständigen Erholung)."),
        ("recovery_success_ratio",
         "Recovery Success",
         fmt_pct(d.get("recovery_success_ratio")),
         "Anteil der Drawdown-Zyklen, die vollständig erholt wurden. <50% bedeutet viele ungelöste Verlustphasen."),
        ("recovery_efficiency",
         "Recovery Efficiency",
         _fmt_eff(d.get("recovery_efficiency")),
         "Drawdown-Tiefe erholt pro Tag (Drawdown% / Erholungstage). Höher = schnellere Heilung relativ zum Schaden."),
        ("calmar",
         "Calmar Ratio",
         fmt_num(d.get("calmar")),
         "Calmar Ratio = Annualisierte Rendite / |Max Drawdown| — bewertet die Rendite relativ zum schlimmsten erlebten Verlust. >1.0 gilt als gut."),
        ("downside_vol",
         "Downside Volatility",
         fmt_pct(d.get("downside_vol")),
         "Standardabweichung nur der negativen Tagesrenditen (annualisiert) — misst das 'schlechte' Risiko ohne positive Schwankungen zu bestrafen."),
    ]

    ampel_rules = {
        "mdd":                   [("bad", lambda x: abs(x)>0.55), ("warn", lambda x: abs(x)>0.30), ("good", lambda x: abs(x)<0.15)],
        "ulcer_index":           [("bad", lambda x: x>20), ("warn", lambda x: x>10), ("good", lambda x: x<5)],
        "martin_ratio":          [("good", lambda x: x>1.5), ("warn", lambda x: x>0.5), ("bad", lambda x: x<=0.5)],
        "pct_time_under_water":  [("bad", lambda x: x>0.60), ("warn", lambda x: x>0.40), ("good", lambda x: x<0.25)],
        "avg_recovery_days":     [("bad", lambda x: x>180), ("warn", lambda x: x>60), ("good", lambda x: x<30)],
        "median_recovery_days":  [("bad", lambda x: x>180), ("warn", lambda x: x>60), ("good", lambda x: x<30)],
        "max_recovery_days":     [("bad", lambda x: x>365), ("warn", lambda x: x>120)],
        "avg_tuw_days":          [("bad", lambda x: x>200), ("warn", lambda x: x>90)],
        "recovery_success_ratio":[("bad", lambda x: x<0.40), ("warn", lambda x: x<0.65), ("good", lambda x: x>=0.75)],
        "recovery_efficiency":   [("good", lambda x: x>0.003), ("warn", lambda x: x>0.001)],
        "calmar":                [("good", lambda x: x>1.0), ("warn", lambda x: x>0.3), ("bad", lambda x: x<=0.3)],
        "downside_vol":          [("bad", lambda x: x>0.30), ("warn", lambda x: x>0.18), ("good", lambda x: x<0.12)],
    }

    def _ampel(key):
        v = d.get(key)
        if v is None: return ""
        for tone, fn in ampel_rules.get(key, []):
            try:
                if fn(v): return _sig(tone) + " "
            except Exception: pass
        return ""

    html_rows = ""
    for i, (key, label, value, tooltip) in enumerate(rows_data):
        sig = _ampel(key)
        bg  = f"background:rgba(182,157,95,0.04);" if i % 2 == 0 else ""
        # ℹ icon with title tooltip
        info = (
            f'<span title="{tooltip}" style="cursor:help;margin-left:5px;'
            f'font-size:10px;color:{GOLD};vertical-align:middle;" >ⓘ</span>'
        )
        html_rows += (
            f'<div style="display:flex;justify-content:space-between;align-items:center;'
            f'padding:7px 12px;border-radius:6px;{bg}">'
            f'<span style="font-size:12px;color:{INK_MID};font-family:Outfit,sans-serif;'
            f'display:flex;align-items:center;">'
            f'{sig}{label}{info if tooltip else ""}</span>'
            f'<span style="font-size:14px;font-weight:600;color:{INK};font-family:Outfit,sans-serif;">'
            f'{value}</span>'
            f'</div>'
        )

    return (
        f'<div style="background:{WHITE};border:1px solid #DDD8CE;border-radius:14px;'
        f'padding:20px 16px;">'
        f'<div style="font-family:Outfit,sans-serif;font-size:10px;letter-spacing:.18em;'
        f'text-transform:uppercase;color:{GOLD};margin-bottom:16px;">Recovery Profile · {symbol}</div>'
        f'{html_rows}'
        f'</div>'
    )


def recovery_cycle_bar_chart(prices: list[dict], years: int = 10) -> go.Figure:
    """Bar chart: one bar per drawdown cycle, coloured by recovery status."""
    if not prices:
        return go.Figure()

    df = pd.DataFrame(prices)
    df["date"] = pd.to_datetime(df["date"])
    cutoff = datetime.now() - timedelta(days=years * 365)
    df = df[df["date"] >= cutoff].sort_values("date").reset_index(drop=True)
    if df.empty:
        return go.Figure()

    closes = df["price"].values.astype(float)
    dates  = df["date"].values

    peaks = np.maximum.accumulate(closes)
    dds   = (closes - peaks) / peaks
    under = dds < 0

    cycles, in_seg, start = [], False, None
    for i, uw in enumerate(under):
        if uw and not in_seg:
            in_seg, start = True, i
        elif not uw and in_seg:
            cycles.append((start, i - 1, i))
            in_seg, start = False, None
    if in_seg and start is not None:
        cycles.append((start, len(closes) - 1, None))

    labels, heights, colors, hover = [], [], [], []
    for seg_s, seg_e, rec_i in cycles:
        pk_i  = max(seg_s - 1, 0)
        seg   = closes[seg_s:seg_e + 1]
        tr_i  = seg_s + int(np.argmin(seg))
        depth = abs(float(dds[tr_i])) * 100
        pk_dt = pd.Timestamp(dates[pk_i]).strftime("%Y-%m")
        if rec_i is not None:
            tr_dt  = pd.Timestamp(dates[tr_i])
            rc_dt  = pd.Timestamp(dates[rec_i])
            d2rec  = int((rc_dt - tr_dt).days)
            labels.append(pk_dt)
            heights.append(d2rec)
            colors.append(f"rgba(77,124,91,0.80)")
            hover.append(f"Peak: {pk_dt}<br>DD: -{depth:.1f}%<br>Recovery: {d2rec}d")
        else:
            labels.append(pk_dt)
            heights.append(int((pd.Timestamp(dates[-1]) - pd.Timestamp(dates[tr_i])).days))
            colors.append(f"rgba(148,72,72,0.70)")
            hover.append(f"Peak: {pk_dt}<br>DD: -{depth:.1f}%<br>⚠ Not yet recovered")

    if not labels:
        return go.Figure()

    fig = go.Figure(go.Bar(
        x=labels, y=heights,
        marker_color=colors,
        marker_line_width=0,
        text=[f"{h}d" for h in heights],
        textposition="outside",
        textfont=dict(size=9, color=INK_MID),
        customdata=hover,
        hovertemplate="%{customdata}<extra></extra>",
    ))

    # Legend annotation
    fig.add_annotation(
        x=0.01, y=1.06, xref="paper", yref="paper",
        text=(f"<span style='color:rgba(77,124,91,0.9)'>■</span> Recovered  "
              f"<span style='color:rgba(148,72,72,0.9)'>■</span> Still under water"),
        showarrow=False, xanchor="left",
        font=dict(size=11, color=INK_MID, family="Outfit, sans-serif"),
    )

    fig.update_layout(
        paper_bgcolor=STONE, plot_bgcolor=STONE,
        height=280,
        margin=dict(l=10, r=10, t=36, b=20),
        showlegend=False,
        xaxis=dict(showgrid=False, tickangle=-40,
                   tickfont=dict(size=10, color=INK_LIGHT)),
        yaxis=dict(showgrid=True, gridcolor=GRID,
                   tickfont=dict(size=10, color=INK_LIGHT),
                   title="Days to recover",
                   title_font=dict(size=10, color=INK_MID)),
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
    """
    Recovery-Path Risk Score (0 = low risk, 100 = high risk).
    Mirrors the Radar 'Risk' factor but expressed as a penalty score.
    Primary: MDD depth, Time Under Water, Recovery Speed, Recovery Success.
    Secondary: Volatility, Beta, Balance Sheet.
    """
    score = 0

    # ── MDD depth (primary, max 22pts) ───────────────────────────
    mdd = d.get("mdd")
    if mdd is not None:
        if abs(mdd) > 0.60:   score += 22
        elif abs(mdd) > 0.40: score += 14
        elif abs(mdd) > 0.25: score += 7

    # ── Ulcer Index — depth × duration (max 18pts) ───────────────
    ulcer = d.get("ulcer_index")
    if ulcer is not None:
        if ulcer > 25:   score += 18
        elif ulcer > 15: score += 10
        elif ulcer > 8:  score += 5

    # ── Time Under Water (max 16pts) ─────────────────────────────
    tuw = d.get("pct_time_under_water")
    if tuw is not None:
        if tuw > 0.70:   score += 16
        elif tuw > 0.50: score += 9
        elif tuw > 0.35: score += 4

    # ── Recovery success rate (max 14pts) ────────────────────────
    rec_success = d.get("recovery_success_ratio")
    if rec_success is not None:
        if rec_success < 0.40:   score += 14
        elif rec_success < 0.65: score += 7

    # ── Avg recovery days (max 12pts) ────────────────────────────
    avg_rec = d.get("avg_recovery_days")
    if avg_rec is not None:
        if avg_rec > 200:  score += 12
        elif avg_rec > 90: score += 7
        elif avg_rec > 45: score += 3

    # ── Balance sheet (max 10pts) ────────────────────────────────
    zscore = d.get("zscore")
    if zscore is not None:
        if zscore < 1.8:  score += 10
        elif zscore < 3.0: score += 5

    deq = d.get("debt_eq")
    if deq is not None:
        if deq > 3.0:   score += 8
        elif deq > 1.5: score += 4

    # ── Volatility secondary (max 8pts) ──────────────────────────
    vol = d.get("vol")
    if vol is not None:
        if vol > 0.55:   score += 8
        elif vol > 0.35: score += 4

    score = min(score, 100)
    if score <= 18:   return score, "Low",      RISE
    if score <= 38:   return score, "Moderate", GOLD
    if score <= 58:   return score, "Elevated", CAUTION
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
    tabs = st.tabs(["📐 Valuation", "📊 Profitability", "🛡  Risk Metrics", "🔄 Recovery Dashboard"])

    with tabs[0]:
        ev = d.get("ev"); evr = d.get("ev_rev"); eve = d.get("ev_ebitda")
        rows = [
            {"Metric": "Enterprise Value",
             "Value": fmt_big(ev, cur), "Signal": _sig(None),
             "Comment": "Total firm value incl. debt"},
            {"Metric": "Trailing P/E",
             "Value": f"{pe:.1f}×" if pe else "—",
             "Signal": _sig("good" if pe and pe < 12 else "warn" if pe and pe > 35 else "bad" if pe and pe > 60 else None),
             "Comment": ("Attractive valuation" if pe and pe < 12
                         else "Growth premium" if pe and pe > 35
                         else "Extreme premium" if pe and pe > 60 else "Fair range")},
            {"Metric": "EV / Revenue",
             "Value": f"{evr:.1f}×" if evr else "—",
             "Signal": _sig("good" if evr and evr < 2 else "warn" if evr and evr > 10 else None),
             "Comment": ("Cheap on revenue" if evr and evr < 2
                         else "Premium revenue multiple" if evr and evr > 10 else "")},
            {"Metric": "EV / EBITDA",
             "Value": f"{eve:.1f}×" if eve else "—",
             "Signal": _sig("good" if eve and eve < 10 else "warn" if eve and eve > 25 else "bad" if eve and eve > 45 else None),
             "Comment": ("Undervalued on EBITDA" if eve and eve < 10
                         else "Growth priced in" if eve and eve > 25 else "")},
            {"Metric": "Price / Book",
             "Value": f"{pb:.1f}×" if pb else "—",
             "Signal": _sig("good" if pb and pb < 1 else "warn" if pb and pb > 5 else None),
             "Comment": "Below book value" if pb and pb < 1 else "High P/B" if pb and pb > 5 else ""},
            {"Metric": "Price / Sales",
             "Value": f"{ps:.1f}×" if ps else "—",
             "Signal": _sig("good" if ps and ps < 1.5 else "warn" if ps and ps > 8 else None),
             "Comment": ("Cheap on sales" if ps and ps < 1.5
                         else "Premium P/S" if ps and ps > 8 else "")},
            {"Metric": "Dividend Yield",
             "Value": fmt_pct(dy),
             "Signal": _sig("good" if dy and dy > 0.03 else "warn" if dy and dy > 0.01 else None),
             "Comment": ("High yield" if dy and dy > 0.05
                         else "Moderate yield" if dy and dy > 0.03
                         else "Low yield" if dy and dy > 0 else "No dividend")},
        ]
        _render_table(rows)

    with tabs[1]:
        pm  = d.get("profit_margin")
        roa = d.get("roa")
        roe = d.get("roe")
        rev = d.get("revenue"); ni = d.get("net_income"); ebitda = d.get("ebitda")
        gp  = d.get("gross_profit")
        rows = [
            {"Metric": "Profit Margin",
             "Value": fmt_pct(pm),
             "Signal": _sig("good" if pm and pm > 0.20 else
                            "warn" if pm and pm > 0.05 else
                            "bad"  if pm is not None and pm <= 0.05 else None),
             "Comment": ("Exceptional margin" if pm and pm > 0.25
                         else "Healthy margin" if pm and pm > 0.10
                         else "Thin margin" if pm and pm > 0 else "Loss-making")},
            {"Metric": "Return on Assets",
             "Value": fmt_pct(roa),
             "Signal": _sig("good" if roa and roa > 0.10 else
                            "warn" if roa and roa > 0.04 else
                            "bad"  if roa is not None and roa <= 0 else None),
             "Comment": ("Strong asset returns" if roa and roa > 0.10
                         else "Negative ROA" if roa and roa < 0 else "")},
            {"Metric": "Return on Equity",
             "Value": fmt_pct(roe),
             "Signal": _sig("good" if roe and roe > 0.20 else
                            "warn" if roe and roe > 0.08 else
                            "bad"  if roe is not None and roe <= 0 else None),
             "Comment": ("Excellent ROE" if roe and roe > 0.20
                         else "Negative ROE" if roe and roe < 0 else "")},
            {"Metric": "Gross Profit",
             "Value": fmt_big(gp, cur), "Signal": _sig(None), "Comment": ""},
            {"Metric": "Revenue (TTM)",
             "Value": fmt_big(rev, cur), "Signal": _sig(None), "Comment": ""},
            {"Metric": "Net Income (TTM)",
             "Value": fmt_big(ni, cur),
             "Signal": _sig("good" if ni and ni > 0 else "bad" if ni and ni < 0 else None),
             "Comment": "Profitable" if ni and ni > 0 else "Loss-making" if ni and ni < 0 else ""},
            {"Metric": "EBITDA",
             "Value": fmt_big(ebitda, cur), "Signal": _sig(None), "Comment": ""},
        ]
        _render_table(rows)

    with tabs[2]:
        mdd_val = d.get("mdd")
        deq = d.get("debt_eq")   # already normalised in fetch (not ×100)
        cr  = d.get("current_ratio")
        qr  = d.get("quick_ratio")
        ic  = d.get("ic")
        # Recovery-path metrics (pre-computed in _compute_risk)
        ulcer      = d.get("ulcer_index")
        tuw        = d.get("pct_time_under_water")
        avg_rec    = d.get("avg_recovery_days")
        median_rec = d.get("median_recovery_days")
        max_rec    = d.get("max_recovery_days")
        rec_suc    = d.get("recovery_success_ratio")
        rec_eff    = d.get("recovery_efficiency")
        dv         = d.get("downside_vol")
        d52l  = d.get("dist_52w_low")
        d52h  = d.get("dist_52w_high")
        w52l  = d.get("w52_low")
        w52h  = d.get("w52_high")
        cur_p = d.get("price")
        low_date  = d.get("w52_low_date")
        high_date = d.get("w52_high_date")
        low_days  = d.get("w52_low_days")
        high_days = d.get("w52_high_days")

        def _days_ago(n):
            if n is None: return ""
            if n == 0:    return "today"
            if n == 1:    return "yesterday"
            if n < 30:    return f"{n}d ago"
            if n < 365:   return f"{n//30}mo ago"
            return f"{n//365}y {(n%365)//30}mo ago"

        # Calmar ratio — now pre-computed in _compute_risk
        calmar = d.get("calmar")

        rows = [
            # ── Price Position ──────────────────────────────────────────
            {"Metric": "52w Low",
             "Value" : f"{cur_sym(d.get('currency','USD'))}{w52l:,.2f}" if w52l else "—",
             "Signal": _sig(None),
             "Comment": (f"{low_date}  ·  {_days_ago(low_days)}" if low_date else
                         "Lowest price in past 52 weeks")},
            {"Metric": "Distance to 52w Low",
             "Value" : f"+{d52l*100:.1f}%" if d52l is not None else "—",
             # INVERTED: near low = buying opportunity = GREEN
             "Signal": _sig("good" if d52l is not None and d52l < 0.10
                            else "warn" if d52l is not None and d52l < 0.25
                            else None),
             "Comment": ("Near 52w low — potential entry" if d52l is not None and d52l < 0.10
                         else "Moderate distance from low" if d52l is not None and d52l < 0.25
                         else "Well above 52w low")},
            {"Metric": "52w High",
             "Value" : f"{cur_sym(d.get('currency','USD'))}{w52h:,.2f}" if w52h else "—",
             "Signal": _sig(None),
             "Comment": (f"{high_date}  ·  {_days_ago(high_days)}" if high_date else
                         "Highest price in past 52 weeks")},
            {"Metric": "Distance from 52w High",
             "Value" : f"{d52h*100:.1f}%" if d52h is not None else "—",
             # Near high = momentum/strength = GREEN; far below = WARN
             "Signal": _sig("good" if d52h is not None and abs(d52h) < 0.05
                            else "warn" if d52h is not None and abs(d52h) > 0.35
                            else None),
             "Comment": ("Near 52w high — strong momentum" if d52h is not None and abs(d52h) < 0.05
                         else f"{abs(d52h)*100:.0f}% off the high" if d52h else "")},
            # ── Market Risk ─────────────────────────────────────────────
            {"Metric": "Beta (β)",
             "Value" : fmt_num(beta),
             "Signal": _sig("bad"  if beta and beta > 2.0
                            else "warn" if beta and beta > 1.3
                            else "good" if beta and beta < 0.7 else None),
             "Comment": ("Very high market sensitivity" if beta and beta > 2.0
                         else "Above-market exposure" if beta and beta > 1.3
                         else "Low correlation / defensive" if beta and beta < 0.7
                         else "Near-market" if beta is not None else "")},
            {"Metric": "Annualised Volatility",
             "Value" : fmt_pct(vol),
             "Signal": _sig("bad"  if vol and vol > 0.50
                            else "warn" if vol and vol > 0.30
                            else "good" if vol and vol < 0.18 else None),
             "Comment": ("Very high swings — speculative" if vol and vol > 0.50
                         else "Elevated volatility" if vol and vol > 0.30
                         else "Low volatility" if vol and vol < 0.18 else "Moderate")},
            {"Metric": "Max Drawdown",
             "Value" : fmt_pct(mdd_val),
             "Signal": _sig("bad"  if mdd_val and abs(mdd_val) > 0.55
                            else "warn" if mdd_val and abs(mdd_val) > 0.30
                            else "good" if mdd_val is not None and abs(mdd_val) < 0.15 else None),
             "Comment": ("Severe peak-to-trough loss" if mdd_val and abs(mdd_val) > 0.55
                         else "Worst peak-to-trough")},
            {"Metric": "Sharpe Ratio",
             "Value" : fmt_num(sharpe),
             "Signal": _sig("good" if sharpe and sharpe > 1.3
                            else "warn" if sharpe and sharpe > 0.6
                            else "bad" if sharpe is not None else None),
             "Comment": ("Excellent risk-adj. return" if sharpe and sharpe > 1.3
                         else "Poor return per unit risk" if sharpe and sharpe < 0.6 else "")},
            {"Metric": "Calmar Ratio",
             "Value" : fmt_num(calmar),
             "Signal": _sig("good" if calmar and calmar > 1.0
                            else "warn" if calmar and calmar > 0.3
                            else "bad" if calmar is not None else None),
             "Comment": ("Strong return/drawdown profile" if calmar and calmar > 1.0
                         else "Weak return for drawdown risk" if calmar and calmar < 0.3 else "")},
            {"Metric": "Downside Volatility",
             "Value" : fmt_pct(dv),
             "Signal": _sig("bad"  if dv and dv > 0.30
                            else "warn" if dv and dv > 0.18
                            else "good" if dv is not None and dv < 0.12 else None),
             "Comment": "Negative-return volatility only"},
            # ── Balance Sheet Risk ───────────────────────────────────────
            {"Metric": "Debt / Equity",
             "Value" : fmt_num(deq),
             "Signal": _sig("bad"  if deq and deq > 3.0
                            else "warn" if deq and deq > 1.5
                            else "good" if deq is not None and deq < 0.4 else None),
             "Comment": ("Very high leverage" if deq and deq > 3.0
                         else "Elevated leverage" if deq and deq > 1.5
                         else "Conservative balance sheet" if deq is not None and deq < 0.4 else "")},
            {"Metric": "Current Ratio",
             "Value" : fmt_num(cr),
             "Signal": _sig("good" if cr and cr > 2.0
                            else "warn" if cr and cr > 1.0
                            else "bad" if cr is not None else None),
             "Comment": ("Strong liquidity" if cr and cr > 2.0
                         else "Liquidity concern" if cr and cr < 1.0 else "Adequate")},
            {"Metric": "Quick Ratio",
             "Value" : fmt_num(qr) if qr else "—",
             "Signal": _sig("good" if qr and qr > 1.2
                            else "warn" if qr and qr > 0.7
                            else "bad" if qr is not None else None),
             "Comment": ("Strong acid test" if qr and qr > 1.2
                         else "Below 1 — watch closely" if qr and qr < 0.7 else "")},
            {"Metric": "Interest Coverage",
             "Value" : f"{ic:.1f}×" if ic else "—",
             "Signal": _sig("good" if ic and ic > 8
                            else "warn" if ic and ic > 3
                            else "bad" if ic is not None else None),
             "Comment": ("Comfortable — debt well covered" if ic and ic > 8
                         else "Debt strain — coverage thin" if ic and ic < 3 else "Adequate")},
            {"Metric": "Altman Z-Score",
             "Value" : fmt_num(zscore_val),
             "Signal": _sig("good" if zscore_val and zscore_val > 3.0
                            else "warn" if zscore_val and zscore_val > 1.8
                            else "bad" if zscore_val is not None else None),
             "Comment": ("Safe zone (>3.0)" if zscore_val and zscore_val > 3.0
                         else "Grey zone (1.8–3.0)" if zscore_val and zscore_val > 1.8
                         else "Distress zone (<1.8)" if zscore_val is not None else "")},
        ]
        _render_table(rows)

    # ── Tab 4: Recovery Dashboard ────────────────────────────────
    with tabs[3]:
        rec_years = max(years, 5)
        st.markdown(
            f'<div class="section-header">Price vs Running Peak · Drawdown from Peak · {rec_years}Y</div>',
            unsafe_allow_html=True)
        st.markdown('<div class="gold-rule" style="margin-bottom:12px;"></div>',
                    unsafe_allow_html=True)

        col_chart_r, col_summary = st.columns([1.5, 1.0])
        with col_chart_r:
            st.plotly_chart(
                recovery_dashboard_chart(prices, symbol, rec_years),
                use_container_width=True, config={"displayModeBar": False}
            )
            st.markdown(
                '<div class="section-header" style="margin-top:8px;">Recovery Days by Cycle</div>',
                unsafe_allow_html=True)
            st.plotly_chart(
                recovery_cycle_bar_chart(prices, rec_years),
                use_container_width=True, config={"displayModeBar": False}
            )
        with col_summary:
            st.markdown(recovery_metrics_html(d, symbol), unsafe_allow_html=True)

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

    # Bar-chart grid — 3 columns × 3 rows
    col_charts = st.columns(3)
    metrics_viz = [
        # Row 1: Valuation + Quality
        ("pe",            "P/E Ratio"),
        ("profit_margin", "Profit Margin"),
        ("roe",           "Return on Equity"),
        # Row 2: Risk profile
        ("vol",           "Annualised Volatility"),
        ("mdd",           "Max Drawdown"),
        ("ulcer_index",   "Ulcer Index"),
        # Row 3: Recovery
        ("pct_time_under_water",  "Time Under Water"),
        ("avg_recovery_days",     "Avg Recovery Days"),
        ("recovery_success_ratio","Recovery Success Rate"),
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
        sc, grade, _ = risk_score(d)
        avg_rec = d.get("avg_recovery_days")
        rows.append({
            "Ticker"        : d["symbol"],
            "Name"          : (d.get("name") or d["symbol"])[:28],
            "Price"         : f'{cur}{d["price"]:,.2f}' if d.get("price") else "—",
            "Mkt Cap"       : fmt_big(d.get("mkt_cap"), cur),
            "P/E"           : f'{d["pe"]:.1f}×'       if d.get("pe")       else "—",
            "P/B"           : f'{d["pb"]:.1f}×'       if d.get("pb")       else "—",
            "Div Yield"     : fmt_pct(d.get("div_yield")),
            "Profit Mg."    : fmt_pct(d.get("profit_margin")),
            "ROE"           : fmt_pct(d.get("roe")),
            "EV/EBITDA"     : f'{d["ev_ebitda"]:.1f}×' if d.get("ev_ebitda") else "—",
            "Beta"          : fmt_num(d.get("beta")),
            "D/E"           : fmt_num(d.get("debt_eq")),   # already normalised in fetch
            "Volatility"    : fmt_pct(d.get("vol")),
            "MDD"           : fmt_pct(d.get("mdd")),
            "Ulcer"         : fmt_num(d.get("ulcer_index")),
            "Avg Rec (d)"   : f"{avg_rec:.0f}" if avg_rec else "—",
            "Rec Success"   : fmt_pct(d.get("recovery_success_ratio")),
            "Risk Score"    : f"{grade} ({sc})",
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
