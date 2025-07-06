import time
import dash
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table, no_update
import plotly.express as px
from redis import Redis
import os
from dotenv import load_dotenv
import pandas as pd
from urllib.parse import urlparse
from datetime import datetime
import asyncio
import nest_asyncio
from pathlib import Path
import json


# Assuming these are in the same directory or a known module
try:
    from .get_custom_data import get_data, top_news
    from .scheduler import main
except ImportError:
    raise ImportError(
        "Cannot import get_custom_data or scheduler. Ensure they are in the correct module path.")

# --- 1. Setup Environment and Redis ---
BASE_DIR = Path(__file__).resolve().parent.parent
dotenv_path = BASE_DIR / 'app' / '.env'

# Load environment variables
load_dotenv(dotenv_path)

# Get environment variables with error handling
REDIS_URL = os.getenv("REDIS_URL")
NEWS_API = os.getenv("NEWS_API_KEY")

if not REDIS_URL or not NEWS_API:
    raise ValueError("Missing REDIS_URL or NEWS_API_KEY in .env file")

NEWS_URL = f"https://newsdata.io/api/1/latest?apikey={NEWS_API}&language=en&q=pizza"

# Initialize Redis client with error handling
try:
    client = Redis.from_url(REDIS_URL, decode_responses=True)
except Exception as e:
    raise ConnectionError(f"Failed to connect to Redis: {str(e)}")

# --- 2. Prepare Dummy Data ---
time_options = [
    {'label': 'Month', 'value': 'monthly'},
    {'label': 'Week', 'value': 'weekly'}
]

category_options = [
    {'label': 'None', 'value': 'summary'},
    {'label': 'Business', 'value': 'business'},
    {'label': 'World', 'value': 'world'},
    {'label': 'Sports', 'value': 'sports'},
    {'label': 'Sci/Tech', 'value': 'sci_tech'}
]

country_options = [
    {'label': 'United States', 'value': 'United States'},
    {'label': 'Canada', 'value': 'Canada'},
    {'label': 'United Kingdom', 'value': 'United Kingdom'},
    {'label': 'Germany', 'value': 'Germany'},
    {'label': 'Australia', 'value': 'Australia'},
    {'label': 'India', 'value': 'India'},
    {'label': 'France', 'value': 'France_en'},
    {'label': 'Japan', 'value': 'Japan_en'},
    {'label': 'Brazil', 'value': 'Brazil_en'},
    {'label': 'China', 'value': 'China_en'},
    {'label': 'Nigeria', 'value': 'Nigeria'},
    {'label': 'Netherlands (English)', 'value': 'Netherlands_en'},
    {'label': 'Netherlands (Dutch)', 'value': 'Netherlands_nl'},
    {'label': 'Zambia', 'value': 'Zambia'},
]

COUNTRY_CODES = {
    'United States': {'gl': 'US', 'hl': 'en', 'ceid': 'US:en'},
    'Canada': {'gl': 'CA', 'hl': 'en', 'ceid': 'CA:en'},
    'United Kingdom': {'gl': 'GB', 'hl': 'en', 'ceid': 'GB:en'},
    'Germany': {'gl': 'DE', 'hl': 'en', 'ceid': 'DE:en'},
    'Australia': {'gl': 'AU', 'hl': 'en', 'ceid': 'AU:en'},
    'India': {'gl': 'IN', 'hl': 'en', 'ceid': 'IN:en'},
    'France_en': {'gl': 'FR', 'hl': 'en', 'ceid': 'FR:en'},
    'Japan_en': {'gl': 'JP', 'hl': 'en', 'ceid': 'JP:en'},
    'Brazil_en': {'gl': 'BR', 'hl': 'en', 'ceid': 'BR:en'},
    'China_en': {'gl': 'CN', 'hl': 'en', 'ceid': 'CN:en'},
    'Nigeria': {'gl': 'NG', 'hl': 'en', 'ceid': 'NG:en'},
    'Netherlands_en': {'gl': 'NL', 'hl': 'en', 'ceid': 'NL:en'},
    'Netherlands_nl': {'gl': 'NL', 'hl': 'nl', 'ceid': 'NL:nl'},
    'Zambia': {'gl': 'ZM', 'hl': 'en', 'ceid': 'ZM:en'},
}

