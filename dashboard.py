"""
RedditOregon Dashboard: Interactive visualization for psychedelic therapy data.
Built with Dash and Plotly with full drilldown support.
"""

import os
import re
from datetime import datetime

import dash
from dash import dcc, html, dash_table, callback, Input, Output, State, no_update
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from database import get_connection, init_database
from detector import (
    RELEVANCE_KEYWORDS, LOCATIONS, SUBSTANCES,
    TREATMENT_SETTINGS, CLINICAL_INDICATIONS
)

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
    'highlight': '#fef08a',    # Yellow highlight
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


def get_highlight_keywords(filter_type: str, filter_value: str) -> list[str]:
    """Get keywords to highlight based on the filter type and value."""
    keywords = []

    if filter_type == 'subreddit':
        # For subreddits, highlight all relevance keywords found
        for category, data in RELEVANCE_KEYWORDS.items():
            keywords.extend(data['terms'])

    elif filter_type == 'location':
        if filter_value in LOCATIONS:
            keywords.extend(LOCATIONS[filter_value])
        # Also add general location terms
        keywords.extend(['oregon', 'colorado', 'portland', 'denver', 'legal', 'licensed'])

    elif filter_type == 'substance':
        if filter_value in SUBSTANCES:
            keywords.extend(SUBSTANCES[filter_value])

    elif filter_type == 'treatment_setting':
        if filter_value in TREATMENT_SETTINGS:
            keywords.extend(TREATMENT_SETTINGS[filter_value])

    elif filter_type == 'clinical_indication':
        if filter_value in CLINICAL_INDICATIONS:
            keywords.extend(CLINICAL_INDICATIONS[filter_value])

    elif filter_type == 'outcome_sentiment':
        if filter_value == 'positive':
            keywords.extend(['helped', 'healing', 'healed', 'better', 'improved',
                           'life-changing', 'transformative', 'breakthrough', 'grateful',
                           'amazing', 'wonderful', 'incredible', 'recommend', 'worth it'])
        elif filter_value == 'negative':
            keywords.extend(['worse', 'bad experience', 'traumatic', 'scary',
                           'horrible', 'awful', 'regret', 'warning', 'scam'])
        elif filter_value == 'mixed':
            keywords.extend(['but', 'however', 'although', 'mixed', 'both'])

    elif filter_type == 'month':
        # For timeline, highlight therapy-related terms
        for category, data in RELEVANCE_KEYWORDS.items():
            keywords.extend(data['terms'][:5])  # Just top 5 from each

    return list(set(keywords))  # Remove duplicates


def highlight_text(text: str, keywords: list[str]) -> list:
    """Highlight keywords in text, returning Dash components."""
    if not text or not keywords:
        return [text] if text else []

    # Sort keywords by length (longest first) to avoid partial matches
    keywords = sorted(set(keywords), key=len, reverse=True)

    # Create pattern for all keywords (case insensitive)
    pattern = '|'.join(re.escape(kw) for kw in keywords if kw)
    if not pattern:
        return [text]

    parts = []
    last_end = 0

    for match in re.finditer(pattern, text, re.IGNORECASE):
        # Add text before match
        if match.start() > last_end:
            parts.append(text[last_end:match.start()])

        # Add highlighted match
        parts.append(html.Mark(
            match.group(),
            style={
                'backgroundColor': COLORS['highlight'],
                'color': '#1e293b',
                'padding': '2px 4px',
                'borderRadius': '3px',
                'fontWeight': 'bold'
            }
        ))
        last_end = match.end()

    # Add remaining text
    if last_end < len(text):
        parts.append(text[last_end:])

    return parts if parts else [text]


