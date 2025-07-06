from dotenv import load_dotenv
import os
from pathlib import Path  # Import Path

# ... (other imports) ...

# Define the base directory (where your main.py and .env file should be relative to)
# Assuming this script is in NEWS_DASHBOARD/app/
BASE_DIR = Path(__file__).resolve().parent.parent
# If the .env is directly in NEWS_DASHBOARD/, then BASE_DIR is just Path(__file__).resolve().parent.parent

# Adjust this if .env is in root or elsewhere
dotenv_path = BASE_DIR / 'app' / '.env'
# print(f"DEBUG: Looking for .env at: {dotenv_path}") # Optional debug print

load_dotenv(dotenv_path)
NEWSAPI_KEY = os.getenv("NEWS_API_KEY")
print(f"DEBUG: NEWSAPI_KEY loaded: {NEWSAPI_KEY}")

# import dash
# from dash.dependencies import Input, Output, State, ALL
# import dash_bootstrap_components as dbc
# from dash import dcc, html, dash_table
# import plotly.express as px
# import pandas as pd
# import numpy as np
# from urllib.parse import urlparse
# from datetime import date, timedelta
# # Import this for theme integration
# from dash_bootstrap_templates import load_figure_template

# # --- 1. Prepare Dummy Data (Same as before) ---
# # Dropdown Options
# time_options = [
#     {'label': 'Month', 'value': 'month'},
#     {'label': 'Week', 'value': 'week'}
# ]

# category_options = [
#     {'label': 'None', 'value': 'none'},
#     {'label': 'Business', 'value': 'business'},
#     {'label': 'World', 'value': 'world'},
#     {'label': 'Sports', 'value': 'sports'},
#     {'label': 'Sci/Tech', 'value': 'sci_tech'}
# ]

# country_options = [
#     {'label': 'USA', 'value': 'usa'},
#     {'label': 'Canada', 'value': 'canada'},
#     {'label': 'UK', 'value': 'uk'},
#     {'label': 'Germany', 'value': 'germany'},
#     {'label': 'Australia', 'value': 'australia'}
# ]

# preferred_category_options = [  # Re-added this as it was in previous versions
#     {'label': 'None', 'value': 'none'},
#     {'label': 'Business', 'value': 'business'},
#     {'label': 'Sports', 'value': 'sports'},
#     {'label': 'Sci/Tech', 'value': 'sci_tech'},
#     {'label': 'World', 'value': 'world'},
# ]


# # Dummy Data for Line Graph
# df_line = pd.DataFrame({
#     "Date": pd.to_datetime(pd.date_range(start="2025-05-27", periods=30, freq="D")),
#     "Sentiment Score": [
#         float(f"{x:.2f}") for x in (
#             (pd.Series(range(30)) * 0.1) +
#             (pd.Series(np.random.rand(30)) * 0.5) +
#             # Adjusted sin multiplier for less extreme swings
#             (np.sin(np.linspace(0, 4 * np.pi, 30)) * 0.5) + 0.5
#         )
#     ]
# })
# fig_line = px.line(df_line, x="Date", y="Sentiment Score", title="Overall Sentiment Trend",
#                    markers=True, line_shape="linear")
# # Template set to white as per user's last provided code
# fig_line.update_layout(hovermode="x unified", template="plotly_white")

# # Dummy Data for Pie Chart
# df_pie = pd.DataFrame({
#     "Sentiment": ["Positive", "Neutral", "Negative"],
#     "Count": [45, 30, 25]
# })
# fig_pie = px.pie(df_pie, names="Sentiment", values="Count", title="Sentiment Distribution",
#                  color_discrete_map={'Positive': '#28a745', 'Neutral': '#ffc107', 'Negative': '#dc3545'})
# fig_pie.update_traces(textposition='inside', textinfo='percent+label')
# fig_pie.update_layout(showlegend=True)

# # Dummy Data for Table
# df_table = pd.DataFrame({
#     "Keyword": ["Inflation", "AI", "Elections", "Climate", "Healthcare"],
#     "Mentions": [1500, 1200, 900, 750, 600],
#     "Avg. Sentiment": [0.65, 0.72, 0.45, 0.58, 0.61]
# })

