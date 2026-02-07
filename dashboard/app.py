"""
TopstepX Analytics Dashboard
Streamlit Application
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.schema import init_database
from database.repository import TradeRepository
from services.analytics import AnalyticsService
from services.data_collector import DataCollector
from dashboard.components.metrics import (
    render_kpi_row, render_day_analysis, render_stats_row,
    render_duration_row, render_avg_trade_row, render_best_worst_row,
)
from dashboard.components.charts import (
    create_equity_curve, create_daily_pnl_bar,
    create_duration_chart, create_win_rate_by_duration,
)
from dashboard.components.calendar_view import render_monthly_calendar, render_weekly_summary

# Page config
st.set_page_config(
    page_title="TopstepX Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── TopStepX Dark Theme CSS ──────────────────────────────────────
st.markdown("""
<style>
    /* Base background */
    .stApp { background-color: #0D1117; }
    section[data-testid="stSidebar"] { background-color: #151920; }

    /* Remove default streamlit padding/gaps */
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }

    /* Tab styling – multiple selector strategies for compatibility */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0 !important;
        border-bottom: 1px solid #2A2D3E !important;
        background-color: transparent !important;
    }
    /* Target all elements inside tab buttons */
    .stTabs [data-baseweb="tab-list"] button,
    .stTabs [data-baseweb="tab-list"] button *,
    .stTabs [data-baseweb="tab-list"] [role="tab"],
    .stTabs [data-baseweb="tab-list"] [role="tab"] * {
        background-color: transparent !important;
        color: #8A8D98 !important;
        border: none !important;
        font-weight: 500 !important;
        font-size: 14px !important;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"],
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] *,
    .stTabs [data-baseweb="tab-list"] [role="tab"][aria-selected="true"],
    .stTabs [data-baseweb="tab-list"] [role="tab"][aria-selected="true"] * {
        color: #FFFFFF !important;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"],
    .stTabs [data-baseweb="tab-list"] [role="tab"][aria-selected="true"] {
        border-bottom: 2px solid #00C853 !important;
    }
    /* Also target by Streamlit's own class naming */
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #00C853 !important;
    }

    /* Card row spacing */
    [data-testid="stHorizontalBlock"] { gap: 8px !important; }

    /* Labels & text */
    .stSelectbox label, .stDateInput label { color: #FFFFFF; }

    /* Section dividers */
    .section-gap { height: 8px; }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #0D1117; }
    ::-webkit-scrollbar-thumb { background: #2A2D3E; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

GAP = '<div class="section-gap"></div>'


def init_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'collector' not in st.session_state:
        st.session_state.collector = None
    if 'accounts' not in st.session_state:
        st.session_state.accounts = []


def render_sidebar():
    """Render sidebar with controls"""
    st.sidebar.title("TopstepX Analytics")

    # Account selector - only LIVE accounts (TOPX in name)
    repo = TradeRepository()
    accounts = repo.get_accounts()

    # Filter to only LIVE accounts
    accounts = [a for a in accounts if 'TOPX' in a.get('name', '').upper()]

    if accounts:
        account_names = [f"{a['name']} (ID: {a['account_id']})" for a in accounts]
        selected = st.sidebar.selectbox("Select Account", account_names)
        if selected:
            idx = account_names.index(selected)
            st.session_state.selected_account = accounts[idx]

    # Date range
    st.sidebar.markdown("### Date Range")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input("Start", date.today() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End", date.today())

    st.session_state.start_date = start_date
    st.session_state.end_date = end_date

    # Sync button
    st.sidebar.markdown("---")
    if st.sidebar.button("Sync Data from API", type="primary"):
        sync_data()

    return accounts


def sync_data():
    """Sync data from TopstepX API"""
    with st.spinner("Syncing data..."):
        try:
            collector = DataCollector()
            if collector.authenticate():
                accounts = collector.sync_accounts()
                st.sidebar.success(f"Synced {len(accounts)} accounts")

                for acc in accounts:
                    count = collector.sync_trades(acc['id'])
                    st.sidebar.info(f"{acc['name']}: {count} new trades")

                st.rerun()
            else:
                st.sidebar.error("Authentication failed")
        except Exception as e:
            st.sidebar.error(f"Sync failed: {e}")


# ═══════════════════════════════════════════════════════════════
#  Overview Page – TopStepX layout
# ═══════════════════════════════════════════════════════════════
def render_overview_page(trades: list, daily_stats: pd.DataFrame):
    """Render main overview page matching TopStepX design."""
    analytics = AnalyticsService(trades)
    metrics = analytics.get_summary_metrics()

    # ── Row 1–2: KPI cards (2 rows × 3 cols) ──
    render_kpi_row(metrics)

    st.markdown(GAP, unsafe_allow_html=True)

    # ── Daily Account Balance chart (full width) ──
    fig = create_equity_curve(daily_stats)
    st.plotly_chart(fig, use_container_width=True, key="equity_curve")

    st.markdown(GAP, unsafe_allow_html=True)

    # ── Day Analysis row ──
    day_stats = analytics.get_day_of_week_stats()
    render_day_analysis(metrics, day_stats)

    st.markdown(GAP, unsafe_allow_html=True)

    # ── Stats row: Total Trades / Total Lots / Avg Duration ──
    render_stats_row(metrics)

    st.markdown(GAP, unsafe_allow_html=True)

    # ── Duration row: Avg Win Duration / Avg Loss Duration ──
    render_duration_row(metrics)

    st.markdown(GAP, unsafe_allow_html=True)

    # ── Avg Winning / Avg Losing / Trade Direction ──
    render_avg_trade_row(metrics)

    st.markdown(GAP, unsafe_allow_html=True)

    # ── Best / Worst Trade ──
    render_best_worst_row(metrics)

    st.markdown(GAP, unsafe_allow_html=True)

    # ── Charts: Cumulative P/L + Daily P/L ──
    c1, c2 = st.columns(2)
    with c1:
        fig = create_equity_curve(daily_stats)
        st.plotly_chart(fig, use_container_width=True, key="equity_curve_2")
    with c2:
        fig = create_daily_pnl_bar(daily_stats)
        st.plotly_chart(fig, use_container_width=True, key="daily_pnl")

    st.markdown(GAP, unsafe_allow_html=True)

    # ── Charts: Duration Analysis + Win Rate by Duration ──
    duration_data = analytics.get_duration_analysis()
    c1, c2 = st.columns(2)
    with c1:
        fig = create_duration_chart(duration_data)
        st.plotly_chart(fig, use_container_width=True, key="duration_chart")
    with c2:
        fig = create_win_rate_by_duration(duration_data)
        st.plotly_chart(fig, use_container_width=True, key="win_rate_duration")


# ═══════════════════════════════════════════════════════════════
#  Calendar Page
# ═══════════════════════════════════════════════════════════════
def render_calendar_page(trades: list, daily_stats: pd.DataFrame):
    """Render calendar view page"""
    st.markdown("## Monthly P/L Calendar")

    analytics = AnalyticsService(trades)

    col1, col2 = st.columns([1, 4])

    with col1:
        year = st.selectbox("Year", [2024, 2025, 2026], index=2)
        month = st.selectbox("Month", range(1, 13), index=datetime.now().month - 1)

    with col2:
        calendar_data = analytics.get_monthly_calendar(year, month)
        render_monthly_calendar(year, month, calendar_data)

    st.markdown("---")
    render_weekly_summary(daily_stats, year, month)


# ═══════════════════════════════════════════════════════════════
#  Trades Page
# ═══════════════════════════════════════════════════════════════
def render_trades_page(trades: list):
    """Render trades list page"""
    st.markdown("## Trade History")

    if not trades:
        st.info("No trades found for the selected period")
        return

    df = pd.DataFrame(trades)

    # Calculate net_pnl
    df['fees'] = pd.to_numeric(df.get('fees', 0), errors='coerce').fillna(0)
    df['net_pnl'] = df['pnl'] - df['fees']

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        symbols = ['All'] + list(df['symbol'].unique())
        symbol_filter = st.selectbox("Symbol", symbols)
    with col2:
        sides = ['All', 'Long', 'Short']
        side_filter = st.selectbox("Side", sides)
    with col3:
        results = ['All', 'Win', 'Loss']
        result_filter = st.selectbox("Result", results)

    # Apply filters
    filtered = df.copy()
    if symbol_filter != 'All':
        filtered = filtered[filtered['symbol'] == symbol_filter]
    if side_filter != 'All':
        filtered = filtered[filtered['side'] == side_filter]
    if result_filter == 'Win':
        filtered = filtered[filtered['net_pnl'] > 0]
    elif result_filter == 'Loss':
        filtered = filtered[filtered['net_pnl'] < 0]

    # Display table with fees and net_pnl
    display_cols = ['entry_time', 'symbol', 'side', 'quantity', 'entry_price', 'exit_price', 'pnl', 'fees', 'net_pnl', 'duration_seconds']
    st.dataframe(
        filtered[display_cols],
        use_container_width=True,
        hide_index=True
    )

    # Summary with net P/L
    total_fees = filtered['fees'].sum()
    net_pnl = filtered['net_pnl'].sum()
    st.markdown(f"**Total: {len(filtered)} trades | Gross P/L: ${filtered['pnl'].sum():,.2f} | Fees: ${total_fees:,.2f} | Net P/L: ${net_pnl:,.2f}**")


# ═══════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════
def main():
    init_session_state()
    init_database()

    accounts = render_sidebar()

    if not accounts:
        st.warning("No accounts found. Click 'Sync Data from API' to fetch your trading data.")
        st.markdown("""
        ### Setup Instructions
        1. Create a `.env` file with your credentials:
        TOPSTEPX_USERNAME=your_username
        TOPSTEPX_API_KEY=your_api_key
        2. Click 'Sync Data from API' in the sidebar
        """)
        return

    # Get data
    repo = TradeRepository()
    account = st.session_state.get('selected_account', accounts[0])

    trades = repo.get_trades(
        account_id=account['account_id'],
        start_date=st.session_state.get('start_date'),
        end_date=st.session_state.get('end_date')
    )

    daily_stats = pd.DataFrame(repo.get_daily_stats(
        account_id=account['account_id'],
        start_date=st.session_state.get('start_date'),
        end_date=st.session_state.get('end_date')
    ))

    # Navigation tabs
    tab1, tab2, tab3 = st.tabs(["Overview", "Calendar", "Trades"])

    with tab1:
        render_overview_page(trades, daily_stats)

    with tab2:
        render_calendar_page(trades, daily_stats)

    with tab3:
        render_trades_page(trades)


if __name__ == "__main__":
    main()