def create_post_card(row: pd.Series, keywords: list[str], index: int = 0) -> html.Div:
    """Create a card displaying a single post with highlighted keywords and expandable content."""
    title_parts = highlight_text(row.get('title', 'No title'), keywords)
    full_content = row.get('content', '') or ''

    # Preview (first 400 chars) and full content
    preview_length = 400
    is_long = len(full_content) > preview_length
    preview_content = full_content[:preview_length] + ('...' if is_long else '')

    preview_parts = highlight_text(preview_content, keywords)
    full_parts = highlight_text(full_content, keywords) if is_long else preview_parts

    reddit_url = f"https://reddit.com/r/{row.get('subreddit', '')}/comments/{row.get('reddit_id', '')}"

    # Build metadata badges
    badges = []
    if row.get('location'):
        badges.append(html.Span(f"📍 {row['location']}", style={
            'backgroundColor': COLORS['secondary'],
            'padding': '4px 8px',
            'borderRadius': '12px',
            'marginRight': '8px',
            'fontSize': '12px'
        }))
    if row.get('substance'):
        badges.append(html.Span(f"💊 {row['substance']}", style={
            'backgroundColor': COLORS['accent'],
            'padding': '4px 8px',
            'borderRadius': '12px',
            'marginRight': '8px',
            'fontSize': '12px'
        }))
    if row.get('treatment_setting'):
        badges.append(html.Span(f"🏥 {row['treatment_setting']}", style={
            'backgroundColor': COLORS['primary'],
            'padding': '4px 8px',
            'borderRadius': '12px',
            'marginRight': '8px',
            'fontSize': '12px'
        }))
    if row.get('outcome_sentiment'):
        sentiment_colors = {
            'positive': COLORS['success'],
            'negative': COLORS['danger'],
            'mixed': COLORS['warning'],
            'neutral': COLORS['muted']
        }
        badges.append(html.Span(f"💬 {row['outcome_sentiment']}", style={
            'backgroundColor': sentiment_colors.get(row['outcome_sentiment'], COLORS['muted']),
            'padding': '4px 8px',
            'borderRadius': '12px',
            'marginRight': '8px',
            'fontSize': '12px'
        }))

    return html.Div([
        # Header
        html.Div([
            html.Span(f"r/{row.get('subreddit', 'unknown')}", style={
                'color': COLORS['primary'],
                'fontWeight': 'bold',
                'marginRight': '12px'
            }),
            html.Span(f"u/{row.get('author', 'unknown')}", style={
                'color': COLORS['muted'],
                'marginRight': '12px'
            }),
            html.Span(
                pd.to_datetime(row.get('created_utc')).strftime('%Y-%m-%d') if pd.notna(row.get('created_utc')) else '',
                style={'color': COLORS['muted']}
            ),
            html.A('View on Reddit →', href=reddit_url, target='_blank', style={
                'color': COLORS['secondary'],
                'marginLeft': 'auto',
                'textDecoration': 'none'
            })
        ], style={
            'display': 'flex',
            'alignItems': 'center',
            'marginBottom': '8px',
            'flexWrap': 'wrap',
            'gap': '8px'
        }),

        # Title
        html.H4(title_parts, style={
            'color': COLORS['text'],
            'marginBottom': '12px',
            'fontSize': '16px',
            'lineHeight': '1.4'
        }),

        # Badges
        html.Div(badges, style={'marginBottom': '12px'}) if badges else None,

        # Content - expandable if long
        html.Details([
            html.Summary(
                f"{'📖 Click to expand full post' if is_long else '📄 Full post'}",
                style={
                    'color': COLORS['primary'],
                    'cursor': 'pointer',
                    'marginBottom': '12px',
                    'fontSize': '13px',
                    'fontWeight': 'bold'
                }
            ),
            html.Div(full_parts, style={
                'color': COLORS['text'],
                'lineHeight': '1.7',
                'fontSize': '14px',
                'whiteSpace': 'pre-wrap',
                'padding': '12px',
                'backgroundColor': 'rgba(255,255,255,0.05)',
                'borderRadius': '8px',
                'maxHeight': '600px',
                'overflowY': 'auto'
            })
        ], style={'marginBottom': '12px'}) if is_long else html.P(preview_parts, style={
            'color': COLORS['muted'],
            'lineHeight': '1.6',
            'fontSize': '14px',
            'whiteSpace': 'pre-wrap'
        }),

        # Preview for long posts (shown when collapsed)
        html.P(preview_parts, style={
            'color': COLORS['muted'],
            'lineHeight': '1.6',
            'fontSize': '14px',
            'whiteSpace': 'pre-wrap'
        }) if is_long else None,

        # Relevance score
        html.Div([
            html.Span(f"Relevance: {row.get('relevance_score', 0):.2f}", style={
                'color': COLORS['primary'],
                'fontSize': '12px'
            })
        ], style={'marginTop': '8px'})

    ], style={
        'backgroundColor': COLORS['card'],
        'padding': '20px',
        'borderRadius': '12px',
        'marginBottom': '16px',
        'borderLeft': f"4px solid {COLORS['primary']}"
    })


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

    fig = px.bar(
        monthly,
        x='month',
        y='count',
        title='Relevant Posts Over Time (click bar to drill down)',
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
        margin=dict(l=40, r=40, t=60, b=40),
        clickmode='event+select'
    )

    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor=COLORS['card'])
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor=COLORS['card'])
    fig.update_traces(hovertemplate='%{x}<br>Posts: %{y}<extra></extra>')

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
        title='Posts by Subreddit (click bar to drill down)',
        barmode='overlay',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color=COLORS['text'],
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(l=120, r=40, t=80, b=40),
        clickmode='event+select'
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
        title='Geographic Distribution (click slice to drill down)',
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
        title='Substances Mentioned (click bar to drill down)',
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
        margin=dict(l=40, r=40, t=60, b=40),
        clickmode='event+select'
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
        title='Outcome Sentiment (click slice to drill down)',
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
        title='Clinical Indications (click bar to drill down)',
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
        margin=dict(l=100, r=40, t=60, b=40),
        clickmode='event+select'
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
        title='Treatment Settings (click slice to drill down)',
        color_discrete_sequence=px.colors.sequential.Purp
    )

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color=COLORS['text'],
        margin=dict(l=40, r=40, t=60, b=40)
    )

    return fig


