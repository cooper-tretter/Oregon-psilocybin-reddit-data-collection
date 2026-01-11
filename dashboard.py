"""
RedditOregon Dashboard: Interactive visualization for psychedelic therapy data.
Built with Dash and Plotly.
"""

import os
from datetime import datetime

import dash
from dash import dcc, html, dash_table, callback, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from database import get_connection, init_database

# Initialize Dash app
app = dash.Dash(
    __name__,
    title='RedditOregon Dashboard',
    update_title='Loading...',
    suppress_callback_exceptions=True
)

server = app.server  # For gunicorn

# Color scheme
COLORS = {
    'primary': '#10b981',      # Emerald green
    'secondary': '#6366f1',    # Indigo
    'accent': '#8b5cf6',       # Purple
    'success': '#22c55e',      # Green
    'warning': '#f59e0b',      # Amber
    'danger': '#ef4444',       # Red
    'background': '#0f172a',   # Slate 900
    'card': '#1e293b',         # Slate 800
    'text': '#f8fafc',         # Slate 50
    'muted': '#94a3b8',        # Slate 400
}


def get_dataframe() -> pd.DataFrame:
    """Load posts from database into DataFrame."""
    try:
        conn = get_connection()
        df = pd.read_sql_query("""
            SELECT
                id, reddit_id, subreddit, author, title, content, content_length,
                is_comment, is_relevant, relevance_score, category,
                location, substance, treatment_setting, clinical_indication,
                outcome_sentiment, mentions_cost, mentions_facilitator,
                mentions_integration, mentions_preparation, is_legal_context,
                score, num_comments, created_utc, data_source
            FROM posts
            ORDER BY created_utc DESC
        """, conn)
        conn.close()

        if not df.empty and 'created_utc' in df.columns:
            df['created_utc'] = pd.to_datetime(df['created_utc'])
            df['month'] = df['created_utc'].dt.to_period('M').astype(str)

        return df
    except Exception as e:
        print(f"Database error: {e}")
        return pd.DataFrame()


def create_summary_cards(df: pd.DataFrame) -> html.Div:
    """Create summary statistic cards."""
    total = len(df)
    relevant = len(df[df['is_relevant'] == True]) if not df.empty else 0
    locations = df['location'].nunique() if not df.empty else 0
    substances = df['substance'].nunique() if not df.empty else 0

    cards = [
        {'title': 'Total Posts', 'value': f'{total:,}', 'color': COLORS['primary']},
        {'title': 'Relevant Posts', 'value': f'{relevant:,}', 'color': COLORS['success']},
        {'title': 'Locations', 'value': str(locations), 'color': COLORS['secondary']},
        {'title': 'Substances', 'value': str(substances), 'color': COLORS['accent']},
    ]

    return html.Div([
        html.Div([
            html.Div([
                html.H4(card['title'], style={'color': COLORS['muted'], 'fontSize': '14px', 'marginBottom': '8px'}),
                html.H2(card['value'], style={'color': card['color'], 'fontSize': '32px', 'margin': 0}),
            ], style={
                'backgroundColor': COLORS['card'],
                'padding': '20px',
                'borderRadius': '12px',
                'textAlign': 'center',
                'flex': '1',
                'minWidth': '150px',
            })
            for card in cards
        ], style={'display': 'flex', 'gap': '20px', 'flexWrap': 'wrap'})
    ])


def create_timeline_chart(df: pd.DataFrame) -> go.Figure:
    """Create timeline chart of posts over time."""
    if df.empty:
        return go.Figure()

    relevant_df = df[df['is_relevant'] == True]

    if relevant_df.empty or 'month' not in relevant_df.columns:
        return go.Figure()

    monthly = relevant_df.groupby('month').size().reset_index(name='count')

    fig = px.area(
        monthly,
        x='month',
        y='count',
        title='Relevant Posts Over Time',
        color_discrete_sequence=[COLORS['primary']]
    )

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color=COLORS['text'],
        title_font_size=18,
        xaxis_title='Month',
        yaxis_title='Posts',
        showlegend=False,
        margin=dict(l=40, r=40, t=60, b=40)
    )

    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor=COLORS['card'])
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor=COLORS['card'])

    return fig


