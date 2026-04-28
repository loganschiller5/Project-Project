# ══════════════════════════════════════════════════════════════════════════════
# FIN 330 Stock Analytics Dashboard
# Bloomberg-inspired design | Calibri font | Live S&P 500 ticker tape
# ══════════════════════════════════════════════════════════════════════════════
# Structure:
#   1. Imports
#   2. Theme & Styling (Bloomberg palette, Calibri font, ticker tape CSS)
#   3. Ticker Tape (live S&P 500 price scroll)
#   4. Logic / Calculation Functions
#   5. Chart Functions
#   6. Display / UI Functions
#   7. Main App Entry Point
# ══════════════════════════════════════════════════════════════════════════════


# ─── 1. IMPORTS ────────────────────────────────────────────────────────────────
import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import time


# ─── 2. THEME & STYLING ────────────────────────────────────────────────────────
# Bloomberg color palette: near-black background, orange accents, white text.
# All color constants are defined here so changes propagate everywhere.

C_BG        = "#0A0A0A"   # Bloomberg terminal black background
C_SURFACE   = "#111111"   # slightly lighter surface for cards
C_PANEL     = "#1A1A1A"   # sidebar and panel background
C_BORDER    = "#2A2A2A"   # very subtle borders
C_ACCENT    = "#FF6600"   # Bloomberg signature orange
C_ACCENT2   = "#E85500"   # darker orange for hover states
C_GREEN     = "#00C853"   # positive / buy signal green
C_RED       = "#FF1744"   # negative / sell signal red
C_BLUE      = "#2979FF"   # neutral / info blue
C_TEXT      = "#F5F5F5"   # primary white text
C_MUTED     = "#757575"   # secondary grey text
C_TICKER_BG = "#0D0D0D"   # ticker tape background

# Chart line colors
CH_PRICE  = "#FF6600"   # price line (Bloomberg orange)
CH_MA20   = "#FFD600"   # 20-day MA (yellow)
CH_MA50   = "#00BCD4"   # 50-day MA (cyan)
CH_RSI    = "#CE93D8"   # RSI (purple)
CH_PORT   = "#00C853"   # portfolio (green)
CH_BENCH  = "#2979FF"   # benchmark (blue)

# Font stack: Calibri first, fallback to system sans-serif
FONT = "'Calibri', 'Gill Sans', 'Trebuchet MS', Arial, sans-serif"


