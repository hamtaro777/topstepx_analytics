"""
Chart Components - TopStepX Style
"""
import plotly.graph_objects as go
import pandas as pd
from typing import Dict

# ── Shared theme constants ────────────────────────────────────
CARD_BG = "#1A1D2E"
PAGE_BG = "#0D1117"
GRID_COLOR = "#1E2235"
LABEL_COLOR = "#8A8D98"
GREEN = "#00C853"
RED = "#FF5252"
BLUE = "#5B8DEF"

_COMMON_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor=CARD_BG,
    plot_bgcolor=CARD_BG,
    font=dict(color=LABEL_COLOR, size=11),
    title_font=dict(color="#FFFFFF", size=13),
    margin=dict(l=50, r=20, t=40, b=40),
    xaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
    yaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
    height=380,
)


def _apply_layout(fig: go.Figure, **overrides) -> go.Figure:
    layout = {**_COMMON_LAYOUT, **overrides}
    fig.update_layout(**layout)
    return fig


# ═══════════════════════════════════════════════════════════════
#  Daily Account Balance / Cumulative P&L
# ═══════════════════════════════════════════════════════════════
def create_equity_curve(daily_stats: pd.DataFrame) -> go.Figure:
    """Create daily account equity curve with red/green fill."""
    fig = go.Figure()

    if daily_stats.empty or 'cumulative_pnl' not in daily_stats.columns:
        if not daily_stats.empty and 'total_pnl' in daily_stats.columns:
            daily_stats = daily_stats.copy()
            daily_stats['cumulative_pnl'] = daily_stats['total_pnl'].cumsum()
        else:
            return _apply_layout(fig, title="Daily Net Cumulative P&L")

    cum_pnl = daily_stats['cumulative_pnl']
    is_positive = cum_pnl.iloc[-1] >= 0 if len(cum_pnl) > 0 else True
    line_color = GREEN if is_positive else RED
    fill_color = "rgba(0,200,83,0.15)" if is_positive else "rgba(255,82,82,0.15)"

    fig.add_trace(go.Scatter(
        x=daily_stats['date'],
        y=cum_pnl,
        mode='lines+markers',
        fill='tozeroy',
        line=dict(color=line_color, width=2),
        marker=dict(color=line_color, size=5),
        fillcolor=fill_color,
        name='Cumulative P/L',
    ))

    return _apply_layout(fig,
        title="Daily Net Cumulative P&L",
        xaxis_title="Date",
        yaxis_title="Profit",
    )


# ═══════════════════════════════════════════════════════════════
#  Net Daily P&L Bar
# ═══════════════════════════════════════════════════════════════
def create_daily_pnl_bar(daily_stats: pd.DataFrame) -> go.Figure:
    """Create daily P/L bar chart."""
    fig = go.Figure()

    if daily_stats.empty:
        return _apply_layout(fig, title="Net Daily P&L")

    colors = [GREEN if x >= 0 else RED for x in daily_stats['total_pnl']]

    fig.add_trace(go.Bar(
        x=daily_stats['date'],
        y=daily_stats['total_pnl'],
        marker_color=colors,
        name='Daily P/L',
    ))

    return _apply_layout(fig,
        title="Net Daily P&L",
        xaxis_title="Date",
        yaxis_title="Profit",
    )


# ═══════════════════════════════════════════════════════════════
#  Trade Duration Analysis (horizontal bar)
# ═══════════════════════════════════════════════════════════════
def create_duration_chart(duration_data: Dict) -> go.Figure:
    """Create trade duration analysis horizontal bar chart."""
    fig = go.Figure()

    if not duration_data:
        return _apply_layout(fig, title="Trade Duration Analysis")

    labels = list(duration_data.keys())
    counts = [d['count'] for d in duration_data.values()]

    fig.add_trace(go.Bar(
        y=labels,
        x=counts,
        orientation='h',
        marker_color=LABEL_COLOR,
        text=counts,
        textposition='outside',
        textfont=dict(color=LABEL_COLOR, size=10),
    ))

    return _apply_layout(fig,
        title="Trade Duration Analysis",
        xaxis_title="",
        yaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR, autorange="reversed"),
        height=420,
    )


# ═══════════════════════════════════════════════════════════════
#  Win Rate by Duration (horizontal bar, green/red)
# ═══════════════════════════════════════════════════════════════
def create_win_rate_by_duration(duration_data: Dict) -> go.Figure:
    """Create win rate by duration horizontal bar chart."""
    fig = go.Figure()

    if not duration_data:
        return _apply_layout(fig, title="Win Rate Analysis")

    labels = list(duration_data.keys())
    win_rates = [d['win_rate'] for d in duration_data.values()]
    colors = [GREEN if wr >= 50 else RED for wr in win_rates]

    fig.add_trace(go.Bar(
        y=labels,
        x=win_rates,
        orientation='h',
        marker_color=colors,
        text=[f"{wr:.0f}%" for wr in win_rates],
        textposition='outside',
        textfont=dict(color=LABEL_COLOR, size=10),
    ))

    return _apply_layout(fig,
        title="Win Rate Analysis",
        xaxis=dict(range=[0, 100], gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR,
                   dtick=10, ticksuffix="%"),
        yaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR, autorange="reversed"),
        height=420,
    )
