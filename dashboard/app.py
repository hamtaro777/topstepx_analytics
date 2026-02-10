"""
TopstepX Analytics Dashboard
Streamlit Application
"""
import streamlit as st
import pandas as pd
import json
from datetime import datetime, date, timedelta
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.schema import init_database
from database.repository import TradeRepository
from services.analytics import AnalyticsService
from services.data_collector import DataCollector
from config.fees import get_all_fee_settings, set_custom_fee, remove_custom_fee
from dashboard.components.metrics import (
    render_kpi_row, render_day_analysis, render_stats_row,
    render_duration_row, render_avg_trade_row, render_best_worst_row,
)
from dashboard.components.charts import (
    create_equity_curve, create_daily_pnl_bar,
    create_duration_chart, create_win_rate_by_duration,
)
from dashboard.components.calendar_view import render_monthly_calendar, render_weekly_summary

# Credentials file path (stored locally alongside the database)
_BASE_DIR = Path(__file__).parent.parent
_CREDENTIALS_PATH = _BASE_DIR / "data" / "credentials.json"


def _load_saved_credentials() -> dict:
    """Load saved credentials from local file."""
    if _CREDENTIALS_PATH.exists():
        try:
            data = json.loads(_CREDENTIALS_PATH.read_text(encoding="utf-8"))
            return {
                "username": data.get("username", ""),
                "api_key": data.get("api_key", ""),
            }
        except (json.JSONDecodeError, OSError):
            pass
    return {"username": "", "api_key": ""}


def _save_credentials(username: str, api_key: str) -> None:
    """Save credentials to local file."""
    _CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CREDENTIALS_PATH.write_text(
        json.dumps({"username": username, "api_key": api_key}, indent=2),
        encoding="utf-8",
    )