def apply_theme():
    """
    DISPLAY: Inject all CSS for the Bloomberg-style dark theme.
    Covers page, sidebar, metrics, buttons, badges, and the ticker tape.
    Calibri is set as the primary font throughout.

    CHANGES:
    - Ticker tape padding increased from 6px to 14px (taller, still subtle)
    - Expander summary text cleaned up (no overlapping, just shows label)
    - Disclaimer text style added (.disclaimer class)
    - General polish: smoother transitions, subtle glow on hover for metrics
    """
    st.markdown(f"""
    <style>
        /* ── Load Calibri via Google Fonts fallback (system font on Windows) ── */
        @import url('https://fonts.googleapis.com/css2?family=Encode+Sans:wght@300;400;600;700&display=swap');

        /* ── Global page ── */
        html, body, .stApp, [class*="css"] {{
            background-color: {C_BG} !important;
            color: {C_TEXT};
            font-family: {FONT};
        }}

        /* ── Remove default Streamlit padding at the very top ── */
        .block-container {{
            padding-top: 0rem !important;
            padding-bottom: 2rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }}

        /* ── Sidebar ── */
        section[data-testid="stSidebar"] {{
            background-color: {C_PANEL} !important;
            border-right: 2px solid {C_ACCENT};
        }}
        section[data-testid="stSidebar"] * {{
            color: {C_TEXT} !important;
            font-family: {FONT} !important;
        }}
        section[data-testid="stSidebar"] .stRadio label {{
            font-size: 0.9rem;
            letter-spacing: 0.04em;
        }}

        /* ── All text elements use Calibri ── */
        h1, h2, h3, h4, p, span, div, label, input, button, td, th {{
            font-family: {FONT} !important;
        }}

        /* ── Headers ── */
        h1 {{
            color: {C_TEXT} !important;
            font-size: 1.6rem !important;
            font-weight: 700 !important;
            letter-spacing: 0.04em;
        }}
        h2, h3 {{
            color: {C_TEXT} !important;
            font-weight: 600 !important;
            letter-spacing: 0.03em;
        }}

        /* ── Bloomberg-style orange top bar (rendered via HTML below) ── */
        .bbg-topbar {{
            background-color: {C_ACCENT};
            padding: 6px 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0;
        }}
        .bbg-topbar-title {{
            color: #000;
            font-weight: 700;
            font-size: 0.85rem;
            letter-spacing: 0.12em;
            font-family: {FONT};
        }}
        .bbg-topbar-right {{
            color: #000;
            font-size: 0.75rem;
            font-family: {FONT};
            opacity: 0.7;
        }}

        /* ── Ticker tape strip ─────────────────────────────────────────────────
           CHANGE: padding increased from 6px → 14px top/bottom to make the
           tape taller. Still subtle — no border radius or heavy chrome added.
        ── */
        .ticker-wrapper {{
            background-color: {C_TICKER_BG};
            border-top: 1px solid {C_ACCENT};
            border-bottom: 1px solid {C_BORDER};
            overflow: hidden;
            white-space: nowrap;
            padding: 14px 0;        /* ← was 6px, now 14px for a taller tape */
            margin-bottom: 0;
        }}
        .ticker-track {{
            display: inline-block;
            animation: ticker-scroll 90s linear infinite;
        }}
        .ticker-track:hover {{
            animation-play-state: paused;
        }}
        .ticker-item {{
            display: inline-block;
            padding: 0 28px;
            font-size: 0.82rem;     /* slightly larger to fill the taller tape */
            font-family: {FONT};
            letter-spacing: 0.04em;
        }}
        .t-sym  {{ color: {C_TEXT};    font-weight: 700; }}
        .t-price{{ color: #BBBBBB;     margin-left: 6px; }}
        .t-up   {{ color: {C_GREEN};   margin-left: 4px; font-size: 0.78rem; }}
        .t-down {{ color: {C_RED};     margin-left: 4px; font-size: 0.78rem; }}
        @keyframes ticker-scroll {{
            0%   {{ transform: translateX(0); }}
            100% {{ transform: translateX(-50%); }}
        }}

        /* ── Section divider label ── */
        .step-label {{
            font-size: 0.68rem;
            color: {C_MUTED};
            text-transform: uppercase;
            letter-spacing: 0.16em;
            margin-bottom: 0.1rem;
            font-family: {FONT};
        }}

        /* ── Orange accent divider line ── */
        .bbg-divider {{
            border: none;
            border-top: 1px solid {C_ACCENT};
            margin: 0.3rem 0 1rem 0;
            opacity: 0.5;
        }}

        /* ── Metric cards — subtle glow on hover for polish ── */
        [data-testid="stMetric"] {{
            background-color: {C_SURFACE};
            border: 1px solid {C_BORDER};
            border-left: 3px solid {C_ACCENT};
            border-radius: 2px;
            padding: 0.85rem 1rem;
            transition: box-shadow 0.2s ease;
        }}
        [data-testid="stMetric"]:hover {{
            box-shadow: 0 0 12px rgba(255,102,0,0.18);
        }}
        [data-testid="stMetricLabel"] {{
            color: {C_MUTED} !important;
            font-size: 0.7rem !important;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            font-family: {FONT} !important;
        }}
        [data-testid="stMetricValue"] {{
            color: {C_TEXT} !important;
            font-size: 1.35rem !important;
            font-weight: 700 !important;
            font-family: {FONT} !important;
        }}

        /* ── Dataframe ── */
        [data-testid="stDataFrame"] {{
            border: 1px solid {C_BORDER};
            border-radius: 2px;
        }}

        /* ── Run buttons ── */
        .stButton > button {{
            background-color: {C_ACCENT} !important;
            color: #000 !important;
            border: none !important;
            border-radius: 2px !important;
            font-family: {FONT} !important;
            font-weight: 700 !important;
            font-size: 0.85rem !important;
            letter-spacing: 0.06em !important;
            padding: 0.55rem 1.4rem !important;
            width: 100%;
            text-transform: uppercase;
            transition: background-color 0.15s ease;
        }}
        .stButton > button:hover {{
            background-color: {C_ACCENT2} !important;
        }}

        /* ── Download button ── */
        .stDownloadButton > button {{
            background-color: transparent !important;
            color: {C_ACCENT} !important;
            border: 1px solid {C_ACCENT} !important;
            border-radius: 2px !important;
            font-family: {FONT} !important;
            font-size: 0.82rem !important;
            letter-spacing: 0.04em !important;
            width: 100%;
        }}

        /* ── Success / Error alerts ── */
        .stSuccess {{
            background-color: rgba(0, 200, 83, 0.08) !important;
            border-left: 3px solid {C_GREEN} !important;
            border-radius: 2px !important;
            font-family: {FONT} !important;
        }}
        .stError {{
            background-color: rgba(255, 23, 68, 0.08) !important;
            border-left: 3px solid {C_RED} !important;
            border-radius: 2px !important;
        }}

        /* ── Recommendation badges ── */
        .badge-buy {{
            display: inline-block;
            background-color: rgba(0,200,83,0.12);
            color: {C_GREEN};
            border: 1px solid {C_GREEN};
            border-radius: 2px;
            padding: 0.4rem 1.6rem;
            font-size: 1.6rem;
            font-weight: 700;
            letter-spacing: 0.2em;
            font-family: {FONT};
        }}
        .badge-sell {{
            display: inline-block;
            background-color: rgba(255,23,68,0.12);
            color: {C_RED};
            border: 1px solid {C_RED};
            border-radius: 2px;
            padding: 0.4rem 1.6rem;
            font-size: 1.6rem;
            font-weight: 700;
            letter-spacing: 0.2em;
            font-family: {FONT};
        }}
        .badge-hold {{
            display: inline-block;
            background-color: rgba(41,121,255,0.12);
            color: {C_BLUE};
            border: 1px solid {C_BLUE};
            border-radius: 2px;
            padding: 0.4rem 1.6rem;
            font-size: 1.6rem;
            font-weight: 700;
            letter-spacing: 0.2em;
            font-family: {FONT};
        }}

        /* ── Disclaimer text under recommendation ──────────────────────────────
           CHANGE: New .disclaimer class for the financial-advice warning.
           Italic, muted, smaller — clearly secondary to the badge.
        ── */
        .disclaimer {{
            color: {C_MUTED};
            font-size: 0.76rem;
            font-style: italic;
            font-family: {FONT};
            margin-top: 0.6rem;
            border-left: 2px solid {C_BORDER};
            padding-left: 0.6rem;
        }}

        /* ── Radio buttons: Bloomberg tab style ── */
        div[data-testid="stRadio"] > div {{
            gap: 0.3rem;
        }}
        div[data-testid="stRadio"] label {{
            background-color: {C_SURFACE};
            border: 1px solid {C_BORDER};
            border-radius: 2px;
            padding: 0.4rem 0.8rem;
            font-size: 0.82rem;
            font-family: {FONT};
            cursor: pointer;
            width: 100%;
            display: block;
        }}
        div[data-testid="stRadio"] label:has(input:checked) {{
            border-color: {C_ACCENT};
            color: {C_ACCENT};
            background-color: rgba(255,102,0,0.08);
        }}

        /* ── Expander ──────────────────────────────────────────────────────────
           CHANGE: summary now truncates long text with ellipsis so the dropdown
           arrow never overlaps the label. overflow and text-overflow added.
        ── */
        details {{
            border: 1px solid {C_BORDER} !important;
            border-radius: 2px !important;
            background-color: {C_SURFACE} !important;
        }}
        summary {{
            color: {C_MUTED} !important;
            font-size: 0.8rem !important;
            font-family: {FONT} !important;
            white-space: nowrap;          /* ← prevent text from wrapping into arrow */
            overflow: hidden;             /* ← clip text before the arrow */
            text-overflow: ellipsis;      /* ← show "…" if label is cut */
            padding-right: 2rem;          /* ← reserve room for the native arrow */
            display: block;
        }}

        /* ── Slider styling ────────────────────────────────────────────────────
           CHANGE: Sliders used for weights now get orange accent on the thumb
           and track to stay consistent with the Bloomberg palette.
        ── */
        .stSlider > div > div > div > div {{
            background-color: {C_ACCENT} !important;
        }}
        .stSlider [data-testid="stThumbValue"] {{
            color: {C_TEXT} !important;
            font-family: {FONT} !important;
            font-size: 0.78rem !important;
        }}

    </style>
    """, unsafe_allow_html=True)