# Fetch initial data with error handling
try:
    data = client.get("monthly_summary")
    if data:
        data = json.loads(data)
    else:
        data = {
            "line_graph": {
                '2025-06-21 00:00:00': 0.32576,
                '2025-06-23 00:00:00': 0.02052,
                '2025-06-29 00:00:00': 0.07594,
                '2025-06-30 00:00:00': -0.04024
            },
            "pie_chart": {'good': 26, 'okay': 46, 'bad': 18},
            "top_sources": [
                {'source': 'si', 'article_count': 5, 'avg_sentiment': 0.0},
                {'source': 'menafn', 'article_count': 5, 'avg_sentiment': 0.0945},
                {'source': 'economictimes_indiatimes',
                    'article_count': 4, 'avg_sentiment': -0.1383},
                {'source': 'google', 'article_count': 3, 'avg_sentiment': -0.0918},
                {'source': 'yahoo', 'article_count': 2, 'avg_sentiment': 0.3298},
                {'source': 'timesnownews', 'article_count': 2,
                    'avg_sentiment': 0.2014},
                {'source': 'ibtimes', 'article_count': 2, 'avg_sentiment': 0.0174},
                {'source': 'devdiscourse', 'article_count': 2,
                    'avg_sentiment': -0.2796},
                {'source': '9news_au', 'article_count': 2, 'avg_sentiment': 0.8223},
                {'source': 'unionleader', 'article_count': 2, 'avg_sentiment': 0.0}
            ]
        }
except Exception as e:
    print(f"Error loading Redis data: {str(e)}")
    data = {
        "line_graph": {
            '2025-06-21 00:00:00': 0.32576,
            '2025-06-23 00:00:00': 0.02052,
            '2025-06-29 00:00:00': 0.07594,
            '2025-06-30 00:00:00': -0.04024
        },
        "pie_chart": {'good': 26, 'okay': 46, 'bad': 18},
        "top_sources": [
            {'source': 'si', 'article_count': 5, 'avg_sentiment': 0.0},
            {'source': 'menafn', 'article_count': 5, 'avg_sentiment': 0.0945},
            {'source': 'economictimes_indiatimes',
                'article_count': 4, 'avg_sentiment': -0.1383},
            {'source': 'google', 'article_count': 3, 'avg_sentiment': -0.0918},
            {'source': 'yahoo', 'article_count': 2, 'avg_sentiment': 0.3298},
        ]
    }

# --- 3. Prepare Data for Visualizations ---
# Line Graph
line_graph = data['line_graph']
timestamps = [datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
              for ts_str in line_graph.keys()]
sentiments = list(line_graph.values())
df_line = pd.DataFrame({
    "Timestamp": timestamps,
    "Sentiment Score": sentiments
}).sort_values(by="Timestamp")
fig_line = px.line(df_line, x="Timestamp", y="Sentiment Score", title="Overall Sentiment Trend",
                   markers=True, line_shape="linear")
fig_line.update_layout(hovermode="x unified",
                       template="plotly_white", xaxis_rangeslider_visible=True)

# Pie Chart
pie_chart = data['pie_chart']
pie_data = [pie_chart['good'], pie_chart['okay'], pie_chart['bad']]
total = sum(pie_data)
pie_data = [int(round(x / total * 100)) for x in pie_data]
df_pie = pd.DataFrame({
    "Sentiment": ["Positive", "Neutral", "Negative"],
    "Count": pie_data
})
fig_pie = px.pie(df_pie, names="Sentiment", values="Count", title="Sentiment Distribution",
                 color_discrete_map={'Positive': '#28a745', 'Neutral': '#ffc107', 'Negative': '#dc3545'})