# # Dummy News Articles for Scrollable Feed
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
#         "link": "https://www.startupinsights.co/funding/promising-fintech-startup-securhttps://www.startupinsights.co/funding/promising-fintech-startup-secures-oversubscribed-series-b-funding-round-for-expansion.html"},
#     {"title": "Major Sports Event Kicks Off This Weekend",
#         "link": "https://www.sportseverywhere.com/events/annual-international-sports-tournament-kicks-off-this-weekend-full-schedule-and-athlete-profiles.html"},
#     {"title": "Health Organization Issues New Guidelines",
#         "link": "https://www.healthnewsdaily.org/public-health/major-health-organization-issues-new-public-health-guidelines-for-seasonal-illnesses.html"},
#     {"title": "Cultural Festival Draws Record Crowds",
#         "link": "https://www.artsculturemagazine.com/festival-reviews/annual-cultural-arts-festival-draws-record-breaking-crowds-and-acclaim.html"},
# ]


# def create_news_item_component(title, link):
#     parsed_uri = urlparse(link)
#     domain = parsed_uri.netloc
#     link_display_text = domain.replace('www.', '')
#     return html.Div([
#         html.P(html.B(title), style={
#                'margin-bottom': '5px', 'line-height': '1.2'}),
#         html.A(link_display_text, href=link, target="_blank",
#                style={'font-size': '0.85em', 'color': '#007bff', 'word-break': 'break-all'}),
#         html.Hr(style={'margin-top': '10px', 'margin-bottom': '10px',
#                 'border-top': '1px dashed #ced4da'})
#     ], style={'padding': '5px 0'})


# news_elements = [create_news_item_component(
#     article['title'], article['link']) for article in news_articles]


# # --- 2. Initialize Dash App ---
# # Changed theme to VAPOR for better dropdown readability as per previous conversation
# # SELECTED_THEME = dbc.themes.VAPOR # Or dbc.themes.SOLAR, etc. based on preference.
# SELECTED_THEME = dbc.themes.BOOTSTRAP

# app = dash.Dash(__name__, external_stylesheets=[
#                 dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME])
# # Integrates theme with plotly figures
# # load_figure_template(SELECTED_THEME.lower().split('/')[-1].split('.')[0])


# # --- 3. Define Dashboard Layout ---
# app.layout = dbc.Container([

#     # Row 1: Dashboard Title
#     dbc.Row(
#         dbc.Col(
#             html.H1("GLOBAL NEWS SENTIMENT DASHBOARD",
#                     className="text-center my-4 display-4 text-primary"),
#             width=12
#         )
#     ),

#     # Placeholder for the dynamically added input box AND its search button
#     dbc.Row(
#         dbc.Col(
#             html.Div([
#                 html.Div(id='custom-search-input-container'),
#                 # To display search query for demonstration
#                 html.Div(id='custom-search-output')
#             ]),
#             width=12
#         ),
#         className="mb-3"
#     ),

#     # Row 2: Filters (Dropdowns) with new button
#     dbc.Row([
#         # Button for Offcanvas
#         dbc.Col(
#             dbc.Button(
#                 [html.I(className="fa-solid fa-gears me-2"),
#                  "Search Options"],
#                 id="open-options-offcanvas",
#                 color="info",
#                 className="mb-3"
#             ),
#             width="auto",
#             align="end",
#             className="d-flex align-items-end"
#         ),
#         dbc.Col(
#             html.Div([
#                 # Added text-light for dark theme
#                 html.Label("News in the last:",
#                            className="mb-2 lead text-light"),
#                 dcc.Dropdown(
#                     id='time-dropdown',
#                     options=time_options,
#                     value='month',
#                     clearable=False,
#                     className="mb-3"
#                 )
#             ]),
#             md=4,
#             className="d-flex align-items-center justify-content-center flex-column"
#         ),
#         dbc.Col(
#             html.Div([
#                 # Added text-light for dark theme
#                 html.Label("Specific Category:",
#                            className="mb-2 lead text-light"),
#                 dcc.Dropdown(
#                     id='category-dropdown',
#                     options=category_options,
#                     value='none',
#                     clearable=False,
#                     className="mb-3"
#                 )
#             ]),
#             md=4,
#             className="d-flex align-items-center justify-content-center flex-column"
#         )
#     ], justify="center", className="mb-5"),

