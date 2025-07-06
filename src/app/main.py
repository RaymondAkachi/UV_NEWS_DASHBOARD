import dash
from dash.dependencies import Input, Output, State, ALL
import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table
import plotly.express as px
# from redis import Redis
from app.redis_logic.redis import RedisClient
# import os
# from dotenv import load_dotenv
import pandas as pd
from urllib.parse import urlparse
import json
from datetime import datetime
import asyncio
import nest_asyncio
from asgiref.wsgi import WsgiToAsgi  # Import the adapter
import uvicorn
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

from .get_custom_data import get_data, top_news
from .scheduler import startup_function, shutdown_function

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# from pathlib import Path  # Import Path

# # ... (other imports) ...
# BASE_DIR = Path(__file__).resolve().parent.parent

# dotenv_path = BASE_DIR / 'app' / '.env'

# load_dotenv(dotenv_path)
# NEWS_API = os.getenv("NEWS_API_KEY")
# REDIS_URL = os.getenv("REDIS_URL")
# print(f"DEBUG: NEWSAPI_KEY loaded: {NEWS_API}")
# NEWS_URL = f"https://newsdata.io/api/1/latest?apikey={NEWS_API}&language=en&q=pizza"

nest_asyncio.apply()

client = RedisClient()

# --- 1. Prepare Dummy Data (Same as before) ---
# Dropdown Options
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
    # Note: This will fetch English news for Germany based on COUNTRY_CODES
    {'label': 'Germany', 'value': 'Germany'},
    {'label': 'Australia', 'value': 'Australia'},
    # Adding 5 more popular countries
    {'label': 'India', 'value': 'India'},
    {'label': 'France', 'value': 'France_en'},  # English news from France
    {'label': 'Japan', 'value': 'Japan_en'},  # English news from Japan
    {'label': 'Brazil', 'value': 'Brazil_en'},  # English news from Brazil
    # English news from China (often limited, but useful for example)
    {'label': 'China', 'value': 'China_en'},
    # Countries you specifically asked about
    {'label': 'Nigeria', 'value': 'Nigeria'},
    {'label': 'Netherlands (English)', 'value': 'Netherlands_en'},
    # If you also want Dutch news
    {'label': 'Netherlands (Dutch)', 'value': 'Netherlands_nl'},
    {'label': 'Zambia', 'value': 'Zambia'},
    # You can add more as needed
]

COUNTRY_CODES = {
    'United States': {'gl': 'US', 'hl': 'en', 'ceid': 'US:en'},
    'Canada': {'gl': 'CA', 'hl': 'en', 'ceid': 'CA:en'},
    'United Kingdom': {'gl': 'GB', 'hl': 'en', 'ceid': 'GB:en'},
    # English news from Germany
    'Germany': {'gl': 'DE', 'hl': 'en', 'ceid': 'DE:en'},
    'Australia': {'gl': 'AU', 'hl': 'en', 'ceid': 'AU:en'},
    # 5 Most Popular Countries added
    'India': {'gl': 'IN', 'hl': 'en', 'ceid': 'IN:en'},
    # English news from France
    'France_en': {'gl': 'FR', 'hl': 'en', 'ceid': 'FR:en'},
    # English news from Japan
    'Japan_en': {'gl': 'JP', 'hl': 'en', 'ceid': 'JP:en'},
    # English news from Brazil
    'Brazil_en': {'gl': 'BR', 'hl': 'en', 'ceid': 'BR:en'},
    # English news from China
    'China_en': {'gl': 'CN', 'hl': 'en', 'ceid': 'CN:en'},
    # Countries you specifically asked about
    'Nigeria': {'gl': 'NG', 'hl': 'en', 'ceid': 'NG:en'},
    'Netherlands_en': {'gl': 'NL', 'hl': 'en', 'ceid': 'NL:en'},
    # Dutch news for Netherlands
    'Netherlands_nl': {'gl': 'NL', 'hl': 'nl', 'ceid': 'NL:nl'},
    'Zambia': {'gl': 'ZM', 'hl': 'en', 'ceid': 'ZM:en'},
}
custom_search_output_children = None

client.initialize()
data = client.get("monthly_summary")
data = json.loads(data)
if not data['line_graph']:
    custom_search_output_children = html.Div(
        dbc.Alert(
            f"A server error occured",
            color="danger",
            className="mt-3"
        ),
        style={'text-align': 'center'}
    )


# Dummy Data for Line Graph
line_graph = data['line_graph']
# timestamps = line_graph.keys()
timestamps = [datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
              for ts_str in line_graph.keys()]
sentiments = list(line_graph.values())
df_line = pd.DataFrame({
    "Timestamp": timestamps,
    "Sentiment Score": sentiments
})

# df_line['Timestamp'] = df_line['Timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
# df_line['Timestamp'] = df_line['Timestamp']

df = df_line.sort_values(by="Timestamp")
fig_line = px.line(df_line, x="Timestamp", y="Sentiment Score", title="Overall Sentiment Trend",
                   markers=True, line_shape="linear")
fig_line.update_layout(hovermode="x unified", template="plotly_white",
                       xaxis_rangeslider_visible=True)

# Dummy Data for Pie Chart
pie_chart = data['pie_chart']
total = 0
pie_data = [pie_chart['good'], pie_chart['okay'], pie_chart['bad']]
for i in pie_data:
    total += i
pie_data = [x / total * 100 for x in pie_data]
pie_data = [int(round(x)) for x in pie_data]
df_pie = pd.DataFrame({
    "Sentiment": ["Positive", "Neutral", "Negative"],
    "Count": pie_data
})
fig_pie = px.pie(df_pie, names="Sentiment", values="Count", title="Sentiment Distribution",
                 color_discrete_map={'Positive': '#28a745', 'Neutral': '#ffc107', 'Negative': '#dc3545'})
