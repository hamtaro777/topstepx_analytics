"""
Calendar View Component - TopStepX Style
"""
import streamlit as st
import calendar
from datetime import date
from typing import Dict

# ── Color constants (shared with metrics.py) ─────────────────
GREEN = "#00C853"
RED = "#FF5252"
CARD_BG = "#1A1D2E"
CARD_BORDER = "#2A2D3E"
LABEL_COLOR = "#8A8D98"


def _format_pnl(value: float) -> str:
    if value >= 0:
        return f"${value:,.2f}"
    return f"-${abs(value):,.2f}"


def render_monthly_calendar(year: int, month: int, calendar_data: Dict[int, Dict]):
    """Render monthly P/L calendar matching TopStepX design."""
    cal = calendar.Calendar(firstweekday=6)
    month_name = calendar.month_name[month]

    # Month total P/L
    total_pnl = sum(d.get('pnl', 0) for d in calendar_data.values())
    pnl_color = GREEN if total_pnl >= 0 else RED

    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 16px;">
        <span style="color: {pnl_color}; font-size: 18px; font-weight: 700;">
            Monthly P/L: {_format_pnl(total_pnl)}
        </span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"#### {month_name} {year}")

    # Header row
    cols = st.columns(7)
    for i, day_name in enumerate(['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa']):
        cols[i].markdown(f"""
        <div style="text-align: center; color: {LABEL_COLOR}; font-size: 12px; font-weight: 600; padding: 4px 0;">
            {day_name}
        </div>
        """, unsafe_allow_html=True)

    # Calendar weeks
    weeks = cal.monthdayscalendar(year, month)
    today = date.today()

    for week in weeks:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].markdown("""
                <div style="height: 70px; background: transparent;"></div>
                """, unsafe_allow_html=True)
            else:
                day_data = calendar_data.get(day, {})
                pnl = day_data.get('pnl', 0)
                trades = day_data.get('trade_count', 0)
                is_today = (year == today.year and month == today.month and day == today.day)

                # Today indicator
                today_badge = ""
                if is_today:
                    today_badge = f"""
                    <div style="width: 22px; height: 22px; border-radius: 50%; background: #5B8DEF;
                                display: inline-flex; align-items: center; justify-content: center;
                                font-size: 11px; color: #fff; font-weight: 700; margin: 0 auto;">
                        {day}
                    </div>"""
                    day_label = today_badge
                else:
                    day_label = f'<div style="font-size: 12px; color: #ccc; text-align: center;">{day}</div>'

                if trades > 0:
                    color = GREEN if pnl >= 0 else RED
                    # Active day with trades – has colored background tint
                    bg_tint = "rgba(0,200,83,0.08)" if pnl >= 0 else "rgba(255,82,82,0.08)"
                    cols[i].markdown(f"""
                    <div style="
                        background: {bg_tint};
                        border: 1px solid {CARD_BORDER};
                        border-radius: 6px;
                        padding: 6px 4px;
                        text-align: center;
                        height: 70px;
                        box-sizing: border-box;
                    ">
                        {day_label}
                        <div style="color: {color}; font-weight: 700; font-size: 13px;">{_format_pnl(pnl)}</div>
                        <div style="font-size: 9px; color: {LABEL_COLOR};">{trades} trades</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    cols[i].markdown(f"""
                    <div style="
                        border: 1px solid {CARD_BORDER};
                        border-radius: 6px;
                        padding: 6px 4px;
                        text-align: center;
                        height: 70px;
                        box-sizing: border-box;
                    ">
                        {day_label}
                    </div>
                    """, unsafe_allow_html=True)


def render_weekly_summary(daily_stats, year: int, month: int):
    """Render weekly P/L summary in TopStepX card style."""
    import pandas as pd

    if daily_stats.empty:
        return

    # Filter to month
    month_data = daily_stats[
        (pd.to_datetime(daily_stats['date']).dt.year == year) &
        (pd.to_datetime(daily_stats['date']).dt.month == month)
    ]

    if month_data.empty:
        return

    # Group by week
    month_data = month_data.copy()
    month_data['week'] = pd.to_datetime(month_data['date']).dt.isocalendar().week

    weekly = month_data.groupby('week').agg({
        'total_pnl': 'sum',
        'trade_count': 'sum'
    }).reset_index()

    st.markdown("### Weekly Summary")
    for i, row in weekly.iterrows():
        pnl = row['total_pnl']
        color = GREEN if pnl >= 0 else RED
        trades = int(row['trade_count'])
        st.markdown(f"""
        <div style="
            display: flex; justify-content: space-between; align-items: center;
            padding: 10px 16px;
            background: {CARD_BG};
            border: 1px solid {CARD_BORDER};
            border-radius: 6px;
            margin-bottom: 4px;
        ">
            <span style="color: #fff; font-weight: 600;">Week {i+1}</span>
            <span style="color: {color}; font-weight: 700; font-size: 16px;">{_format_pnl(pnl)}</span>
            <span style="color: {LABEL_COLOR}; font-size: 12px;">{trades} trades</span>
        </div>
        """, unsafe_allow_html=True)