def create_subreddit_chart(df: pd.DataFrame) -> go.Figure:
    """Create subreddit distribution chart."""
    if df.empty:
        return go.Figure()

    sub_counts = df.groupby('subreddit').agg(
        total=('id', 'count'),
        relevant=('is_relevant', 'sum')
    ).reset_index()
    sub_counts = sub_counts.sort_values('total', ascending=True).tail(15)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=sub_counts['subreddit'],
        x=sub_counts['total'],
        name='Total',
        orientation='h',
        marker_color=COLORS['muted']
    ))

    fig.add_trace(go.Bar(
        y=sub_counts['subreddit'],
        x=sub_counts['relevant'],
        name='Relevant',
        orientation='h',
        marker_color=COLORS['primary']
    ))

    fig.update_layout(
        title='Posts by Subreddit',
        barmode='overlay',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color=COLORS['text'],
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(l=120, r=40, t=80, b=40)
    )

    return fig


def create_location_chart(df: pd.DataFrame) -> go.Figure:
    """Create geographic distribution chart."""
    if df.empty:
        return go.Figure()

    relevant_df = df[df['is_relevant'] == True]
    loc_counts = relevant_df['location'].value_counts().head(10)

    if loc_counts.empty:
        return go.Figure()

    fig = px.pie(
        values=loc_counts.values,
        names=loc_counts.index,
        title='Geographic Distribution',
        color_discrete_sequence=px.colors.sequential.Emrld
    )

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color=COLORS['text'],
        margin=dict(l=40, r=40, t=60, b=40)
    )

    return fig


def create_substance_chart(df: pd.DataFrame) -> go.Figure:
    """Create substance distribution chart."""
    if df.empty:
        return go.Figure()

    relevant_df = df[df['is_relevant'] == True]
    sub_counts = relevant_df['substance'].value_counts().head(10)

    if sub_counts.empty:
        return go.Figure()

    fig = px.bar(
        x=sub_counts.index,
        y=sub_counts.values,
        title='Substances Mentioned',
        color=sub_counts.values,
        color_continuous_scale='Emrld'
    )

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color=COLORS['text'],
        showlegend=False,
        coloraxis_showscale=False,
        xaxis_title='Substance',
        yaxis_title='Posts',
        margin=dict(l=40, r=40, t=60, b=40)
    )

    return fig


def create_sentiment_chart(df: pd.DataFrame) -> go.Figure:
    """Create outcome sentiment distribution chart."""
    if df.empty:
        return go.Figure()

    relevant_df = df[df['is_relevant'] == True]
    sentiment_counts = relevant_df['outcome_sentiment'].value_counts()

    if sentiment_counts.empty:
        return go.Figure()

    colors = {
        'positive': COLORS['success'],
        'negative': COLORS['danger'],
        'mixed': COLORS['warning'],
        'neutral': COLORS['muted']
    }

    fig = px.pie(
        values=sentiment_counts.values,
        names=sentiment_counts.index,
        title='Outcome Sentiment',
        color=sentiment_counts.index,
        color_discrete_map=colors
    )

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color=COLORS['text'],
        margin=dict(l=40, r=40, t=60, b=40)
    )

    return fig


def create_indication_chart(df: pd.DataFrame) -> go.Figure:
    """Create clinical indication distribution chart."""
    if df.empty:
        return go.Figure()

    relevant_df = df[df['is_relevant'] == True]
    ind_counts = relevant_df['clinical_indication'].value_counts().head(8)

    if ind_counts.empty:
        return go.Figure()

    fig = px.bar(
        x=ind_counts.values,
        y=ind_counts.index,
        orientation='h',
        title='Clinical Indications',
        color=ind_counts.values,
        color_continuous_scale='Purp'
    )

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color=COLORS['text'],
        showlegend=False,
        coloraxis_showscale=False,
        xaxis_title='Posts',
        yaxis_title='',
        margin=dict(l=100, r=40, t=60, b=40)
    )

    return fig