def create_drilldown_panel() -> html.Div:
    """Create the drilldown panel component."""
    return html.Div([
        # Header with close button
        html.Div([
            html.H3(id='drilldown-title', style={
                'color': COLORS['text'],
                'margin': 0
            }),
            html.Button('✕ Close', id='close-drilldown', style={
                'backgroundColor': 'transparent',
                'border': f'1px solid {COLORS["muted"]}',
                'color': COLORS['text'],
                'padding': '8px 16px',
                'borderRadius': '8px',
                'cursor': 'pointer'
            })
        ], style={
            'display': 'flex',
            'justifyContent': 'space-between',
            'alignItems': 'center',
            'marginBottom': '20px',
            'paddingBottom': '16px',
            'borderBottom': f'1px solid {COLORS["card"]}'
        }),

        # Filter info
        html.Div(id='drilldown-filter-info', style={
            'backgroundColor': COLORS['card'],
            'padding': '12px 16px',
            'borderRadius': '8px',
            'marginBottom': '20px',
            'color': COLORS['muted']
        }),

        # Posts container
        html.Div(id='drilldown-posts', style={
            'maxHeight': '70vh',
            'overflowY': 'auto'
        })

    ], id='drilldown-panel', style={
        'display': 'none',
        'position': 'fixed',
        'top': '0',
        'right': '0',
        'width': '50%',
        'height': '100vh',
        'backgroundColor': COLORS['background'],
        'padding': '24px',
        'boxShadow': f'-4px 0 24px rgba(0,0,0,0.5)',
        'zIndex': '1000',
        'overflowY': 'auto'
    })


