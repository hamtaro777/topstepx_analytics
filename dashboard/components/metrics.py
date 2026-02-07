"""
Metric Card Components
"""
import streamlit as st


def metric_card(label: str, value: str, delta: str = None, color: str = "normal"):
    """Display a metric card"""
    if color == "positive":
        value_color = "#00C853"
    elif color == "negative":
        value_color = "#FF5252"
    else:
        value_color = "#FFFFFF"
    
    st.markdown(f"""
    <div style="
        background: #1E1E1E;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #333;
    ">
        <div style="color: #888; font-size: 12px;">{label}</div>
        <div style="color: {value_color}; font-size: 24px; font-weight: bold;">{value}</div>
        {f'<div style="color: #888; font-size: 12px;">{delta}</div>' if delta else ''}
    </div>
    """, unsafe_allow_html=True)


def render_kpi_row(metrics: dict):
    """Render a row of KPI metrics"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        pnl = metrics['total_pnl']
        color = "positive" if pnl >= 0 else "negative"
        metric_card("Total P/L", f"${pnl:,.2f}", color=color)
    
    with col2:
        metric_card("Trade Win %", f"{metrics['win_rate']:.2f}%")
    
    with col3:
        rr = metrics['rr_ratio']
        metric_card("Avg Win:Avg Loss", f"{rr:.2f}", 
                   f"${metrics['avg_win']:,.2f} : ${metrics['avg_loss']:,.2f}")
    
    with col4:
        pf = metrics['profit_factor']
        color = "positive" if pf >= 1 else "negative"
        metric_card("Profit Factor", f"{pf:.2f}", color=color)


def render_trade_stats(metrics: dict):
    """Render trade statistics section"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Total Trades**")
        st.markdown(f"### {metrics['total_trades']}")
        st.markdown("**Loss Trades**")
        st.markdown(f"### {metrics['loss_count']}")
    
    with col2:
        from services.analytics import format_duration
        st.markdown("**Avg Win Duration**")
        st.markdown(f"### {format_duration(metrics['avg_win_duration'])}")
        st.markdown("**Avg Loss Duration**")
        st.markdown(f"### {format_duration(metrics['avg_loss_duration'])}")
    
    with col3:
        st.markdown("**Avg Winning Trade**")
        st.markdown(f"### ${metrics['avg_win']:,.2f}")
        st.markdown("**Avg Losing Trade**")
        st.markdown(f"### -${metrics['avg_loss']:,.2f}")