fig_pie.update_traces(textposition='inside', textinfo='percent+label')
fig_pie.update_layout(showlegend=True)

# Table
top_sources = data['top_sources']
df_table = pd.DataFrame([
    {"Sources": i['source'], "Art. Count": i['article_count'],
        "Avg. Sentiment": i['avg_sentiment']}
    for i in top_sources
])

# News Articles
try:
    news_articles = top_news(
        "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en")
except Exception as e:
    print(f"Error fetching news: {str(e)}")
    news_articles = []


def create_news_item_component(title, link):
    parsed_uri = urlparse(link)
    domain = parsed_uri.netloc.replace('www.', '')
    return html.Div([
        html.P(html.B(title), style={
               'margin-bottom': '5px', 'line-height': '1.2'}),
        html.A(domain, href=link, target="_blank",
               style={'font-size': '0.85em', 'color': '#007bff', 'word-break': 'break-all'}),
        html.Hr(style={'margin': '10px 0', 'border-top': '1px dashed #ced4da'})
    ], style={'padding': '5px 0'})


news_elements = [create_news_item_component(
    article['title'], article['link']) for article in news_articles]


# --- 4. Initialize Dash App ---
app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[
    dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME
])
# server = app.server  # Expose for gunicorn

# --- 5. Define Dashboard Layout ---
app.layout = dbc.Container([
    # Stores
    dcc.Store(id='last-searched-query-store', data=''),
    dcc.Store(id='search-mode', data='default'),
    dcc.Store(id='search-status-store', data='idle'),
    dcc.Store(id='search-trigger-store', data=0),
    dcc.Store(id='last-search-timestamp-store', data=None),
    dcc.Store(id='validated-search-nclicks-store', data=0),
    dcc.Store(id='validated-search-query-store', data=None),
    dcc.Store(id='query-for-loading-message-store', data=''),

    # Row 1: Title
    dbc.Row(
        dbc.Col(
            html.H1("GLOBAL NEWS DASHBOARD",
                    className="text-center my-4 display-4 text-primary"),
            width=12
        )
    ),

    # Row 2: Custom Search Input
    dbc.Row(
        dbc.Col(
            html.Div([
                html.Div(id='custom-search-input-container'),
                html.Div(id='custom-search-output')
            ]),
            width=12
        ),
        className="mb-3"
    ),

    # Row 3: Filters
    dbc.Row([
        dbc.Col(
            dbc.Button(
                [html.I(className="fa-solid fa-gears me-2"), "Search Options"],
                id="open-options-offcanvas",
                color="info",
                className="mb-3"
            ),
            width="auto",
            className="d-flex align-items-end"
        ),
        dbc.Col(
            html.Div([
                html.Label("News in the last:", className="mb-2 lead"),
                dcc.Dropdown(
                    id='time-dropdown',
                    options=time_options,
                    value='monthly',
                    clearable=False,
                    className="mb-3"
                )
            ]),
            md=4,
            className="d-flex align-items-center justify-content-center flex-column"
        ),
        dbc.Col(
            html.Div([
                html.Label("Specific Category:", className="mb-2 lead"),
                dcc.Dropdown(
                    id='category-dropdown',
                    options=category_options,
                    value='summary',
                    clearable=False,
                    className="mb-3"
                )
            ]),
            md=4,
            className="d-flex align-items-center justify-content-center flex-column"
        )
    ], justify="center", className="mb-5"),

    # Offcanvas for Search Options
    dbc.Offcanvas(
        id="offcanvas-search-options",
        title="Search Settings",
        is_open=False,
        placement="start",
        children=[
            html.P("Choose your search mode:"),
            dbc.Row([
                dbc.Col(
                    dbc.Button("Default Search", id="default-search-button",
                               color="primary", size="lg", className="me-2 w-100"),
                    className="mb-2"
                ),
                dbc.Col(
                    dbc.Button("Custom Search", id="custom-search-button",
                               color="success", size="lg", className="w-100"),
                )
            ], className="g-2")
        ]
    ),

    # Row 4: Graphs
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Sentiment Trend Over Time", className="h5"),
                dbc.CardBody(
                    dcc.Graph(id='sentiment-line-graph', figure=fig_line))
            ], className="shadow-sm border-0"),
            md=6,
            className="mb-4"
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Overall Sentiment Distribution",
                               className="h5"),
                dbc.CardBody(
                    dcc.Graph(id='sentiment-pie-chart', figure=fig_pie))
            ], className="shadow-sm border-0"),
            md=6,
            className="mb-4"
        )
    ], className="mb-5"),

    # Row 5: Table and News
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Top Keywords & Sentiment", className="h5"),
                dbc.CardBody(
                    dash_table.DataTable(
                        id='keyword-table',
                        columns=[{"name": i, "id": i}
                                 for i in df_table.columns],
                        data=df_table.to_dict('records'),
                        style_table={'overflowX': 'auto'},
                        style_header={'backgroundColor': 'white',
                                      'fontWeight': 'bold'},
                        style_data_conditional=[
                            {'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'}],
                        export_headers='display',
                        export_format='xlsx'
                    )
                )
            ], className="shadow-sm border-0"),
            md=6,
            className="mb-4"
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader(
                    dbc.Row([
                        dbc.Col(html.Span("Top News in ",
                                className="h5 me-2"), width="auto"),
                        dbc.Col(
                            dcc.Dropdown(
                                id='country-dropdown',
                                options=country_options,
                                value='United States',
                                clearable=False,
                                className="flex-grow-1"
                            ),
                            width=True
                        )
                    ], align="center", justify="start")
                ),
                dbc.CardBody(
                    html.Div(
                        news_elements,
                        id='news-bar',
                        style={
                            'height': '350px',
                            'overflowY': 'scroll',
                            'border': '1px solid #e9ecef',
                            'padding': '10px',
                            'border-radius': '0.25rem',
                            'background-color': '#f8f9fa'
                        }
                    ),
                    className="p-0"
                )
            ], className="shadow-sm border-0"),
            md=6,
            className="mb-4"
        )
    ], className="mb-4")
], fluid=True, className="p-4")

