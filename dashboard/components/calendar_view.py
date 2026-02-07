"""
Calendar View Component
"""
import streamlit as st
import calendar
from datetime import date
from typing import Dict


def render_monthly_calendar(year: int, month: int, calendar_data: Dict[int, Dict]):
    """Render monthly P/L calendar"""
    cal = calendar.Calendar(firstweekday=6)
    month_name = calendar.month_name[month]
    
    st.markdown(f"### {month_name} {year}")
    
    # Header row
    cols = st.columns(7)
    for i, day_name in enumerate(['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']):
        cols[i].markdown(f"**{day_name}**")
    
    # Calendar weeks
    weeks = cal.monthdayscalendar(year, month)
    
    for week in weeks:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].markdown("")
            else:
                day_data = calendar_data.get(day, {})
                pnl = day_data.get('pnl', 0)
                trades = day_data.get('trade_count', 0)
                
                if trades > 0:
                    color = "#00C853" if pnl >= 0 else "#FF5252"
                    cols[i].markdown(f"""
                    <div style="
                        background: #1E1E1E;
                        padding: 5px;
                        border-radius: 4px;
                        text-align: center;
                        border-left: 3px solid {color};
                    ">
                        <div style="font-size: 12px;">{day}</div>
                        <div style="color: {color}; font-weight: bold;">${pnl:,.0f}</div>
                        <div style="font-size: 10px; color: #888;">{trades} trades</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    cols[i].markdown(f"""
                    <div style="padding: 5px; text-align: center;">
                        <div style="font-size: 12px; color: #666;">{day}</div>
                    </div>
                    """, unsafe_allow_html=True)


def render_weekly_summary(daily_stats, year: int, month: int):
    """Render weekly P/L summary"""
    import pandas as pd
    from datetime import datetime
    
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
        color = "#00C853" if pnl >= 0 else "#FF5252"
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; padding: 5px; border-bottom: 1px solid #333;">
            <span>Week {i+1}</span>
            <span style="color: {color}; font-weight: bold;">${pnl:,.2f}</span>
            <span style="color: #888;">{int(row['trade_count'])} trades</span>
        </div>
        """, unsafe_allow_html=True)