def style_chart(ax, fig, title=""):
    """
    DISPLAY: Apply Bloomberg-style dark theme to a matplotlib chart.
    Orange accent on the title, grey grid lines, no top/right spines.
    """
    fig.patch.set_facecolor(C_SURFACE)
    ax.set_facecolor(C_BG)
    ax.set_title(title, color=C_TEXT, fontsize=10, pad=10,
                 fontfamily="DejaVu Sans", fontweight="bold")
    ax.set_xlabel(ax.get_xlabel(), color=C_MUTED, fontsize=8, fontfamily="DejaVu Sans")
    ax.set_ylabel(ax.get_ylabel(), color=C_MUTED, fontsize=8, fontfamily="DejaVu Sans")
    ax.tick_params(colors=C_MUTED, labelsize=7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(C_BORDER)
    ax.spines["bottom"].set_color(C_BORDER)
    ax.grid(True, color="#1E1E1E", linewidth=0.6, alpha=0.8)
    # Orange bottom border line (Bloomberg style)
    ax.axhline(y=ax.get_ylim()[0], color=C_ACCENT, linewidth=1.2, alpha=0.4)
    legend = ax.get_legend()
    if legend:
        legend.get_frame().set_facecolor(C_SURFACE)
        legend.get_frame().set_edgecolor(C_BORDER)
        for text in legend.get_texts():
            text.set_color(C_TEXT)
            text.set_fontsize(7)


# ─── 3. TICKER TAPE ────────────────────────────────────────────────────────────
# Fetches live prices for key S&P 500 stocks and renders a scrolling HTML ticker.
# The list below covers major index components across sectors.

# Major S&P 500 stocks for the ticker tape (spread across sectors)
TICKER_SYMBOLS = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "BRK-B",
    "JPM", "V", "UNH", "XOM", "JNJ", "WMT", "MA", "PG", "HD",
    "CVX", "MRK", "LLY", "ABBV", "PEP", "KO", "AVGO", "COST",
    "MCD", "TMO", "ACN", "CSCO", "CRM", "BAC", "WFC", "GS", "MS",
    "SPY", "QQQ", "DIA"
]


@st.cache_data(ttl=300)  # Cache for 5 minutes so the page doesn't re-fetch on every interaction
def fetch_ticker_data(symbols: list) -> list:
    """
    DATA: Fetch current price and daily change for all ticker tape symbols.
    Returns a list of dicts: {symbol, price, change_pct}.
    Uses yfinance batch download for speed. Cached for 5 minutes (ttl=300).
    """
    results = []
    try:
        # Download all at once for speed (much faster than one-by-one)
        raw = yf.download(symbols, period="2d", progress=False, threads=True)["Close"]
        if raw.empty:
            return results
        # Handle single-ticker edge case (returns a Series, not DataFrame)
        if isinstance(raw, pd.Series):
            raw = raw.to_frame()
        for sym in symbols:
            if sym not in raw.columns:
                continue
            col = raw[sym].dropna()
            if len(col) < 2:
                continue
            price      = col.iloc[-1]
            prev_price = col.iloc[-2]
            chg_pct    = ((price - prev_price) / prev_price) * 100
            results.append({
                "symbol":     sym,
                "price":      price,
                "change_pct": chg_pct
            })
    except Exception:
        pass  # If fetch fails, ticker tape just won't render (non-critical)
    return results


def render_ticker_tape():
    """
    DISPLAY: Render the Bloomberg-style scrolling ticker tape.
    Fetches live data, builds HTML for each stock item, then doubles
    the items so the scroll loops seamlessly.

    CHANGE: Tape height increased via CSS (padding: 14px 0 in apply_theme).
    Font size also bumped slightly to 0.82rem to fill the extra height.
    """
    data = fetch_ticker_data(TICKER_SYMBOLS)

    if not data:
        # Silently skip the tape if data is unavailable (e.g. network issue)
        return

    # Build each ticker item as an HTML span
    items_html = ""
    for item in data:
        sym    = item["symbol"]
        price  = item["price"]
        chg    = item["change_pct"]
        arrow  = "▲" if chg >= 0 else "▼"
        cls    = "t-up" if chg >= 0 else "t-down"
        items_html += (
            f'<span class="ticker-item">'
            f'<span class="t-sym">{sym}</span>'
            f'<span class="t-price">${price:.2f}</span>'
            f'<span class="{cls}">{arrow} {abs(chg):.2f}%</span>'
            f'</span>'
            f'<span style="color:#2A2A2A; font-size:0.7rem;">|</span>'
        )

    # Double the items so the scroll loops seamlessly
    scrolling_html = f"""
    <div class="ticker-wrapper">
        <div class="ticker-track">
            {items_html}{items_html}
        </div>
    </div>
    """
    st.markdown(scrolling_html, unsafe_allow_html=True)


