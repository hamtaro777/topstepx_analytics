"""
Metric Card Components - TopStepX Style
"""
import streamlit as st
from services.analytics import format_duration


# ── Color constants ──────────────────────────────────────────────
GREEN = "#00C853"
RED = "#FF5252"
CARD_BG = "#1A1D2E"
CARD_BORDER = "#2A2D3E"
LABEL_COLOR = "#8A8D98"
VALUE_COLOR = "#FFFFFF"


def _pnl_color(value: float) -> str:
    return GREEN if value >= 0 else RED


def _format_pnl(value: float) -> str:
    if value >= 0:
        return f"${value:,.2f}"
    return f"-${abs(value):,.2f}"


def _card(label: str, value_html: str, subtitle_html: str = "") -> str:
    """Base card HTML template matching TopStepX design."""
    return f"""
    <div style="
        background: {CARD_BG};
        padding: 16px 20px;
        border-radius: 8px;
        border: 1px solid {CARD_BORDER};
        height: 100%;
        box-sizing: border-box;
    ">
        <div style="color: {LABEL_COLOR}; font-size: 12px; margin-bottom: 8px; font-weight: 500;">
            {label}
        </div>
        {value_html}
        {subtitle_html}
    </div>
    """


def _val(text: str, color: str = VALUE_COLOR, size: str = "28px") -> str:
    return f'<div style="color: {color}; font-size: {size}; font-weight: 700; line-height: 1.2;">{text}</div>'


def _sub(text: str) -> str:
    return f'<div style="color: {LABEL_COLOR}; font-size: 11px; margin-top: 4px;">{text}</div>'


def _right_detail(text: str, color: str = LABEL_COLOR) -> str:
    return f'<span style="color: {color}; font-size: 13px; font-weight: 500;">{text}</span>'


# ── Win Rate Donut (SVG) ────────────────────────────────────────
def _win_rate_donut_svg(win_pct: float, win_count: int, loss_count: int, size: int = 56) -> str:
    """Render a small SVG donut chart for win rate."""
    r = 20
    c = size // 2
    circumference = 2 * 3.14159 * r
    win_arc = circumference * win_pct / 100
    loss_arc = circumference - win_arc
    return f"""
    <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" style="vertical-align: middle;">
        <circle cx="{c}" cy="{c}" r="{r}" fill="none" stroke="{RED}" stroke-width="5"
                stroke-dasharray="{loss_arc} {win_arc}"
                stroke-dashoffset="{circumference * 0.25}"
                transform="rotate(-90 {c} {c})"/>
        <circle cx="{c}" cy="{c}" r="{r}" fill="none" stroke="{GREEN}" stroke-width="5"
                stroke-dasharray="{win_arc} {loss_arc}"
                stroke-dashoffset="{circumference * 0.25}"
                transform="rotate(-90 {c} {c})"/>
        <text x="{c - 12}" y="{c - 6}" fill="{GREEN}" font-size="8" font-weight="bold">{win_count}</text>
        <text x="{c + 4}" y="{c + 10}" fill="{RED}" font-size="8" font-weight="bold">{loss_count}</text>
    </svg>
    """


# ── Profit Factor Donut (SVG) ───────────────────────────────────
def _profit_factor_donut_svg(gross_profit: float, gross_loss: float, size: int = 56) -> str:
    total = gross_profit + gross_loss
    if total == 0:
        pct = 50
    else:
        pct = gross_profit / total * 100
    r = 20
    c = size // 2
    circumference = 2 * 3.14159 * r
    profit_arc = circumference * pct / 100
    loss_arc = circumference - profit_arc
    return f"""
    <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" style="vertical-align: middle;">
        <circle cx="{c}" cy="{c}" r="{r}" fill="none" stroke="{RED}" stroke-width="5"
                stroke-dasharray="{loss_arc} {profit_arc}"
                stroke-dashoffset="{circumference * 0.25}"
                transform="rotate(-90 {c} {c})"/>
        <circle cx="{c}" cy="{c}" r="{r}" fill="none" stroke="{GREEN}" stroke-width="5"
                stroke-dasharray="{profit_arc} {loss_arc}"
                stroke-dashoffset="{circumference * 0.25}"
                transform="rotate(-90 {c} {c})"/>
    </svg>
    """