fig_pie.update_traces(textposition='inside', textinfo='percent+label')
fig_pie.update_layout(showlegend=True)

# Dummy Data for Table
top_sources = data['top_sources']
sources = []
article_counts = []
avg_sentiments = []

for i in top_sources:
    sources.append(i['source'])
    article_counts.append(i['article_count'])
    avg_sentiments.append(i['avg_sentiment'])

df_table = pd.DataFrame({
    "Sources": sources,
    "Art. Count": article_counts,
    "Avg. Sentiment": avg_sentiments
})

# Dummy News Articles for Scrollable Feed
news_articles = top_news(
    "https://news.google.com/rss?hl=en-US&gl=NG&ceid=US:en")
# news_articles = [
#     {"title": "Tech Giant Unveils New AI Processor",
#         "link": "https://www.verylongexample.com/ai-innovation/tech-giant-unveils-revolutionary-new-artificial-intelligence-processor-details.html"},
#     {"title": "Global Markets React to Interest Rate Hike",
#         "link": "https://www.financeworldnews.org/economy/global-markets-show-mixed-reactions-to-recent-central-bank-interest-rate-hike-analysis.html"},
#     {"title": "Breakthrough in Renewable Energy Storage",
#         "link": "https://www.greenenergynow.net/research/new-breakthrough-in-long-duration-renewable-energy-storage-technology-paving-the-way.html"},
#     {"title": "Local Charity Exceeds Fundraising Goal",
#         "link": "https://www.communityvoice.com/local-updates/local-charity-campaign-exceeds-fundraising-goal-thanks-to-overwhelming-community-support.html"},
#     {"title": "New Study on Climate Change Impacts",
#         "link": "https://www.environmentalsciencejournal.org/climate-research/comprehensive-new-study-highlights-severe-climate-change-impacts-globally.html"},
#     {"title": "Startup Secures Series B Funding Round",
#         "link": "https://www.startupinsights.co/funding/promising-fintech-startup-secures-oversubscribed-series-b-funding-round-for-expansion.html"},
#     {"title": "Major Sports Event Kicks Off This Weekend",
#         "link": "https://www.sportseverywhere.com/events/annual-international-sports-tournament-kicks-off-this-weekend-full-schedule-and-athlete-profiles.html"},
#     {"title": "Health Organization Issues New Guidelines",
#         "link": "https://www.healthnewsdaily.org/public-health/major-health-organization-issues-new-public-health-guidelines-for-seasonal-illnesses.html"},
#     {"title": "Cultural Festival Draws Record Crowds",
#         "link": "https://www.artsculturemagazine.com/festival-reviews/annual-cultural-arts-festival-draws-record-breaking-crowds-and-acclaim.html"},
# ]

# Function to create a news item div (same as before)


def create_news_item_component(title, link):
    parsed_uri = urlparse(link)
    domain = parsed_uri.netloc
    link_display_text = domain.replace('www.', '')
    return html.Div([
        html.P(html.B(title), style={
               'margin-bottom': '5px', 'line-height': '1.2'}),
        html.A(link_display_text, href=link, target="_blank",
               style={'font-size': '0.85em', 'color': '#007bff', 'word-break': 'break-all'}),
        html.Hr(style={'margin-top': '10px', 'margin-bottom': '10px',
                'border-top': '1px dashed #ced4da'})
    ], style={'padding': '5px 0'})


news_elements = [create_news_item_component(
    article['title'], article['link']) for article in news_articles]


# --- 2. Initialize Dash App ---
app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[
                dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME])
# Added dbc.icons.FONT_AWESOME for a potential settings icon on the button

# EXPOSE THE SERVER for Gunicorn
server = app.server  # This line is essential!
wsgi_app = app.server
asgi_app = WsgiToAsgi(wsgi_app)


# --- 3. Define Dashboard Layout ---
app.layout = dbc.Container([

    # Storing needed values in browser session
    dcc.Store(id='last-searched-query-store', data=''),
    dcc.Store(id='search-mode', data='default'),

    # Row 1: Dashboard Title
    dbc.Row(
        dbc.Col(
            html.H1("GLOBAL NEWS DASHBOARD",
                    className="text-center my-4 display-4 text-primary"),
            width=12
        )
    ),

    # Placeholder for the dynamically added input box
    dbc.Row(
        dbc.Col(
            html.Div([
                html.Div(id='custom-search-input-container'),
                # To display search query for demonstration
                html.Div(id='custom-search-output',
                         children=custom_search_output_children)
            ]),
            width=12
        ),
        className="mb-3"
    ),

    # Row 2: Filters (Dropdowns) with new button
    dbc.Row([
        # Button for Offcanvas
        dbc.Col(
            dbc.Button(
                [html.I(className="fa-solid fa-gears me-2"),
                 "Search Options"],  # Gear icon
                id="open-options-offcanvas",
                color="info",  # Info color for secondary action
                className="mb-3"
            ),
            width="auto",  # Adjust width to content
            align="end",  # Align button to the bottom of the column
            className="d-flex align-items-end"  # Use flexbox for vertical alignment
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

    # dbc.Offcanvas for search options
    dbc.Offcanvas(
        id="offcanvas-search-options",
        title="Search Settings",
        is_open=False,  # Initially closed
        placement="start",  # Opens from the left
        children=[
            html.P("Choose your search mode:"),
            dbc.Row([
                dbc.Col(
                    dbc.Button("Default Search", id="default-search-button",
                               color="primary", size="lg", className="me-2 w-100"),  # w-100 for full width
                    className="mb-2"
                ),
                dbc.Col(
                    dbc.Button("Custom Search", id="custom-search-button",
                               color="success", size="lg", className="w-100"),
                )
            ], className="g-2")  # g-2 for gap between columns
        ]
    ),

    # Row 3: Graphs (Line Chart and Pie Chart)
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Sentiment Trend Over Time", className="h5"),
                dbc.CardBody(
                    dcc.Graph(id='sentiment-line-graph', figure=fig_line)
                )
            ], className="shadow-sm border-0"),
            md=6,
            className="mb-4"
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Overall Sentiment Distribution",
                               className="h5"),
                dbc.CardBody(
                    dcc.Graph(id='sentiment-pie-chart', figure=fig_pie)
                )
            ], className="shadow-sm border-0"),
            md=6,
            className="mb-4"
        )
    ], className="mb-5"),

    # Row 4: Table and Scrollable News
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
                        style_header={
                            'backgroundColor': 'white',
                            'fontWeight': 'bold'
                        },
                        style_data_conditional=[
                            {'if': {'row_index': 'odd'},
                                'backgroundColor': 'rgb(248, 248, 248)'}
                        ],
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