# --- 6. Callbacks ---

# Toggle Offcanvas


@app.callback(
    Output("offcanvas-search-options", "is_open"),
    Input("open-options-offcanvas", "n_clicks"),
    State("offcanvas-search-options", "is_open"),
    prevent_initial_call=True
)
def toggle_offcanvas(n_clicks, is_open):
    return not is_open if n_clicks else is_open

# Handle Custom Search Button


@app.callback(
    [
        Output("custom-search-input-container", "children"),
        Output("time-dropdown", "disabled"),
        Output("time-dropdown", "value"),
        Output("category-dropdown", "disabled"),
        Output("category-dropdown", "value"),
        Output("offcanvas-search-options", "is_open"),
        Output("search-mode", "data"),
        Output("custom-search-output", "children")
    ],
    Input("custom-search-button", "n_clicks"),
    prevent_initial_call=True
)
def handle_custom_search_button(n_clicks):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    input_box = dbc.InputGroup([
        dbc.Input(
            id="custom-search-query-input",
            placeholder="Enter custom search query...",
            type="text",
            className="form-control-lg bg-dark text-light border-secondary"
        ),
        dbc.Button(
            [html.I(className="fa-solid fa-magnifying-glass me-2"), "Search"],
            id="apply-custom-search",
            color="primary",
            className="btn-lg"
        )
    ], className="mb-3")

    return (
        input_box,
        True,  # Disable time dropdown
        None,  # Clear time value
        True,  # Disable category dropdown
        None,  # Clear category value
        False,  # Close offcanvas
        "custom",
        None  # Clear custom search output
    )