# ── Avg Win / Avg Loss Bar (SVG) ────────────────────────────────
def _avg_win_loss_bar_svg(avg_win: float, avg_loss: float) -> str:
    total = avg_win + avg_loss
    if total == 0:
        win_pct = 50
    else:
        win_pct = avg_win / total * 100
    return f"""
    <div style="margin-top: 6px;">
        <div style="display: flex; height: 8px; border-radius: 4px; overflow: hidden; background: #333;">
            <div style="width: {win_pct}%; background: {GREEN};"></div>
            <div style="width: {100 - win_pct}%; background: {RED};"></div>
        </div>
        <div style="display: flex; justify-content: space-between; margin-top: 4px;">
            <span style="color: {GREEN}; font-size: 11px; font-weight: 600;">${avg_win:,.2f}</span>
            <span style="color: {RED}; font-size: 11px; font-weight: 600;">-${avg_loss:,.2f}</span>
        </div>
    </div>
    """


# ── Direction Donut (SVG) ───────────────────────────────────────
def _direction_donut_svg(long_pct: float, long_count: int, short_count: int, size: int = 56) -> str:
    r = 20
    c = size // 2
    circumference = 2 * 3.14159 * r
    long_arc = circumference * long_pct / 100
    short_arc = circumference - long_arc
    return f"""
    <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" style="vertical-align: middle;">
        <circle cx="{c}" cy="{c}" r="{r}" fill="none" stroke="{RED}" stroke-width="5"
                stroke-dasharray="{short_arc} {long_arc}"
                stroke-dashoffset="{circumference * 0.25}"
                transform="rotate(-90 {c} {c})"/>
        <circle cx="{c}" cy="{c}" r="{r}" fill="none" stroke="{GREEN}" stroke-width="5"
                stroke-dasharray="{long_arc} {short_arc}"
                stroke-dashoffset="{circumference * 0.25}"
                transform="rotate(-90 {c} {c})"/>
        <text x="{c - 14}" y="{c - 6}" fill="{GREEN}" font-size="8" font-weight="bold">{long_count}</text>
        <text x="{c + 2}" y="{c + 10}" fill="{RED}" font-size="8" font-weight="bold">{short_count}</text>
    </svg>
    """


# ═══════════════════════════════════════════════════════════════
#  Public renderers
# ═══════════════════════════════════════════════════════════════

