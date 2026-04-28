# ══════════════════════════════════════════════════════════════════════════════
# FIN 330 — Stock Analytics Dashboard
# Dark terminal theme | Mobile-first | Live ticker tape
# ══════════════════════════════════════════════════════════════════════════════
# Structure:
#   1. Imports
#   2. Color & Font Constants
#   3. CSS Theme  (apply_theme)
#   4. Ticker Tape
#   5. Calculation Functions  (pure math — no Streamlit calls)
#   6. Chart Functions        (matplotlib — no st calls)
#   7. UI / Display Functions (all st calls live here)
#   8. Main Entry Point
# ══════════════════════════════════════════════════════════════════════════════


# ─── 1. IMPORTS ────────────────────────────────────────────────────────────────
import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import datetime


# ─── 2. COLOR & FONT CONSTANTS ─────────────────────────────────────────────────
# Change one value here and it propagates throughout the entire app.

C_BG        = "#0A0A0A"   # near-black page background
C_SURFACE   = "#111111"   # card / chart surface
C_PANEL     = "#141414"   # sidebar background
C_BORDER    = "#262626"   # subtle borders
C_ACCENT    = "#FF6600"   # signature orange accent
C_ACCENT2   = "#CC5200"   # darker orange for pressed states
C_GREEN     = "#00C853"   # positive / BUY green
C_RED       = "#FF1744"   # negative / SELL red
C_BLUE      = "#2979FF"   # HOLD / neutral blue
C_TEXT      = "#F0F0F0"   # primary white text
C_MUTED     = "#707070"   # secondary muted text
C_TICKER_BG = "#0D0D0D"   # ticker strip background

# Chart line colors
CH_PRICE = "#FF6600"   # price line
CH_MA20  = "#FFD600"   # 20-day MA (yellow)
CH_MA50  = "#00BCD4"   # 50-day MA (cyan)
CH_RSI   = "#CE93D8"   # RSI (purple)
CH_PORT  = "#00C853"   # portfolio return (green)
CH_BENCH = "#2979FF"   # benchmark return (blue)

# Font stack — Calibri if available (Windows), clean fallback everywhere else
FONT = "'Calibri', 'Trebuchet MS', Arial, sans-serif"


# ─── 3. CSS THEME ──────────────────────────────────────────────────────────────