# Handle Default Search Button


@app.callback(
    [
        Output("custom-search-input-container",
               "children", allow_duplicate=True),
        Output("time-dropdown", "disabled", allow_duplicate=True),
        Output("time-dropdown", "value", allow_duplicate=True),
        Output("category-dropdown", "disabled", allow_duplicate=True),
        Output("category-dropdown", "value", allow_duplicate=True),
        Output("offcanvas-search-options", "is_open", allow_duplicate=True),
        Output("search-mode", "data", allow_duplicate=True),
        Output("custom-search-output", "children", allow_duplicate=True),
        Output('keyword-table', 'data', allow_duplicate=True),
        Output('sentiment-line-graph', 'figure', allow_duplicate=True),
        Output('sentiment-pie-chart', 'figure', allow_duplicate=True),
        Output('news-bar', 'children', allow_duplicate=True)
    ],
    Input("default-search-button", "n_clicks"),
    prevent_initial_call=True
)
def handle_default_search_button(n_clicks):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    try:
        data = client.get("monthly_summary")
        if data:
            data = json.loads(data)
        else:
            raise ValueError("No data found in Redis for monthly_summary")
    except Exception as e:
        print(f"Error fetching default data: {str(e)}")
        data = {
            "line_graph": {
                '2025-06-21 00:00:00': 0.32576,
                '2025-06-23 00:00:00': 0.02052,
                '2025-06-29 00:00:00': 0.07594,
                '2025-06-30 00:00:00': -0.04024
            },
            "pie_chart": {'good': 26, 'okay': 46, 'bad': 18},
            "top_sources": [
                {'source': 'si', 'article_count': 5, 'avg_sentiment': 0.0},
                {'source': 'menafn', 'article_count': 5, 'avg_sentiment': 0.0945}
            ]
        }

    # Line Graph
    line_graph = data['line_graph']
    timestamps = [datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                  for ts_str in line_graph.keys()]
    sentiments = list(line_graph.values())
    df_line = pd.DataFrame({
        "Timestamp": timestamps,
        "Sentiment Score": sentiments
    }).sort_values(by="Timestamp")
    fig_line = px.line(df_line, x="Timestamp", y="Sentiment Score", title="Overall Sentiment Trend",
                       markers=True, line_shape="linear")
    fig_line.update_layout(
        hovermode="x unified", template="plotly_white", xaxis_rangeslider_visible=True)

    # Pie Chart
    pie_chart = data['pie_chart']
    pie_data = [pie_chart['good'], pie_chart['okay'], pie_chart['bad']]
    total = sum(pie_data)
    pie_data = [int(round(x / total * 100)) for x in pie_data]
    df_pie = pd.DataFrame({
        "Sentiment": ["Positive", "Neutral", "Negative"],
        "Count": pie_data
    })
    fig_pie = px.pie(df_pie, names="Sentiment", values="Count", title="Sentiment Distribution",
                     color_discrete_map={'Positive': '#28a745', 'Neutral': '#ffc107', 'Negative': '#dc3545'})
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    fig_pie.update_layout(showlegend=True)

    # Table
    top_sources = data['top_sources']
    df_table = pd.DataFrame([
        {"Sources": i['source'], "Art. Count": i['article_count'],
            "Avg. Sentiment": i['avg_sentiment']}
        for i in top_sources
    ])

    # News
    try:
        news_articles = top_news(
            "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en")
        news_elements = [create_news_item_component(
            article['title'], article['link']) for article in news_articles]
    except Exception as e:
        print(f"Error fetching news: {str(e)}")
        news_elements = [html.Div(
            dbc.Alert("Failed to fetch news.", color="warning", className="mt-3"))]

    return (
        None,  # Clear input box
        False,  # Enable time dropdown
        'monthly',  # Reset time value
        False,  # Enable category dropdown
        'summary',  # Reset category value
        False,  # Close offcanvas
        "default",
        None,  # Clear custom search output
        df_table.to_dict('records'),
        fig_line,
        fig_pie,
        news_elements
    )