def render_kpi_row(metrics: dict):
    """Render top 2 rows of KPI cards (3 per row) matching TopStepX."""

    # ── Row 1 ──
    c1, c2, c3 = st.columns(3)

    with c1:
        pnl = metrics['total_pnl']
        st.markdown(_card(
            "Total P&L",
            _val(_format_pnl(pnl), _pnl_color(pnl)),
        ), unsafe_allow_html=True)

    with c2:
        wr = metrics['win_rate']
        donut = _win_rate_donut_svg(wr, metrics['win_count'], metrics['loss_count'])
        st.markdown(_card(
            "Trade Win %",
            f"""<div style="display: flex; align-items: center; gap: 12px;">
                {_val(f"{wr:.2f}%")}
                {donut}
            </div>""",
        ), unsafe_allow_html=True)

    with c3:
        rr = metrics['rr_ratio']
        bar = _avg_win_loss_bar_svg(metrics['avg_win'], metrics['avg_loss'])
        st.markdown(_card(
            "Avg Win / Avg Loss",
            _val(f"{rr:.2f}"),
            bar,
        ), unsafe_allow_html=True)

    st.markdown('<div style="height: 8px;"></div>', unsafe_allow_html=True)

    # ── Row 2 ──
    c4, c5, c6 = st.columns(3)

    with c4:
        dwp = metrics.get('day_win_pct', 0)
        active = metrics.get('active_days', 0)
        if active > 0:
            val_text = f"{dwp:.0f}%"
        else:
            val_text = "No trades"
        st.markdown(_card(
            "Day Win %",
            _val(val_text),
        ), unsafe_allow_html=True)

    with c5:
        pf = metrics['profit_factor']
        donut = _profit_factor_donut_svg(metrics['gross_profit'], metrics['gross_loss'])
        gp = metrics['gross_profit']
        gl = metrics['gross_loss']
        st.markdown(_card(
            "Profit Factor",
            f"""<div style="display: flex; align-items: center; gap: 12px;">
                {_val(f"{pf:.2f}")}
                {donut}
            </div>""",
            f"""<div style="display: flex; justify-content: space-around; margin-top: 4px;">
                <span style="color: {GREEN}; font-size: 10px;">${gp:,.2f}</span>
                <span style="color: {RED}; font-size: 10px;">-${gl:,.2f}</span>
            </div>""",
        ), unsafe_allow_html=True)

    with c6:
        bdp = metrics.get('best_day_pct', 0)
        st.markdown(_card(
            "Best Day % of Total Profit",
            _val(f"{bdp:.2f}%"),
        ), unsafe_allow_html=True)


def render_day_analysis(metrics: dict, day_stats: dict):
    """Render day analysis row (Most Active / Most Profitable / Least Profitable)."""
    if not day_stats:
        return

    most_active = max(day_stats.items(), key=lambda x: x[1]['trade_count'])
    most_profitable = max(day_stats.items(), key=lambda x: x[1]['total_pnl'])
    least_profitable = min(day_stats.items(), key=lambda x: x[1]['total_pnl'])

    c1, c2, c3 = st.columns(3)

    with c1:
        active_days = metrics.get('active_days', 0)
        total_trades = metrics.get('total_trades', 0)
        avg_per_day = metrics.get('avg_trades_per_day', 0)
        st.markdown(_card(
            "Most Active Day",
            _val(most_active[0]),
            f"""<div style="color: {LABEL_COLOR}; font-size: 11px; margin-top: 6px; line-height: 1.6;">
                {active_days} active days<br>
                {total_trades} total trades<br>
                {avg_per_day:.2f} avg trades/day
            </div>""",
        ), unsafe_allow_html=True)

    with c2:
        pnl = most_profitable[1]['total_pnl']
        st.markdown(_card(
            "Most Profitable Day",
            f"""<div style="display: flex; justify-content: space-between; align-items: center;">
                {_val(most_profitable[0])}
                <span style="color: {_pnl_color(pnl)}; font-size: 20px; font-weight: 700;">{_format_pnl(pnl)}</span>
            </div>""",
        ), unsafe_allow_html=True)

    with c3:
        pnl = least_profitable[1]['total_pnl']
        st.markdown(_card(
            "Least Profitable Day",
            f"""<div style="display: flex; justify-content: space-between; align-items: center;">
                {_val(least_profitable[0])}
                <span style="color: {_pnl_color(pnl)}; font-size: 20px; font-weight: 700;">{_format_pnl(pnl)}</span>
            </div>""",
        ), unsafe_allow_html=True)


def render_stats_row(metrics: dict):
    """Render Total Trades / Total Lots / Avg Duration row."""
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(_card(
            "Total Number of Trades",
            _val(str(metrics['total_trades'])),
        ), unsafe_allow_html=True)

    with c2:
        st.markdown(_card(
            "Total Number of Lots Traded",
            _val(str(metrics.get('total_lots', 0))),
        ), unsafe_allow_html=True)

    with c3:
        dur = format_duration(metrics['avg_duration_seconds'])
        st.markdown(_card(
            "Average Trade Duration",
            _val(dur),
        ), unsafe_allow_html=True)