def create_treatment_setting_chart(df: pd.DataFrame) -> go.Figure:
    """Create treatment setting distribution chart."""
    if df.empty:
        return go.Figure()

    relevant_df = df[df['is_relevant'] == True]
    setting_counts = relevant_df['treatment_setting'].value_counts()

    if setting_counts.empty:
        return go.Figure()

    fig = px.pie(
        values=setting_counts.values,
        names=setting_counts.index,
        title='Treatment Settings',
        color_discrete_sequence=px.colors.sequential.Purp
    )

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color=COLORS['text'],
        margin=dict(l=40, r=40, t=60, b=40)
    )

    return fig


def create_posts_table(df: pd.DataFrame) -> dash_table.DataTable:
    """Create posts data table."""
    if df.empty:
        return dash_table.DataTable()

    relevant_df = df[df['is_relevant'] == True].head(100)

    display_df = relevant_df[[
        'subreddit', 'title', 'location', 'substance',
        'treatment_setting', 'clinical_indication', 'outcome_sentiment',
        'relevance_score', 'created_utc'
    ]].copy()

    display_df['created_utc'] = display_df['created_utc'].dt.strftime('%Y-%m-%d')
    display_df['relevance_score'] = display_df['relevance_score'].round(2)

    return dash_table.DataTable(
        data=display_df.to_dict('records'),
        columns=[{'name': col, 'id': col} for col in display_df.columns],
        style_table={'overflowX': 'auto'},
        style_cell={
            'backgroundColor': COLORS['card'],
            'color': COLORS['text'],
            'textAlign': 'left',
            'padding': '10px',
            'whiteSpace': 'normal',
            'height': 'auto',
            'maxWidth': '300px',
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',
        },
        style_header={
            'backgroundColor': COLORS['background'],
            'fontWeight': 'bold',
            'borderBottom': f'2px solid {COLORS["primary"]}'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgba(30, 41, 59, 0.5)'
            }
        ],
        page_size=20,
        page_action='native',
        sort_action='native',
        filter_action='native',
    )


# App layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1('RedditOregon Dashboard', style={
            'color': COLORS['primary'],
            'marginBottom': '8px'
        }),
        html.P('Psychedelic Therapy Experience Data Analysis', style={
            'color': COLORS['muted'],
            'fontSize': '16px'
        }),
    ], style={
        'textAlign': 'center',
        'padding': '30px',
        'backgroundColor': COLORS['card'],
        'borderBottom': f'2px solid {COLORS["primary"]}',
        'marginBottom': '30px'
    }),

    # Main content
    html.Div([
        # Summary cards
        html.Div(id='summary-cards', style={'marginBottom': '30px'}),

        # Charts row 1
        html.Div([
            html.Div([
                dcc.Graph(id='timeline-chart', style={'height': '400px'})
            ], style={'flex': '2', 'minWidth': '400px'}),
            html.Div([
                dcc.Graph(id='location-chart', style={'height': '400px'})
            ], style={'flex': '1', 'minWidth': '300px'}),
        ], style={
            'display': 'flex',
            'gap': '20px',
            'marginBottom': '30px',
            'flexWrap': 'wrap'
        }),

        # Charts row 2
        html.Div([
            html.Div([
                dcc.Graph(id='subreddit-chart', style={'height': '500px'})
            ], style={'flex': '1', 'minWidth': '400px'}),
            html.Div([
                dcc.Graph(id='substance-chart', style={'height': '500px'})
            ], style={'flex': '1', 'minWidth': '400px'}),
        ], style={
            'display': 'flex',
            'gap': '20px',
            'marginBottom': '30px',
            'flexWrap': 'wrap'
        }),

        # Charts row 3
        html.Div([
            html.Div([
                dcc.Graph(id='sentiment-chart', style={'height': '400px'})
            ], style={'flex': '1', 'minWidth': '300px'}),
            html.Div([
                dcc.Graph(id='indication-chart', style={'height': '400px'})
            ], style={'flex': '1', 'minWidth': '300px'}),
            html.Div([
                dcc.Graph(id='setting-chart', style={'height': '400px'})
            ], style={'flex': '1', 'minWidth': '300px'}),
        ], style={
            'display': 'flex',
            'gap': '20px',
            'marginBottom': '30px',
            'flexWrap': 'wrap'
        }),

        # Posts table
        html.Div([
            html.H3('Relevant Posts', style={
                'color': COLORS['text'],
                'marginBottom': '20px'
            }),
            html.Div(id='posts-table')
        ], style={
            'backgroundColor': COLORS['card'],
            'padding': '20px',
            'borderRadius': '12px'
        }),

        # Footer
        html.Div([
            html.P([
                'RedditOregon Data Collection | ',
                f'Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M")}'
            ], style={'color': COLORS['muted'], 'textAlign': 'center'})
        ], style={'marginTop': '40px', 'paddingBottom': '40px'})

    ], style={
        'maxWidth': '1400px',
        'margin': '0 auto',
        'padding': '0 20px'
    }),

    # Store for data
    dcc.Store(id='data-store'),

    # Interval for refresh
    dcc.Interval(id='refresh-interval', interval=300000, n_intervals=0)  # 5 min

], style={
    'backgroundColor': COLORS['background'],
    'minHeight': '100vh',
    'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
})


