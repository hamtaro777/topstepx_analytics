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


def _card_html(label: str, body: str, min_h: int = 120) -> str:
    """Minimal card wrapper. Keep body HTML as simple as possible."""
    return (
        f'<div style="background:{CARD_BG};padding:16px 20px;border-radius:8px;'
        f'border:1px solid {CARD_BORDER};box-sizing:border-box;min-height:{min_h}px;">'
        f'<div style="color:{LABEL_COLOR};font-size:12px;margin-bottom:8px;font-weight:500;">{label}</div>'
        f'{body}'
        f'</div>'
    )


def _big(text: str, color: str = VALUE_COLOR, size: str = "28px") -> str:
    return f'<div style="color:{color};font-size:{size};font-weight:700;line-height:1.2;">{text}</div>'


def _small(text: str, color: str = LABEL_COLOR) -> str:
    return f'<div style="color:{color};font-size:11px;margin-top:4px;">{text}</div>'


def _render(html: str):
    """Shorthand for st.markdown with unsafe_allow_html."""
    st.markdown(html, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  Public renderers
# ═══════════════════════════════════════════════════════════════

def render_kpi_row(metrics: dict):
    """Render top 2 rows of KPI cards (3 per row)."""

    # ── Row 1 ──
    c1, c2, c3 = st.columns(3)

    with c1:
        pnl = metrics['total_pnl']
        _render(_card_html("Total P&L", _big(_format_pnl(pnl), _pnl_color(pnl))))

    with c2:
        wr = metrics['win_rate']
        wc = metrics['win_count']
        lc = metrics['loss_count']
        body = (
            _big(f"{wr:.2f}%")
            + f'<div style="margin-top:6px;font-size:12px;">'
            f'<span style="color:{GREEN};font-weight:600;">{wc}</span>'
            f'<span style="color:{LABEL_COLOR};"> W</span>'
            f'<span style="color:{LABEL_COLOR};margin:0 6px;">|</span>'
            f'<span style="color:{RED};font-weight:600;">{lc}</span>'
            f'<span style="color:{LABEL_COLOR};"> L</span>'
            f'</div>'
        )
        _render(_card_html("Trade Win %", body))

    with c3:
        rr = metrics['rr_ratio']
        avg_w = metrics['avg_win']
        avg_l = metrics['avg_loss']
        total = avg_w + avg_l
        win_pct = (avg_w / total * 100) if total > 0 else 50
        body = (
            f'<div style="display:flex;align-items:center;gap:16px;">'
            f'<div style="color:{VALUE_COLOR};font-size:28px;font-weight:700;line-height:1.2;white-space:nowrap;">{rr:.2f}</div>'
            f'<div style="flex:1;min-width:0;">'
            f'<div style="display:flex;height:8px;border-radius:4px;overflow:hidden;background:#333;">'
            f'<div style="width:{win_pct}%;background:{GREEN};"></div>'
            f'<div style="width:{100-win_pct}%;background:{RED};"></div>'
            f'</div>'
            f'<div style="display:flex;justify-content:space-between;margin-top:6px;">'
            f'<span style="color:{GREEN};font-size:14px;font-weight:600;">${avg_w:,.2f}</span>'
            f'<span style="color:{RED};font-size:14px;font-weight:600;">-${avg_l:,.2f}</span>'
            f'</div></div></div>'
        )
        _render(_card_html("Avg Win / Avg Loss", body))

    _render('<div style="height:8px;"></div>')

    # ── Row 2 ──
    c4, c5, c6 = st.columns(3)

    with c4:
        dwp = metrics.get('day_win_pct', 0)
        active = metrics.get('active_days', 0)
        val_text = f"{dwp:.0f}%" if active > 0 else "No trades"
        _render(_card_html("Day Win %", _big(val_text)))

    with c5:
        pf = metrics['profit_factor']
        gp = metrics['gross_profit']
        gl = metrics['gross_loss']
        body = (
            _big(f"{pf:.2f}")
            + f'<div style="margin-top:6px;font-size:11px;">'
            f'<span style="color:{GREEN};font-weight:600;">${gp:,.2f}</span>'
            f'<span style="color:{LABEL_COLOR};margin:0 6px;">|</span>'
            f'<span style="color:{RED};font-weight:600;">-${gl:,.2f}</span>'
            f'</div>'
        )
        _render(_card_html("Profit Factor", body))

    with c6:
        bdp = metrics.get('best_day_pct', 0)
        _render(_card_html("Best Day % of Total Profit", _big(f"{bdp:.2f}%")))


def render_day_analysis(metrics: dict, day_stats: dict):
    """Render day analysis row."""
    if not day_stats:
        return

    most_active = max(day_stats.items(), key=lambda x: x[1]['trade_count'])
    most_profitable = max(day_stats.items(), key=lambda x: x[1]['total_pnl'])
    least_profitable = min(day_stats.items(), key=lambda x: x[1]['total_pnl'])

    c1, c2, c3 = st.columns(3)

    with c1:
        ad = metrics.get('active_days', 0)
        tt = metrics.get('total_trades', 0)
        apd = metrics.get('avg_trades_per_day', 0)
        body = (
            _big(most_active[0])
            + f'<div style="color:{LABEL_COLOR};font-size:11px;margin-top:6px;line-height:1.6;">'
            f'{ad} active days | {tt} total trades | {apd:.2f} avg/day</div>'
        )
        _render(_card_html("Most Active Day", body))

    with c2:
        pnl = most_profitable[1]['total_pnl']
        body = (
            f'<div style="display:flex;justify-content:space-between;align-items:center;">'
            + _big(most_profitable[0])
            + f'<span style="color:{_pnl_color(pnl)};font-size:20px;font-weight:700;">{_format_pnl(pnl)}</span>'
            f'</div>'
        )
        _render(_card_html("Most Profitable Day", body))

    with c3:
        pnl = least_profitable[1]['total_pnl']
        body = (
            f'<div style="display:flex;justify-content:space-between;align-items:center;">'
            + _big(least_profitable[0])
            + f'<span style="color:{_pnl_color(pnl)};font-size:20px;font-weight:700;">{_format_pnl(pnl)}</span>'
            f'</div>'
        )
        _render(_card_html("Least Profitable Day", body))


def render_stats_row(metrics: dict):
    """Render Total Trades / Total Lots / Avg Duration row."""
    c1, c2, c3 = st.columns(3)
    with c1:
        _render(_card_html("Total Number of Trades", _big(str(metrics['total_trades']))))
    with c2:
        _render(_card_html("Total Number of Lots Traded", _big(str(metrics.get('total_lots', 0)))))
    with c3:
        _render(_card_html("Average Trade Duration", _big(format_duration(metrics['avg_duration_seconds']))))


def render_duration_row(metrics: dict):
    """Render Avg Win Duration / Avg Loss Duration row."""
    c1, c2 = st.columns(2)
    with c1:
        _render(_card_html("Average Win Duration", _big(format_duration(metrics['avg_win_duration']))))
    with c2:
        _render(_card_html("Average Loss Duration", _big(format_duration(metrics['avg_loss_duration']))))


def render_avg_trade_row(metrics: dict):
    """Render Avg Winning / Avg Losing / Direction row."""
    c1, c2, c3 = st.columns(3)

    with c1:
        _render(_card_html("Avg Winning Trade", _big(f"${metrics['avg_win']:,.2f}", GREEN)))

    with c2:
        _render(_card_html("Avg Losing Trade", _big(f"-${metrics['avg_loss']:,.2f}", RED)))

    with c3:
        lp = metrics['long_pct']
        total = metrics['total_trades']
        lc = int(total * lp / 100) if total > 0 else 0
        sc = total - lc
        body = (
            _big(f"{lp:.2f}%")
            + f'<div style="margin-top:6px;font-size:12px;">'
            f'<span style="color:{GREEN};font-weight:600;">{lc}</span>'
            f'<span style="color:{LABEL_COLOR};"> Long</span>'
            f'<span style="color:{LABEL_COLOR};margin:0 6px;">|</span>'
            f'<span style="color:{RED};font-weight:600;">{sc}</span>'
            f'<span style="color:{LABEL_COLOR};"> Short</span>'
            f'</div>'
        )
        _render(_card_html("Trade Direction %", body))


def render_best_worst_row(metrics: dict):
    """Render Best Trade / Worst Trade row."""
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
        detail = f"{side} {qty} /{sym} @ {entry_p} → {exit_p}" if sym else ""
        body = (
            f'<div style="display:flex;justify-content:space-between;align-items:flex-start;">'
            + _big(_format_pnl(pnl), GREEN, "26px")
            + f'<div style="color:{LABEL_COLOR};font-size:10px;text-align:right;line-height:1.5;">'
            f'{detail}</div></div>'
        )
        if dt:
            body += f'<div style="color:{LABEL_COLOR};font-size:10px;margin-top:4px;">{dt}</div>'
        _render(_card_html("Best Trade", body))

    with c2:
        pnl = metrics['worst_trade_pnl']
        sym = extract_base_symbol(metrics.get('worst_trade_symbol', ''))
        side = metrics.get('worst_trade_side', '')
        qty = metrics.get('worst_trade_qty', 0)
        entry_p = metrics.get('worst_trade_entry', 0)
        exit_p = metrics.get('worst_trade_exit', 0)
        dt = metrics.get('worst_trade_date', '')
        detail = f"{side} {qty} /{sym} @ {entry_p} → {exit_p}" if sym else ""
        body = (
            f'<div style="display:flex;justify-content:space-between;align-items:flex-start;">'
            + _big(_format_pnl(pnl), RED, "26px")
            + f'<div style="color:{LABEL_COLOR};font-size:10px;text-align:right;line-height:1.5;">'
            f'{detail}</div></div>'
        )
        if dt:
            body += f'<div style="color:{LABEL_COLOR};font-size:10px;margin-top:4px;">{dt}</div>'
        _render(_card_html("Worst Trade", body))


def render_trade_stats(metrics: dict):
    """Legacy compat."""
    pass
