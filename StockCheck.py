"""
STOCK · HAUS — Streamlit Edition
Live Yahoo Finance data via yfinance (server-side, no CORS issues)

Enhanced version:
- Recovery-/Path-Risk oriented risk model
- Volatility is treated as secondary signal
- Drawdown depth + duration + recovery quality are central
- Integrated Recovery Dashboard
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
# DESIGN TOKENS
# ═══════════════════════════════════════════════════════════════

GOLD = "#B69D5F"
GOLD_DEEP = "#9A8243"
GOLD_PALE = "#EDE4CC"
STONE = "#F5F1EB"
INK = "#1E1E1E"
INK_MID = "#6E6E6E"
INK_LIGHT = "#9C9C9C"
RISE = "#4D7C5B"
FALL = "#944848"
CAUTION = "#A08030"
DEPTH = "#5B6B8A"
WHITE = "#FFFFFF"
GRID = "#DDD8CE"

# ═══════════════════════════════════════════════════════════════
# GLOBAL CSS
# ═══════════════════════════════════════════════════════════════

st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300&family=Outfit:wght@300;400;500;600&display=swap');

  .stApp {{ background: {STONE}; }}
  [data-testid="stSidebar"] {{ background: {WHITE}; border-right: 1px solid #DDD8CE; }}
  [data-testid="stSidebar"] * {{ font-family: 'Outfit', sans-serif; }}

  h1, h2, h3 {{ font-family: 'Cormorant Garamond', Georgia, serif !important; color: {INK}; }}
  p, span, div {{ font-family: 'Outfit', sans-serif; }}

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

  [data-testid="stDataFrame"] {{ border-radius: 12px; overflow: hidden; }}

  .gold-rule {{
    height: 1px;
    background: linear-gradient(90deg, {GOLD}, {GOLD_PALE}, transparent);
    margin: 12px 0 24px 0;
  }}

  .section-header {{
    font-family: 'Outfit', sans-serif;
    font-size: 10px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    font-weight: 600;
    color: {GOLD};
    margin-bottom: 8px;
  }}

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

  .summary-card {{
    background: {WHITE};
    border: 1px solid #DDD8CE;
    border-radius: 14px;
    padding: 20px 24px;
    min-height: 300px;
  }}
  .summary-title {{
    font-family: 'Outfit', sans-serif;
    font-size: 14px;
    letter-spacing: .04em;
    color: {INK};
    font-weight: 700;
    margin-bottom: 18px;
  }}
  .summary-row {{
    display:flex;
    justify-content:space-between;
    align-items:baseline;
    padding:4px 0;
  }}
  .summary-label {{
    font-size:12px;
    color:{INK_MID};
    font-family:'Outfit', sans-serif;
  }}
  .summary-value {{
    font-size:14px;
    color:{INK};
    font-weight:700;
    font-family:'Outfit', sans-serif;
  }}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def _search_session() -> requests.Session:
    import random
    ua_pool = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    ]
    session = requests.Session()
    session.headers.update({
        "User-Agent": random.choice(ua_pool),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
    })
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    retry = Retry(
        total=3,
        backoff_factor=1.2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session

def _safe(val):
    try:
        v = float(val)
        return None if (np.isnan(v) or np.isinf(v)) else v
    except Exception:
        return None

def _row(df: pd.DataFrame, *keys):
    for k in keys:
        for label in df.index:
            if k.lower() in str(label).lower():
                row = df.loc[label]
                for col in df.columns:
                    v = _safe(row[col])
                    if v is not None:
                        return v
    return None

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
    if a >= 1e12:
        return f"{cur}{v/1e12:.2f}T"
    if a >= 1e9:
        return f"{cur}{v/1e9:.2f}B"
    if a >= 1e6:
        return f"{cur}{v/1e6:.2f}M"
    return f"{cur}{v:,.0f}"

def cur_sym(c: str) -> str:
    return {
        "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "CHF": "Fr.",
        "HKD": "HK$", "CAD": "C$", "AUD": "A$", "INR": "₹", "CNY": "¥"
    }.get(c, c)

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
            "Signal": st.column_config.TextColumn("", width="small"),
            "Metric": st.column_config.TextColumn("Metric", width="medium"),
            "Value": st.column_config.TextColumn("Value", width="small"),
            "Comment": st.column_config.TextColumn("Assessment"),
        },
    )

def _base_layout(height=260):
    return dict(
        font_family="Outfit, sans-serif",
        paper_bgcolor=STONE,
        plot_bgcolor=STONE,
        margin=dict(l=10, r=10, t=40, b=20),
        height=height,
        xaxis=dict(
            showgrid=False,
            tickfont=dict(size=10, color=INK_LIGHT),
            zeroline=False,
            showline=False
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=GRID,
            gridwidth=1,
            tickfont=dict(size=10, color=INK_LIGHT),
            zeroline=False,
            showline=False
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            x=0,
            font=dict(size=11, color=INK_MID),
        ),
    )

# ═══════════════════════════════════════════════════════════════
# RECOVERY CORE
# ═══════════════════════════════════════════════════════════════

def extract_recovery_cycles_from_closes(closes: np.ndarray, dates) -> pd.DataFrame:
    if closes is None or len(closes) < 3 or dates is None or len(dates) != len(closes):
        return pd.DataFrame()

    closes = np.asarray(closes, dtype=float)
    dates = pd.to_datetime(pd.Index(dates))

    peaks = np.maximum.accumulate(closes)
    drawdowns = (closes - peaks) / peaks
    underwater = drawdowns < 0

    segments = []
    in_seg = False
    start = None

    for i, uw in enumerate(underwater):
        if uw and not in_seg:
            in_seg = True
            start = i
        elif not uw and in_seg:
            segments.append((start, i - 1, i))
            in_seg = False
            start = None

    if in_seg and start is not None:
        segments.append((start, len(closes) - 1, None))

    cycles = []

    for seg_start, seg_end, recovery_idx in segments:
        peak_idx = max(seg_start - 1, 0)
        peak_price = closes[peak_idx]

        segment_prices = closes[seg_start:seg_end + 1]
        if len(segment_prices) == 0:
            continue

        rel_trough_idx = int(np.argmin(segment_prices))
        trough_idx = seg_start + rel_trough_idx
        trough_price = closes[trough_idx]
        dd_depth = (trough_price - peak_price) / peak_price if peak_price > 0 else np.nan

        peak_date = pd.Timestamp(dates[peak_idx])
        trough_date = pd.Timestamp(dates[trough_idx])

        if recovery_idx is not None:
            recovery_date = pd.Timestamp(dates[recovery_idx])
            days_to_recover = int((recovery_date - trough_date).days)
            time_under_water = int((recovery_date - peak_date).days)
            recovered = True
            recovery_efficiency = abs(dd_depth) / days_to_recover if days_to_recover > 0 else np.nan
        else:
            recovery_date = pd.NaT
            days_to_recover = np.nan
            time_under_water = int((pd.Timestamp(dates[-1]) - peak_date).days)
            recovered = False
            recovery_efficiency = np.nan

        cycles.append({
            "peak_date": peak_date,
            "peak_price": peak_price,
            "trough_date": trough_date,
            "trough_price": trough_price,
            "recovery_date": recovery_date,
            "drawdown_depth_pct": dd_depth * 100,
            "days_to_trough": int((trough_date - peak_date).days),
            "days_to_recover": days_to_recover,
            "time_under_water_days": time_under_water,
            "recovered": recovered,
            "recovery_efficiency": recovery_efficiency,
        })

    if not cycles:
        return pd.DataFrame()

    return pd.DataFrame(cycles).sort_values("peak_date").reset_index(drop=True)

def extract_recovery_cycles(prices: list[dict], years: int = 10) -> pd.DataFrame:
    df = _prices_to_df(prices, years)
    if df.empty:
        return pd.DataFrame()

    return extract_recovery_cycles_from_closes(
        df["price"].astype(float).values,
        pd.to_datetime(df["date"]).values
    )

def _empty_risk_dict() -> dict:
    return {
        "vol": None,
        "downside_vol": None,
        "mdd": None,
        "sharpe": None,
        "ulcer_index": None,
        "pct_time_under_water": None,
        "avg_recovery_days": None,
        "max_recovery_days": None,
        "recovery_success_ratio": None,
        "recovery_efficiency": None,
    }

def _compute_risk(closes: np.ndarray, dates=None) -> dict:
    if closes is None or len(closes) < 60:
        return _empty_risk_dict()

    closes = np.asarray(closes, dtype=float)
    closes = closes[np.isfinite(closes) & (closes > 0)]

    if len(closes) < 60:
        return _empty_risk_dict()

    log_ret = np.diff(np.log(closes))
    if len(log_ret) < 20:
        return _empty_risk_dict()

    daily_vol = float(np.std(log_ret))
    ann_vol = daily_vol * np.sqrt(252)

    downside = log_ret[log_ret < 0]
    downside_vol = float(np.std(downside) * np.sqrt(252)) if len(downside) > 5 else None

    ann_return = float(np.mean(log_ret) * 252)
    sharpe = (ann_return - 0.04) / ann_vol if ann_vol > 0 else None

    peaks = np.maximum.accumulate(closes)
    drawdowns = (closes - peaks) / peaks

    mdd = float(np.min(drawdowns))
    ulcer_index = float(np.sqrt(np.mean((drawdowns * 100.0) ** 2)))
    pct_time_under_water = float(np.mean(drawdowns < 0))

    avg_recovery_days = None
    max_recovery_days = None
    recovery_success_ratio = None
    recovery_efficiency = None

    if dates is not None and len(dates) == len(closes):
        cycles_df = extract_recovery_cycles_from_closes(closes, dates)
        if not cycles_df.empty:
            recovered = cycles_df[cycles_df["recovered"] == True]
            avg_recovery_days = float(recovered["days_to_recover"].mean()) if not recovered.empty else None
            max_recovery_days = int(recovered["days_to_recover"].max()) if not recovered.empty else None
            recovery_success_ratio = float(recovered.shape[0] / cycles_df.shape[0]) if cycles_df.shape[0] > 0 else None
            recovery_efficiency = float(recovered["recovery_efficiency"].mean()) if not recovered.empty else None

    return {
        "vol": float(ann_vol),
        "downside_vol": downside_vol,
        "mdd": float(mdd),
        "sharpe": float(sharpe) if sharpe is not None else None,
        "ulcer_index": ulcer_index,
        "pct_time_under_water": pct_time_under_water,
        "avg_recovery_days": avg_recovery_days,
        "max_recovery_days": max_recovery_days,
        "recovery_success_ratio": recovery_success_ratio,
        "recovery_efficiency": recovery_efficiency,
    }

def _altman_z_v2(ta, retained, ebitda_val, mkt_cap, revenue, cur_assets, cur_liab, total_liab):
    try:
        if not ta or ta <= 0 or not mkt_cap or not revenue:
            return None
        wc = (cur_assets or 0) - (cur_liab or 0)
        ebit = (ebitda_val or 0) * 0.85
        tl = total_liab or 1
        A = wc / ta
        B = (retained or 0) / ta
        C = ebit / ta
        D = mkt_cap / tl
        E = revenue / ta
        z = 1.2 * A + 1.4 * B + 3.3 * C + 0.6 * D + 1.0 * E
        return round(z, 2) if 0 < z < 50 else None
    except Exception:
        return None

# ═══════════════════════════════════════════════════════════════
# DATA FETCH
# ═══════════════════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner=False)
def fetch_ticker_data(symbol: str) -> dict:
    try:
        tk = yf.Ticker(symbol)

        fi = tk.fast_info
        fi_price = _safe(getattr(fi, "last_price", None))
        fi_prev = _safe(getattr(fi, "previous_close", None))
        fi_mktcap = _safe(getattr(fi, "market_cap", None))
        fi_currency = (getattr(fi, "currency", None) or "USD")
        fi_shares = _safe(getattr(fi, "shares", None))
        fi_exchange = (getattr(fi, "exchange", None) or "")

        info = {}
        try:
            info = tk.info or {}
            if len(info) < 5 or list(info.keys()) == ["maxAge"]:
                info = {}
        except Exception:
            info = {}

        bad_names = {
            "EQUITY", "ETF", "INDEX", "MUTUALFUND", "CURRENCY",
            "FUTURE", "OPTION", symbol.upper()
        }
        raw_name = (info.get("longName") or info.get("shortName") or "").strip()
        name = raw_name if raw_name and raw_name.upper() not in bad_names else symbol.upper()

        if name == symbol.upper():
            try:
                results = yf.Search(symbol, max_results=1).quotes
                if results:
                    q = results[0]
                    candidate = q.get("longname") or q.get("shortname") or ""
                    if candidate and candidate.upper() not in bad_names:
                        name = candidate
            except Exception:
                pass

        currency = info.get("currency") or fi_currency
        sector = info.get("sector") or "—"
        industry = info.get("industry") or "—"
        country = info.get("country") or "—"
        exchange = info.get("exchange") or fi_exchange or "—"
        bio = info.get("longBusinessSummary") or ""
        employees = info.get("fullTimeEmployees")

        price = fi_price or fi_prev or _safe(info.get("regularMarketPrice"))
        mkt_cap = fi_mktcap or _safe(info.get("marketCap"))
        shares = fi_shares or _safe(info.get("sharesOutstanding"))

        revenue = net_income = ebitda_val = gross_profit = None
        interest_exp = None
        try:
            inc = tk.income_stmt
            if inc is not None and not inc.empty:
                revenue = _row(inc, "Total Revenue")
                net_income = _row(inc, "Net Income")
                gross_profit = _row(inc, "Gross Profit")
                ebitda_val = _row(inc, "EBITDA", "Normalized EBITDA")
                interest_exp = _row(inc, "Interest Expense")
                if ebitda_val is None:
                    ebit = _row(inc, "EBIT", "Operating Income")
                    da = _row(
                        inc,
                        "Depreciation",
                        "Reconciled Depreciation",
                        "Depreciation And Amortization"
                    )
                    if ebit is not None and da is not None:
                        ebitda_val = ebit + abs(da)
        except Exception:
            pass

        total_assets = total_liab = retained = None
        cur_assets = cur_liab = total_debt = equity = None
        try:
            bs = tk.balance_sheet
            if bs is not None and not bs.empty:
                total_assets = _row(bs, "Total Assets")
                total_liab = _row(bs, "Total Liab", "Total Liabilities Net Minority Interest")
                retained = _row(bs, "Retained Earnings")
                cur_assets = _row(bs, "Current Assets", "Total Current Assets")
                cur_liab = _row(bs, "Current Liabilities", "Total Current Liabilities")
                total_debt = _row(bs, "Total Debt", "Long Term Debt")
                equity = _row(
                    bs,
                    "Stockholders Equity",
                    "Total Stockholder Equity",
                    "Common Stock Equity",
                    "Total Equity Gross Minority Interest"
                )
        except Exception:
            pass

        prices = []
        hist_close = np.array([])
        hist_dates = pd.Index([])

        try:
            hist = tk.history(period="10y", auto_adjust=True, actions=False, timeout=20)
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
        except Exception:
            pass

        hist_returns = np.array([])
        if len(hist_close) > 1:
            hist_returns = np.diff(np.log(hist_close[hist_close > 0]))

        beta = _safe(info.get("beta"))
        if beta is None and len(hist_returns) > 60:
            try:
                spy = yf.Ticker("^GSPC").history(period="5y", auto_adjust=True, actions=False, timeout=15)
                if spy is not None and not spy.empty:
                    spy = spy[["Close"]].dropna()
                    spy.index = pd.to_datetime(spy.index).tz_localize(None)
                    spy_ret = np.diff(np.log(spy["Close"].values.astype(float)))
                    n = min(len(hist_returns), len(spy_ret))
                    if n > 60:
                        x, y = spy_ret[-n:], hist_returns[-n:]
                        cov = np.cov(x, y)[0, 1]
                        var = np.var(x)
                        if var > 0:
                            beta = round(cov / var, 2)
            except Exception:
                pass

        pe = _safe(info.get("trailingPE"))
        if pe is None and mkt_cap and net_income and net_income > 0:
            pe = round(mkt_cap / net_income, 2)

        ps = _safe(info.get("priceToSalesTrailing12Months"))
        if ps is None and mkt_cap and revenue and revenue > 0:
            ps = round(mkt_cap / revenue, 2)

        pb = _safe(info.get("priceToBook"))
        if pb is None and mkt_cap and equity and equity > 0:
            pb = round(mkt_cap / equity, 2)

        ev = _safe(info.get("enterpriseValue"))
        if ev is None and mkt_cap and total_debt:
            ev = mkt_cap + (total_debt or 0)

        ev_rev = _safe(info.get("enterpriseToRevenue"))
        ev_ebitda = _safe(info.get("enterpriseToEbitda"))
        if ev_rev is None and ev and revenue and revenue > 0:
            ev_rev = round(ev / revenue, 2)
        if ev_ebitda is None and ev and ebitda_val and ebitda_val > 0:
            ev_ebitda = round(ev / ebitda_val, 2)

        profit_mg = _safe(info.get("profitMargins"))
        if profit_mg is None and net_income and revenue and revenue > 0:
            profit_mg = net_income / revenue

        roe = _safe(info.get("returnOnEquity"))
        if roe is None and net_income and equity and equity > 0:
            roe = net_income / equity

        roa = _safe(info.get("returnOnAssets"))
        if roa is None and net_income and total_assets and total_assets > 0:
            roa = net_income / total_assets

        debt_eq = _safe(info.get("debtToEquity"))
        if debt_eq is not None:
            debt_eq /= 100
        elif total_debt and equity and equity != 0:
            debt_eq = total_debt / equity

        cur_ratio = _safe(info.get("currentRatio"))
        if cur_ratio is None and cur_assets and cur_liab and cur_liab != 0:
            cur_ratio = cur_assets / cur_liab

        quick_r = _safe(info.get("quickRatio"))
        if quick_r is None and cur_assets and cur_liab and cur_liab != 0:
            quick_r = cur_assets / cur_liab

        ic = None
        if ebitda_val and interest_exp and abs(interest_exp) > 0:
            ic = ebitda_val / abs(interest_exp)

        div_yield = _safe(info.get("dividendYield")) or 0.0
        if div_yield and div_yield > 1.0:
            div_yield = div_yield / 100

        if div_yield == 0.0:
            try:
                divs = tk.dividends
                if divs is not None and not divs.empty and price and price > 0:
                    divs.index = pd.to_datetime(divs.index).tz_localize(None)
                    cutoff = datetime.now() - timedelta(days=366)
                    last_year = divs[divs.index >= cutoff]
                    if not last_year.empty:
                        annual_div = float(last_year.sum())
                        div_yield = annual_div / price
            except Exception:
                pass

        if div_yield and div_yield > 0.25:
            div_yield = 0.0

        payout = _safe(info.get("payoutRatio")) or 0.0

        zscore = _altman_z_v2(
            total_assets, retained, ebitda_val, mkt_cap,
            revenue, cur_assets, cur_liab, total_liab
        )
        risk = _compute_risk(hist_close, hist_dates if len(hist_dates) == len(hist_close) else None)

        w52_low = w52_high = dist_52w_low = dist_52w_high = None
        w52_low_date = w52_high_date = None
        w52_low_days = w52_high_days = None
        try:
            if len(hist_close) >= 20:
                window_closes = hist_close[-252:] if len(hist_close) >= 252 else hist_close
                window_dates = hist_dates[-252:] if len(hist_dates) >= 252 else hist_dates

                low_idx = int(np.argmin(window_closes))
                high_idx = int(np.argmax(window_closes))

                w52_low = float(window_closes[low_idx])
                w52_high = float(window_closes[high_idx])

                w52_low_date = window_dates[low_idx]
                w52_high_date = window_dates[high_idx]

                today = pd.Timestamp.now().normalize()
                w52_low_days = int((today - pd.Timestamp(w52_low_date)).days)
                w52_high_days = int((today - pd.Timestamp(w52_high_date)).days)

                if price and w52_low > 0:
                    dist_52w_low = (price - w52_low) / w52_low
                if price and w52_high > 0:
                    dist_52w_high = (price - w52_high) / w52_high
        except Exception:
            pass

        return {
            "symbol": symbol,
            "name": name,
            "sector": sector,
            "industry": industry,
            "country": country,
            "exchange": exchange,
            "currency": currency,
            "employees": employees,
            "bio": bio,
            "price": price,
            "mkt_cap": mkt_cap,
            "shares": shares,
            "pe": pe,
            "ps": ps,
            "pb": pb,
            "ev": ev,
            "ev_rev": ev_rev,
            "ev_ebitda": ev_ebitda,
            "profit_margin": profit_mg,
            "roa": roa,
            "roe": roe,
            "revenue": revenue,
            "net_income": net_income,
            "ebitda": ebitda_val,
            "gross_profit": gross_profit,
            "div_yield": div_yield,
            "payout": payout,
            "beta": beta,
            "ic": ic,
            "debt_eq": debt_eq,
            "current_ratio": cur_ratio,
            "quick_ratio": quick_r,
            "zscore": zscore,
            **risk,
            "w52_low": w52_low,
            "w52_high": w52_high,
            "w52_low_date": w52_low_date.strftime("%Y-%m-%d") if w52_low_date is not None else None,
            "w52_high_date": w52_high_date.strftime("%Y-%m-%d") if w52_high_date is not None else None,
            "w52_low_days": w52_low_days,
            "w52_high_days": w52_high_days,
            "dist_52w_low": dist_52w_low,
            "dist_52w_high": dist_52w_high,
            "prices": prices,
        }

    except Exception as e:
        return {"symbol": symbol, "error": str(e), "prices": []}

@st.cache_data(ttl=300, show_spinner=False)
def search_tickers(query: str) -> list[dict]:
    if len(query) < 1:
        return []
    try:
        session = _search_session()
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=8&newsCount=0&listsCount=0"
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
# CHARTS
# ═══════════════════════════════════════════════════════════════

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
    rgb = ",".join(str(int(color.lstrip("#")[i:i+2], 16)) for i in (0, 2, 4))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["price"],
        mode="lines",
        line=dict(color=color, width=1.6),
        fill="tozeroy",
        fillcolor=f"rgba({rgb},0.07)",
        hovertemplate=f"%{{x|%b %d, %Y}}<br>{cur_sym(cur)}%{{y:.2f}}<extra></extra>",
        name=symbol
    ))
    fig.update_layout(**_base_layout(260), showlegend=False)
    return fig

def income_chart(d: dict) -> go.Figure:
    cur = cur_sym(d.get("currency", "USD"))
    candidates = [
        ("Revenue", d.get("revenue"), GOLD),
        ("EBITDA", d.get("ebitda"), DEPTH),
        ("Net Income", d.get("net_income"), RISE if (d.get("net_income") or 0) >= 0 else FALL),
    ]
    items = [(lbl, val, col) for lbl, val, col in candidates if val is not None]

    if not items:
        fig = go.Figure()
        fig.add_annotation(
            text="Income data unavailable",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=13, color=INK_LIGHT)
        )
        fig.update_layout(**_base_layout(260))
        return fig

    labels = [i[0] for i in items]
    values = [i[1] / 1e9 for i in items]
    colors = [i[2] for i in items]

    fig = go.Figure(go.Bar(
        x=labels,
        y=values,
        marker_color=colors,
        text=[f"{cur}{v:.1f}B" for v in values],
        textposition="outside",
        textfont=dict(size=11, color=INK_MID),
        hovertemplate="%{x}: " + cur + "%{y:.2f}B<extra></extra>",
    ))
    fig.update_traces(marker_line_width=0, width=0.45)
    fig.update_layout(**_base_layout(260), showlegend=False)
    return fig

def factor_radar(d: dict, symbol: str) -> tuple[go.Figure, dict]:
    def _clamp(v, lo, hi):
        if v is None:
            return None
        return max(lo, min(hi, v))

    def _avg(vals):
        vals = [v for v in vals if v is not None]
        return round(sum(vals) / len(vals)) if vals else 50

    valuation = _avg([
        _clamp(100 - ((d.get("pe") or 20) - 5) * 1.5, 0, 100) if d.get("pe") else None,
        _clamp(100 - ((d.get("ps") or 5) - 1) * 8, 0, 100) if d.get("ps") else None,
        _clamp(100 - ((d.get("pb") or 3) - 1) * 12, 0, 100) if d.get("pb") else None,
        _clamp(100 - ((d.get("ev_ebitda") or 12) - 6) * 2.5, 0, 100) if d.get("ev_ebitda") else None,
    ])
    quality = _avg([
        _clamp((d.get("profit_margin") or 0) * 300, 0, 100),
        _clamp((d.get("roe") or 0) * 250, 0, 100),
        _clamp((d.get("roa") or 0) * 500, 0, 100),
    ])
    growth = _avg([
        _clamp(100 / d.get("ps") * 15, 0, 100) if d.get("ps") else None,
        _clamp(100 / d.get("ev_rev") * 12, 0, 100) if d.get("ev_rev") else None,
    ])
    risk = _avg([
        _clamp(100 + (d.get("mdd") or -0.3) * 120, 0, 100),
        _clamp(100 - (d.get("ulcer_index") or 10) * 3.5, 0, 100),
        _clamp(100 - (d.get("pct_time_under_water") or 0.5) * 100, 0, 100),
        _clamp((d.get("recovery_success_ratio") or 0.5) * 100, 0, 100),
    ])

    momentum = 50
    if d.get("prices") and len(d["prices"]) > 260:
        closes = [p["price"] for p in d["prices"]]
        r1y = (closes[-1] - closes[-252]) / closes[-252] * 100
        momentum = round(_clamp(50 + r1y * 0.5, 0, 100))

    convexity = 50
    if d.get("prices") and len(d["prices"]) > 60:
        closes = np.array([p["price"] for p in d["prices"]], dtype=float)
        rets = np.diff(np.log(closes[closes > 0]))
        if len(rets) > 20:
            convexity = round(_clamp(50 + float(pd.Series(rets).skew()) * 20, 0, 100))

    dividend = round(_clamp((d.get("div_yield") or 0) * 1000, 0, 100)) if d.get("div_yield") else 30
    liquidity = _avg([
        _clamp(((d.get("current_ratio") or 1.0) - 0.5) / 2.5 * 100, 0, 100),
        _clamp(100 - (d.get("debt_eq") or 1.0) * 30, 0, 100),
        _clamp((d.get("ic") or 5.0) * 4, 0, 100),
    ])

    factors = {
        "Valuation": valuation,
        "Quality": quality,
        "Growth": growth,
        "Risk": risk,
        "Momentum": momentum,
        "Convexity": convexity,
        "Dividend": dividend,
        "Liquidity": liquidity,
    }

    labels = list(factors.keys())
    values = list(factors.values())
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
                gridcolor=GRID,
                linecolor=GRID
            ),
            angularaxis=dict(
                tickfont=dict(size=12, color=INK),
                gridcolor=GRID,
                linecolor=GRID
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
    low = d.get("w52_low")
    high = d.get("w52_high")
    price = d.get("price")

    if not low or not high or not price or high <= low:
        return None

    span = high - low
    p_pct = (price - low) / span * 100
    price_color = RISE if p_pct >= 66 else FALL if p_pct <= 33 else GOLD

    fig = go.Figure()
    pad = span * 0.22

    fig.add_shape(
        type="rect", x0=0.25, x1=0.75, y0=low - pad * 0.3, y1=high + pad * 0.3,
        fillcolor="rgba(182,157,95,0.04)", line=dict(width=0), layer="below"
    )
    fig.add_shape(
        type="line", x0=0.5, x1=0.5, y0=low, y1=high,
        line=dict(color=GRID, width=2), layer="below"
    )
    fig.add_shape(
        type="line", x0=0.3, x1=0.7, y0=price, y1=price,
        line=dict(color=price_color, width=3)
    )
    fig.add_trace(go.Scatter(
        x=[0.5], y=[price], mode="markers",
        marker=dict(size=16, color=price_color, line=dict(color=WHITE, width=2.5)),
        showlegend=False,
        hovertemplate=f"<b>Current</b><br>{cur_sym(d.get('currency','USD'))}{price:,.2f}<extra></extra>",
    ))

    fig.update_layout(
        paper_bgcolor=STONE,
        plot_bgcolor=STONE,
        height=340,
        margin=dict(l=10, r=10, t=20, b=20),
        xaxis=dict(range=[0, 1], showgrid=False, showticklabels=False, zeroline=False, showline=False, fixedrange=True),
        yaxis=dict(range=[low - pad, high + pad], showgrid=False, showticklabels=False, zeroline=False, showline=False, fixedrange=True),
        showlegend=False,
        annotations=[dict(
            x=0.08, y=(low + high) / 2, xref="x", yref="y",
            text=f"<b style='font-size:22px;color:{price_color}'>{p_pct:.0f}%</b><br><span style='font-size:9px;color:{INK_LIGHT}'>OF RANGE</span>",
            showarrow=False
        )]
    )
    return fig

def comparison_chart(all_data: list[dict], metric: str, label: str) -> go.Figure:
    labels = [d["symbol"] for d in all_data]
    values = [d.get(metric) for d in all_data]
    colors = [GOLD if v is not None else "#DDD8CE" for v in values]
    clean_v = [v if v is not None else 0 for v in values]

    fig = go.Figure(go.Bar(
        x=labels,
        y=clean_v,
        marker_color=colors,
        text=[f"{v:.2f}" if v is not None else "N/A" for v in values],
        textposition="outside",
        textfont=dict(size=11, color=INK_MID),
        hovertemplate="%{x}: %{y:.2f}<extra></extra>",
    ))
    fig.update_traces(marker_line_width=0, width=0.45)
    fig.update_layout(
        **_base_layout(240),
        title=dict(text=label, font=dict(size=11, color=INK_LIGHT), x=0, xanchor="left"),
        showlegend=False
    )
    return fig

def portfolio_returns_chart(all_data: list[dict], years: int = 3) -> go.Figure:
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
        fig.add_trace(go.Scatter(
            x=df["date"],
            y=df["norm"],
            mode="lines",
            name=d["symbol"],
            line=dict(color=palette[i % len(palette)], width=1.8),
            hovertemplate=f"<b>{d['symbol']}</b><br>%{{x|%b %Y}}<br>%{{y:.1f}}<extra></extra>",
        ))

    base = _base_layout(320).copy()
    base.pop("yaxis", None)
    fig.update_layout(
        **base,
        yaxis=dict(
            showgrid=True,
            gridcolor=GRID,
            gridwidth=1,
            tickfont=dict(size=10, color=INK_LIGHT),
            zeroline=False,
            showline=False,
            title="Indexed (base = 100)",
            title_font=dict(size=11, color=INK_MID),
        )
    )
    return fig

# ═══════════════════════════════════════════════════════════════
# RECOVERY DASHBOARD CHARTS
# ═══════════════════════════════════════════════════════════════

def _prices_to_df(prices: list[dict], years: int = 10) -> pd.DataFrame:
    if not prices:
        return pd.DataFrame(columns=["date", "price"])
    df = pd.DataFrame(prices).copy()
    df["date"] = pd.to_datetime(df["date"])
    cutoff = datetime.now() - timedelta(days=years * 365)
    df = df[df["date"] >= cutoff].sort_values("date").reset_index(drop=True)
    return df

def price_vs_running_peak_chart(prices: list[dict], years: int = 10) -> go.Figure:
    df = _prices_to_df(prices, years)
    if df.empty:
        return go.Figure()

    df["peak"] = df["price"].cummax()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["price"],
        mode="lines", line=dict(color=INK, width=2),
        name="Price",
        hovertemplate="%{x|%b %d, %Y}<br>Price: %{y:.2f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["peak"],
        mode="lines", line=dict(color=GOLD, width=1.8, dash="dash"),
        name="Running Peak",
        hovertemplate="%{x|%b %d, %Y}<br>Peak: %{y:.2f}<extra></extra>",
    ))
    fig.update_layout(
        **_base_layout(300),
        title=dict(text="Price vs Running Peak", x=0.5, xanchor="center", font=dict(size=15, color=INK))
    )
    return fig

def drawdown_from_peak_chart(prices: list[dict], years: int = 10) -> go.Figure:
    df = _prices_to_df(prices, years)
    if df.empty:
        return go.Figure()

    df["peak"] = df["price"].cummax()
    df["drawdown_pct"] = (df["price"] - df["peak"]) / df["peak"] * 100

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["drawdown_pct"],
        mode="lines",
        line=dict(color="#A85A5A", width=2),
        fill="tozeroy",
        fillcolor="rgba(148,72,72,0.18)",
        hovertemplate="%{x|%b %d, %Y}<br>Drawdown: %{y:.2f}%<extra></extra>",
    ))

    base = _base_layout(300).copy()
    base.pop("xaxis", None)
    base.pop("yaxis", None)

    fig.update_layout(
        **base,
        title=dict(text="Drawdown from Prior Peak", x=0.5, xanchor="center", font=dict(size=15, color=INK)),
        showlegend=False,
        xaxis=dict(
            showgrid=False,
            tickfont=dict(size=10, color=INK_LIGHT),
            zeroline=False,
            showline=False
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=GRID,
            tickfont=dict(size=10, color=INK_LIGHT),
            ticksuffix="%",
            zeroline=True,
            zerolinecolor=GRID
        )
    )
    return fig

def recovery_days_by_cycle_chart(cycles_df: pd.DataFrame) -> go.Figure:
    if cycles_df is None or cycles_df.empty:
        fig = go.Figure()
        fig.update_layout(
            **_base_layout(300),
            title=dict(text="Recovery Days by Drawdown Cycle", x=0.5, xanchor="center", font=dict(size=15, color=INK)),
            annotations=[dict(
                text="No drawdown cycles found",
                x=0.5, y=0.5, xref="paper", yref="paper",
                showarrow=False, font=dict(size=13, color=INK_LIGHT)
            )]
        )
        return fig

    df = cycles_df.copy()
    df["cycle_label"] = df["peak_date"].dt.strftime("%Y-%m")
    df["bar_value"] = df["days_to_recover"].fillna(df["time_under_water_days"])
    df["bar_color"] = np.where(df["recovered"], "rgba(77,124,91,0.80)", "rgba(148,72,72,0.70)")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["cycle_label"],
        y=df["bar_value"],
        marker_color=df["bar_color"],
        hovertemplate="<b>%{x}</b><br>Days: %{y:.0f}<extra></extra>",
    ))

    base = _base_layout(300).copy()
    base.pop("xaxis", None)
    base.pop("yaxis", None)

    fig.update_layout(
        **base,
        title=dict(text="Recovery Days by Drawdown Cycle", x=0.5, xanchor="center", font=dict(size=15, color=INK)),
        showlegend=False,
        xaxis=dict(showgrid=False, tickangle=-45, tickfont=dict(size=10, color=INK_LIGHT)),
        yaxis=dict(
            showgrid=True,
            gridcolor=GRID,
            tickfont=dict(size=10, color=INK_LIGHT),
            title="Days",
            title_font=dict(size=11, color=INK_MID)
        )
    )
    return fig

def recovery_summary_html(d: dict, symbol: str, cycles_df: pd.DataFrame) -> str:
    median_rec = None
    avg_tuw_days = None

    if cycles_df is not None and not cycles_df.empty:
        recovered = cycles_df[cycles_df["recovered"] == True]
        median_rec = float(recovered["days_to_recover"].median()) if not recovered.empty else None
        avg_tuw_days = float(cycles_df["time_under_water_days"].mean()) if not cycles_df.empty else None

    rows = [
        ("Max Drawdown", fmt_pct(d.get("mdd"))),
        ("Ulcer Index", fmt_num(d.get("ulcer_index"))),
        ("Time Under Water", fmt_pct(d.get("pct_time_under_water"))),
        ("Recovery Success", fmt_pct(d.get("recovery_success_ratio"))),
        ("Avg Recovery Days", fmt_num(d.get("avg_recovery_days"), 1)),
        ("Median Recovery Days", fmt_num(median_rec, 1)),
        ("Max Recovery Days", fmt_num(d.get("max_recovery_days"), 1)),
        ("Avg TUW Days", fmt_num(avg_tuw_days, 1)),
        ("Recovery Efficiency", fmt_num(d.get("recovery_efficiency"), 6)),
    ]

    html_rows = "".join(
        f'<div class="summary-row"><div class="summary-label">{label}</div><div class="summary-value">{value}</div></div>'
        for label, value in rows
    )

    return f"""
    <div class="summary-card">
      <div class="summary-title">{symbol} · Recovery Summary</div>
      {html_rows}
    </div>
    """

# ═══════════════════════════════════════════════════════════════
# RISK SCORE
# ═══════════════════════════════════════════════════════════════

def risk_score(d: dict) -> tuple[int, str, str]:
    score = 0

    zscore = d.get("zscore")
    if zscore is not None:
        if zscore < 1.8:
            score += 20
        elif zscore < 3.0:
            score += 10

    debt_eq = d.get("debt_eq")
    if debt_eq is not None:
        if debt_eq > 2.0:
            score += 15
        elif debt_eq > 1.0:
            score += 8

    mdd = d.get("mdd")
    if mdd is not None:
        if abs(mdd) > 0.60:
            score += 20
        elif abs(mdd) > 0.40:
            score += 12
        elif abs(mdd) > 0.25:
            score += 6

    tuw = d.get("pct_time_under_water")
    if tuw is not None:
        if tuw > 0.70:
            score += 18
        elif tuw > 0.50:
            score += 10
        elif tuw > 0.35:
            score += 5

    avg_rec = d.get("avg_recovery_days")
    if avg_rec is not None:
        if avg_rec > 180:
            score += 18
        elif avg_rec > 90:
            score += 10
        elif avg_rec > 45:
            score += 5

    rec_success = d.get("recovery_success_ratio")
    if rec_success is not None:
        if rec_success < 0.40:
            score += 15
        elif rec_success < 0.65:
            score += 8

    ulcer = d.get("ulcer_index")
    if ulcer is not None:
        if ulcer > 25:
            score += 15
        elif ulcer > 15:
            score += 8

    vol = d.get("vol")
    if vol is not None:
        if vol > 0.55:
            score += 8
        elif vol > 0.35:
            score += 4

    score = min(score, 100)

    if score <= 20:
        return score, "Low", RISE
    if score <= 40:
        return score, "Moderate", GOLD
    if score <= 60:
        return score, "Elevated", CAUTION
    return score, "High", FALL

# ═══════════════════════════════════════════════════════════════
# DETAIL VIEW
# ═══════════════════════════════════════════════════════════════

def render_ticker_detail(symbol: str, years: int):
    with st.spinner(f"Loading {symbol}…"):
        d = fetch_ticker_data(symbol)

    if "error" in d and not d.get("name"):
        st.error(f"⚠️ Could not load **{symbol}**: {d['error']}")
        return

    cur = cur_sym(d.get("currency", "USD"))
    prices = d.get("prices", [])

    st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)
    col_name, col_price = st.columns([2, 1])

    with col_name:
        meta = " · ".join(filter(None, [d.get("exchange", ""), d.get("sector", ""), d.get("industry", "")]))
        if meta:
            st.markdown(
                f'<div style="font-size:11px;color:{GOLD};letter-spacing:.2em;text-transform:uppercase;margin-bottom:4px;">{meta}</div>',
                unsafe_allow_html=True
            )
        st.markdown(
            f'<div class="hero-name">{d.get("name", symbol)}</div><div class="hero-ticker">{symbol}</div>',
            unsafe_allow_html=True
        )
        if d.get("bio"):
            st.markdown(
                f'<p style="font-size:13px;color:{INK_MID};line-height:1.75;max-width:560px;margin-top:12px;">{d["bio"][:450]}...</p>',
                unsafe_allow_html=True
            )

    with col_price:
        if d.get("price"):
            st.markdown(
                f'<div style="text-align:right;">'
                f'<div style="font-size:9px;color:{GOLD};letter-spacing:.2em;text-transform:uppercase;">Current Price</div>'
                f'<div class="hero-price">{cur}{d["price"]:,.2f}</div>'
                f'<div style="font-size:11px;color:{INK_LIGHT};margin-top:6px;">Cap {fmt_big(d.get("mkt_cap"), cur)} · {d.get("currency","USD")}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)

    pe, ps, pb = d.get("pe"), d.get("ps"), d.get("pb")
    dy, beta, vol = d.get("div_yield") or 0, d.get("beta"), d.get("vol")

    k1, k2, k3, k4, k5, k6, k7, k8 = st.columns(8)
    with k1:
        st.metric("P/E", f"{pe:.1f}×" if pe else "—")
    with k2:
        st.metric("P/S", f"{ps:.1f}×" if ps else "—")
    with k3:
        st.metric("P/B", f"{pb:.1f}×" if pb else "—")
    with k4:
        st.metric("Div. Yield", fmt_pct(dy) if dy else "—")
    with k5:
        d52l_val = d.get("dist_52w_low")
        st.metric("vs 52w Low", f"+{d52l_val*100:.1f}%" if d52l_val is not None else "—")
    with k6:
        st.metric("Beta (β)", f"{beta:.2f}" if beta else "—")
    with k7:
        st.metric("Volatility", fmt_pct(vol))
    with k8:
        d52h_val = d.get("dist_52w_high")
        st.metric("vs 52w High", f"{d52h_val*100:.1f}%" if d52h_val is not None else "—")

    st.markdown("&nbsp;", unsafe_allow_html=True)

    r52_fig = range_52w_chart(d)
    if r52_fig is not None:
        col_chart, col_52w, col_income = st.columns([1.1, 0.45, 0.75])
    else:
        col_chart, col_income = st.columns([1.2, 0.8])
        col_52w = None

    with col_chart:
        st.markdown('<div class="section-header">Price History</div>', unsafe_allow_html=True)
        st.plotly_chart(
            price_chart(prices, symbol, d.get("currency", "USD"), years),
            use_container_width=True,
            config={"displayModeBar": False}
        )

    if col_52w is not None:
        with col_52w:
            st.markdown('<div class="section-header">52-Week Range</div>', unsafe_allow_html=True)
            st.plotly_chart(r52_fig, use_container_width=True, config={"displayModeBar": False})

    with col_income:
        st.markdown('<div class="section-header">Income Statement (TTM)</div>', unsafe_allow_html=True)
        st.plotly_chart(income_chart(d), use_container_width=True, config={"displayModeBar": False})

    # Recovery Dashboard
    cycles_df = extract_recovery_cycles(prices, years=max(years, 5))

    st.markdown('<div class="section-header" style="margin-top:10px;">Recovery Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)

    top_left, top_right = st.columns([1.45, 1.0])
    with top_left:
        st.plotly_chart(
            price_vs_running_peak_chart(prices, years=max(years, 5)),
            use_container_width=True,
            config={"displayModeBar": False}
        )
    with top_right:
        st.markdown(recovery_summary_html(d, symbol, cycles_df), unsafe_allow_html=True)

    bot_left, bot_right = st.columns([1.45, 1.0])
    with bot_left:
        st.plotly_chart(
            drawdown_from_peak_chart(prices, years=max(years, 5)),
            use_container_width=True,
            config={"displayModeBar": False}
        )
    with bot_right:
        st.plotly_chart(
            recovery_days_by_cycle_chart(cycles_df),
            use_container_width=True,
            config={"displayModeBar": False}
        )

    score, grade, color = risk_score(d)
    radar_fig, factors = factor_radar(d, symbol)
    col_radar, col_risk = st.columns([1, 1])

    with col_radar:
        st.markdown('<div class="section-header">Factor Scorecard</div>', unsafe_allow_html=True)
        st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)
        st.plotly_chart(radar_fig, use_container_width=True, config={"displayModeBar": False})

    with col_risk:
        st.markdown('<div class="section-header">Factor Scores</div>', unsafe_allow_html=True)
        st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)
        for fname, fscore in factors.items():
            bar_color = RISE if fscore >= 65 else (FALL if fscore <= 35 else GOLD)
            st.markdown(f"""
            <div style="margin-bottom:14px;">
              <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
                <span style="font-size:11px;color:{INK_MID};font-weight:500;">{fname}</span>
                <span style="font-size:16px;font-weight:600;color:{bar_color};">{fscore}</span>
              </div>
              <div style="height:5px;background:#EDE8DF;border-radius:3px;overflow:hidden;">
                <div style="width:{fscore}%;height:100%;background:{bar_color};border-radius:3px;"></div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="margin-top:20px;padding:16px 20px;background:{WHITE};
             border:1px solid #DDD8CE;border-radius:12px;">
          <div style="font-size:9px;color:{INK_LIGHT};letter-spacing:.16em;text-transform:uppercase;margin-bottom:6px;">Path Risk Profile</div>
          <div style="font-size:24px;font-weight:600;color:{color};">{grade} Risk</div>
          <div style="height:6px;background:#EDE8DF;border-radius:3px;overflow:hidden;margin-top:10px;">
            <div style="width:{min(score,100)}%;height:100%;background:linear-gradient(90deg,{RISE},{CAUTION},{FALL});border-radius:3px;"></div>
          </div>
          <div style="font-size:11px;color:{INK_LIGHT};margin-top:6px;">Score: <b style="color:{color};">{score}/100</b></div>
        </div>
        """, unsafe_allow_html=True)

    tabs = st.tabs(["📐 Valuation", "📊 Profitability", "🛡 Risk Metrics"])

    with tabs[0]:
        rows = [
            {"Metric": "Enterprise Value", "Value": fmt_big(d.get("ev"), cur), "Signal": _sig(None), "Comment": "Total firm value incl. debt"},
            {"Metric": "Trailing P/E", "Value": f"{pe:.1f}×" if pe else "—", "Signal": _sig("good" if pe and pe < 10 else "warn" if pe and pe > 50 else None), "Comment": ""},
            {"Metric": "EV / Revenue", "Value": f"{d.get('ev_rev'):.1f}×" if d.get("ev_rev") else "—", "Signal": _sig(None), "Comment": ""},
            {"Metric": "EV / EBITDA", "Value": f"{d.get('ev_ebitda'):.1f}×" if d.get("ev_ebitda") else "—", "Signal": _sig(None), "Comment": ""},
            {"Metric": "Price / Book", "Value": f"{pb:.1f}×" if pb else "—", "Signal": _sig("good" if pb and pb < 1 else None), "Comment": ""},
            {"Metric": "Price / Sales", "Value": f"{ps:.1f}×" if ps else "—", "Signal": _sig(None), "Comment": ""},
            {"Metric": "Dividend Yield", "Value": fmt_pct(dy), "Signal": _sig("good" if dy and dy > 0.05 else None), "Comment": ""},
        ]
        _render_table(rows)

    with tabs[1]:
        rows = [
            {"Metric": "Profit Margin", "Value": fmt_pct(d.get("profit_margin")), "Signal": _sig("good" if d.get("profit_margin") and d["profit_margin"] > 0.2 else None), "Comment": ""},
            {"Metric": "Return on Assets", "Value": fmt_pct(d.get("roa")), "Signal": _sig("good" if d.get("roa") and d["roa"] > 0.1 else None), "Comment": ""},
            {"Metric": "Return on Equity", "Value": fmt_pct(d.get("roe")), "Signal": _sig("good" if d.get("roe") and d["roe"] > 0.25 else None), "Comment": ""},
            {"Metric": "Revenue (TTM)", "Value": fmt_big(d.get("revenue"), cur), "Signal": _sig(None), "Comment": ""},
            {"Metric": "Net Income (TTM)", "Value": fmt_big(d.get("net_income"), cur), "Signal": _sig("good" if d.get("net_income") and d["net_income"] > 0 else "bad" if d.get("net_income") and d["net_income"] < 0 else None), "Comment": ""},
            {"Metric": "EBITDA", "Value": fmt_big(d.get("ebitda"), cur), "Signal": _sig(None), "Comment": ""},
        ]
        _render_table(rows)

    with tabs[2]:
        median_rec = None
        avg_tuw_days = None
        if not cycles_df.empty:
            recovered = cycles_df[cycles_df["recovered"] == True]
            median_rec = float(recovered["days_to_recover"].median()) if not recovered.empty else None
            avg_tuw_days = float(cycles_df["time_under_water_days"].mean()) if not cycles_df.empty else None

        def _days_ago(n):
            if n is None:
                return ""
            if n == 0:
                return "today"
            if n == 1:
                return "yesterday"
            if n < 30:
                return f"{n}d ago"
            if n < 365:
                return f"{n//30}mo ago"
            return f"{n//365}y {(n%365)//30}mo ago"

        rows = [
            {"Metric": "52w Low", "Value": f"{cur_sym(d.get('currency','USD'))}{d.get('w52_low'):,.2f}" if d.get("w52_low") else "—", "Signal": _sig(None), "Comment": f"{d.get('w52_low_date')} · {_days_ago(d.get('w52_low_days'))}" if d.get("w52_low_date") else ""},
            {"Metric": "Distance to 52w Low", "Value": f"+{d.get('dist_52w_low')*100:.1f}%" if d.get("dist_52w_low") is not None else "—", "Signal": _sig(None), "Comment": ""},
            {"Metric": "52w High", "Value": f"{cur_sym(d.get('currency','USD'))}{d.get('w52_high'):,.2f}" if d.get("w52_high") else "—", "Signal": _sig(None), "Comment": f"{d.get('w52_high_date')} · {_days_ago(d.get('w52_high_days'))}" if d.get("w52_high_date") else ""},
            {"Metric": "Distance from 52w High", "Value": f"{d.get('dist_52w_high')*100:.1f}%" if d.get("dist_52w_high") is not None else "—", "Signal": _sig(None), "Comment": ""},
            {"Metric": "Beta (β)", "Value": fmt_num(d.get("beta")), "Signal": _sig(None), "Comment": ""},
            {"Metric": "Annualised Volatility", "Value": fmt_pct(d.get("vol")), "Signal": _sig(None), "Comment": "Dispersion only; recovery profile is decisive"},
            {"Metric": "Downside Volatility", "Value": fmt_pct(d.get("downside_vol")), "Signal": _sig(None), "Comment": ""},
            {"Metric": "Max Drawdown", "Value": fmt_pct(d.get("mdd")), "Signal": _sig(None), "Comment": "Worst peak-to-trough loss"},
            {"Metric": "Ulcer Index", "Value": fmt_num(d.get("ulcer_index")), "Signal": _sig(None), "Comment": "Depth × duration of drawdowns"},
            {"Metric": "Time Under Water", "Value": fmt_pct(d.get("pct_time_under_water")), "Signal": _sig(None), "Comment": "Share of time below prior highs"},
            {"Metric": "Avg Recovery Days", "Value": fmt_num(d.get("avg_recovery_days"), 1), "Signal": _sig(None), "Comment": ""},
            {"Metric": "Median Recovery Days", "Value": fmt_num(median_rec, 1), "Signal": _sig(None), "Comment": ""},
            {"Metric": "Max Recovery Days", "Value": fmt_num(d.get("max_recovery_days"), 1), "Signal": _sig(None), "Comment": ""},
            {"Metric": "Avg TUW Days", "Value": fmt_num(avg_tuw_days, 1), "Signal": _sig(None), "Comment": ""},
            {"Metric": "Recovery Success Rate", "Value": fmt_pct(d.get("recovery_success_ratio")), "Signal": _sig(None), "Comment": ""},
            {"Metric": "Recovery Efficiency", "Value": fmt_num(d.get("recovery_efficiency"), 6), "Signal": _sig(None), "Comment": ""},
            {"Metric": "Sharpe Ratio", "Value": fmt_num(d.get("sharpe")), "Signal": _sig(None), "Comment": ""},
            {"Metric": "Debt / Equity", "Value": fmt_num(d.get("debt_eq")), "Signal": _sig(None), "Comment": ""},
            {"Metric": "Current Ratio", "Value": fmt_num(d.get("current_ratio")), "Signal": _sig(None), "Comment": ""},
            {"Metric": "Quick Ratio", "Value": fmt_num(d.get("quick_ratio")), "Signal": _sig(None), "Comment": ""},
            {"Metric": "Interest Coverage", "Value": f"{d.get('ic'):.1f}×" if d.get("ic") else "—", "Signal": _sig(None), "Comment": ""},
            {"Metric": "Altman Z-Score", "Value": fmt_num(d.get("zscore")), "Signal": _sig(None), "Comment": ""},
        ]
        _render_table(rows)

# ═══════════════════════════════════════════════════════════════
# COMPARISON
# ═══════════════════════════════════════════════════════════════

def render_comparison(symbols: list[str], years: int):
    st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-header">Cross-Comparison · {len(symbols)} Securities · Live</div>', unsafe_allow_html=True)

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

    st.markdown(f'<div class="section-header">Indexed Returns (Base = 100, {years}Y)</div>', unsafe_allow_html=True)
    st.plotly_chart(portfolio_returns_chart(valid, years), use_container_width=True, config={"displayModeBar": False})

    col_charts = st.columns(3)
    metrics_viz = [
        ("pe", "P/E Ratio"),
        ("profit_margin", "Profit Margin"),
        ("roe", "Return on Equity"),
        ("vol", "Annualised Volatility"),
        ("ulcer_index", "Ulcer Index"),
        ("pct_time_under_water", "Time Under Water"),
    ]
    for i, (key, label) in enumerate(metrics_viz):
        with col_charts[i % 3]:
            st.plotly_chart(comparison_chart(valid, key, label), use_container_width=True, config={"displayModeBar": False})

    st.markdown('<div class="section-header">Summary Table</div>', unsafe_allow_html=True)
    rows = []
    for d in valid:
        cur = cur_sym(d.get("currency", "USD"))
        sc, grade, _ = risk_score(d)
        rows.append({
            "Ticker": d["symbol"],
            "Name": (d.get("name") or d["symbol"])[:28],
            "Price": f'{cur}{d["price"]:,.2f}' if d.get("price") else "—",
            "Mkt Cap": fmt_big(d.get("mkt_cap"), cur),
            "P/E": f'{d["pe"]:.1f}×' if d.get("pe") else "—",
            "P/B": f'{d["pb"]:.1f}×' if d.get("pb") else "—",
            "Div Yield": fmt_pct(d.get("div_yield")),
            "Profit Mg.": fmt_pct(d.get("profit_margin")),
            "ROE": fmt_pct(d.get("roe")),
            "EV/EBITDA": f'{d["ev_ebitda"]:.1f}×' if d.get("ev_ebitda") else "—",
            "Beta": fmt_num(d.get("beta")),
            "D/E": fmt_num(d.get("debt_eq")),
            "Volatility": fmt_pct(d.get("vol")),
            "Ulcer": fmt_num(d.get("ulcer_index")),
            "TUW": fmt_pct(d.get("pct_time_under_water")),
            "Avg Rec Days": fmt_num(d.get("avg_recovery_days"), 1),
            "Recovery %": fmt_pct(d.get("recovery_success_ratio")),
            "Risk Score": f"{grade} ({sc})",
        })

    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    csv_buf = pd.DataFrame(rows).to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇ Export Comparison CSV",
        data=csv_buf,
        file_name="stock_haus_comparison.csv",
        mime="text/csv"
    )

# ═══════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════

def render_sidebar() -> tuple[list[str], int, str]:
    with st.sidebar:
        st.markdown(f"""
        <div style="padding: 16px 0 24px;">
          <div style="font-family:'Cormorant Garamond',serif;font-size:22px;font-weight:600;color:{INK};letter-spacing:.12em;">STOCK · HAUS</div>
          <div style="font-size:8px;color:{INK_LIGHT};letter-spacing:.28em;text-transform:uppercase;margin-top:2px;">Intelligence &amp; Analytics · Live</div>
          <div style="height:1px;background:linear-gradient(90deg,{GOLD},{GOLD_PALE},transparent);margin-top:12px;"></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f'<div class="section-header">Search Ticker</div>', unsafe_allow_html=True)
        query = st.text_input("", placeholder="AAPL, BMW.DE, 7203.T…", label_visibility="collapsed", key="search_q")

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

        st.markdown(f'<div class="section-header" style="margin-top:20px;">Watchlist</div>', unsafe_allow_html=True)
        bulk = st.text_area("Add tickers (comma/space separated)", placeholder="MSFT, TSLA, LVMH.PA…", height=80)
        if st.button("＋ Add to Watchlist", use_container_width=True):
            news = [t.strip().upper() for t in bulk.replace(",", " ").split() if t.strip()]
            current = st.session_state.get("tickers", ["AAPL"])
            st.session_state.tickers = list(dict.fromkeys(current + news))
            if news:
                st.session_state.active = news[0]
            st.rerun()

        tickers = st.session_state.get("tickers", ["AAPL"])
        if tickers:
            st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
            to_remove = None
            for sym in tickers:
                c1, c2 = st.columns([3, 1])
                with c1:
                    if st.button(sym, key=f"sel_{sym}", use_container_width=True):
                        st.session_state.active = sym
                        st.session_state.view_mode = "detail"
                        st.rerun()
                with c2:
                    if st.button("✕", key=f"rm_{sym}"):
                        to_remove = sym
            if to_remove:
                st.session_state.tickers = [t for t in tickers if t != to_remove]
                if st.session_state.get("active") == to_remove and st.session_state.tickers:
                    st.session_state.active = st.session_state.tickers[0]
                st.rerun()

        st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
        if len(tickers) >= 2:
            if st.button("⇄ Compare All", use_container_width=True):
                st.session_state.view_mode = "compare"
                st.rerun()

        st.markdown(f'<div class="section-header" style="margin-top:24px;">Time Window</div>', unsafe_allow_html=True)
        yr = st.select_slider(
            "",
            options=[1, 2, 3, 5, 10],
            value=st.session_state.get("years", 3),
            format_func=lambda x: f"{x}Y",
            label_visibility="collapsed"
        )
        st.session_state.years = yr

        st.markdown(f"""
        <div style="margin-top:32px;padding:12px 16px;background:{STONE};border-radius:8px;border:1px solid #DDD8CE;">
          <div style="font-size:9px;color:{INK_LIGHT};letter-spacing:.1em;text-transform:uppercase;line-height:1.8;">
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
    if "tickers" not in st.session_state:
        st.session_state.tickers = ["AAPL"]
    if "active" not in st.session_state:
        st.session_state.active = "AAPL"
    if "view_mode" not in st.session_state:
        st.session_state.view_mode = "detail"
    if "years" not in st.session_state:
        st.session_state.years = 3

    tickers, years, mode = render_sidebar()

    if st.session_state.active not in tickers and tickers:
        st.session_state.active = tickers[0]

    if not tickers:
        st.markdown(f"""
        <div style="text-align:center;padding:100px 20px;">
          <div style="font-size:28px;color:{INK_MID};font-weight:400;margin-bottom:10px;">Begin your analysis</div>
          <div style="font-size:13px;color:{INK_LIGHT};">Search any ticker in the sidebar — US, EU, Asia, all exchanges.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    if mode == "compare" and len(tickers) >= 2:
        render_comparison(tickers, years)
    else:
        render_ticker_detail(st.session_state.active, years)

    st.markdown(f"""
    <div style="margin-top:60px;border-top:1px solid #DDD8CE;padding:20px 0;display:flex;justify-content:space-between;">
      <span style="font-size:10px;color:#C5BFB5;letter-spacing:.14em;">STOCK · HAUS</span>
      <span style="font-size:9px;color:#DDD8CE;">Live data via Yahoo Finance · 5 min cache · No CORS proxies</span>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