def apply_theme():
    """
    DISPLAY: Inject CSS for the dark terminal theme.

    Key rules:
    - Only hides footer and the top deploy toolbar — NOT the sidebar toggle,
      so the sidebar remains reachable on mobile.
    - Mobile: block container uses tight horizontal padding (0.75 rem).
    - Desktop: padding widens to 2 rem via media query.
    - Expander: Streamlit renders its own header button; we only strip the
      raw <summary> element that overlaps it.
    - Columns stack to single-column on screens narrower than 600 px.
    """
    st.markdown(f"""
    <style>
    /* ── Global font & background ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, .stApp, [class*="css"] {{
        background-color: {C_BG} !important;
        color: {C_TEXT};
        font-family: {FONT};
    }}

    /* ── Hide ONLY footer and top deploy toolbar — sidebar stays intact ── */
    footer {{ visibility: hidden !important; height: 0 !important; }}
    [data-testid="stToolbar"] {{ display: none !important; }}

    /* ── Reduce top padding so the orange bar sits flush ── */
    [data-testid="stAppViewContainer"] > .main {{
        padding-top: 0 !important;
    }}
    .block-container {{
        padding-top: 0 !important;
        padding-bottom: 2rem !important;
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
        max-width: 100% !important;
    }}
    @media (min-width: 768px) {{
        .block-container {{
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }}
    }}

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {{
        background-color: {C_PANEL} !important;
        border-right: 2px solid {C_ACCENT} !important;
    }}
    section[data-testid="stSidebar"] * {{
        color: {C_TEXT} !important;
        font-family: {FONT} !important;
    }}
    /* Sidebar toggle arrow: keep visible but tint it orange */
    [data-testid="collapsedControl"] {{
        color: {C_ACCENT} !important;
        background: {C_PANEL} !important;
    }}

    /* ── Orange top bar ── */
    .top-bar {{
        background: {C_ACCENT};
        padding: 7px 14px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 4px;
        margin-bottom: 0;
    }}
    .top-bar-title {{
        color: #000;
        font-weight: 700;
        font-size: 0.82rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }}
    .top-bar-right {{
        color: #000;
        font-size: 0.72rem;
        opacity: 0.7;
    }}

    /* ── Ticker tape ── */
    .ticker-wrapper {{
        background: {C_TICKER_BG};
        border-top: 1px solid {C_ACCENT};
        border-bottom: 1px solid {C_BORDER};
        overflow: hidden;
        white-space: nowrap;
        padding: 12px 0;
    }}
    .ticker-track {{
        display: inline-block;
        animation: ticker-scroll 80s linear infinite;
    }}
    .ticker-track:hover {{ animation-play-state: paused; }}
    .ticker-item {{
        display: inline-block;
        padding: 0 20px;
        font-size: 0.79rem;
        letter-spacing: 0.02em;
    }}
    .t-sym   {{ color: {C_TEXT};   font-weight: 700; }}
    .t-price {{ color: #AAAAAA;   margin-left: 5px; }}
    .t-up    {{ color: {C_GREEN}; margin-left: 4px; font-size: 0.74rem; }}
    .t-down  {{ color: {C_RED};   margin-left: 4px; font-size: 0.74rem; }}
    @keyframes ticker-scroll {{
        0%   {{ transform: translateX(0); }}
        100% {{ transform: translateX(-50%); }}
    }}

    /* ── Hero / landing card ── */
    .hero-card {{
        background: linear-gradient(135deg, #111111 0%, #1a0900 100%);
        border: 1px solid {C_BORDER};
        border-left: 4px solid {C_ACCENT};
        border-radius: 4px;
        padding: 2rem 1.4rem 1.8rem;
        margin: 1.2rem 0 1.4rem;
        text-align: center;
    }}
    .hero-title {{
        font-size: clamp(1.3rem, 4vw, 1.9rem);
        font-weight: 700;
        color: {C_TEXT};
        letter-spacing: 0.04em;
        margin-bottom: 0.4rem;
    }}
    .hero-title span {{ color: {C_ACCENT}; }}
    .hero-sub {{
        color: {C_MUTED};
        font-size: 0.86rem;
        line-height: 1.6;
        margin-bottom: 1.3rem;
    }}
    .hero-chips {{
        display: flex;
        flex-wrap: wrap;
        gap: 7px;
        justify-content: center;
        margin-bottom: 1.3rem;
    }}
    .chip {{
        background: rgba(255,102,0,0.1);
        border: 1px solid rgba(255,102,0,0.3);
        color: {C_ACCENT};
        border-radius: 3px;
        padding: 4px 11px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.06em;
    }}
    .hero-hint {{
        color: {C_MUTED};
        font-size: 0.78rem;
    }}
    .hero-hint strong {{ color: {C_TEXT}; }}

    /* ── Step labels & dividers ── */
    .step-label {{
        font-size: 0.62rem;
        color: {C_MUTED};
        text-transform: uppercase;
        letter-spacing: 0.18em;
        margin-bottom: 0.05rem;
    }}
    .acc-divider {{
        border: none;
        border-top: 1px solid {C_ACCENT};
        margin: 0.25rem 0 0.9rem;
        opacity: 0.45;
    }}

    /* ── Metric cards ── */
    [data-testid="stMetric"] {{
        background: {C_SURFACE} !important;
        border: 1px solid {C_BORDER} !important;
        border-left: 3px solid {C_ACCENT} !important;
        border-radius: 3px !important;
        padding: 0.75rem 0.9rem !important;
        transition: box-shadow 0.2s;
    }}
    [data-testid="stMetric"]:hover {{
        box-shadow: 0 0 10px rgba(255,102,0,0.14);
    }}
    [data-testid="stMetricLabel"] {{
        color: {C_MUTED} !important;
        font-size: 0.64rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.1em !important;
    }}
    [data-testid="stMetricValue"] {{
        color: {C_TEXT} !important;
        font-size: 1.2rem !important;
        font-weight: 700 !important;
    }}

    /* ── Buttons ── */
    .stButton > button {{
        background: {C_ACCENT} !important;
        color: #000 !important;
        border: none !important;
        border-radius: 3px !important;
        font-weight: 700 !important;
        font-size: 0.82rem !important;
        letter-spacing: 0.08em !important;
        padding: 0.55rem 1rem !important;
        width: 100% !important;
        text-transform: uppercase !important;
        transition: background 0.15s ease !important;
    }}
    .stButton > button:hover {{
        background: {C_ACCENT2} !important;
    }}

    /* ── Download button ── */
    .stDownloadButton > button {{
        background: transparent !important;
        color: {C_ACCENT} !important;
        border: 1px solid {C_ACCENT} !important;
        border-radius: 3px !important;
        font-size: 0.79rem !important;
        width: 100% !important;
    }}

    /* ── Alerts ── */
    .stSuccess {{
        background: rgba(0,200,83,0.07) !important;
        border-left: 3px solid {C_GREEN} !important;
        border-radius: 2px !important;
    }}
    .stError {{
        background: rgba(255,23,68,0.07) !important;
        border-left: 3px solid {C_RED} !important;
        border-radius: 2px !important;
    }}

    /* ── BUY / SELL / HOLD badges ── */
    .badge-buy {{
        display: inline-block;
        background: rgba(0,200,83,0.1);
        color: {C_GREEN};
        border: 1px solid {C_GREEN};
        border-radius: 3px;
        padding: 0.45rem 1.8rem;
        font-size: 1.45rem;
        font-weight: 700;
        letter-spacing: 0.18em;
    }}
    .badge-sell {{
        display: inline-block;
        background: rgba(255,23,68,0.1);
        color: {C_RED};
        border: 1px solid {C_RED};
        border-radius: 3px;
        padding: 0.45rem 1.8rem;
        font-size: 1.45rem;
        font-weight: 700;
        letter-spacing: 0.18em;
    }}
    .badge-hold {{
        display: inline-block;
        background: rgba(41,121,255,0.1);
        color: {C_BLUE};
        border: 1px solid {C_BLUE};
        border-radius: 3px;
        padding: 0.45rem 1.8rem;
        font-size: 1.45rem;
        font-weight: 700;
        letter-spacing: 0.18em;
    }}

    /* ── Disclaimer text ── */
    .disclaimer {{
        color: {C_MUTED};
        font-size: 0.72rem;
        font-style: italic;
        margin-top: 0.65rem;
        border-left: 2px solid {C_BORDER};
        padding-left: 0.6rem;
        line-height: 1.5;
    }}

    /* ── Expander ────────────────────────────────────────────────────────────
       Streamlit renders its own header button for expanders. The raw <summary>
       underneath it causes the doubled "arrow + text" overlap.
       We only hide the raw <summary> — Streamlit's styled button still works.
    ── */
    [data-testid="stExpander"] details summary {{
        display: none !important;
    }}
    [data-testid="stExpander"] {{
        background: {C_SURFACE} !important;
        border: 1px solid {C_BORDER} !important;
        border-radius: 3px !important;
    }}

    /* ── Radio buttons ── */
    div[data-testid="stRadio"] label {{
        background: {C_SURFACE};
        border: 1px solid {C_BORDER};
        border-radius: 3px;
        padding: 0.38rem 0.7rem;
        font-size: 0.82rem;
        cursor: pointer;
        display: block;
        margin-bottom: 3px;
        transition: border-color 0.15s;
    }}
    div[data-testid="stRadio"] label:has(input:checked) {{
        border-color: {C_ACCENT};
        color: {C_ACCENT} !important;
        background: rgba(255,102,0,0.07);
    }}

    /* ── Sliders ── */
    [data-testid="stSlider"] [role="slider"] {{
        background: {C_ACCENT} !important;
    }}

    /* ── Text inputs ── */
    [data-testid="stTextInput"] input {{
        background: {C_SURFACE} !important;
        border: 1px solid {C_BORDER} !important;
        border-radius: 3px !important;
        color: {C_TEXT} !important;
        font-family: {FONT} !important;
    }}
    [data-testid="stTextInput"] input:focus {{
        border-color: {C_ACCENT} !important;
        box-shadow: 0 0 0 1px {C_ACCENT}44 !important;
    }}

    /* ── Dataframe ── */
    [data-testid="stDataFrame"] {{
        border: 1px solid {C_BORDER} !important;
        border-radius: 3px !important;
    }}

    /* ── Page-level headers ── */
    h1, h2, h3 {{
        color: {C_TEXT} !important;
        font-family: {FONT} !important;
    }}

    /* ── Mobile: stack columns on narrow screens ── */
    @media (max-width: 600px) {{
        [data-testid="column"] {{
            min-width: 100% !important;
            width: 100% !important;
        }}
        .badge-buy, .badge-sell, .badge-hold {{
            font-size: 1.15rem;
            padding: 0.4rem 1rem;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)


# ─── 4. TICKER TAPE ────────────────────────────────────────────────────────────
# Live market prices — cached 5 minutes to avoid hammering Yahoo Finance.

TICKER_SYMBOLS = [
    "AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA",
    "JPM","V","UNH","XOM","JNJ","WMT","MA","PG","HD",
    "CVX","MRK","LLY","ABBV","PEP","KO","AVGO","COST",
    "MCD","TMO","BAC","WFC","GS","MS",
    "SPY","QQQ","DIA"
]


@st.cache_data(ttl=300)
def fetch_ticker_data(symbols: list) -> list:
    """
    DATA: Batch-download 2 days of closing prices for all tape symbols.
    Returns a list of dicts: {symbol, price, change_pct}.
    Cached for 5 minutes (ttl=300) — yfinance is slow for large batches.
    """
    results = []
    try:
        raw = yf.download(symbols, period="2d", progress=False, threads=True)["Close"]
        if raw.empty:
            return results
        if isinstance(raw, pd.Series):
            raw = raw.to_frame()
        for sym in symbols:
            if sym not in raw.columns:
                continue
            col = raw[sym].dropna()
            if len(col) < 2:
                continue
            price = float(col.iloc[-1])
            prev  = float(col.iloc[-2])
            chg   = (price - prev) / prev * 100
            results.append({"symbol": sym, "price": price, "change_pct": chg})
    except Exception:
        pass   # if fetch fails, the tape is simply skipped — non-critical
    return results


def render_ticker_tape():
    """
    DISPLAY: Build and inject the scrolling HTML ticker tape.
    Items are duplicated so the CSS scroll animation loops seamlessly.
    """
    data = fetch_ticker_data(TICKER_SYMBOLS)
    if not data:
        return

    items = ""
    for d in data:
        arrow = "▲" if d["change_pct"] >= 0 else "▼"
        cls   = "t-up" if d["change_pct"] >= 0 else "t-down"
        items += (
            f'<span class="ticker-item">'
            f'<span class="t-sym">{d["symbol"]}</span>'
            f'<span class="t-price">${d["price"]:.2f}</span>'
            f'<span class="{cls}">{arrow}{abs(d["change_pct"]):.2f}%</span>'
            f'</span>'
            f'<span style="color:#303030;margin:0 2px;font-size:0.65rem;">|</span>'
        )

    # Duplicate items so the loop has no visible seam
    st.markdown(
        f'<div class="ticker-wrapper">'
        f'<div class="ticker-track">{items}{items}</div>'
        f'</div>',
        unsafe_allow_html=True
    )


# ─── 5. CALCULATION FUNCTIONS ──────────────────────────────────────────────────
# Pure math — zero Streamlit calls in this section.


# ── Stock Analysis helpers ──────────────────────────────────────────────────

def fetch_stock_data(ticker: str):
    """DATA: Download 6 months of daily OHLCV for one ticker."""
    stock = yf.Ticker(ticker)
    df    = stock.history(period="6mo")
    return stock, df


def calc_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    """PROCESSING: Append MA20 and MA50 columns to the price DataFrame."""
    df["MA20"] = df["Close"].rolling(20).mean()
    df["MA50"] = df["Close"].rolling(50).mean()
    return df


def calc_trend(df: pd.DataFrame) -> str:
    """
    PROCESSING: Classify trend as Uptrend / Downtrend / Mixed.
    Logic: Price > MA20 > MA50 → Strong Uptrend. Reverse → Strong Downtrend.
    """
    price = df["Close"].iloc[-1]
    ma20  = df["MA20"].iloc[-1]
    ma50  = df["MA50"].iloc[-1]
    if price > ma20 > ma50:  return "Strong Uptrend"
    if price < ma20 < ma50:  return "Strong Downtrend"
    return "Mixed Trend"


def calc_rsi(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    """
    PROCESSING: 14-day RSI appended as df['RSI'].
    RSI > 70 → overbought. RSI < 30 → oversold.
    """
    delta    = df["Close"].diff()
    gain     = delta.clip(lower=0).rolling(window).mean()
    loss     = (-delta.clip(upper=0)).rolling(window).mean()
    rs       = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df


def interpret_rsi(rsi: float) -> str:
    """PROCESSING: Human-readable RSI signal label."""
    if rsi > 70:  return "Overbought (Possible Sell)"
    if rsi < 30:  return "Oversold (Possible Buy)"
    return "Neutral"


def calc_volatility(df: pd.DataFrame) -> float:
    """
    PROCESSING: 20-day annualised volatility expressed as a percentage.
    Formula: rolling_std(20) × √252 × 100.
    """
    return df["Close"].pct_change().rolling(20).std().iloc[-1] * np.sqrt(252) * 100


def calc_annualized_return(df: pd.DataFrame) -> float:
    """
    PROCESSING: Annualised return from the 6-month window.
    Formula: (end/start)^(252/n) − 1, result in %.
    252 = approximate US trading days per year.
    """
    start = df["Close"].iloc[0]
    end   = df["Close"].iloc[-1]
    n     = len(df)
    return ((end / start) ** (252 / n) - 1) * 100


def classify_volatility(vol: float) -> str:
    """PROCESSING: Bucket annualised volatility into High / Medium / Low."""
    if vol > 40:  return "High"
    if vol >= 25: return "Medium"
    return "Low"


def build_recommendation(ticker, trend, rsi, vol_level, vol):
    """
    PROCESSING: Combine trend + RSI + volatility into a BUY / SELL / HOLD call.
    Returns (recommendation_string, explanation_string).
    """
    if trend == "Strong Uptrend" and rsi < 70:
        rec = "BUY"
        exp = (
            f"{ticker} is in a strong uptrend (Price > 20-Day MA > 50-Day MA) "
            f"with RSI not yet overbought ({rsi:.1f}). "
            f"Volatility is {vol_level.lower()} at {vol:.1f}%. Conditions support a buy."
        )
    elif trend == "Strong Downtrend" or rsi > 70:
        rec = "SELL"
        exp = (
            f"{ticker} shows a downtrend or overbought RSI ({rsi:.1f}). "
            f"Trend: {trend}. Volatility: {vol_level.lower()} ({vol:.1f}%). "
            "Consider reducing exposure."
        )
    else:
        rec = "HOLD"
        exp = (
            f"Mixed signals for {ticker}. Trend: {trend}. "
            f"RSI: {rsi:.1f} (Neutral). "
            f"Volatility: {vol_level.lower()} ({vol:.1f}%). "
            "Wait for a clearer signal before acting."
        )
    return rec, exp


# ── Portfolio Dashboard helpers ─────────────────────────────────────────────

def fetch_portfolio_data(tickers: list, benchmark: str) -> pd.DataFrame:
    """DATA: 1 year of closing prices for all portfolio tickers plus benchmark."""
    raw = yf.download(tickers + [benchmark], period="1y", progress=False)["Close"]
    return raw


def calc_portfolio_returns(raw, tickers, weights, benchmark):
    """
    PROCESSING: Weighted portfolio returns and cumulative growth curves.
    Returns: returns_df, port_daily, bench_daily, port_cumulative, bench_cumulative.
    """
    rets       = raw.pct_change().dropna()
    port_rets  = rets[tickers].dot(weights)
    bench_rets = rets[benchmark]
    port_cum   = (1 + port_rets).cumprod()
    bench_cum  = (1 + bench_rets).cumprod()
    return rets, port_rets, bench_rets, port_cum, bench_cum


def calc_performance_metrics(port_rets, bench_rets, port_cum, bench_cum):
    """
    PROCESSING: Total return, outperformance, annualised volatility, Sharpe ratio.
    Sharpe uses a 0% risk-free rate assumption.
    """
    total_ret = (port_cum.iloc[-1]  - 1) * 100
    bench_ret = (bench_cum.iloc[-1] - 1) * 100
    outperf   = total_ret - bench_ret
    port_vol  = port_rets.std()  * np.sqrt(252) * 100
    bench_vol = bench_rets.std() * np.sqrt(252) * 100
    ann_ret   = port_rets.mean() * 252
    sharpe    = ann_ret / (port_rets.std() * np.sqrt(252))
    return total_ret, bench_ret, outperf, port_vol, bench_vol, sharpe


def build_interpretation(benchmark, total_ret, bench_ret,
                          outperf, port_vol, bench_vol, sharpe) -> list:
    """
    PROCESSING: Produce 3 plain-English summary sentences from metrics.
    """
    lines = []
    word = "outperformed" if outperf > 0 else "underperformed"
    lines.append(f"The portfolio {word} {benchmark} by {abs(outperf):.2f}%.")

    risk_word = "more" if port_vol > bench_vol else "less"
    lines.append(
        f"The portfolio carried {risk_word} risk than the benchmark "
        f"({port_vol:.2f}% vs {bench_vol:.2f}% annualised volatility)."
    )

    if sharpe > 1:
        lines.append(f"A Sharpe ratio of {sharpe:.2f} indicates good risk-adjusted returns.")
    elif sharpe > 0:
        lines.append(f"A Sharpe ratio of {sharpe:.2f} indicates modest risk-adjusted returns.")
    else:
        lines.append(
            f"A Sharpe ratio of {sharpe:.2f} — returns did not compensate for risk taken."
        )
    return lines


# ─── 6. CHART FUNCTIONS ────────────────────────────────────────────────────────
# Each function returns a styled matplotlib Figure. No st.pyplot() here.

def _style(ax, fig, title=""):
    """
    DISPLAY: Apply dark terminal theme to any matplotlib Axes.
    Called by every chart function below.
    """
    fig.patch.set_facecolor(C_SURFACE)
    ax.set_facecolor(C_BG)
    ax.set_title(title, color=C_TEXT, fontsize=9.5, pad=8, fontweight="bold")
    ax.set_xlabel(ax.get_xlabel(), color=C_MUTED, fontsize=7.5)
    ax.set_ylabel(ax.get_ylabel(), color=C_MUTED, fontsize=7.5)
    ax.tick_params(colors=C_MUTED, labelsize=6.5)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(C_BORDER)
    ax.spines["bottom"].set_color(C_BORDER)
    ax.grid(True, color="#1C1C1C", linewidth=0.5, alpha=0.9)
    ax.axhline(ax.get_ylim()[0], color=C_ACCENT, linewidth=0.9, alpha=0.3)
    leg = ax.get_legend()
    if leg:
        leg.get_frame().set_facecolor(C_SURFACE)
        leg.get_frame().set_edgecolor(C_BORDER)
        for t in leg.get_texts():
            t.set_color(C_TEXT)
            t.set_fontsize(7)


def chart_price_ma(df, ticker):
    """DISPLAY: Close price with 20-day and 50-day moving average overlays."""
    fig, ax = plt.subplots(figsize=(10, 3.2))
    ax.plot(df.index, df["Close"], label="Price",     color=CH_PRICE, lw=1.8)
    ax.plot(df.index, df["MA20"],  label="20-Day MA", color=CH_MA20,  lw=1.1, ls="--")
    ax.plot(df.index, df["MA50"],  label="50-Day MA", color=CH_MA50,  lw=1.1, ls="--")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price ($)")
    ax.legend(loc="upper left", fontsize=7)
    _style(ax, fig, f"{ticker}  |  PRICE & MOVING AVERAGES")
    fig.tight_layout()
    return fig


def chart_rsi(df, ticker):
    """DISPLAY: 14-day RSI with overbought (70) and oversold (30) shading."""
    fig, ax = plt.subplots(figsize=(10, 2.4))
    ax.plot(df.index, df["RSI"], label="RSI (14)", color=CH_RSI, lw=1.5)
    ax.axhline(70, color=C_RED,   ls="--", lw=0.85, label="Overbought 70")
    ax.axhline(30, color=C_GREEN, ls="--", lw=0.85, label="Oversold 30")
    ax.fill_between(df.index, 70, 100, alpha=0.05, color=C_RED)
    ax.fill_between(df.index, 0,  30,  alpha=0.05, color=C_GREEN)
    ax.set_ylim(0, 100)
    ax.set_xlabel("Date")
    ax.set_ylabel("RSI")
    ax.legend(loc="upper left", fontsize=7)
    _style(ax, fig, f"{ticker}  |  RSI (14-DAY)")
    fig.tight_layout()
    return fig


def chart_cumulative_returns(port_cum, bench_cum, benchmark):
    """DISPLAY: Cumulative growth-of-$1 chart — portfolio vs benchmark."""
    fig, ax = plt.subplots(figsize=(10, 3.2))
    ax.plot(port_cum.index,  port_cum,  label="Portfolio", color=CH_PORT,  lw=2)
    ax.plot(bench_cum.index, bench_cum, label=benchmark,   color=CH_BENCH, lw=1.5, ls="--")
    ax.axhline(1.0, color=C_MUTED, lw=0.65, ls=":")
    ax.set_xlabel("Date")
    ax.set_ylabel("Growth of $1")
    ax.legend(loc="upper left", fontsize=7)
    _style(ax, fig, "PORTFOLIO vs BENCHMARK  |  CUMULATIVE RETURN")
    fig.tight_layout()
    return fig


def chart_individual_returns(returns, tickers):
    """DISPLAY: Bar chart of each stock's 1-year total return (green = gain, red = loss)."""
    ind    = ((1 + returns[tickers]).cumprod().iloc[-1] - 1) * 100
    colors = [C_GREEN if v >= 0 else C_RED for v in ind.values]
    w      = max(6, len(tickers) * 1.3)
    fig, ax = plt.subplots(figsize=(w, 3.2))
    ax.bar(ind.index, ind.values, color=colors, width=0.55, alpha=0.9)
    ax.axhline(0, color=C_MUTED, lw=0.7)
    ax.set_xlabel("Ticker")
    ax.set_ylabel("Return (%)")
    for i, (t, v) in enumerate(ind.items()):
        offset = 0.8 if v >= 0 else -3.2
        ax.text(i, v + offset, f"{v:.1f}%",
                ha="center", fontsize=7.5,
                color=C_GREEN if v >= 0 else C_RED)
    _style(ax, fig, "INDIVIDUAL STOCK RETURNS  |  1 YEAR")
    fig.tight_layout()
    return fig


# ─── 7. UI / DISPLAY FUNCTIONS ─────────────────────────────────────────────────
# All st.* calls live here — no calculations or chart building in this section.

def ui_step_header(n: int, title: str):
    """DISPLAY: Numbered step label, subheader, and a thin orange divider."""
    st.markdown(f"<p class='step-label'>Step {n}</p>", unsafe_allow_html=True)
    st.subheader(title)
    st.markdown("<hr class='acc-divider'>", unsafe_allow_html=True)


def ui_badge(rec: str, explanation: str):
    """
    DISPLAY: Coloured BUY / SELL / HOLD badge, explanation text, and disclaimer.
    The disclaimer is required per project spec.
    """
    cls = {"BUY": "badge-buy", "SELL": "badge-sell"}.get(rec, "badge-hold")
    st.markdown(f"<div class='{cls}'>{rec}</div>", unsafe_allow_html=True)
    st.write("")
    st.write(explanation)
    st.markdown(
        "<p class='disclaimer'>This is the recommendation based off of the shown "
        "variables. This is not financial advice.</p>",
        unsafe_allow_html=True
    )


def ui_landing_stock():
    """
    DISPLAY: Hero card shown on the Stock Analysis page before analysis runs.
    Replaces the previous plain grey placeholder text.
    """
    st.markdown(f"""
    <div class="hero-card">
        <div class="hero-title">STOCK <span>ANALYTICS</span></div>
        <div class="hero-sub">
            Real-time signals, moving averages, momentum, and volatility —<br>
            all in one professional dashboard.
        </div>
        <div class="hero-chips">
            <span class="chip">TREND ANALYSIS</span>
            <span class="chip">RSI MOMENTUM</span>
            <span class="chip">VOLATILITY</span>
            <span class="chip">TRADING SIGNAL</span>
            <span class="chip">ANNUALISED RETURN</span>
        </div>
        <div class="hero-hint">
            Enter a <strong>ticker symbol</strong> in the sidebar and press
            <strong>Run Analysis</strong> to begin.
        </div>
    </div>
    """, unsafe_allow_html=True)


def ui_landing_portfolio():
    """
    DISPLAY: Hero card shown on the Portfolio Dashboard page before analysis runs.
    """
    st.markdown(f"""
    <div class="hero-card">
        <div class="hero-title">PORTFOLIO <span>DASHBOARD</span></div>
        <div class="hero-sub">
            Multi-asset return analytics, risk metrics, and benchmark comparison —<br>
            customise your holdings with the sidebar sliders.
        </div>
        <div class="hero-chips">
            <span class="chip">CUMULATIVE RETURN</span>
            <span class="chip">VOLATILITY</span>
            <span class="chip">SHARPE RATIO</span>
            <span class="chip">BENCHMARK</span>
            <span class="chip">OUTPERFORMANCE</span>
        </div>
        <div class="hero-hint">
            Set tickers &amp; adjust weights in the sidebar, then press
            <strong>Run Analysis</strong>.
        </div>
    </div>
    """, unsafe_allow_html=True)


def ui_stock_analysis(ticker: str):
    """
    DISPLAY: Renders all 5 steps of Stock Analysis.
    Steps: Data Collection → Trend → Momentum (RSI) → Volatility → Recommendation.
    """

    # ── Step 1: Data Collection ───────────────────────────────────────────────
    ui_step_header(1, "Data Collection")
    _, df = fetch_stock_data(ticker)

    if df.empty:
        st.error(f"No data found for '{ticker}'. Please check the ticker symbol.")
        st.stop()

    st.success(f"✓  6 months of daily data loaded for **{ticker}**")

    # Expander: label is short and descriptive; the raw <summary> is CSS-hidden
    # so there is no double-arrow or overlapping text.
    with st.expander("View Raw Data (Last 10 Rows)"):
        st.dataframe(
            df[["Open", "High", "Low", "Close", "Volume"]].tail(10),
            use_container_width=True
        )

    # ── Step 2: Trend Analysis ────────────────────────────────────────────────
    ui_step_header(2, "Trend Analysis  |  Moving Averages")
    df    = calc_moving_averages(df)
    trend = calc_trend(df)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Current Price", f"${df['Close'].iloc[-1]:.2f}")
    c2.metric("20-Day MA",     f"${df['MA20'].iloc[-1]:.2f}")
    c3.metric("50-Day MA",     f"${df['MA50'].iloc[-1]:.2f}")
    c4.metric("Trend Signal",  trend)

    st.pyplot(chart_price_ma(df, ticker), use_container_width=True)

    # ── Step 3: Momentum / RSI ────────────────────────────────────────────────
    ui_step_header(3, "Momentum  |  14-Day RSI")
    df        = calc_rsi(df)
    rsi_value = float(df["RSI"].iloc[-1])
    rsi_sig   = interpret_rsi(rsi_value)

    c1, c2 = st.columns(2)
    c1.metric("RSI (14-Day)", f"{rsi_value:.2f}")
    c2.metric("Signal",       rsi_sig)

    st.pyplot(chart_rsi(df, ticker), use_container_width=True)

    # ── Step 4: Volatility & Annualised Return ────────────────────────────────
    ui_step_header(4, "Volatility & Return  |  20-Day Annualised")
    vol      = calc_volatility(df)
    vol_lvl  = classify_volatility(vol)
    ann_ret  = calc_annualized_return(df)

    c1, c2, c3 = st.columns(3)
    c1.metric("Annualised Volatility", f"{vol:.2f}%")
    c2.metric("Volatility Level",       vol_lvl)
    c3.metric("Annualised Return",      f"{ann_ret:.2f}%")

    # ── Step 5: Trading Recommendation ───────────────────────────────────────
    ui_step_header(5, "Trading Recommendation")
    rec, exp = build_recommendation(ticker, trend, rsi_value, vol_lvl, vol)
    ui_badge(rec, exp)

    # ── Download ──────────────────────────────────────────────────────────────
    st.markdown(
        f"<hr style='border-top:1px solid {C_BORDER};margin-top:2rem'>",
        unsafe_allow_html=True
    )
    st.download_button(
        label="Download Stock Data as CSV",
        data=df.to_csv().encode("utf-8"),
        file_name=f"{ticker}_analysis.csv",
        mime="text/csv"
    )


def ui_portfolio_dashboard(tickers_input: str, weights: list, benchmark: str):
    """
    DISPLAY: Renders all 6 steps of the Portfolio Dashboard.
    Steps: Setup → Data → Return Calculations → Performance Metrics
           → Interpretation → Individual Stock Returns.
    Works with any number of tickers (not restricted to 5).
    """
    tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

    # Input guards
    if not tickers:
        st.error("Enter at least one ticker symbol.")
        st.stop()
    if len(weights) != len(tickers):
        st.error("Weight count does not match ticker count. Please adjust the sidebar.")
        st.stop()
    if abs(sum(weights) - 1.0) > 0.01:
        st.error(f"Weights sum to {sum(weights):.2f} — they must equal 1.00.")
        st.stop()

    # ── Step 1: Portfolio Setup ───────────────────────────────────────────────
    ui_step_header(1, "Portfolio Setup")
    weight_df = pd.DataFrame({
        "Ticker": tickers,
        "Weight": [f"{w:.1%}" for w in weights]
    })
    c1, _ = st.columns([1, 3])
    c1.dataframe(weight_df, use_container_width=True, hide_index=True)

    # ── Step 2: Data Collection ───────────────────────────────────────────────
    ui_step_header(2, "Data Collection  |  1 Year")
    raw = fetch_portfolio_data(tickers, benchmark)

    if raw.empty:
        st.error("Could not download price data. Check your ticker symbols.")
        st.stop()

    st.success(f"✓  1 year of data loaded for: **{', '.join(tickers + [benchmark])}**")

    with st.expander("View Closing Prices (Last 5 Rows)"):
        st.dataframe(raw.tail(5), use_container_width=True)

    # ── Step 3: Return Calculations ───────────────────────────────────────────
    ui_step_header(3, "Return Calculations  |  Portfolio vs Benchmark")
    rets, port_rets, bench_rets, port_cum, bench_cum = \
        calc_portfolio_returns(raw, tickers, weights, benchmark)

    st.pyplot(
        chart_cumulative_returns(port_cum, bench_cum, benchmark),
        use_container_width=True
    )

    # ── Step 4: Performance Metrics ──────────────────────────────────────────
    ui_step_header(4, "Performance Metrics")
    total_ret, bench_ret, outperf, port_vol, bench_vol, sharpe = \
        calc_performance_metrics(port_rets, bench_rets, port_cum, bench_cum)

    c1, c2, c3 = st.columns(3)
    c1.metric("Portfolio Return",   f"{total_ret:.2f}%")
    c2.metric("Benchmark Return",   f"{bench_ret:.2f}%",
              delta=f"{outperf:+.2f}% vs benchmark")
    c3.metric("Outperformance",     f"{outperf:+.2f}%")

    st.write("")

    c4, c5, c6 = st.columns(3)
    c4.metric("Portfolio Volatility",  f"{port_vol:.2f}%")
    c5.metric("Benchmark Volatility",  f"{bench_vol:.2f}%")
    c6.metric("Sharpe Ratio",          f"{sharpe:.2f}")

    # ── Step 5: Interpretation ────────────────────────────────────────────────
    ui_step_header(5, "Interpretation")
    for line in build_interpretation(
        benchmark, total_ret, bench_ret,
        outperf, port_vol, bench_vol, sharpe
    ):
        st.write(f"• {line}")

    # ── Step 6: Individual Stock Returns ──────────────────────────────────────
    st.write("")
    ui_step_header(6, "Individual Stock Returns")
    st.pyplot(chart_individual_returns(rets, tickers), use_container_width=True)

    # ── Download ──────────────────────────────────────────────────────────────
    st.markdown(
        f"<hr style='border-top:1px solid {C_BORDER};margin-top:2rem'>",
        unsafe_allow_html=True
    )
    combined = pd.DataFrame({"Portfolio": port_rets, benchmark: bench_rets})
    st.download_button(
        label="Download Portfolio Returns as CSV",
        data=combined.to_csv().encode("utf-8"),
        file_name="portfolio_returns.csv",
        mime="text/csv"
    )


# ─── 8. MAIN ENTRY POINT ───────────────────────────────────────────────────────

def main():
    # set_page_config must be the very first Streamlit call
    st.set_page_config(
        page_title="FIN 330 | Analytics Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"   # sidebar open on load (including mobile)
    )

    # Inject CSS theme
    apply_theme()

    # ── Orange top bar ────────────────────────────────────────────────────────
    now = datetime.datetime.now().strftime("%H:%M  %b %d, %Y")
    st.markdown(f"""
    <div class="top-bar">
        <span class="top-bar-title">FIN 330 &nbsp;|&nbsp; ANALYTICS DASHBOARD</span>
        <span class="top-bar-right">LIVE DATA · {now}</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Scrolling ticker tape ─────────────────────────────────────────────────
    render_ticker_tape()

    # Small vertical spacer between tape and content
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # ── Sidebar header ────────────────────────────────────────────────────────
    st.sidebar.markdown(f"""
    <div style="padding:10px 0 6px;">
        <span style="color:{C_ACCENT};font-size:1.05rem;font-weight:700;
                     letter-spacing:0.1em;">FIN 330</span><br>
        <span style="color:{C_MUTED};font-size:0.7rem;letter-spacing:0.06em;">
            ANALYTICS DASHBOARD
        </span>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown(
        f"<hr style='border-top:2px solid {C_ACCENT};margin:0.3rem 0 0.6rem;'>",
        unsafe_allow_html=True
    )

    # ── Navigation ────────────────────────────────────────────────────────────
    section = st.sidebar.radio(
        "Navigate",
        ["Stock Analysis", "Portfolio Dashboard"],
        label_visibility="collapsed"
    )

    st.sidebar.markdown(
        f"<hr style='border-top:1px solid {C_BORDER};margin:0.5rem 0;'>",
        unsafe_allow_html=True
    )

    # ══ STOCK ANALYSIS PAGE ══════════════════════════════════════════════════

    if section == "Stock Analysis":
        st.sidebar.markdown(
            f"<p style='color:{C_MUTED};font-size:0.66rem;text-transform:uppercase;"
            f"letter-spacing:0.14em;margin-bottom:0.3rem;'>Stock Settings</p>",
            unsafe_allow_html=True
        )
        ticker = st.sidebar.text_input("Ticker Symbol", "AAPL").upper().strip()
        st.sidebar.write("")
        run = st.sidebar.button("Run Analysis")

        # Page header
        st.markdown(
            f"<h2 style='color:{C_ACCENT};font-weight:700;letter-spacing:0.05em;"
            f"margin-bottom:0;font-size:clamp(1.1rem,3vw,1.45rem);'>STOCK ANALYSIS</h2>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<p style='color:{C_MUTED};margin-top:0.15rem;font-size:0.82rem;'>"
            "Individual stock trend, momentum, volatility and trading recommendation.</p>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<hr style='border-top:1px solid {C_BORDER};margin-bottom:1rem;'>",
            unsafe_allow_html=True
        )

        if run:
            ui_stock_analysis(ticker)
        else:
            ui_landing_stock()

    # ══ PORTFOLIO DASHBOARD PAGE ════════════════════════════════════════════

    elif section == "Portfolio Dashboard":
        st.sidebar.markdown(
            f"<p style='color:{C_MUTED};font-size:0.66rem;text-transform:uppercase;"
            f"letter-spacing:0.14em;margin-bottom:0.3rem;'>Portfolio Settings</p>",
            unsafe_allow_html=True
        )

        tickers_input = st.sidebar.text_input(
            "Tickers (comma-separated)",
            "AAPL, MSFT, JPM, AMZN, NVDA"
        )
        benchmark = st.sidebar.text_input("Benchmark ETF", "SPY").upper().strip()

        # Parse tickers so sliders can be built per-ticker immediately
        raw_tickers = [t.strip().upper()
                       for t in tickers_input.split(",") if t.strip()]

        # ── Weight sliders — one per ticker, auto-normalised ──────────────────
        weights_raw = []
        if raw_tickers:
            st.sidebar.markdown(
                f"<p style='color:{C_MUTED};font-size:0.66rem;text-transform:uppercase;"
                f"letter-spacing:0.12em;margin-top:0.5rem;margin-bottom:0.2rem;'>Weights</p>",
                unsafe_allow_html=True
            )
            default_w = round(1.0 / len(raw_tickers), 2)
            for t in raw_tickers:
                w = st.sidebar.slider(
                    label=t,
                    min_value=0.0,
                    max_value=1.0,
                    value=default_w,
                    step=0.01,
                    key=f"w_{t}"
                )
                weights_raw.append(w)

            # Normalise so weights always sum to exactly 1.00
            total_w = sum(weights_raw)
            if total_w > 0:
                weights_norm = [w / total_w for w in weights_raw]
            else:
                weights_norm = [1.0 / len(raw_tickers)] * len(raw_tickers)

            st.sidebar.caption("Weights auto-normalised → sum = 1.00")
        else:
            weights_norm = []

        st.sidebar.write("")
        run = st.sidebar.button("Run Analysis")

        # Page header
        st.markdown(
            f"<h2 style='color:{C_ACCENT};font-weight:700;letter-spacing:0.05em;"
            f"margin-bottom:0;font-size:clamp(1.1rem,3vw,1.45rem);'>PORTFOLIO DASHBOARD</h2>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<p style='color:{C_MUTED};margin-top:0.15rem;font-size:0.82rem;'>"
            "Multi-asset return analytics, risk metrics and benchmark comparison.</p>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<hr style='border-top:1px solid {C_BORDER};margin-bottom:1rem;'>",
            unsafe_allow_html=True
        )

        if run:
            ui_portfolio_dashboard(tickers_input, weights_norm, benchmark)
        else:
            ui_landing_portfolio()


# ── Run ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