# Trigger Search and Loading


@app.callback(
    [
        Output("custom-search-output", "children", allow_duplicate=True),
        Output("last-search-timestamp-store", "data", allow_duplicate=True),
        Output('search-trigger-store', 'data'),
        Output('search-status-store', 'data', allow_duplicate=True),
        Output('validated-search-nclicks-store', 'data'),
        Output('validated-search-query-store', 'data'),
        Output('query-for-loading-message-store', 'data')
    ],
    Input("apply-custom-search", "n_clicks"),
    [
        State("custom-search-query-input", "value"),
        State("last-searched-query-store", "data"),
        State("last-search-timestamp-store", "data")
    ],
    prevent_initial_call=True
)
def trigger_search_and_loading(n_clicks, current_search_query, last_searched_query, last_search_timestamp):
    if not n_clicks:
        raise no_update

    cleaned_current_query = current_search_query.strip() if current_search_query else ''
    current_timestamp = time.time()

    if not cleaned_current_query:
        return (
            dbc.Alert("Please enter a search query.",
                      color="warning", className="mt-3"),
            no_update,
            no_update,
            'idle',
            no_update,
            no_update,
            no_update
        )

    if last_search_timestamp is not None:
        time_elapsed = current_timestamp - last_search_timestamp
        if time_elapsed < 5:
            remaining_time = round(5 - time_elapsed, 1)
            return (
                dbc.Alert(
                    f"Please wait. Searched too recently. Try again in {remaining_time} seconds.",
                    color="warning", className="mt-3"
                ),
                current_timestamp,
                no_update,
                'idle',
                no_update,
                no_update,
                no_update
            )

    if cleaned_current_query == last_searched_query:
        return (
            dbc.Alert(f"'{cleaned_current_query}' was last searched. No new action needed.",
                      color="info", className="mt-3"),
            no_update,
            no_update,
            'idle',
            no_update,
            no_update,
            no_update
        )

    return (
        None,
        current_timestamp,
        n_clicks,
        'loading',
        n_clicks,
        cleaned_current_query,
        cleaned_current_query
    )

# Perform Custom Search


@app.callback(
    [
        Output("custom-search-output", "children", allow_duplicate=True),
        Output("last-searched-query-store", "data"),
        Output('keyword-table', 'data'),
        Output('sentiment-line-graph', 'figure'),
        Output('sentiment-pie-chart', 'figure'),
        Output('news-bar', 'children'),
        Output("country-dropdown", "value"),
        Output('search-status-store', 'data', allow_duplicate=True)
    ],
    Input("validated-search-nclicks-store", "data"),
    State("validated-search-query-store", "data"),
    prevent_initial_call=True
)
def perform_custom_search(validated_n_clicks, validated_query):
    if not validated_n_clicks or not validated_query:
        raise no_update

    try:
        dates, sentiments, pie_data, top_headlines = get_data(validated_query)
    except Exception as e:
        print(f"Error in get_data: {str(e)}")
        return (
            dbc.Alert("Failed to fetch custom search data.",
                      color="danger", className="mt-3"),
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            'error'
        )

    df_line = pd.DataFrame({
        "Timestamp": pd.to_datetime(dates),
        "Sentiment Score": sentiments
    })
    fig_line = px.line(df_line, x="Timestamp", y="Sentiment Score", title=f"Sentiment Trend for '{validated_query}'",
                       markers=True, line_shape="linear")
    fig_line.update_layout(hovermode="x unified", template="plotly_white")

    df_pie = pd.DataFrame({
        "Sentiment": ["Positive", "Neutral", "Negative"],
        "Count": pie_data
    })
    fig_pie = px.pie(df_pie, names="Sentiment", values="Count", title="Sentiment Distribution",
                     color_discrete_map={'Positive': '#28a745', 'Neutral': '#ffc107', 'Negative': '#dc3545'})
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    fig_pie.update_layout(showlegend=True)

    news_elements = [create_news_item_component(
        article['title'], article['link']) for article in top_headlines]

    return (
        None,
        validated_query,
        [],  # Empty table for now
        fig_line,
        fig_pie,
        news_elements,
        "United States",
        'success'
    )