# ─── 4. LOGIC / CALCULATION FUNCTIONS ──────────────────────────────────────────
# Pure math functions. No Streamlit calls here.

# ── Stock Analysis (Part 1) ──

def fetch_stock_data(ticker: str):
    """
    DATA: Download 6 months of daily OHLCV data for one stock.
    Returns the Ticker object and historical DataFrame.
    """
    stock = yf.Ticker(ticker)
    df    = stock.history(period="6mo")
    return stock, df


def calc_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    """
    PROCESSING: Add 20-day and 50-day simple moving averages.
    These smooth noise and reveal the underlying price trend.
    """
    df["MA20"] = df["Close"].rolling(window=20).mean()
    df["MA50"] = df["Close"].rolling(window=50).mean()
    return df


def calc_trend(df: pd.DataFrame) -> str:
    """
    PROCESSING: Classify trend using price vs moving averages.
    Price > MA20 > MA50 = uptrend. Reverse = downtrend. Else = mixed.
    """
    price = df["Close"].iloc[-1]
    ma20  = df["MA20"].iloc[-1]
    ma50  = df["MA50"].iloc[-1]
    if price > ma20 > ma50:
        return "Strong Uptrend"
    elif price < ma20 < ma50:
        return "Strong Downtrend"
    return "Mixed Trend"