@callback(
    Output('data-store', 'data'),
    Input('refresh-interval', 'n_intervals')
)
def load_data(n):
    """Load data from database."""
    df = get_dataframe()
    return df.to_json(date_format='iso', orient='split')


@callback(
    Output('summary-cards', 'children'),
    Input('data-store', 'data')
)
def update_summary(data):
    """Update summary cards."""
    if not data:
        return html.Div("No data available")
    df = pd.read_json(data, orient='split')
    return create_summary_cards(df)


@callback(
    Output('timeline-chart', 'figure'),
    Input('data-store', 'data')
)
def update_timeline(data):
    if not data:
        return go.Figure()
    df = pd.read_json(data, orient='split')
    if 'created_utc' in df.columns:
        df['created_utc'] = pd.to_datetime(df['created_utc'])
        df['month'] = df['created_utc'].dt.to_period('M').astype(str)
    return create_timeline_chart(df)


@callback(
    Output('subreddit-chart', 'figure'),
    Input('data-store', 'data')
)
def update_subreddit(data):
    if not data:
        return go.Figure()
    df = pd.read_json(data, orient='split')
    return create_subreddit_chart(df)


@callback(
    Output('location-chart', 'figure'),
    Input('data-store', 'data')
)
def update_location(data):
    if not data:
        return go.Figure()
    df = pd.read_json(data, orient='split')
    return create_location_chart(df)


@callback(
    Output('substance-chart', 'figure'),
    Input('data-store', 'data')
)
def update_substance(data):
    if not data:
        return go.Figure()
    df = pd.read_json(data, orient='split')
    return create_substance_chart(df)


@callback(
    Output('sentiment-chart', 'figure'),
    Input('data-store', 'data')
)
def update_sentiment(data):
    if not data:
        return go.Figure()
    df = pd.read_json(data, orient='split')
    return create_sentiment_chart(df)


@callback(
    Output('indication-chart', 'figure'),
    Input('data-store', 'data')
)
def update_indication(data):
    if not data:
        return go.Figure()
    df = pd.read_json(data, orient='split')
    return create_indication_chart(df)


@callback(
    Output('setting-chart', 'figure'),
    Input('data-store', 'data')
)
def update_setting(data):
    if not data:
        return go.Figure()
    df = pd.read_json(data, orient='split')
    return create_treatment_setting_chart(df)


@callback(
    Output('posts-table', 'children'),
    Input('data-store', 'data')
)
def update_table(data):
    if not data:
        return html.Div("No data available")
    df = pd.read_json(data, orient='split')
    if 'created_utc' in df.columns:
        df['created_utc'] = pd.to_datetime(df['created_utc'])
    return create_posts_table(df)


def init_app():
    """Initialize the application."""
    try:
        init_database()
        print("Database initialized")
    except Exception as e:
        print(f"Database init warning: {e}")


if __name__ == '__main__':
    init_app()

    port = int(os.getenv('DASH_PORT', 8051))
    debug = os.getenv('DASH_DEBUG', 'False').lower() == 'true'

    print(f"\nStarting RedditOregon Dashboard on http://127.0.0.1:{port}")
    app.run(debug=debug, port=port)