def _clear_saved_credentials() -> None:
    """Delete saved credentials file."""
    if _CREDENTIALS_PATH.exists():
        _CREDENTIALS_PATH.unlink()

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

    /* Streamlit header – make transparent so it doesn't hide tab text */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
    }

    /* Push content below the fixed header */
    .block-container { padding-top: 3rem; padding-bottom: 1rem; }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px !important;
        border-bottom: 1px solid #2A2D3E !important;
        background-color: transparent !important;
    }
    .stTabs [data-baseweb="tab-list"] button[data-baseweb="tab"] {
        background-color: transparent !important;
        font-size: 14px !important;
        padding: 8px 16px !important;
    }
    .stTabs [data-baseweb="tab-list"] button[data-baseweb="tab"],
    .stTabs [data-baseweb="tab-list"] button[data-baseweb="tab"] div,
    .stTabs [data-baseweb="tab-list"] button[data-baseweb="tab"] p,
    .stTabs [data-baseweb="tab-list"] button[data-baseweb="tab"] span {
        color: #8A8D98 !important;
        -webkit-text-fill-color: #8A8D98 !important;
    }
    .stTabs [data-baseweb="tab-list"] button[data-baseweb="tab"][aria-selected="true"],
    .stTabs [data-baseweb="tab-list"] button[data-baseweb="tab"][aria-selected="true"] div,
    .stTabs [data-baseweb="tab-list"] button[data-baseweb="tab"][aria-selected="true"] p,
    .stTabs [data-baseweb="tab-list"] button[data-baseweb="tab"][aria-selected="true"] span {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }
    .stTabs [data-baseweb="tab-list"] button[data-baseweb="tab"][aria-selected="true"] {
        border-bottom: 2px solid #00C853 !important;
    }
    [data-baseweb="tab-highlight"] {
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
    if 'credentials' not in st.session_state:
        st.session_state.credentials = {"username": "", "api_key": ""}
    if 'collector' not in st.session_state:
        st.session_state.collector = None
    if 'accounts' not in st.session_state:
        st.session_state.accounts = []


def render_login_page():
    """Render login page for entering API credentials."""
    st.markdown("## TopstepX Analytics")
    st.markdown("TopstepX の認証情報を入力してください。")

    saved = _load_saved_credentials()

    with st.form("login_form"):
        username = st.text_input("Username", value=saved["username"])
        api_key = st.text_input("API Key", value=saved["api_key"], type="password")
        save_creds = st.checkbox("認証情報をローカルに保存する（次回から自動入力）", value=bool(saved["username"]))
        submitted = st.form_submit_button("ログイン & データ同期", type="primary")

    if submitted:
        if not username or not api_key:
            st.error("Username と API Key の両方を入力してください。")
            return False

        with st.spinner("認証中..."):
            try:
                collector = DataCollector(username=username, api_key=api_key)
                if collector.authenticate():
                    st.session_state.authenticated = True
                    st.session_state.credentials = {"username": username, "api_key": api_key}
                    st.session_state.collector = collector

                    if save_creds:
                        _save_credentials(username, api_key)
                    else:
                        _clear_saved_credentials()

                    # Sync accounts & trades on login
                    accounts = collector.sync_accounts()
                    live_accounts = [a for a in accounts if 'TOPX' in a.get('name', '').upper()]
                    for acc in live_accounts:
                        collector.sync_trades(acc['id'], acc.get('name', ''))
                    st.session_state.accounts = live_accounts

                    st.success(f"ログイン成功！ {len(live_accounts)} 件の LIVE アカウントを同期しました。")
                    st.rerun()
                else:
                    st.error("認証に失敗しました。Username と API Key を確認してください。")
            except Exception as e:
                st.error(f"認証エラー: {e}")
        return False

    # Auto-login if saved credentials exist and user hasn't interacted yet
    return False


def _render_fee_settings():
    """Render fee customization UI inside a sidebar expander."""
    fee_settings = get_all_fee_settings()

    st.caption("手数料を変更すると再同期時に反映されます。")

    for sym in sorted(fee_settings.keys()):
        info = fee_settings[sym]
        col_sym, col_fee, col_btn = st.columns([2, 3, 1])
        with col_sym:
            st.text(sym)
        with col_fee:
            new_val = st.number_input(
                f"fee_{sym}",
                value=info["active"],
                min_value=0.0,
                step=0.01,
                format="%.2f",
                key=f"fee_input_{sym}",
                label_visibility="collapsed",
            )
        with col_btn:
            if info["custom"] is not None:
                if st.button("↩", key=f"fee_reset_{sym}", help="デフォルトに戻す"):
                    remove_custom_fee(sym)
                    st.rerun()

        # Save if changed
        if abs(new_val - info["active"]) > 0.001:
            set_custom_fee(sym, round(new_val, 2))
            st.rerun()


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

    # Fee settings
    st.sidebar.markdown("---")
    with st.sidebar.expander("Fee Settings"):
        _render_fee_settings()

    # Logout button
    st.sidebar.markdown("---")
    if st.sidebar.button("Logout"):
        _clear_saved_credentials()
        st.session_state.authenticated = False
        st.session_state.credentials = {"username": "", "api_key": ""}
        st.session_state.collector = None
        st.rerun()

    return accounts


def sync_data():
    """Sync data from TopstepX API using session credentials"""
    creds = st.session_state.get("credentials", {})
    username = creds.get("username", "")
    api_key = creds.get("api_key", "")

    if not username or not api_key:
        st.sidebar.error("認証情報がありません。再ログインしてください。")
        return

    with st.spinner("Syncing data..."):
        try:
            collector = DataCollector(username=username, api_key=api_key)
            if collector.authenticate():
                accounts = collector.sync_accounts()
                live_accounts = [a for a in accounts if 'TOPX' in a.get('name', '').upper()]
                st.sidebar.success(f"Synced {len(live_accounts)} accounts")

                for acc in live_accounts:
                    count = collector.sync_trades(acc['id'], acc.get('name', ''))
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
    display_cols = ['entry_time', 'exit_time', 'symbol', 'side', 'quantity', 'entry_price', 'exit_price', 'pnl', 'fees', 'net_pnl', 'duration_seconds']
    st.dataframe(
        filtered[display_cols],
        use_container_width=True,
        hide_index=True
    )

    # Summary with net P/L
    total_fees = filtered['fees'].sum()
    net_pnl = filtered['net_pnl'].sum()
    st.markdown(f"**Total: {len(filtered)} trades | Gross P/L: \\${filtered['pnl'].sum():,.2f} | Fees: \\${total_fees:,.2f} | Net P/L: \\${net_pnl:,.2f}**")


# ═══════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════
def main():
    init_session_state()
    init_database()

    # Try auto-login with saved credentials
    if not st.session_state.authenticated:
        saved = _load_saved_credentials()
        if saved["username"] and saved["api_key"]:
            st.session_state.credentials = saved
            st.session_state.authenticated = True

    # Show login page if not authenticated
    if not st.session_state.authenticated:
        render_login_page()
        return

    accounts = render_sidebar()

    if not accounts:
        st.warning("アカウントが見つかりません。サイドバーの「Sync Data from API」でデータを同期してください。")
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
