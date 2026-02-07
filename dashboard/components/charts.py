"""
Chart Components
"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, List


def create_equity_curve(daily_stats: pd.DataFrame) -> go.Figure:
    """Create daily account equity curve"""
    fig = go.Figure()
    
    if daily_stats.empty or 'cumulative_pnl' not in daily_stats.columns:
        # Calculate cumulative P/L if not present
        if not daily_stats.empty and 'total_pnl' in daily_stats.columns:
            daily_stats = daily_stats.copy()
            daily_stats['cumulative_pnl'] = daily_stats['total_pnl'].cumsum()
        else:
            return fig
    
    fig.add_trace(go.Scatter(
        x=daily_stats['date'],
        y=daily_stats['cumulative_pnl'],
        mode='lines',
        fill='tozeroy',
        line=dict(color='#00C853', width=2),
        fillcolor='rgba(0, 200, 83, 0.1)',
        name='Cumulative P/L'
    ))
    
    fig.update_layout(
        title='Daily Net Cumulative P/L',
        template='plotly_dark',
        paper_bgcolor='#0D0D0D',
        plot_bgcolor='#0D0D0D',
        xaxis_title='Date',
        yaxis_title='P/L ($)',
        height=400
    )
    
    return fig


def create_daily_pnl_bar(daily_stats: pd.DataFrame) -> go.Figure:
    """Create daily P/L bar chart"""
    fig = go.Figure()
    
    if daily_stats.empty:
        return fig
    
    colors = ['#00C853' if x >= 0 else '#FF5252' for x in daily_stats['total_pnl']]
    
    fig.add_trace(go.Bar(
        x=daily_stats['date'],
        y=daily_stats['total_pnl'],
        marker_color=colors,
        name='Daily P/L'
    ))
    
    fig.update_layout(
        title='Net Daily P/L',
        template='plotly_dark',
        paper_bgcolor='#0D0D0D',
        plot_bgcolor='#0D0D0D',
        xaxis_title='Date',
        yaxis_title='P/L ($)',
        height=400
    )
    
    return fig


def create_direction_pie(long_pct: float, short_pct: float) -> go.Figure:
    """Create trade direction pie chart"""
    fig = go.Figure(data=[go.Pie(
        labels=['Long', 'Short'],
        values=[long_pct, short_pct],
        hole=0.6,
        marker_colors=['#00C853', '#FF5252']
    )])
    
    fig.update_layout(
        title='Trade Direction %',
        template='plotly_dark',
        paper_bgcolor='#0D0D0D',
        height=300,
        showlegend=True
    )
    
    return fig


def create_duration_chart(duration_data: Dict) -> go.Figure:
    """Create trade duration analysis chart"""
    if not duration_data:
        return go.Figure()
    
    labels = list(duration_data.keys())
    counts = [d['count'] for d in duration_data.values()]
    
    fig = go.Figure(data=[go.Bar(
        y=labels,
        x=counts,
        orientation='h',
        marker_color='#2196F3'
    )])
    
    fig.update_layout(
        title='Trade Duration Analysis',
        template='plotly_dark',
        paper_bgcolor='#0D0D0D',
        plot_bgcolor='#0D0D0D',
        xaxis_title='Number of Trades',
        height=400
    )
    
    return fig


def create_win_rate_by_duration(duration_data: Dict) -> go.Figure:
    """Create win rate by duration chart"""
    if not duration_data:
        return go.Figure()
    
    labels = list(duration_data.keys())
    win_rates = [d['win_rate'] for d in duration_data.values()]
    
    colors = ['#00C853' if wr >= 50 else '#FF5252' for wr in win_rates]
    
    fig = go.Figure(data=[go.Bar(
        y=labels,
        x=win_rates,
        orientation='h',
        marker_color=colors
    )])
    
    fig.update_layout(
        title='Win Rate Analysis by Duration',
        template='plotly_dark',
        paper_bgcolor='#0D0D0D',
        plot_bgcolor='#0D0D0D',
        xaxis_title='Win Rate (%)',
        xaxis=dict(range=[0, 100]),
        height=400
    )
    
    return fig