# --- 4. Callbacks for Offcanvas and Dynamic Content ---

# Callback to open/close the offcanvas


@app.callback(
    Output("offcanvas-search-options", "is_open"),
    Input("open-options-offcanvas", "n_clicks"),
    State("offcanvas-search-options", "is_open"),
    prevent_initial_call=True
)
def toggle_offcanvas(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

# Callback for Custom Search / Default Search buttons


@app.callback(
    # To add/remove the input box
    Output("custom-search-input-container", "children"),
    Output("time-dropdown", "disabled"),
    Output("time-dropdown", "value"),
    Output("category-dropdown", "disabled"),
    Output("category-dropdown", "value"),
    Output("offcanvas-search-options", "is_open", allow_duplicate=True),
    # Corrected ID to match previous advice
    Output("search-mode", "data"),
    # Allow_duplicate needed if other callbacks also target this
    Output("custom-search-output", "children", allow_duplicate=True),
    Input("custom-search-button", "n_clicks"),
    prevent_initial_call=True
)
def handle_custom_search_button(n_clicks):
    if n_clicks is None:
        raise dash.exceptions.PreventUpdate

    # Show custom input box
    input_box = dbc.InputGroup(
        [
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
        ],
        className="mb-3"
    )

    # Disable and clear dropdowns
    time_disabled = True
    time_value = None
    category_disabled = True
    category_value = None

    offcanvas_open = False  # Close offcanvas

    search_mode = "custom"  # Set search mode

    # Reset/clear the output area that might have old search results
    custom_search_output_children = None  # Or html.Div() if you prefer an empty div

    return (
        input_box,
        time_disabled,
        time_value,
        category_disabled,
        category_value,
        offcanvas_open,
        search_mode,
        custom_search_output_children
    )


@app.callback(
    # Allow_duplicate if custom search also targets it
    Output("custom-search-input-container", "children", allow_duplicate=True),
    Output("time-dropdown", "disabled", allow_duplicate=True),
    Output("time-dropdown", "value", allow_duplicate=True),
    Output("category-dropdown", "disabled", allow_duplicate=True),
    Output("category-dropdown", "value", allow_duplicate=True),
    Output("offcanvas-search-options", "is_open", allow_duplicate=True),
    # Corrected ID and allow_duplicate
    Output("search-mode", "data", allow_duplicate=True),
    # Allow_duplicate needed if other callbacks also target this
    Output("custom-search-output", "children", allow_duplicate=True),

    # Set data charts back to normal
    Output('keyword-table', 'data', allow_duplicate=True),
    Output('sentiment-line-graph', 'figure', allow_duplicate=True),
    Output('sentiment-pie-chart', 'figure', allow_duplicate=True),
    Output('news-bar', 'children', allow_duplicate=True),

    # Output('category-dropdown', 'value', allow_duplicate=True),
    # Output('time-dropdown', 'value', allow_duplicate=True),

    Input("default-search-button", "n_clicks"),
    State('search-mode', 'data'),
    prevent_initial_call=True
)
def handle_default_search_button(n_clicks, search_mode):
    if n_clicks is None:
        raise dash.exceptions.PreventUpdate

    # Hide custom input box
    input_box = None  # Remove the input group

    # Enable and reset dropdowns
    time_disabled = False
    time_value = 'monthly'  # Default value
    category_disabled = False
    category_value = 'summary'  # Default value

    offcanvas_open = False  # Close offcanvas

    # Clear any previous custom search output if it exists
    custom_search_output_children = None  # Or html.Div()

    if search_mode == "custom":
        data = client.get("monthly_summary")
        print(data, "Hello")
        data = json.loads(data)

        if not data['line_graph']:
            custom_search_output_children = html.Div(
                dbc.Alert(
                    f"A server error occured",
                    color="danger",
                    className="mt-3"
                ),
                style={'text-align': 'center'}
            )

        # Dummy Data for Line Graph
        line_graph = data['line_graph']
        # timestamps = line_graph.keys()
        timestamps = [datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                      for ts_str in line_graph.keys()]
        sentiments = list(line_graph.values())
        df_line = pd.DataFrame({
            "Timestamp": timestamps,
            "Sentiment Score": sentiments
        })

        df = df_line.sort_values(by="Timestamp")
        fig_line = px.line(df, x="Timestamp", y="Sentiment Score", title="Overall Sentiment Trend",
                           markers=True, line_shape="linear")
        fig_line.update_layout(hovermode="x unified", template="plotly_white",
                               xaxis_rangeslider_visible=True)

        # Dummy Data for Pie Chart
        pie_chart = data['pie_chart']
        total = 0
        pie_data = [pie_chart['good'], pie_chart['okay'], pie_chart['bad']]
        for i in pie_data:
            total += i
        pie_data = [x / total * 100 for x in pie_data]
        pie_data = [int(round(x)) for x in pie_data]
        df_pie = pd.DataFrame({
            "Sentiment": ["Positive", "Neutral", "Negative"],
            "Count": pie_data
        })
        fig_pie = px.pie(df_pie, names="Sentiment", values="Count", title="Sentiment Distribution",
                         color_discrete_map={'Positive': '#28a745', 'Neutral': '#ffc107', 'Negative': '#dc3545'})
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(showlegend=True)

        # Dummy Data for Table
        top_sources = data['top_sources']
        sources = []
        article_counts = []
        avg_sentiments = []

        for i in top_sources:
            sources.append(i['source'])
            article_counts.append(i['article_count'])
            avg_sentiments.append(i['avg_sentiment'])

        df_table = pd.DataFrame({
            "Sources": sources,
            "Art. Count": article_counts,
            "Avg. Sentiment": avg_sentiments
        })

        df_table_json = df_table.to_dict('records')
        # Dummy News Articles for Scrollable Feed
        news_articles = top_news(
            "https://news.google.com/rss?hl=en-US&gl=NG&ceid=US:en")

        news_elements = [create_news_item_component(
            article['title'], article['link']) for article in news_articles]

    else:
        df_table_json = dash.no_update
        fig_line = dash.no_update
        fig_pie = dash.no_update
        news_elements = dash.no_update

    search_mode = "default"  # Set search mode

    return (
        input_box,
        time_disabled,
        time_value,
        category_disabled,
        category_value,
        offcanvas_open,
        search_mode,
        custom_search_output_children,
        df_table_json,
        fig_line,
        fig_pie,
        news_elements
        # "monthly",
        # "summary"
    )


# @app.callback(
#     # To add/remove the input box
#     Output("custom-search-output", "children"),
#     Output("custom-search-input-container", "children"),
#     Output("time-dropdown", "disabled"),  # To disable/enable the time dropdown
#     Output("time-dropdown", "value"),  # To reset its value
#     # To disable/enable the category dropdown
#     Output("category-dropdown", "disabled"),
#     Output("category-dropdown", "value"),  # To reset its value
#     Output("offcanvas-search-options", "is_open",
#            allow_duplicate=True),  # To close offcanvas
#     Output("search-mode", "data"),
#     Input("custom-search-button", "n_clicks"),
#     Input("default-search-button", "n_clicks"),
#     State("search-mode", "data"),
#     # Use State to know if a click occurred, but not trigger on initial load for these
#     # States for dropdowns not needed as we just reset them
#     prevent_initial_call=True
# )
# def handle_search_mode(custom_clicks, default_clicks, search_mode):
#     ctx = dash.callback_context
#     if not ctx.triggered_id:
#         raise dash.exceptions.PreventUpdate

#     triggered_id = ctx.triggered_id

#     # Default state: no custom input, dropdowns enabled and default values
#     input_box = None
#     time_disabled = False
#     time_value = 'month'
#     category_disabled = False
#     category_value = 'none'
#     offcanvas_open = False  # Close offcanvas after selection

#     if triggered_id == "custom-search-button":
#         search_mode = "custom"
#         input_box = dbc.InputGroup(
#             [
#                 dbc.Input(
#                     id="custom-search-query-input",
#                     placeholder="Enter custom search query...",
#                     type="text",
#                     # Added dark theme classes
#                     className="form-control-lg bg-dark text-light border-secondary"
#                 ),
#                 dbc.Button(
#                     # Search icon
#                     [html.I(className="fa-solid fa-magnifying-glass me-2"), "Search"],
#                     id="apply-custom-search",
#                     color="primary",
#                     className="btn-lg"  # Ensure button is same size as input
#                 )
#             ],
#             className="mb-3"  # Margin for the whole input group
#         )
#         time_disabled = True
#         time_value = None  # Set to None to clear/grey out
#         category_disabled = True
#         category_value = None  # Set to None to clear/grey out
#         search_output = dash.no_update
#     elif triggered_id == "default-search-button":
#         # Nothing to do, default state already set
#         if search_mode == "default":
#             pass
#         input_box = None
#         search_output = None
#         search_mode = "default"

#     return search_output, input_box, time_disabled, time_value, category_disabled, category_value, offcanvas_open, search_mode


@app.callback(
    Output("custom-search-output", "children"),
    Output("last-searched-query-store", "data"),
    Output('keyword-table', 'data'),
    Output('sentiment-line-graph', 'figure'),
    Output('sentiment-pie-chart', 'figure'),
    Output('news-bar', 'children'),
    Output("country-dropdown", "value"),
    Input("apply-custom-search", "n_clicks"),
    State("custom-search-query-input", "value"),
    # Input: Get the last stored query
    State("last-searched-query-store", "data"),
    prevent_initial_call=True,
    running=[(Output("apply-custom-search", "disabled"), True, False)]
)
def perform_custom_search(n_clicks, current_search_query, last_searched_query):
    # Ensure n_clicks is not None (first load scenario) and remove leading/trailing whitespace
    if n_clicks is None:
        raise dash.exceptions.PreventUpdate

    cleaned_current_query = current_search_query.strip() if current_search_query else ''

    if cleaned_current_query:
        # Perform search action

        search_message = html.Div(
            dbc.Alert(f"Search for: '{cleaned_current_query}' completed",
                      color="success", className="mt-3"),
            style={'text-align': 'center'}
        )

        dates, sentiments, pie_data, top_headlines = get_data(
            cleaned_current_query)
        if dates == []:
            search_message = html.Div(
                dbc.Alert(
                    f"A server error occured",
                    color="danger",
                    className="mt-3"
                ),
                style={'text-align': 'center'}
            )

        df_line = pd.DataFrame({
            "Timestamp": dates,
            "Sentiment Score": sentiments
        })

        df_line["Timestamp"] = pd.to_datetime(df_line["Timestamp"])

        fig_line = px.line(df_line, x="Timestamp", y="Sentiment Score", title="Overall Sentiment Trend (Your Data)",
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

        # Return the message and update the store with the new query
        return search_message, cleaned_current_query, [], fig_line, fig_pie, news_elements, "United States"
    elif not cleaned_current_query:
        # User pressed search with an empty input
        search_message = html.Div(
            dbc.Alert("Please enter a search query.",
                      color="warning", className="mt-3"),
            style={'text-align': 'center'}
        )
        # Do not update the store as no valid search was made
        return search_message, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    else:
        # Query is the same as the last one, prevent update
        search_message = html.Div(
            dbc.Alert(f"'{cleaned_current_query}' was last searched. No new action.",
                      color="info", className="mt-3"),
            style={'text-align': 'center'}
        )
        # Return the "no new action" message but don't update the store's data
        return search_message, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update


@app.callback(
    # allow_duplicate=True is important!
    Output('news-bar', 'children', allow_duplicate=True),
    # No other outputs for now, but you could add more for other dashboards if needed
    Input("country-dropdown", "value"),
    State("search-mode", "data"),  # Corrected ID: 'search-mode-store'
    State("last-searched-query-store", "data"),
    prevent_initial_call=True  # Prevents the callback from firing on app load
)
def top_news_in_country(selected_country_value, current_search_mode, last_searched_query):
    # Ensure current_search_mode is not None (e.g., during very initial load if store hasn't populated)
    if current_search_mode is None:
        raise dash.exceptions.PreventUpdate

    # Get country parameters
    # Use .get() with a default to prevent KeyError if selected_country_value is unexpected
    country_params = COUNTRY_CODES.get(
        selected_country_value, COUNTRY_CODES['United States'])
    hl = country_params['hl']
    gl = country_params['gl']
    ceid = country_params['ceid']

    news_elements = []  # Initialize news_elements to an empty list

    if current_search_mode == 'default':
        # In default mode, get general top news for the selected country
        url = f"https://news.google.com/rss?hl={hl}-{gl}&gl={gl}&ceid={ceid}"
        # Debugging
        print(
            f"Fetching default news for {selected_country_value} from URL: {url}")
        top_headlines = top_news(url)
        news_elements = [create_news_item_component(
            article['title'], article['link']) for article in top_headlines]

    elif current_search_mode == 'custom':
        # In custom mode, use the last searched query with the new country
        if last_searched_query:  # Check if there's actually a query to search for
            # Ensure the query is URL-encoded if it contains spaces or special characters
            # requests.get will handle this mostly, but for constructing the URL,
            # it's good practice to ensure it's clean for the 'q' parameter.
            # However, Google News RSS often handles spaces naturally with just '+'
            # Let's revert to last_searched_query directly for query part, as it's cleaner.
            cleaned_input_for_url = last_searched_query.strip().replace(
                ' ', '+')  # Replace spaces with '+'

            url = f"https://news.google.com/rss/search?q={cleaned_input_for_url}&hl={hl}&gl={gl}&ceid={ceid}"
            # Debugging
            print(
                f"Fetching custom news for '{last_searched_query}' in {selected_country_value} from URL: {url}")
            top_headlines = top_news(url)
            news_elements = [create_news_item_component(
                article['title'], article['link']) for article in top_headlines]
        else:
            # If no last custom query exists, show a message
            news_elements = html.Div(
                dbc.Alert("No custom search query available. Please perform a custom search first.",
                          color="info", className="mt-3"),
                style={'text-align': 'center'}
            )
            print("No last custom query, showing message.")  # Debugging
    else:
        # This case should ideally not happen if search-mode-store is well-managed
        news_elements = html.Div(
            dbc.Alert("Unknown search mode. Please select Default or Custom search.",
                      color="danger", className="mt-3"),
            style={'text-align': 'center'}
        )
        # Debugging
        print(f"Unknown search mode encountered: {current_search_mode}")

    if not news_elements:  # If no news was fetched or an error occurred
        news_elements = html.Div(
            dbc.Alert("Could not fetch news for the selected country/query. Please try again.",
                      color="warning", className="mt-3"),
            style={'text-align': 'center'}
        )

    return news_elements


@app.callback(
    Output('keyword-table', 'data', allow_duplicate=True),
    Output('sentiment-line-graph', 'figure', allow_duplicate=True),
    Output('sentiment-pie-chart', 'figure', allow_duplicate=True),
    Output('news-bar', 'children', allow_duplicate=True),

    Input('time-dropdown', 'value'),
    Input('category-dropdown', 'value'),
    State("country-dropdown", "value"),
    prevent_initial_call=True
)
def time_and_cat_sort(selected_time_value, selected_category_value, selected_country):
    # This callback should ONLY run when in 'default' search mode
    # It must also be prevented if triggered while in 'custom' mode.

    # Handle initial None values if dropdowns can start empty
    # If your dropdowns always have a default value, this check might be less critical.
    if selected_time_value is None or selected_category_value is None:
        print("Time or Category dropdown value is None, preventing update.")
        raise dash.exceptions.PreventUpdate

    redis_key = f"{selected_time_value}_{selected_category_value}"
    data = client.get(redis_key)

    data = json.loads(data)

    # Dummy Data for Line Graph
    line_graph = data['line_graph']
    # timestamps = line_graph.keys()
    timestamps = [datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                  for ts_str in line_graph.keys()]
    sentiments = list(line_graph.values())
    df_line = pd.DataFrame({
        "Timestamp": timestamps,
        "Sentiment Score": sentiments
    })

    df = df_line.sort_values(by="Timestamp")
    fig_line = px.line(df, x="Timestamp", y="Sentiment Score", title="Overall Sentiment Trend",
                       markers=True, line_shape="linear")
    fig_line.update_layout(hovermode="x unified", template="plotly_white",
                           xaxis_rangeslider_visible=True)

    # Dummy Data for Pie Chart
    pie_chart = data['pie_chart']
    total = 0
    pie_data = [pie_chart['good'], pie_chart['okay'], pie_chart['bad']]
    for i in pie_data:
        total += i
    pie_data = [x / total * 100 for x in pie_data]
    pie_data = [int(round(x)) for x in pie_data]
    df_pie = pd.DataFrame({
        "Sentiment": ["Positive", "Neutral", "Negative"],
        "Count": pie_data
    })
    fig_pie = px.pie(df_pie, names="Sentiment", values="Count", title="Sentiment Distribution",
                     color_discrete_map={'Positive': '#28a745', 'Neutral': '#ffc107', 'Negative': '#dc3545'})
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    fig_pie.update_layout(showlegend=True)

    # Dummy Data for Table
    top_sources = data['top_sources']
    sources = []
    article_counts = []
    avg_sentiments = []

    for i in top_sources:
        sources.append(i['source'])
        article_counts.append(i['article_count'])
        avg_sentiments.append(i['avg_sentiment'])

    df_table = pd.DataFrame({
        "Sources": sources,
        "Art. Count": article_counts,
        "Avg. Sentiment": avg_sentiments
    })

    df_table_json = df_table.to_dict('records')
    # Dummy News Articles for Scrollable Feed

    country_params = COUNTRY_CODES.get(
        selected_country, COUNTRY_CODES['United States'])
    hl = country_params['hl']
    gl = country_params['gl']
    ceid = country_params['ceid']

    url = f"https://news.google.com/rss/search?q={selected_category_value}&hl={hl}-{gl}&gl={gl}&ceid={ceid}"
    if selected_category_value == "summary":
        url = f"https://news.google.com/rss?hl={hl}-{gl}&gl={gl}&ceid={ceid}"

    news_articles = top_news(url)
    news_elements = [create_news_item_component(
        article['title'], article['link']) for article in news_articles]

    return (
        df_table_json,
        fig_line,
        fig_pie,
        news_elements
    )


@asynccontextmanager
async def lifespan(app: WsgiToAsgi) -> AsyncGenerator[None, None]:
    """
    Manage the startup and shutdown of the scheduler alongside the ASGI app.
    """
    try:
        await startup_function()  # Start the scheduler before the app
        logger.info("Application startup completed")
        yield
    finally:
        await shutdown_function()  # Shut down the scheduler after the app
        logger.info("Application shutdown completed")


def get_lifespan():
    """Return the lifespan context manager for Uvicorn."""
    return lifespan(asgi_app)


async def main():
    config = uvicorn.Config(asgi_app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    try:
        await startup_function()  # Run startup tasks
        logger.info("Application startup completed")
        await server.serve()      # Start the server
    finally:
        await shutdown_function()  # Ensure shutdown tasks run
        logger.info("Application shutdown completed")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        pass
    # uvicorn.run(
    #     asgi_app,  # Use the ASGI-wrapped Dash app
    #     host="0.0.0.0",
    #     port=8000,
    #     # lifespan="on",  # Enable lifespan events
    #     lifespan=get_lifespan)


# # Run the App
# if __name__ == '__main__':

#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)

#     # Schedule the main() task
#     loop.create_task(main())

    # app.run()

# @app.callback(
#     Output('news-bar', 'children', allow_duplicate=True),
#     Input("country-dropdown", "value"),
#     State("search-mode", "data"),
#     State("last-searched-query-store", "data"),
#    prevent_initial_call=True
# )
# def top_news_in_country(search_mode, country_val, last_searched):

#     COUNTRY_CODES = {
#         'United States': {'gl': 'US', 'hl': 'en', 'ceid': 'US:en'},
#         'Canada': {'gl': 'CA', 'hl': 'en', 'ceid': 'CA:en'},
#         'United Kingdom': {'gl': 'GB', 'hl': 'en', 'ceid': 'GB:en'},
#         # English news from Germany
#         'Germany': {'gl': 'DE', 'hl': 'en', 'ceid': 'DE:en'},
#         'Australia': {'gl': 'AU', 'hl': 'en', 'ceid': 'AU:en'},
#         # 5 Most Popular Countries added
#         'India': {'gl': 'IN', 'hl': 'en', 'ceid': 'IN:en'},
#         # English news from France
#         'France_en': {'gl': 'FR', 'hl': 'en', 'ceid': 'FR:en'},
#         # English news from Japan
#         'Japan_en': {'gl': 'JP', 'hl': 'en', 'ceid': 'JP:en'},
#         # English news from Brazil
#         'Brazil_en': {'gl': 'BR', 'hl': 'en', 'ceid': 'BR:en'},
#         # English news from China
#         'China_en': {'gl': 'CN', 'hl': 'en', 'ceid': 'CN:en'},
#         # Countries you specifically asked about
#         'Nigeria': {'gl': 'NG', 'hl': 'en', 'ceid': 'NG:en'},
#         'Netherlands_en': {'gl': 'NL', 'hl': 'en', 'ceid': 'NL:en'},
#         # Dutch news for Netherlands
#         'Netherlands_nl': {'gl': 'NL', 'hl': 'nl', 'ceid': 'NL:nl'},
#         'Zambia': {'gl': 'ZM', 'hl': 'en', 'ceid': 'ZM:en'},
#     }
#     hl = COUNTRY_CODES[country_val]['hl']
#     gl = COUNTRY_CODES[country_val]['gl']
#     ceid = COUNTRY_CODES[country_val]['ceid']
#     if search_mode == 'default':
#         url = f"https://news.google.com/rss?hl={hl}&gl={gl}&ceid={ceid}"
#     else:
#         cleaned_input = last_searched.split()
#         cleaned_input = ''.join(cleaned_input)

#         url = f"https://news.google.com/rss/search?q={cleaned_input}&hl={hl}&gl={gl}&ceid={ceid}"
#     top_headlines = top_news(url)
#     news_elements = [create_news_item_component(
#         article['title'], article['link']) for article in top_headlines]
#     return news_elements
# --- 5. Run the App ---
# from dash import Dash, html, dcc, Input, Output, callback
# import pandas as pd
# import plotly.express as px

# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# app = Dash(__name__, external_stylesheets=external_stylesheets)

# df = pd.read_csv('https://plotly.github.io/datasets/country_indicators.csv')


# app.layout = html.Div([
#     html.Div([

#         html.Div([
#             dcc.Dropdown(
#                 df['Indicator Name'].unique(),
#                 'Fertility rate, total (births per woman)',
#                 id='crossfilter-xaxis-column',
#             ),
#             dcc.RadioItems(
#                 ['Linear', 'Log'],
#                 'Linear',
#                 id='crossfilter-xaxis-type',
#                 labelStyle={'display': 'inline-block', 'marginTop': '5px'}
#             )
#         ],
#             style={'width': '49%', 'display': 'inline-block'}),

#         html.Div([
#             dcc.Dropdown(
#                 df['Indicator Name'].unique(),
#                 'Life expectancy at birth, total (years)',
#                 id='crossfilter-yaxis-column'
#             ),
#             dcc.RadioItems(
#                 ['Linear', 'Log'],
#                 'Linear',
#                 id='crossfilter-yaxis-type',
#                 labelStyle={'display': 'inline-block', 'marginTop': '5px'}
#             )
#         ], style={'width': '49%', 'float': 'right', 'display': 'inline-block'})
#     ], style={
#         'padding': '10px 5px'
#     }),

#     html.Div([
#         dcc.Graph(
#             id='crossfilter-indicator-scatter',
#             hoverData={'points': [{'customdata': 'Japan'}]}
#         )
#     ], style={'width': '49%', 'display': 'inline-block', 'padding': '0 20'}),
#     html.Div([
#         dcc.Graph(id='x-time-series'),
#         dcc.Graph(id='y-time-series'),
#     ], style={'display': 'inline-block', 'width': '49%'}),

#     html.Div(dcc.Slider(
#         df['Year'].min(),
#         df['Year'].max(),
#         step=None,
#         id='crossfilter-year--slider',
#         value=df['Year'].max(),
#         marks={str(year): str(year) for year in df['Year'].unique()}
#     ), style={'width': '49%', 'padding': '0px 20px 20px 20px'})
# ])


# @callback(
#     Output('crossfilter-indicator-scatter', 'figure'),
#     Input('crossfilter-xaxis-column', 'value'),
#     Input('crossfilter-yaxis-column', 'value'),
#     Input('crossfilter-xaxis-type', 'value'),
#     Input('crossfilter-yaxis-type', 'value'),
#     Input('crossfilter-year--slider', 'value'))
# def update_graph(xaxis_column_name, yaxis_column_name,
#                  xaxis_type, yaxis_type,
#                  year_value):
#     dff = df[df['Year'] == year_value]

#     fig = px.scatter(x=dff[dff['Indicator Name'] == xaxis_column_name]['Value'],
#                      y=dff[dff['Indicator Name'] ==
#                            yaxis_column_name]['Value'],
#                      hover_name=dff[dff['Indicator Name'] ==
#                                     yaxis_column_name]['Country Name']
#                      )

#     fig.update_traces(
#         customdata=dff[dff['Indicator Name'] == yaxis_column_name]['Country Name'])

#     fig.update_xaxes(title=xaxis_column_name,
#                      type='linear' if xaxis_type == 'Linear' else 'log')

#     fig.update_yaxes(title=yaxis_column_name,
#                      type='linear' if yaxis_type == 'Linear' else 'log')

#     fig.update_layout(
#         margin={'l': 40, 'b': 40, 't': 10, 'r': 0}, hovermode='closest')

#     return fig


# def create_time_series(dff, axis_type, title):

#     fig = px.scatter(dff, x='Year', y='Value')

#     fig.update_traces(mode='lines+markers')

#     fig.update_xaxes(showgrid=False)

#     fig.update_yaxes(type='linear' if axis_type == 'Linear' else 'log')

#     fig.add_annotation(x=0, y=0.85, xanchor='left', yanchor='bottom',
#                        xref='paper', yref='paper', showarrow=False, align='left',
#                        text=title)

#     fig.update_layout(height=225, margin={'l': 20, 'b': 30, 'r': 10, 't': 10})

#     return fig


# @callback(
#     Output('x-time-series', 'figure'),
#     Input('crossfilter-indicator-scatter', 'hoverData'),
#     Input('crossfilter-xaxis-column', 'value'),
#     Input('crossfilter-xaxis-type', 'value'))
# def update_x_timeseries(hoverData, xaxis_column_name, axis_type):
#     country_name = hoverData['points'][0]['customdata']
#     dff = df[df['Country Name'] == country_name]
#     dff = dff[dff['Indicator Name'] == xaxis_column_name]
#     title = '<b>{}</b><br>{}'.format(country_name, xaxis_column_name)
#     return create_time_series(dff, axis_type, title)


# @callback(
#     Output('y-time-series', 'figure'),
#     Input('crossfilter-indicator-scatter', 'hoverData'),
#     Input('crossfilter-yaxis-column', 'value'),
#     Input('crossfilter-yaxis-type', 'value'))
# def update_y_timeseries(hoverData, yaxis_column_name, axis_type):
#     dff = df[df['Country Name'] == hoverData['points'][0]['customdata']]
#     dff = dff[dff['Indicator Name'] == yaxis_column_name]
#     return create_time_series(dff, axis_type, yaxis_column_name)


# if __name__ == '__main__':
#     app.run(debug=True)


# from dash_extensions.enrich import DashProxy, Output, Input, MultiplexerTransform
# from dash.dependencies import ClientsideFunction
# # import dash
# # from dash import dcc, html, Input, Output
# from dash_extensions.enrich import Input, Output, html, dcc
# import plotly.express as px
# import redis.asyncio as redis
# import json
# import pandas as pd
# import asyncio
# import os
# from dotenv import load_dotenv
# # from .scheduler import scheduler

# from apscheduler.schedulers.asyncio import AsyncIOScheduler
# from apscheduler.triggers.cron import CronTrigger
# from apscheduler.triggers.interval import IntervalTrigger
# from app.scheduled.delete_old_news import delete_old_news_articles
# from app.scheduled.store_in_redis import store_data_in_redis
# from .store_in_db import store_in_db

# # Load environment and set up Redis
# load_dotenv()
# REDIS_URL = os.getenv("REDIS_URL")
# redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# CATEGORY_KEYS = {
#     'world': 'world',
#     'business': 'business',
#     'sci_tech': 'sci_tech',
#     'sports': 'sports'
# }


# def get_summary_key(time_range, category):
#     if category:
#         return f"{time_range}_{category}"
#     return f"{time_range}_summary"

# # Async data fetch wrappers for Redis


# async def fetch_summary_data(time_range, category):
#     key = get_summary_key(time_range, category)
#     raw = await redis_client.get(key)
#     return json.loads(raw) if raw else {}


# async def fetch_headlines(category):
#     raw = await redis_client.get("headline_news")
#     if not raw:
#         return []
#     all_headlines = json.loads(raw)
#     return all_headlines.get(category, [])

# # Initialize Dash app
# app = DashProxy(__name__, transforms=[MultiplexerTransform()])
# app.title = "News Sentiment Dashboard"

# # Layout
# app.layout = html.Div([
#     html.H1("News Sentiment Dashboard"),

#     html.Div([
#         html.Label("Time Range"),
#         dcc.Dropdown(
#             id='time-filter',
#             options=[
#                 {'label': 'Last Week', 'value': 'weekly'},
#                 {'label': 'Last Month', 'value': 'monthly'}
#             ],
#             value='weekly'
#         ),
#     ], style={'width': '48%', 'display': 'inline-block'}),

#     html.Div([
#         html.Label("Category"),
#         dcc.Dropdown(
#             id='category-filter',
#             options=[
#                 {'label': 'World', 'value': 'world'},
#                 {'label': 'Business', 'value': 'business'},
#                 {'label': 'Sci/Tech', 'value': 'sci_tech'},
#                 {'label': 'Sports', 'value': 'sports'}
#             ],
#             value='world'
#         ),
#     ], style={'width': '48%', 'display': 'inline-block'}),

#     dcc.Graph(id='line-chart'),
#     dcc.Graph(id='pie-chart'),

#     html.H3("Top News Sources"),
#     html.Div(id='news-sources-table'),

#     html.H3("Top Headlines"),
#     html.Div(id='headlines-section')
# ])

# # Async callback pattern using dash-extensions for coroutine support


# @app.callback(
#     Output('line-chart', 'figure'),
#     Output('pie-chart', 'figure'),
#     Output('news-sources-table', 'children'),
#     Output('headlines-section', 'children'),
#     Input('time-filter', 'value'),
#     Input('category-filter', 'value')
# )
# def update_dashboard(time_range, category):
#     # Coroutine wrapper to handle async redis reads
#     loop = asyncio.get_event_loop()
#     summary, headlines = loop.run_until_complete(asyncio.gather(
#         fetch_summary_data(time_range, category),
#         fetch_headlines(category)
#     ))

#     if not summary:
#         empty_fig = px.line(title="No Data Available")
#         return empty_fig, empty_fig, html.P("No data available."), html.P("No data available.")

#     # Line Chart
#     line_df = pd.DataFrame(summary['line_graph'])
#     line_fig = px.line(line_df, x='date', y='avg_sentiment',
#                        title='Average Sentiment Over Time')

#     # Pie Chart
#     pie_data = pd.DataFrame.from_dict(
#         summary['pie_chart'], orient='index', columns=['count']).reset_index()
#     pie_data.columns = ['Sentiment', 'Count']
#     pie_fig = px.pie(pie_data, names='Sentiment',
#                      values='Count', title='Sentiment Distribution')

#     # Top News Sources Table
#     sources_df = pd.DataFrame(summary['top_sources'])
#     sources_table = html.Table([
#         html.Thead(html.Tr([html.Th(col) for col in [
#                    'Source', 'Article Count', 'Avg. Sentiment']])),
#         html.Tbody([
#             html.Tr([
#                 html.Td(row['source']),
#                 html.Td(row['article_count']),
#                 html.Td(f"{row['avg_sentiment']:.2f}")
#             ]) for _, row in sources_df.iterrows()
#         ])
#     ])

#     # Headlines List
#     headlines_section = html.Ul([
#         html.Li(f"{item['title']} ({item['source']})") for item in headlines[:5]
#     ])

#     return line_fig, pie_fig, sources_table, headlines_section


# async def delete_old_news():
#     print("Async: Deleting old news...")
#     await delete_old_news_articles()


# async def periodic_task():
#     print("Async: Running periodic task...")
#     await store_in_db()               # Wait until DB storing finishes
#     await store_data_in_redis()       # Then store in Redis

# # Initialize AsyncIOScheduler
# scheduler = AsyncIOScheduler()

# # Add jobs directly without wrap_async
# scheduler.add_job(delete_old_news, CronTrigger(
#     hour=0, minute=0), id='daily_cleanup')
# scheduler.add_job(periodic_task, IntervalTrigger(hours=6), id='six_hour_job')


# if __name__ == '__main__':
#     # scheduler.start()
#     # print("scheduler started")

#     app.run(debug=True)