#     # dbc.Offcanvas for search options
#     dbc.Offcanvas(
#         id="offcanvas-search-options",
#         title="Search Settings",
#         is_open=False,
#         placement="start",
#         children=[
#             # Added text-light for dark theme
#             html.P("Choose your search mode:", className="text-light"),
#             dbc.Row([
#                 dbc.Col(
#                     dbc.Button("Default Search", id="default-search-button",
#                                color="primary", size="lg", className="me-2 w-100"),
#                     className="mb-2"
#                 ),
#                 dbc.Col(
#                     dbc.Button("Custom Search", id="custom-search-button",
#                                color="success", size="lg", className="w-100"),
#                 )
#             ], className="g-2")
#         ]
#     ),

#     # Row 3: Graphs (Line Chart and Pie Chart)
#     dbc.Row([
#         dbc.Col(
#             dbc.Card([
#                 # Added text-white bg-dark for dark theme
#                 dbc.CardHeader("Sentiment Trend Over Time",
#                                className="h5 text-white bg-dark"),
#                 dbc.CardBody(
#                     dcc.Graph(id='sentiment-line-graph', figure=fig_line)
#                 )
#             ], className="shadow-sm border-0 bg-dark"),  # Added bg-dark for dark theme
#             md=6,
#             className="mb-4"
#         ),
#         dbc.Col(
#             dbc.Card([
#                 dbc.CardHeader("Overall Sentiment Distribution",
#                                className="h5 text-white bg-dark"),  # Added text-white bg-dark for dark theme
#                 dbc.CardBody(
#                     dcc.Graph(id='sentiment-pie-chart', figure=fig_pie)
#                 )
#             ], className="shadow-sm border-0 bg-dark"),  # Added bg-dark for dark theme
#             md=6,
#             className="mb-4"
#         )
#     ], className="mb-5"),

#     # Row 4: Table and Scrollable News
#     dbc.Row([
#         dbc.Col(
#             dbc.Card([
#                 # Added text-white bg-dark for dark theme
#                 dbc.CardHeader("Top Keywords & Sentiment",
#                                className="h5 text-white bg-dark"),
#                 dbc.CardBody(
#                     dash_table.DataTable(
#                         id='keyword-table',
#                         columns=[{"name": i, "id": i}
#                                  for i in df_table.columns],
#                         data=df_table.to_dict('records'),
#                         # Adjusted for dark theme
#                         style_table={
#                             'overflowX': 'auto', 'backgroundColor': '#343a40', 'color': 'white'},
#                         style_header={
#                             'backgroundColor': '#495057',  # Adjusted for dark theme
#                             'fontWeight': 'bold',
#                             'color': 'white'  # Ensure header text is white
#                         },
#                         style_data_conditional=[
#                             {'if': {'row_index': 'odd'},
#                              'backgroundColor': '#3b4248'},  # Adjusted for dark theme
#                         ],
#                         style_cell={
#                             'backgroundColor': '#343a40',  # Adjusted for dark theme
#                             'color': 'white',  # Ensure cell text is white
#                             'border': '1px solid #495057'  # Adjusted for dark theme
#                         },
#                         export_headers='display',
#                         export_format='xlsx'
#                     )
#                 )
#             ], className="shadow-sm border-0 bg-dark"),  # Added bg-dark for dark theme
#             md=6,
#             className="mb-4"
#         ),
#         dbc.Col(
#             dbc.Card([
#                 dbc.CardHeader(
#                     dbc.Row([
#                         dbc.Col(
#                             html.Div([
#                                 # Added text-white for dark theme
#                                 html.Span("Top News in ",
#                                           className="h5 text-white"),
#                                 dcc.Dropdown(
#                                     id='country-dropdown',
#                                     options=country_options,
#                                     value='usa',
#                                     clearable=False,
#                                     className="flex-grow-1"
#                                 )
#                             ], className="d-flex align-items-center"),
#                             md=6,
#                             className="p-0"
#                         ),
#                         dbc.Col(
#                             html.Div([
#                                 # Added text-white for dark theme
#                                 html.Span(
#                                     "Category:", className="h5 text-white"),
#                                 dcc.Dropdown(
#                                     # Ensure this ID matches the one in preferred_category_options
#                                     id='preferred-category-dropdown',
#                                     options=preferred_category_options,  # Using the new options list
#                                     value='none',
#                                     clearable=False,
#                                     className="flex-grow-1"
#                                 )
#                             ], className="d-flex align-items-center"),
#                             md=6,
#                             className="p-0"
#                         )
#                     ], align="center", className="g-2")
#                 ),
#                 dbc.CardBody(
#                     html.Div(
#                         news_elements,
#                         style={
#                             'height': '350px',
#                             'overflowY': 'scroll',
#                             'border': '1px solid #495057',  # Adjusted for dark theme
#                             'padding': '10px',
#                             'border-radius': '0.25rem',
#                             'background-color': '#343a40'  # Adjusted for dark theme
#                         }
#                     ),
#                     className="p-0"
#                 )
#             ], className="shadow-sm border-0 bg-dark"),  # Added bg-dark for dark theme
#             md=6,
#             className="mb-4"
#         )
#     ], className="mb-4")