# Display Searching Message


@app.callback(
    [
        Output("custom-search-output", "children", allow_duplicate=True),
        Output("apply-custom-search", "disabled")
    ],
    Input("search-trigger-store", "data"),
    State("query-for-loading-message-store", "data"),
    prevent_initial_call=True,
    running=[
        (
            Output("custom-search-output", "children"),
            html.Div(
                # Static placeholder; actual message will be set in callback
                dbc.Alert("Searching...", color="info", className="mt-3"),
                style={'textAlign': 'center'}
            ),
            None
        ),
        (Output("apply-custom-search", "disabled"), True, False)
    ]
)
def display_searching_message(trigger_data, current_query):
    if trigger_data is None:
        return no_update, no_update

    # Access the query from the state
    query = dash.callback_context.states.get(
        'query-for-loading-message-store.data', '').strip()

    # Return the dynamic searching message
    return (
        html.Div(
            dbc.Alert(
                f"Searching for '{query}'..." if query else "Searching...",
                color="info",
                className="mt-3"
            ),
            style={'textAlign': 'center'}
        ),
        no_update
    )

# Handle Search Status Display


@app.callback(
    Output("custom-search-output", "children", allow_duplicate=True),
    Input("search-status-store", "data"),
    State("last-searched-query-store", "data"),
    prevent_initial_call=True
)
def handle_search_status_display(status, last_searched_query):
    if status == 'success':
        return html.Div(
            dbc.Alert(f"Search for '{last_searched_query.strip()}' completed!",
                      color="success", className="mt-3"),
            style={'textAlign': 'center'}
        )
    return no_update

# Update News Based on Country


@app.callback(
    Output('news-bar', 'children', allow_duplicate=True),
    Input("country-dropdown", "value"),
    [
        State("search-mode", "data"),
        State("last-searched-query-store", "data")
    ],
    prevent_initial_call=True
)
def top_news_in_country(selected_country_value, current_search_mode, last_searched_query):
    if not current_search_mode:
        raise dash.exceptions.PreventUpdate

    country_params = COUNTRY_CODES.get(
        selected_country_value, COUNTRY_CODES['United States'])
    hl, gl, ceid = country_params['hl'], country_params['gl'], country_params['ceid']

    try:
        if current_search_mode == 'default':
            url = f"https://news.google.com/rss?hl={hl}&gl={gl}&ceid={ceid}"
        else:
            if not last_searched_query:
                return html.Div(dbc.Alert("No custom search query available.", color="info", className="mt-3"))
            cleaned_query = last_searched_query.strip().replace(' ', '+')
            url = f"https://news.google.com/rss/search?q={cleaned_query}&hl={hl}&gl={gl}&ceid={ceid}"

        top_headlines = top_news(url)
        news_elements = [create_news_item_component(
            article['title'], article['link']) for article in top_headlines]
    except Exception as e:
        print(f"Error fetching news: {str(e)}")
        news_elements = [html.Div(
            dbc.Alert("Could not fetch news.", color="warning", className="mt-3"))]

    return news_elements

# Update Visualizations Based on Time and Category