# App layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1('RedditOregon Dashboard', style={
            'color': COLORS['primary'],
            'marginBottom': '8px'
        }),
        html.P('Psychedelic Therapy Experience Data Analysis - Click any chart element to drill down', style={
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

    # Drilldown panel
    create_drilldown_panel(),

    # Store for data
    dcc.Store(id='data-store'),

    # Store for current drilldown state
    dcc.Store(id='drilldown-state', data={'visible': False, 'type': None, 'value': None}),

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


# Drilldown callbacks
@callback(
    Output('drilldown-state', 'data'),
    [Input('subreddit-chart', 'clickData'),
     Input('location-chart', 'clickData'),
     Input('substance-chart', 'clickData'),
     Input('sentiment-chart', 'clickData'),
     Input('indication-chart', 'clickData'),
     Input('setting-chart', 'clickData'),
     Input('timeline-chart', 'clickData'),
     Input('close-drilldown', 'n_clicks')],
    State('drilldown-state', 'data'),
    prevent_initial_call=True
)
def handle_chart_clicks(sub_click, loc_click, substance_click, sentiment_click,
                        indication_click, setting_click, timeline_click, close_click,
                        current_state):
    """Handle clicks on any chart and update drilldown state."""
    ctx = dash.callback_context

    if not ctx.triggered:
        return no_update

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Handle close button
    if trigger_id == 'close-drilldown':
        return {'visible': False, 'type': None, 'value': None}

    # Map chart IDs to their filter types and how to extract the value
    click_data = ctx.triggered[0]['value']

    if not click_data or 'points' not in click_data or not click_data['points']:
        return no_update

    point = click_data['points'][0]

    if trigger_id == 'subreddit-chart':
        value = point.get('y', point.get('label'))
        return {'visible': True, 'type': 'subreddit', 'value': value}

    elif trigger_id == 'location-chart':
        value = point.get('label', point.get('customdata'))
        return {'visible': True, 'type': 'location', 'value': value}

    elif trigger_id == 'substance-chart':
        value = point.get('x', point.get('label'))
        return {'visible': True, 'type': 'substance', 'value': value}

    elif trigger_id == 'sentiment-chart':
        value = point.get('label', point.get('customdata'))
        return {'visible': True, 'type': 'outcome_sentiment', 'value': value}

    elif trigger_id == 'indication-chart':
        value = point.get('y', point.get('label'))
        return {'visible': True, 'type': 'clinical_indication', 'value': value}

    elif trigger_id == 'setting-chart':
        value = point.get('label', point.get('customdata'))
        return {'visible': True, 'type': 'treatment_setting', 'value': value}

    elif trigger_id == 'timeline-chart':
        value = point.get('x', point.get('label'))
        return {'visible': True, 'type': 'month', 'value': value}

    return no_update


@callback(
    [Output('drilldown-panel', 'style'),
     Output('drilldown-title', 'children'),
     Output('drilldown-filter-info', 'children'),
     Output('drilldown-posts', 'children')],
    [Input('drilldown-state', 'data')],
    State('data-store', 'data'),
    prevent_initial_call=True
)
def update_drilldown_panel(state, data):
    """Update the drilldown panel based on state."""
    base_style = {
        'position': 'fixed',
        'top': '0',
        'right': '0',
        'width': '50%',
        'height': '100vh',
        'backgroundColor': COLORS['background'],
        'padding': '24px',
        'boxShadow': f'-4px 0 24px rgba(0,0,0,0.5)',
        'zIndex': '1000',
        'overflowY': 'auto'
    }

    if not state or not state.get('visible'):
        return {**base_style, 'display': 'none'}, '', '', []

    if not data:
        return {**base_style, 'display': 'block'}, 'No data', '', []

    df = pd.read_json(data, orient='split')
    if 'created_utc' in df.columns:
        df['created_utc'] = pd.to_datetime(df['created_utc'])
        df['month'] = df['created_utc'].dt.to_period('M').astype(str)

    filter_type = state.get('type')
    filter_value = state.get('value')

    # Filter dataframe
    if filter_type == 'month' and filter_value:
        # Handle different month formats from chart clicks
        # Try exact match first, then partial match
        filtered_df = df[df['month'] == filter_value]
        if filtered_df.empty:
            # Try matching just the year-month part
            filtered_df = df[df['month'].str.contains(str(filter_value)[:7], na=False)]
    elif filter_type and filter_value:
        filtered_df = df[df[filter_type] == filter_value]
    else:
        filtered_df = df

    # Only show relevant posts
    filtered_df = filtered_df[filtered_df['is_relevant'] == True]

    # Sort by relevance score
    filtered_df = filtered_df.sort_values('relevance_score', ascending=False).head(50)

    # Get keywords to highlight
    keywords = get_highlight_keywords(filter_type, filter_value)

    # Create title
    fv = filter_value or 'Unknown'
    title_map = {
        'subreddit': f'Posts from r/{fv}',
        'location': f'Posts mentioning {fv}',
        'substance': f'Posts about {fv}',
        'outcome_sentiment': f'{fv.title() if fv else "Unknown"} sentiment posts',
        'clinical_indication': f'Posts about {fv}',
        'treatment_setting': f'Posts about {fv} settings',
        'month': f'Posts from {fv}'
    }
    title = title_map.get(filter_type, 'Posts')

    # Create filter info
    filter_info = f"Showing {len(filtered_df)} relevant posts. Highlighted keywords: {', '.join(keywords[:10])}{'...' if len(keywords) > 10 else ''}"

    # Create post cards
    post_cards = [create_post_card(row, keywords) for _, row in filtered_df.iterrows()]

    if not post_cards:
        post_cards = [html.Div("No matching posts found", style={'color': COLORS['muted'], 'padding': '20px'})]

    return {**base_style, 'display': 'block'}, title, filter_info, post_cards


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