#     # Added bg-secondary text-light for overall dark theme
# ], fluid=True, className="p-4 bg-secondary text-light")


# # --- 4. Callbacks for Offcanvas and Dynamic Content ---

# # Callback to open/close the offcanvas
# @app.callback(
#     Output("offcanvas-search-options", "is_open"),
#     Input("open-options-offcanvas", "n_clicks"),
#     State("offcanvas-search-options", "is_open"),
#     prevent_initial_call=True
# )
# def toggle_offcanvas(n_clicks, is_open):
#     if n_clicks:
#         return not is_open
#     return is_open


# # Callback for Custom Search / Default Search buttons
# @app.callback(
#     Output("custom-search-input-container", "children"),
#     Output("time-dropdown", "disabled"),
#     Output("time-dropdown", "value"),
#     Output("category-dropdown", "disabled"),
#     Output("category-dropdown", "value"),
#     Output("offcanvas-search-options", "is_open", allow_duplicate=True),
#     Input("custom-search-button", "n_clicks"),
#     Input("default-search-button", "n_clicks"),
#     prevent_initial_call=True
# )
# def handle_search_mode(custom_clicks, default_clicks):
#     ctx = dash.callback_context
#     if not ctx.triggered_id:
#         raise dash.exceptions.PreventUpdate

#     triggered_id = ctx.triggered_id

#     input_group = None
#     time_disabled = False
#     time_value = 'month'
#     category_disabled = False
#     category_value = 'none'
#     offcanvas_open = False

#     if triggered_id == "custom-search-button":
#         input_group = dbc.InputGroup(
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
#         time_value = None
#         category_disabled = True
#         category_value = None
#     elif triggered_id == "default-search-button":
#         pass

#     return input_group, time_disabled, time_value, category_disabled, category_value, offcanvas_open

# # New Callback for the custom search button


# @app.callback(
#     # Display output below the input
#     Output("custom-search-output", "children"),
#     Input("apply-custom-search", "n_clicks"),
#     State("custom-search-query-input", "value"),
#     prevent_initial_call=True
# )
# def perform_custom_search(n_clicks, search_query):
#     if n_clicks and search_query:
#         # In a real application, you'd process the search_query here
#         # and update your graphs/tables based on the result.
#         return html.Div(
#             dbc.Alert(f"Searching for: '{search_query}'...",
#                       color="success", className="mt-3"),
#             style={'text-align': 'center'}
#         )
#     elif n_clicks and not search_query:
#         return html.Div(
#             dbc.Alert("Please enter a search query.",
#                       color="warning", className="mt-3"),
#             style={'text-align': 'center'}
#         )
#     return ""


# # --- 5. Run the App ---
# if __name__ == '__main__':
#     # Changed from app.run to app.run_server for typical Dash usage
#     app.run(port=9000, debug=True)