@app.callback(
    [
        Output('keyword-table', 'data', allow_duplicate=True),
        Output('sentiment-line-graph', 'figure', allow_duplicate=True),
        Output('sentiment-pie-chart', 'figure', allow_duplicate=True),
        Output('news-bar', 'children', allow_duplicate=True)
    ],
    [
        Input('time-dropdown', 'value'),
        Input('category-dropdown', 'value'),
        State("country-dropdown", "value"),
        State("search-mode", "data")
    ],
    prevent_initial_call=True
)
def time_and_cat_sort(selected_time_value, selected_category_value, selected_country, search_mode):
    if search_mode != 'default' or not selected_time_value or not selected_category_value:
        raise dash.exceptions.PreventUpdate

    redis_key = f"{selected_time_value}_{selected_category_value}"
    try:
        data = client.get(redis_key)
        if data:
            data = json.loads(data)
        else:
            raise ValueError(f"No data found in Redis for key: {redis_key}")
    except Exception as e:
        print(f"Error fetching Redis data: {str(e)}")
        data = {
            "line_graph": {
                '2025-06-21 00:00:00': 0.32576,
                '2025-06-23 00:00:00': 0.02052,
                '2025-06-29 00:00:00': 0.07594,
                '2025-06-30 00:00:00': -0.04024
            },
            "pie_chart": {'good': 26, 'okay': 46, 'bad': 18},
            "top_sources": [
                {'source': 'si', 'article_count': 5, 'avg_sentiment': 0.0},
                {'source': 'menafn', 'article_count': 5, 'avg_sentiment': 0.0945}
            ]
        }

    # Line Graph
    line_graph = data['line_graph']
    timestamps = [datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                  for ts_str in line_graph.keys()]
    sentiments = list(line_graph.values())
    df_line = pd.DataFrame({
        "Timestamp": timestamps,
        "Sentiment Score": sentiments
    }).sort_values(by="Timestamp")
    fig_line = px.line(df_line, x="Timestamp", y="Sentiment Score", title="Overall Sentiment Trend",
                       markers=True, line_shape="linear")
    fig_line.update_layout(
        hovermode="x unified", template="plotly_white", xaxis_rangeslider_visible=True)

    # Pie Chart
    pie_chart = data['pie_chart']
    pie_data = [pie_chart['good'], pie_chart['okay'], pie_chart['bad']]
    total = sum(pie_data)
    pie_data = [int(round(x / total * 100)) for x in pie_data]
    df_pie = pd.DataFrame({
        "Sentiment": ["Positive", "Neutral", "Negative"],
        "Count": pie_data
    })
    fig_pie = px.pie(df_pie, names="Sentiment", values="Count", title="Sentiment Distribution",
                     color_discrete_map={'Positive': '#28a745', 'Neutral': '#ffc107', 'Negative': '#dc3545'})
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    fig_pie.update_layout(showlegend=True)

    # Table
    top_sources = data['top_sources']
    df_table = pd.DataFrame([
        {"Sources": i['source'], "Art. Count": i['article_count'],
            "Avg. Sentiment": i['avg_sentiment']}
        for i in top_sources
    ])

    # News
    country_params = COUNTRY_CODES.get(
        selected_country, COUNTRY_CODES['United States'])
    hl, gl, ceid = country_params['hl'], country_params['gl'], country_params['ceid']
    url = f"https://news.google.com/rss?hl={hl}&gl={gl}&ceid={ceid}" if selected_category_value == "summary" else \
        f"https://news.google.com/rss/search?q={selected_category_value}&hl={hl}&gl={gl}&ceid={ceid}"

    try:
        news_articles = top_news(url)
        news_elements = [create_news_item_component(
            article['title'], article['link']) for article in news_articles]
    except Exception as e:
        print(f"Error fetching news: {str(e)}")
        news_elements = [html.Div(
            dbc.Alert("Could not fetch news.", color="warning", className="mt-3"))]

    return (
        df_table.to_dict('records'),
        fig_line,
        fig_pie,
        news_elements
    )


# --- 7. Run the App ---
if __name__ == '__main__':
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(main())
        app.run(debug=True, port="9000")
    except Exception as e:
        print(f"Error running app: {str(e)}")