def calc_rsi(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    """
    PROCESSING: Calculate 14-day RSI (Relative Strength Index).
    Measures momentum: above 70 = overbought, below 30 = oversold.
    Formula: RSI = 100 - (100 / (1 + avg_gain / avg_loss))
    """
    delta    = df["Close"].diff()
    gain     = delta.clip(lower=0)
    loss     = -delta.clip(upper=0)
    avg_gain = gain.rolling(window).mean()
    avg_loss = loss.rolling(window).mean()
    rs       = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df


def interpret_rsi(rsi_value: float) -> str:
    """PROCESSING: Translate RSI value into a buy/sell/neutral signal."""
    if rsi_value > 70:
        return "Overbought (Possible Sell)"
    elif rsi_value < 30:
        return "Oversold (Possible Buy)"
    return "Neutral"


def calc_volatility(df: pd.DataFrame) -> float:
    """
    PROCESSING: 20-day annualized volatility = daily_std * sqrt(252) * 100.
    Higher value = more price risk.
    """
    daily_returns = df["Close"].pct_change()
    return daily_returns.rolling(window=20).std().iloc[-1] * np.sqrt(252) * 100


def calc_annualized_return(df: pd.DataFrame) -> float:
    """
    PROCESSING: Annualized return from 6-month price data.
    CHANGE (NEW): Added to show alongside volatility on the Stock Analysis page.
    Formula: (end_price / start_price) ^ (252 / trading_days) - 1, expressed as %.
    252 is the standard number of US trading days in a year.
    """
    start_price   = df["Close"].iloc[0]
    end_price     = df["Close"].iloc[-1]
    trading_days  = len(df)
    # Annualize the 6-month return by scaling to a full year
    ann_return    = ((end_price / start_price) ** (252 / trading_days) - 1) * 100
    return ann_return


def classify_volatility(volatility: float) -> str:
    """PROCESSING: Bucket volatility into High (>40%), Medium (25-40%), Low (<25%)."""
    if volatility > 40:
        return "High"
    elif volatility >= 25:
        return "Medium"
    return "Low"


def build_recommendation(ticker, trend, rsi_value, vol_level, volatility):
    """
    PROCESSING: Combine trend, RSI, and volatility into a BUY / SELL / HOLD call.
    Returns (recommendation, explanation) strings.
    """
    if trend == "Strong Uptrend" and rsi_value < 70:
        rec = "BUY"
        exp = (
            f"{ticker} is in a strong uptrend (Price > 20MA > 50MA) "
            f"and RSI is not overbought ({rsi_value:.1f}). "
            f"Volatility is {vol_level.lower()} ({volatility:.1f}%). "
            "Conditions support a buy."
        )
    elif trend == "Strong Downtrend" or rsi_value > 70:
        rec = "SELL"
        exp = (
            f"{ticker} shows a downtrend or overbought RSI ({rsi_value:.1f}). "
            f"Trend: {trend}. Volatility: {vol_level.lower()} ({volatility:.1f}%). "
            "Consider reducing exposure."
        )
    else:
        rec = "HOLD"
        exp = (
            f"Mixed signals for {ticker}. Trend: {trend}. "
            f"RSI: {rsi_value:.1f} (Neutral). "
            f"Volatility: {vol_level.lower()} ({volatility:.1f}%). "
            "Wait for a clearer signal."
        )
    return rec, exp


# ── Portfolio Dashboard (Part 2) ──

def fetch_portfolio_data(tickers: list, benchmark: str) -> pd.DataFrame:
    """
    DATA: Download 1 year of closing prices for all portfolio stocks + benchmark.
    Each column in the returned DataFrame is one ticker.
    """
    all_tickers = tickers + [benchmark]
    raw = yf.download(all_tickers, period="1y", progress=False)["Close"]
    return raw


def calc_portfolio_returns(raw, tickers, weights, benchmark):
    """
    PROCESSING: Compute daily and cumulative returns for the portfolio and benchmark.
    Portfolio daily return = weighted dot product of individual stock returns.
    Cumulative = (1 + daily_return).cumprod() shows growth of $1 invested.
    """
    returns              = raw.pct_change().dropna()
    portfolio_returns    = returns[tickers].dot(weights)
    benchmark_returns    = returns[benchmark]
    portfolio_cumulative = (1 + portfolio_returns).cumprod()
    benchmark_cumulative = (1 + benchmark_returns).cumprod()
    return returns, portfolio_returns, benchmark_returns, portfolio_cumulative, benchmark_cumulative


def calc_performance_metrics(portfolio_returns, benchmark_returns, portfolio_cumulative, benchmark_cumulative):
    """
    PROCESSING: Total return, annualized volatility, and Sharpe ratio.
    Sharpe = annualized return / annualized std. Assumes 0% risk-free rate.
    """
    total_return           = (portfolio_cumulative.iloc[-1] - 1) * 100
    benchmark_total_return = (benchmark_cumulative.iloc[-1] - 1) * 100
    outperformance         = total_return - benchmark_total_return
    port_volatility        = portfolio_returns.std() * np.sqrt(252) * 100
    bench_volatility       = benchmark_returns.std() * np.sqrt(252) * 100
    annualized_return      = portfolio_returns.mean() * 252
    sharpe_ratio           = annualized_return / (portfolio_returns.std() * np.sqrt(252))
    return total_return, benchmark_total_return, outperformance, port_volatility, bench_volatility, sharpe_ratio


def build_interpretation(benchmark, total_return, benchmark_total_return,
                          outperformance, port_volatility, bench_volatility, sharpe_ratio) -> list:
    """
    PROCESSING: Convert metrics into three plain-English interpretation sentences.
    """
    lines = []
    if outperformance > 0:
        lines.append(f"The portfolio outperformed {benchmark} by {outperformance:.2f}%.")
    else:
        lines.append(f"The portfolio underperformed {benchmark} by {abs(outperformance):.2f}%.")
    if port_volatility > bench_volatility:
        lines.append(f"The portfolio carried more risk than the benchmark ({port_volatility:.2f}% vs {bench_volatility:.2f}% volatility).")
    else:
        lines.append(f"The portfolio carried less risk than the benchmark ({port_volatility:.2f}% vs {bench_volatility:.2f}% volatility).")
    if sharpe_ratio > 1:
        lines.append(f"A Sharpe ratio of {sharpe_ratio:.2f} suggests good risk-adjusted returns.")
    elif sharpe_ratio > 0:
        lines.append(f"A Sharpe ratio of {sharpe_ratio:.2f} suggests modest risk-adjusted returns.")
    else:
        lines.append(f"A Sharpe ratio of {sharpe_ratio:.2f} suggests returns did not compensate for the risk taken.")
    return lines


# ─── 5. CHART FUNCTIONS ────────────────────────────────────────────────────────
# Each function builds and returns one styled matplotlib figure.
# No st.pyplot() calls here, keeping chart building separate from display.

def chart_price_ma(df, ticker):
    """DISPLAY: Price line chart with 20-day and 50-day moving averages."""
    fig, ax = plt.subplots(figsize=(12, 3.5))
    ax.plot(df.index, df["Close"], label="Close Price", color=CH_PRICE, linewidth=1.8)
    ax.plot(df.index, df["MA20"],  label="20-Day MA",   color=CH_MA20,  linestyle="--", linewidth=1)
    ax.plot(df.index, df["MA50"],  label="50-Day MA",   color=CH_MA50,  linestyle="--", linewidth=1)
    ax.set_xlabel("Date")
    ax.set_ylabel("Price ($)")
    ax.legend(loc="upper left")
    style_chart(ax, fig, title=f"{ticker}  |  PRICE & MOVING AVERAGES")
    fig.tight_layout()
    return fig


def chart_rsi(df, ticker):
    """DISPLAY: RSI chart with shaded overbought/oversold zones."""
    fig, ax = plt.subplots(figsize=(12, 2.5))
    ax.plot(df.index, df["RSI"], label="RSI (14)", color=CH_RSI, linewidth=1.5)
    ax.axhline(70, color=C_RED,   linestyle="--", linewidth=0.9, label="Overbought (70)")
    ax.axhline(30, color=C_GREEN, linestyle="--", linewidth=0.9, label="Oversold (30)")
    ax.fill_between(df.index, 70, 100, alpha=0.06, color=C_RED)    # red zone above 70
    ax.fill_between(df.index, 0,  30,  alpha=0.06, color=C_GREEN)  # green zone below 30
    ax.set_ylim(0, 100)
    ax.set_xlabel("Date")
    ax.set_ylabel("RSI")
    ax.legend(loc="upper left")
    style_chart(ax, fig, title=f"{ticker}  |  RSI (14-DAY)")
    fig.tight_layout()
    return fig


def chart_cumulative_returns(portfolio_cumulative, benchmark_cumulative, benchmark):
    """DISPLAY: Cumulative return chart: portfolio vs benchmark (growth of $1)."""
    fig, ax = plt.subplots(figsize=(12, 3.5))
    ax.plot(portfolio_cumulative.index, portfolio_cumulative, label="Portfolio", color=CH_PORT,  linewidth=2)
    ax.plot(benchmark_cumulative.index, benchmark_cumulative, label=benchmark,   color=CH_BENCH, linewidth=1.5, linestyle="--")
    ax.axhline(1.0, color=C_MUTED, linewidth=0.7, linestyle=":")   # break-even line
    ax.set_xlabel("Date")
    ax.set_ylabel("Growth of $1")
    ax.legend(loc="upper left")
    style_chart(ax, fig, title="PORTFOLIO vs BENCHMARK  |  CUMULATIVE RETURN")
    fig.tight_layout()
    return fig


def chart_individual_returns(returns, tickers):
    """DISPLAY: Bar chart of each stock's 1-year total return. Green = gain, red = loss."""
    individual_returns = ((1 + returns[tickers]).cumprod().iloc[-1] - 1) * 100
    colors = [C_GREEN if v >= 0 else C_RED for v in individual_returns.values]
    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.bar(individual_returns.index, individual_returns.values, color=colors, width=0.5, alpha=0.9)
    ax.axhline(0, color=C_MUTED, linewidth=0.8)
    ax.set_xlabel("Ticker")
    ax.set_ylabel("Return (%)")
    # Value labels on top of each bar
    for i, (t, val) in enumerate(individual_returns.items()):
        offset = 0.8 if val >= 0 else -3.5
        ax.text(i, val + offset, f"{val:.1f}%",
                ha="center", fontsize=8,
                color=C_GREEN if val >= 0 else C_RED)
    style_chart(ax, fig, title="INDIVIDUAL STOCK RETURNS (1 YEAR)")
    fig.tight_layout()
    return fig


# ─── 6. DISPLAY / UI FUNCTIONS ─────────────────────────────────────────────────
# All st.* rendering calls live here. No math in this section.

def ui_step_header(step_num: int, title: str):
    """DISPLAY: Bloomberg-style step header with small uppercase label and orange divider."""
    st.markdown(f"<p class='step-label'>Step {step_num}</p>", unsafe_allow_html=True)
    st.subheader(title)
    st.markdown("<hr class='bbg-divider'>", unsafe_allow_html=True)


def ui_badge(recommendation: str, explanation: str):
    """
    DISPLAY: Colored BUY / SELL / HOLD badge with explanation text and disclaimer below.
    CHANGE: Added a disclaimer line under the badge/explanation using the .disclaimer CSS class.
    """
    badge_class = {
        "BUY":  "badge-buy",
        "SELL": "badge-sell",
        "HOLD": "badge-hold"
    }.get(recommendation, "badge-hold")

    # Badge and explanation
    st.markdown(f"<div class='{badge_class}'>{recommendation}</div>", unsafe_allow_html=True)
    st.write("")
    st.write(explanation)

    # ── CHANGE: Disclaimer text ────────────────────────────────────────────────
    # Displayed below the recommendation explanation in a muted italic style.
    st.markdown(
        "<p class='disclaimer'>"
        "This is the recommendation based off of the shown variables. "
        "This is not financial advice."
        "</p>",
        unsafe_allow_html=True
    )


def ui_stock_analysis(ticker: str):
    """
    DISPLAY: Render all 5 steps for Stock Analysis.
    Calls calculation functions for data, then renders each step.

    CHANGES:
    - Step 4 now shows Annualized Return alongside Annualized Volatility.
    - Expander label shortened to just "Data" (no overlapping with arrow).
    - Disclaimer added inside ui_badge (Step 5).
    """

    # ── Step 1: Data Collection ───────────────────────────────────────────────
    ui_step_header(1, "Data Collection")
    stock, df = fetch_stock_data(ticker)

    if df.empty:
        st.error(f"No data found for '{ticker}'. Check the ticker symbol.")
        st.stop()

    st.success(f"6 months of daily data loaded for {ticker}")

    # CHANGE: Expander label shortened to "Data" — prevents text/arrow overlap.
    with st.expander("Data", expanded=False):
        st.dataframe(df[["Open", "High", "Low", "Close", "Volume"]].tail(10),
                     use_container_width=True)

    # ── Step 2: Trend Analysis ────────────────────────────────────────────────
    ui_step_header(2, "Trend Analysis  |  Moving Averages")
    df    = calc_moving_averages(df)
    trend = calc_trend(df)
    price = df["Close"].iloc[-1]
    ma20  = df["MA20"].iloc[-1]
    ma50  = df["MA50"].iloc[-1]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Current Price", f"${price:.2f}")
    col2.metric("20-Day MA",     f"${ma20:.2f}")
    col3.metric("50-Day MA",     f"${ma50:.2f}")
    col4.metric("Trend Signal",  trend)

    st.pyplot(chart_price_ma(df, ticker), use_container_width=True)

    # ── Step 3: RSI Momentum ──────────────────────────────────────────────────
    ui_step_header(3, "Momentum  |  14-Day RSI")
    df        = calc_rsi(df)
    rsi_value = df["RSI"].iloc[-1]
    rsi_sig   = interpret_rsi(rsi_value)

    col1, col2 = st.columns(2)
    col1.metric("RSI (14-Day)", f"{rsi_value:.2f}")
    col2.metric("Signal",       rsi_sig)

    st.pyplot(chart_rsi(df, ticker), use_container_width=True)

    # ── Step 4: Volatility ────────────────────────────────────────────────────
    ui_step_header(4, "Volatility  |  20-Day Annualized")
    volatility     = calc_volatility(df)
    vol_level      = classify_volatility(volatility)
    ann_return     = calc_annualized_return(df)   # ← CHANGE: new metric

    # CHANGE: Three metrics now — Annualized Return added next to Volatility.
    col1, col2, col3 = st.columns(3)
    col1.metric("Annualized Volatility", f"{volatility:.2f}%")
    col2.metric("Volatility Level",      vol_level)
    col3.metric("Annualized Return",     f"{ann_return:.2f}%")  # ← CHANGE: new

    # ── Step 5: Recommendation ────────────────────────────────────────────────
    ui_step_header(5, "Trading Recommendation")
    rec, exp = build_recommendation(ticker, trend, rsi_value, vol_level, volatility)
    # ui_badge now also renders the disclaimer below the explanation
    ui_badge(rec, exp)

    # ── Download ──────────────────────────────────────────────────────────────
    st.markdown(f"<hr style='border-top:1px solid {C_BORDER}; margin-top:2rem'>",
                unsafe_allow_html=True)
    csv = df.to_csv().encode("utf-8")
    st.download_button(
        label="Download Stock Data as CSV",
        data=csv,
        file_name=f"{ticker}_stock_analysis.csv",
        mime="text/csv"
    )


def ui_portfolio_dashboard(tickers_input: str, weights: list, benchmark: str):
    """
    DISPLAY: Render all 6 steps for the Portfolio Dashboard.
    Validates inputs, calls calculation functions, then renders results.

    CHANGES:
    - weights now received as a list of floats from sliders (not parsed here).
    - Ticker count is no longer restricted to exactly 5 — any number works.
    - Expander label shortened to "Data" to fix arrow/text overlap.
    """

    # Parse comma-separated tickers
    tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

    # Validate: at least 1 ticker, weights list must match ticker count
    if len(tickers) < 1:
        st.error("Enter at least one stock ticker.")
        st.stop()
    if len(weights) != len(tickers):
        # This shouldn't happen since sliders are built from tickers, but guard anyway
        st.error("Number of weights does not match number of tickers.")
        st.stop()
    if abs(sum(weights) - 1.0) > 0.01:
        st.error(f"Weights must sum to 1.00. Current sum: {sum(weights):.2f}")
        st.stop()

    # ── Step 1: Portfolio Setup ───────────────────────────────────────────────
    ui_step_header(1, "Portfolio Setup")
    weight_df = pd.DataFrame({"Ticker": tickers, "Weight": [f"{w:.0%}" for w in weights]})
    col1, _ = st.columns([1, 3])
    col1.dataframe(weight_df, use_container_width=True, hide_index=True)

    # ── Step 2: Data Collection ───────────────────────────────────────────────
    ui_step_header(2, "Data Collection  |  1 Year")
    raw = fetch_portfolio_data(tickers, benchmark)

    if raw.empty:
        st.error("Could not download data. Check your ticker symbols.")
        st.stop()

    st.success(f"1 year of closing prices loaded for: {', '.join(tickers + [benchmark])}")

    # CHANGE: Expander label shortened to "Data" — fixes arrow/text overlap.
    with st.expander("Data", expanded=False):
        st.dataframe(raw.tail(5), use_container_width=True)

    # ── Step 3: Return Calculations ───────────────────────────────────────────
    ui_step_header(3, "Return Calculations  |  Portfolio vs Benchmark")
    returns, portfolio_returns, benchmark_returns, portfolio_cumulative, benchmark_cumulative = \
        calc_portfolio_returns(raw, tickers, weights, benchmark)

    st.pyplot(chart_cumulative_returns(portfolio_cumulative, benchmark_cumulative, benchmark),
              use_container_width=True)

    # ── Step 4: Performance Metrics ───────────────────────────────────────────
    ui_step_header(4, "Performance Metrics")
    total_return, benchmark_total_return, outperformance, \
    port_volatility, bench_volatility, sharpe_ratio = \
        calc_performance_metrics(portfolio_returns, benchmark_returns,
                                  portfolio_cumulative, benchmark_cumulative)

    col1, col2, col3 = st.columns(3)
    col1.metric("Portfolio Return",  f"{total_return:.2f}%")
    col2.metric("Benchmark Return",  f"{benchmark_total_return:.2f}%",
                delta=f"{outperformance:+.2f}% vs benchmark")
    col3.metric("Outperformance",    f"{outperformance:+.2f}%")

    st.write("")

    col4, col5, col6 = st.columns(3)
    col4.metric("Portfolio Volatility",  f"{port_volatility:.2f}%")
    col5.metric("Benchmark Volatility",  f"{bench_volatility:.2f}%")
    col6.metric("Sharpe Ratio",          f"{sharpe_ratio:.2f}")

    # ── Step 5: Interpretation ────────────────────────────────────────────────
    ui_step_header(5, "Interpretation")
    lines = build_interpretation(benchmark, total_return, benchmark_total_return,
                                  outperformance, port_volatility, bench_volatility, sharpe_ratio)
    for line in lines:
        st.write(f"• {line}")

    # ── Step 6: Individual Stock Returns ──────────────────────────────────────
    st.write("")
    ui_step_header(6, "Individual Stock Returns")
    st.pyplot(chart_individual_returns(returns, tickers), use_container_width=True)

    # ── Download ──────────────────────────────────────────────────────────────
    st.markdown(f"<hr style='border-top:1px solid {C_BORDER}; margin-top:2rem'>",
                unsafe_allow_html=True)
    combined = pd.DataFrame({"Portfolio": portfolio_returns, benchmark: benchmark_returns})
    csv = combined.to_csv().encode("utf-8")
    st.download_button(
        label="Download Portfolio Returns as CSV",
        data=csv,
        file_name="portfolio_returns.csv",
        mime="text/csv"
    )


# ─── 7. MAIN APP ENTRY POINT ───────────────────────────────────────────────────
# Page config, theme, Bloomberg header bar, ticker tape, sidebar nav, section routing.

def main():
    # Must be the very first Streamlit call
    st.set_page_config(
        page_title="FIN 330 | Bloomberg Dashboard",
        page_icon="📊",
        layout="wide"
    )

    # Apply Bloomberg CSS theme
    apply_theme()

    # ── Bloomberg-style orange top bar ────────────────────────────────────────
    import datetime
    now_str = datetime.datetime.now().strftime("%H:%M:%S  %b %d, %Y")
    st.markdown(f"""
    <div class="bbg-topbar">
        <span class="bbg-topbar-title">FIN 330  &nbsp;|&nbsp;  STOCK ANALYTICS TERMINAL</span>
        <span class="bbg-topbar-right">YAHOO FINANCE DATA  &nbsp;&bull;&nbsp;  {now_str}</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Live S&P 500 ticker tape (fetches real prices, cached 5 min) ──────────
    render_ticker_tape()

    # ── Main page title below the tape ───────────────────────────────────────
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    st.sidebar.markdown(f"""
    <div style='padding:12px 0 4px 0;'>
        <span style='color:{C_ACCENT}; font-size:1.1rem; font-weight:700;
                     letter-spacing:0.1em; font-family:{FONT};'>FIN 330</span><br>
        <span style='color:{C_MUTED}; font-size:0.72rem; letter-spacing:0.06em;
                     font-family:{FONT};'>ANALYTICS TERMINAL</span>
    </div>
    """, unsafe_allow_html=True)
    st.sidebar.markdown(f"<hr style='border-top:2px solid {C_ACCENT}; margin:0.5rem 0'>",
                        unsafe_allow_html=True)

    # Navigation radio: Stock Analysis or Portfolio Dashboard
    section = st.sidebar.radio(
        "Navigate",
        ["Stock Analysis", "Portfolio Dashboard"],
        label_visibility="collapsed"
    )
    st.sidebar.markdown(f"<hr style='border-top:1px solid {C_BORDER}; margin:0.5rem 0'>",
                        unsafe_allow_html=True)

    # ── Stock Analysis section ────────────────────────────────────────────────
    if section == "Stock Analysis":
        st.sidebar.markdown(
            f"<p style='color:{C_MUTED}; font-size:0.7rem; text-transform:uppercase; "
            f"letter-spacing:0.12em; font-family:{FONT};'>Stock Settings</p>",
            unsafe_allow_html=True
        )
        ticker = st.sidebar.text_input("Ticker Symbol", "AAPL").upper()
        st.sidebar.write("")
        run = st.sidebar.button("Run Analysis")

        # Page header
        st.markdown(
            f"<h2 style='color:{C_ACCENT}; font-family:{FONT}; font-weight:700; "
            f"letter-spacing:0.05em; margin-bottom:0;'>STOCK ANALYSIS</h2>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<p style='color:{C_MUTED}; font-family:{FONT}; margin-top:0.1rem; "
            f"font-size:0.85rem;'>Individual stock trend, momentum, volatility, and recommendation.</p>",
            unsafe_allow_html=True
        )
        st.markdown(f"<hr style='border-top:1px solid {C_BORDER}; margin-bottom:1.2rem'>",
                    unsafe_allow_html=True)

        if run:
            ui_stock_analysis(ticker)
        else:
            st.markdown(
                f"<p style='color:{C_MUTED}; margin-top:1.5rem; font-family:{FONT};'>"
                "Enter a ticker symbol in the sidebar and click Run Analysis.</p>",
                unsafe_allow_html=True
            )

    # ── Portfolio Dashboard section ───────────────────────────────────────────
    elif section == "Portfolio Dashboard":
        st.sidebar.markdown(
            f"<p style='color:{C_MUTED}; font-size:0.7rem; text-transform:uppercase; "
            f"letter-spacing:0.12em; font-family:{FONT};'>Portfolio Settings</p>",
            unsafe_allow_html=True
        )

        # ── CHANGE: Any number of stocks (not restricted to 5) ────────────────
        # The user types tickers; sliders are generated dynamically below.
        tickers_input = st.sidebar.text_input(
            "Tickers (comma-separated)",
            "AAPL, MSFT, JPM, AMZN, NVDA"
        )
        benchmark = st.sidebar.text_input("Benchmark ETF", "SPY").upper()

        # Parse tickers immediately so sliders can be built
        raw_tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

        # ── CHANGE: Weight sliders (one per ticker, auto-normalized) ──────────
        # Each slider lets the user pick a raw weight 0.0–1.0.
        # Weights are then normalized so they always sum to exactly 1.00,
        # so the user never has to manually balance them.
        weights_raw = []
        if raw_tickers:
            st.sidebar.markdown(
                f"<p style='color:{C_MUTED}; font-size:0.7rem; text-transform:uppercase; "
                f"letter-spacing:0.1em; font-family:{FONT}; margin-top:0.6rem;'>Weights</p>",
                unsafe_allow_html=True
            )
            default_w = round(1.0 / len(raw_tickers), 2)
            for t in raw_tickers:
                w = st.sidebar.slider(
                    t,                    # label = ticker symbol (clean, no overlap)
                    min_value=0.0,
                    max_value=1.0,
                    value=default_w,
                    step=0.01,
                    key=f"w_{t}"
                )
                weights_raw.append(w)

            # Normalize so weights always sum to 1.00
            total_w = sum(weights_raw)
            if total_w > 0:
                weights_normalized = [w / total_w for w in weights_raw]
            else:
                weights_normalized = [1.0 / len(raw_tickers)] * len(raw_tickers)

            # Show the live normalized sum as feedback
            st.sidebar.markdown(
                f"<p style='color:{C_MUTED}; font-size:0.72rem; font-family:{FONT}; "
                f"margin-top:0.3rem;'>Auto-normalized — sum = 1.00</p>",
                unsafe_allow_html=True
            )
        else:
            weights_normalized = []

        st.sidebar.write("")
        run = st.sidebar.button("Run Analysis")

        # Page header
        st.markdown(
            f"<h2 style='color:{C_ACCENT}; font-family:{FONT}; font-weight:700; "
            f"letter-spacing:0.05em; margin-bottom:0;'>PORTFOLIO DASHBOARD</h2>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<p style='color:{C_MUTED}; font-family:{FONT}; margin-top:0.1rem; "
            f"font-size:0.85rem;'>Multi-asset portfolio return, risk, and benchmark comparison.</p>",
            unsafe_allow_html=True
        )
        st.markdown(f"<hr style='border-top:1px solid {C_BORDER}; margin-bottom:1.2rem'>",
                    unsafe_allow_html=True)

        if run:
            # Pass the normalized weight list to the dashboard renderer
            ui_portfolio_dashboard(tickers_input, weights_normalized, benchmark)
        else:
            st.markdown(
                f"<p style='color:{C_MUTED}; margin-top:1.5rem; font-family:{FONT};'>"
                "Enter your tickers and benchmark in the sidebar, adjust weights with "
                "the sliders, then click Run Analysis.</p>",
                unsafe_allow_html=True
            )


# Run the app
if __name__ == "__main__":
    main()