def render_duration_row(metrics: dict):
    """Render Avg Win Duration / Avg Loss Duration row."""
    c1, c2 = st.columns(2)

    with c1:
        st.markdown(_card(
            "Average Win Duration",
            _val(format_duration(metrics['avg_win_duration'])),
        ), unsafe_allow_html=True)

    with c2:
        st.markdown(_card(
            "Average Loss Duration",
            _val(format_duration(metrics['avg_loss_duration'])),
        ), unsafe_allow_html=True)


def render_avg_trade_row(metrics: dict):
    """Render Avg Winning / Avg Losing / Direction row."""
    c1, c2, c3 = st.columns(3)

    with c1:
        avg_w = metrics['avg_win']
        st.markdown(_card(
            "Avg Winning Trade",
            _val(f"${avg_w:,.2f}", GREEN),
        ), unsafe_allow_html=True)

    with c2:
        avg_l = metrics['avg_loss']
        st.markdown(_card(
            "Avg Losing Trade",
            _val(f"-${avg_l:,.2f}", RED),
        ), unsafe_allow_html=True)

    with c3:
        long_pct = metrics['long_pct']
        total = metrics['total_trades']
        long_count = int(total * long_pct / 100) if total > 0 else 0
        short_count = total - long_count
        donut = _direction_donut_svg(long_pct, long_count, short_count)
        st.markdown(_card(
            "Trade Direction %",
            f"""<div style="display: flex; align-items: center; gap: 12px;">
                {_val(f"{long_pct:.2f}%")}
                {donut}
            </div>""",
        ), unsafe_allow_html=True)


def render_best_worst_row(metrics: dict):
    """Render Best Trade / Worst Trade row with details."""
    from config.fees import extract_base_symbol
    c1, c2 = st.columns(2)

    with c1:
        pnl = metrics['best_trade_pnl']
        sym = extract_base_symbol(metrics.get('best_trade_symbol', ''))
        side = metrics.get('best_trade_side', '')
        qty = metrics.get('best_trade_qty', 0)
        entry_p = metrics.get('best_trade_entry', 0)
        exit_p = metrics.get('best_trade_exit', 0)
        dt = metrics.get('best_trade_date', '')
        detail = f"{side} {qty} /{sym} @ {entry_p}<br>Exited @ {exit_p}<br>{dt}" if sym else ""
        st.markdown(_card(
            "Best Trade",
            f"""<div style="display: flex; justify-content: space-between; align-items: flex-start;">
                {_val(_format_pnl(pnl), GREEN, "26px")}
                <div style="color: {LABEL_COLOR}; font-size: 10px; text-align: right; line-height: 1.5;">{detail}</div>
            </div>""",
        ), unsafe_allow_html=True)

    with c2:
        pnl = metrics['worst_trade_pnl']
        sym = extract_base_symbol(metrics.get('worst_trade_symbol', ''))
        side = metrics.get('worst_trade_side', '')
        qty = metrics.get('worst_trade_qty', 0)
        entry_p = metrics.get('worst_trade_entry', 0)
        exit_p = metrics.get('worst_trade_exit', 0)
        dt = metrics.get('worst_trade_date', '')
        detail = f"{side} {qty} /{sym} @ {entry_p}<br>Exited @ {exit_p}<br>{dt}" if sym else ""
        st.markdown(_card(
            "Worst Trade",
            f"""<div style="display: flex; justify-content: space-between; align-items: flex-start;">
                {_val(_format_pnl(pnl), RED, "26px")}
                <div style="color: {LABEL_COLOR}; font-size: 10px; text-align: right; line-height: 1.5;">{detail}</div>
            </div>""",
        ), unsafe_allow_html=True)


def render_trade_stats(metrics: dict):
    """Legacy compat - no longer used in new layout."""
    pass
