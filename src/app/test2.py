# import dash
# from dash.dependencies import Input, Output, State, ALL
# import dash_bootstrap_components as dbc
# from dash import dcc, html, dash_table
# import plotly.express as px
# import pandas as pd
# import numpy as np
# from urllib.parse import urlparse
# from datetime import date, timedelta
# from dash_bootstrap_templates import load_figure_template
# import time
# import requests
# import xml.etree.ElementTree as ET
# import redis # Import redis
# import json # For serializing/deserializing data to/from Redis
# from apscheduler.schedulers.background import BackgroundScheduler # For scheduling tasks

# # --- Redis Connection ---
# # Make sure to configure your Redis connection details
# # If Redis is running on localhost:6379 without password, this is usually sufficient.
# # Otherwise, adjust host, port, db, password.
# REDIS_HOST = 'localhost'
# REDIS_PORT = 6379
# REDIS_DB = 0
# REDIS_PASSWORD = None # Set to your password if applicable

# r = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password=REDIS_PASSWORD)

# # --- APScheduler Setup ---
# scheduler = BackgroundScheduler()

# # --- 1. Prepare Initial Data & Helper Functions ---

# # Dropdown Options (as before)
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

# country_options_list = [
#     {'label': 'United States', 'value': 'United States'},
#     {'label': 'Canada', 'value': 'Canada'},
#     {'label': 'United Kingdom', 'value': 'United Kingdom'},
#     {'label': 'Germany', 'value': 'Germany'},
#     {'label': 'Australia', 'value': 'Australia'},
#     {'label': 'India', 'value': 'India'},
#     {'label': 'France', 'value': 'France_en'}, # English news from France
#     {'label': 'Japan', 'value': 'Japan_en'}, # English news from Japan
#     {'label': 'Brazil', 'value': 'Brazil_en'}, # English news from Brazil
#     {'label': 'China', 'value': 'China_en'}, # English news from China (often limited, but useful for example)
#     {'label': 'Nigeria', 'value': 'Nigeria'},
#     {'label': 'Netherlands (English)', 'value': 'Netherlands_en'},
#     {'label': 'Netherlands (Dutch)', 'value': 'Netherlands_nl'},
#     {'label': 'Zambia', 'value': 'Zambia'},
# ]

# preferred_category_options = [
#     {'label': 'None', 'value': 'none'},
#     {'label': 'Business', 'value': 'business'},
#     {'label': 'Sports', 'value': 'sports'},
#     {'label': 'Sci/Tech', 'value': 'sci_tech'},
#     {'label': 'World', 'value': 'world'},
# ]

# COUNTRY_CODES = {
#     'United States': {'gl': 'US', 'hl': 'en', 'ceid': 'US:en'},
#     'Canada': {'gl': 'CA', 'hl': 'en', 'ceid': 'CA:en'},
#     'United Kingdom': {'gl': 'GB', 'hl': 'en', 'ceid': 'GB:en'},
#     'Germany': {'gl': 'DE', 'hl': 'en', 'ceid': 'DE:en'},
#     'Australia': {'gl': 'AU', 'hl': 'en', 'ceid': 'AU:en'},
#     'India': {'gl': 'IN', 'hl': 'en', 'ceid': 'IN:en'},
#     'France_en': {'gl': 'FR', 'hl': 'en', 'ceid': 'FR:en'},
#     'Japan_en': {'gl': 'JP', 'hl': 'en', 'ceid': 'JP:en'},
#     'Brazil_en': {'gl': 'BR', 'hl': 'en', 'ceid': 'BR:en'},
#     'China_en': {'gl': 'CN', 'hl': 'en', 'ceid': 'CN:en'},
#     'Nigeria': {'gl': 'NG', 'hl': 'en', 'ceid': 'NG:en'},
#     'Netherlands_en': {'gl': 'NL', 'hl': 'en', 'ceid': 'NL:en'},
#     'Netherlands_nl': {'gl': 'NL', 'hl': 'nl', 'ceid': 'NL:nl'},
#     'Zambia': {'gl': 'ZM', 'hl': 'en', 'ceid': 'ZM:en'},
# }


# # Helper for creating news item components (as before)
# def create_news_item_component(title, link):
#     parsed_uri = urlparse(link)
#     domain = parsed_uri.netloc
#     link_display_text = domain.replace('www.', '')
#     return html.Div([
#         html.P(html.B(title), style={'margin-bottom': '5px', 'line-height': '1.2'}),
#         html.A(link_display_text, href=link, target="_blank",
#                style={'font-size': '0.85em', 'color': '#007bff', 'word-break': 'break-all'}),
#         html.Hr(style={'margin-top': '10px', 'margin-bottom': '10px', 'border-top': '1px dashed #ced4da'})
#     ], style={'padding': '5px 0'})


# # --- 2. Data Fetching and Processing Functions (Updated) ---

# # This function will be called by APScheduler AND by get_data if cache is empty
# def fetch_and_process_news(query, country_gl, country_hl, country_ceid):
#     """
#     Fetches news from Google RSS, processes it (simulated), and returns structured data.
#     This function is responsible for the actual data logic.
#     """
#     print(f"--- Fetching and processing data for query: '{query}', country: {country_gl} ---")

#     rss_feed_url = ""
#     if query:
#         cleaned_query_for_url = query.strip().replace(' ', '+')
#         rss_feed_url = f"https://news.google.com/rss/search?q={cleaned_query_for_url}&hl={country_hl}-{country_gl}&gl={country_gl}&ceid={country_ceid}:{country_hl}"
#     else:
#         # For general news (default mode with no specific query)
#         rss_feed_url = f"https://news.google.com/rss?hl={country_hl}-{country_gl}&gl={country_gl}&ceid={country_ceid}:{country_hl}"

#     print(f"Fetching from URL: {rss_feed_url}")

#     # Step 1: Fetch raw RSS data
#     top_headlines_raw = top_news(rss_feed_url) # Using your top_news function here

#     # Step 2: Simulate further processing (sentiment, keywords, etc.)
#     # This is where your actual NLP/sentiment analysis/keyword extraction would go.
#     # For now, we'll continue with the dummy logic.

#     # Simulate sentiment trend over time
#     num_articles = len(top_headlines_raw) if top_headlines_raw else 10 # Ensure at least 10 for dummy data
#     dates = pd.to_datetime(pd.date_range(end=pd.Timestamp.now(), periods=num_articles, freq="-H")) # Last N hours
#     sentiments = np.random.rand(num_articles) * (0.8 if "good" in query.lower() else 0.4) - 0.2
#     sentiments = [float(f"{s:.2f}") for s in sentiments]

#     df_line_data = pd.DataFrame({
#         "Timestamp": dates,
#         "Sentiment Score": sentiments
#     })
#     # Convert Timestamp to string for JSON serialization
#     df_line_data['Timestamp'] = df_line_data['Timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')


#     # Simulate sentiment distribution (pie chart data)
#     if "positive" in query.lower():
#         pie_data = [70, 20, 10]
#     elif "negative" in query.lower():
#         pie_data = [10, 20, 70]
#     elif "neutral" in query.lower():
#         pie_data = [20, 60, 20]
#     else:
#         pie_data = [np.random.randint(20, 50), np.random.randint(20, 50), np.random.randint(20, 50)]
#         total = sum(pie_data)
#         pie_data = [x / total * 100 for x in pie_data] # Normalize to 100%
#         pie_data = [int(round(x)) for x in pie_data]


#     # Simulate keyword table data
#     keywords = ["Inflation", "AI", "Elections", "Climate", "Healthcare", "Economy", "Technology"]
#     num_keywords = min(5, len(top_headlines_raw) if top_headlines_raw else 5) # Max 5 keywords
#     df_table_data = pd.DataFrame({
#         "Keyword": np.random.choice(keywords, num_keywords, replace=False),
#         "Mentions": np.random.randint(500, 2000, num_keywords),
#         "Avg. Sentiment": np.random.rand(num_keywords) * 0.4 + 0.3 # Between 0.3 and 0.7
#     })
#     df_table_data["Avg. Sentiment"] = df_table_data["Avg. Sentiment"].apply(lambda x: float(f"{x:.2f}"))
#     table_data_dict = df_table_data.to_dict('records')


#     # Prepare top headlines for news bar
#     # Use top_headlines_raw directly, as it comes from top_news function
#     # Add a check to limit the number of articles if too many
#     top_headlines_for_display = top_headlines_raw[:min(len(top_headlines_raw), 15)] # Limit to 15 articles

#     return {
#         'line_graph': df_line_data.to_dict('records'),
#         'pie_chart': pie_data,
#         'keyword_table': table_data_dict,
#         'news_articles': top_headlines_for_display
#     }

# # Function to fetch data from Redis cache or generate if not found
# def get_data_from_cache_or_generate(query, country_gl, country_hl, country_ceid):
#     """
#     Retrieves processed news data from Redis cache. If not found,
#     it calls fetch_and_process_news and stores the result in Redis.
#     """
#     # Create a unique key for the cached data
#     cache_key = f"news_data:{query.lower()}:{country_gl.lower()}"

#     cached_data = r.get(cache_key)

#     if cached_data:
#         print(f"Data found in Redis cache for key: {cache_key}")
#         try:
#             data = json.loads(cached_data)
#             # Reconstruct DataFrame for line graph
#             data['line_graph'] = pd.DataFrame(data['line_graph'])
#             data['line_graph']['Timestamp'] = pd.to_datetime(data['line_graph']['Timestamp'])
#             return data['line_graph'], data['pie_chart'], data['keyword_table'], data['news_articles']
#         except json.JSONDecodeError as e:
#             print(f"Error decoding cached data for {cache_key}: {e}. Re-fetching.")
#             # Fall through to re-fetch
#     else:
#         print(f"Data not found in Redis cache for key: {cache_key}. Fetching and storing.")

#     # If data not in cache or decoding failed, fetch and store
#     processed_data = fetch_and_process_news(query, country_gl, country_hl, country_ceid)

#     # Store the processed data in Redis (convert DataFrames to list of dicts for JSON)
#     # Set an expiry time, e.g., 6 hours (6 * 3600 seconds)
#     # This expiry is a fallback in case APScheduler fails, ensuring data doesn't get too stale
#     r.setex(cache_key, 6 * 3600, json.dumps(processed_data)) # Store for 6 hours

#     # Return data in the format expected by callbacks
#     return (
#         pd.DataFrame(processed_data['line_graph']),
#         processed_data['pie_chart'],
#         processed_data['keyword_table'],
#         processed_data['news_articles']
#     )


# # --- APScheduler Job ---
# def scheduled_data_update():
#     """
#     This function is run by APScheduler to periodically update data in Redis.
#     It should iterate through common queries and countries to pre-populate cache.
#     """
#     print(f"--- Running scheduled data update at {pd.Timestamp.now()} ---")
#     # Define a list of common queries/countries to pre-fetch for
#     # This helps ensure popular searches are always fresh in cache
#     queries_to_update = [
#         ("economy", "United States"),
#         ("technology", "United States"),
#         ("climate change", "United States"),
#         ("sports", "United States"),
#         ("politics", "United States"),
#         ("economy", "Nigeria"),
#         ("technology", "Nigeria"),
#         ("politics", "Nigeria"),
#         ("default", "United States"), # For default general news
#         ("default", "Nigeria"), # For default general news in Nigeria
#         ("default", "United Kingdom"),
#         ("default", "Canada")
#         # Add more relevant queries and countries
#     ]

#     for query, country_name in queries_to_update:
#         country_params = COUNTRY_CODES.get(country_name)
#         if not country_params:
#             print(f"Warning: Country '{country_name}' not found in COUNTRY_CODES.")
#             continue

#         gl = country_params['gl']
#         hl = country_params['hl']
#         ceid = country_params['ceid']

#         # Determine the actual query string for the RSS fetch
#         fetch_query = query if query != "default" else "" # Use empty string for general news

#         try:
#             processed_data = fetch_and_process_news(fetch_query, gl, hl, ceid)
#             cache_key = f"news_data:{fetch_query.lower()}:{gl.lower()}"
#             r.setex(cache_key, 6 * 3600, json.dumps(processed_data))
#             print(f"Successfully updated cache for key: {cache_key}")
#         except Exception as e:
#             print(f"Error during scheduled update for '{query}' in {country_name}: {e}")

# # --- Initialize APScheduler ---
# # Run the scheduled_data_update function every 6 hours
# scheduler.add_job(scheduled_data_update, 'interval', hours=6)
# # You might want to run it once immediately on startup
# # scheduler.add_job(scheduled_data_update, 'date', run_date=pd.Timestamp.now() + pd.Timedelta(seconds=5))
# scheduler.start()


# # --- Initial Dashboard Data Loading ---
# # This ensures that when the app first loads, there's some data in Redis
# # for the default view without waiting for APScheduler's first run.
# # You could choose to call scheduled_data_update directly here,
# # or just populate for the initial default view.
# print("--- Populating initial default data into Redis if not present ---")
# initial_query = "" # For general news
# initial_country_name = "United States"
# initial_country_params = COUNTRY_CODES.get(initial_country_name)
# if initial_country_params:
#     initial_gl = initial_country_params['gl']
#     initial_hl = initial_country_params['hl']
#     initial_ceid = initial_country_params['ceid']
#     try:
#         # Use get_data_from_cache_or_generate to ensure it's in cache
#         initial_line_df, initial_pie_data, initial_table_data_list, initial_news_articles_list = \
#             get_data_from_cache_or_generate(initial_query, initial_gl, initial_hl, initial_ceid)

#         # Convert initial_line_df to dict for plotly express
#         fig_line_initial = px.line(initial_line_df, x="Timestamp", y="Sentiment Score", title="Overall Sentiment Trend",
#                                markers=True, line_shape="linear")
#         fig_line_initial.update_layout(hovermode="x unified", template="plotly_white", xaxis_title="Date and Time")

#         all_sentiments_initial = pd.DataFrame({
#             "Sentiment": ["Positive", "Neutral", "Negative"],
#             "Count": 0
#         })
#         current_pie_data_initial = pd.DataFrame({
#             "Sentiment": ["Positive", "Neutral", "Negative"],
#             "Count": initial_pie_data
#         })
#         df_pie_final_initial = pd.merge(all_sentiments_initial, current_pie_data_initial, on="Sentiment", how="left", suffixes=('_initial', '_actual'))
#         df_pie_final_initial["Count"] = df_pie_final_initial["Count_actual"].fillna(0).astype(int)
#         df_pie_final_initial = df_pie_final_initial[["Sentiment", "Count"]]

#         fig_pie_initial = px.pie(df_pie_final_initial, names="Sentiment", values="Count", title="Sentiment Distribution",
#                                  color_discrete_map={'Positive': '#28a745', 'Neutral': '#ffc107', 'Negative': '#dc3545'},
#                                  category_orders={"Sentiment": ["Positive", "Neutral", "Negative"]})
#         fig_pie_initial.update_traces(textposition='inside', textinfo='percent+label')
#         fig_pie_initial.update_layout(showlegend=True, title_x=0.5)


#         news_elements_initial = [create_news_item_component(article['title'], article['link']) for article in initial_news_articles_list]
#     except Exception as e:
#         print(f"Error during initial data load: {e}")
#         # Fallback to dummy data if Redis or fetch fails on startup
#         df_line_initial = pd.DataFrame({"Timestamp": pd.to_datetime([]), "Sentiment Score": []})
#         fig_line_initial = px.line(df_line_initial, x="Timestamp", y="Sentiment Score", title="Overall Sentiment Trend (No Data)",
#                                markers=True, line_shape="linear")
#         fig_line_initial.update_layout(hovermode="x unified", template="plotly_white")

#         fig_pie_initial = px.pie(names=["No Data"], values=[1], title="No Data Available")
#         fig_pie_initial.update_traces(marker=dict(colors=['#6c757d'])) # Gray for no data
#         initial_table_data_list = []
#         news_elements_initial = [html.Div(dbc.Alert("Failed to load initial data. Please check Redis/network.", color="danger"))]
# else:
#     # Fallback if initial_country_name not found (shouldn't happen with "United States")
#     print("Initial country 'United States' not found in COUNTRY_CODES.")
#     df_line_initial = pd.DataFrame({"Timestamp": pd.to_datetime([]), "Sentiment Score": []})
#     fig_line_initial = px.line(df_line_initial, x="Timestamp", y="Sentiment Score", title="Overall Sentiment Trend (No Data)",
#                            markers=True, line_shape="linear")
#     fig_line_initial.update_layout(hovermode="x unified", template="plotly_white")

#     fig_pie_initial = px.pie(names=["No Data"], values=[1], title="No Data Available")
#     fig_pie_initial.update_traces(marker=dict(colors=['#6c757d']))
#     initial_table_data_list = []
#     news_elements_initial = [html.Div(dbc.Alert("Failed to load initial data. Please check COUNTRY_CODES.", color="danger"))]


# # --- 2. Initialize Dash App ---
# SELECTED_THEME = dbc.themes.VAPOR

# app = dash.Dash(__name__, external_stylesheets=[
#     SELECTED_THEME,
#     dbc.icons.FONT_AWESOME
# ], suppress_callback_exceptions=True) # suppress_callback_exceptions is crucial here!


# # --- 3. Define Dashboard Layout ---
# app.layout = dbc.Container([
#     dcc.Store(id='last-searched-query-store', data=''),
#     dcc.Store(id='alert-visibility-store', data={'show': False, 'timestamp': None}),
#     dcc.Store(id='search-mode-store', data='default'),
#     dcc.Interval(
#         id='alert-interval',
#         interval=1000,
#         n_intervals=0,
#         disabled=True
#     ),

#     dbc.Row(
#         dbc.Col(
#             html.Div([
#                 html.Div(id='custom-search-input-container'),
#                 html.Div(id='custom-search-output')
#             ]),
#             width=12
#         ),
#         className="mb-3"
#     ),

#     dbc.Row(
#         dbc.Col(
#             html.H1("GLOBAL NEWS SENTIMENT DASHBOARD",
#                     className="text-center my-4 display-4 text-primary"),
#             width=12
#         )
#     ),

#     dbc.Row([
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
#                 html.Label("News in the last:", className="mb-2 lead text-light"),
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
#                 html.Label("Specific Category:", className="mb-2 lead text-light"),
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

#     dbc.Offcanvas(
#         id="offcanvas-search-options",
#         title="Search Settings",
#         is_open=False,
#         placement="start",
#         children=[
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

#     dbc.Row([
#         dbc.Col(
#             dbc.Card([
#                 dbc.CardHeader("Sentiment Trend Over Time", className="h5 text-white bg-dark"),
#                 dbc.CardBody(
#                     dcc.Graph(id='sentiment-line-graph', figure=fig_line_initial)
#                 )
#             ], className="shadow-sm border-0 bg-dark"),
#             md=6,
#             className="mb-4"
#         ),
#         dbc.Col(
#             dbc.Card([
#                 dbc.CardHeader("Overall Sentiment Distribution",
#                                className="h5 text-white bg-dark"),
#                 dbc.CardBody(
#                     dcc.Graph(id='sentiment-pie-chart', figure=fig_pie_initial)
#                 )
#             ], className="shadow-sm border-0 bg-dark"),
#             md=6,
#             className="mb-4"
#         )
#     ], className="mb-5"),

#     dbc.Row([
#         dbc.Col(
#             dbc.Card([
#                 dbc.CardHeader(
#                     dbc.Row([
#                         dbc.Col(html.Span("Top Keywords & Sentiment", className="h5 text-white"), width="auto"),
#                         dbc.Col(
#                             dbc.Button(
#                                 [html.I(className="fa-solid fa-eraser me-1"), "Clear Table"],
#                                 id="clear-table-button",
#                                 color="warning",
#                                 size="sm",
#                                 className="ms-auto"
#                             ),
#                             width="auto",
#                             className="d-flex align-items-center"
#                         )
#                     ], align="center", justify="between")
#                 ),
#                 dbc.CardBody(
#                     dash_table.DataTable(
#                         id='keyword-table',
#                         columns=[{"name": i, "id": i}
#                                  for i in pd.DataFrame(initial_table_data_list).columns] if initial_table_data_list else [],
#                         data=initial_table_data_list,
#                         style_table={'overflowX': 'auto', 'backgroundColor': '#343a40', 'color': 'white'},
#                         style_header={
#                             'backgroundColor': '#495057',
#                             'fontWeight': 'bold',
#                             'color': 'white'
#                         },
#                         style_data_conditional=[
#                             {'if': {'row_index': 'odd'},
#                              'backgroundColor': '#3b4248'},
#                         ],
#                         style_cell={
#                             'backgroundColor': '#343a40',
#                             'color': 'white',
#                             'border': '1px solid #495057'
#                         },
#                         export_headers='display',
#                         export_format='xlsx'
#                     )
#                 )
#             ], className="shadow-sm border-0 bg-dark"),
#             md=6,
#             className="mb-4"
#         ),
#         dbc.Col(
#             dbc.Card([
#                 dbc.CardHeader(
#                     dbc.Row([
#                         dbc.Col(
#                             html.Div([
#                                 html.Span("Top News in ", className="h5 text-white"),
#                                 dcc.Dropdown(
#                                     id='country-dropdown',
#                                     options=country_options_list,
#                                     value='United States',
#                                     clearable=False,
#                                     className="flex-grow-1"
#                                 )
#                             ], className="d-flex align-items-center"),
#                             md=6,
#                             className="p-0"
#                         ),
#                         dbc.Col(
#                             html.Div([
#                                 html.Span("Category:", className="h5 text-white"),
#                                 dcc.Dropdown(
#                                     id='preferred-category-dropdown',
#                                     options=preferred_category_options,
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
#                         news_elements_initial,
#                         id='news-bar',
#                         style={
#                             'height': '350px',
#                             'overflowY': 'scroll',
#                             'border': '1px solid #495057',
#                             'padding': '10px',
#                             'border-radius': '0.25rem',
#                             'background-color': '#343a40'
#                         }
#                     ),
#                     className="p-0"
#                 )
#             ], className="shadow-sm border-0 bg-dark"),
#             md=6,
#             className="mb-4"
#         )
#     ], className="mb-4")

# ], fluid=True, className="p-4 bg-secondary text-light")


# # --- 4. Callbacks ---

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

# @app.callback(
#     Output("custom-search-input-container", "children"),
#     Output("time-dropdown", "disabled"),
#     Output("time-dropdown", "value"),
#     Output("category-dropdown", "disabled"),
#     Output("category-dropdown", "value"),
#     Output("offcanvas-search-options", "is_open", allow_duplicate=True),
#     Output("search-mode-store", "data"),
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
#     search_mode = 'default'

#     if triggered_id == "custom-search-button":
#         input_group = dbc.InputGroup(
#             [
#                 dbc.Input(
#                     id="custom-search-query-input",
#                     placeholder="Enter custom search query...",
#                     type="text",
#                     className="form-control-lg bg-dark text-light border-secondary"
#                 ),
#                 dbc.Button(
#                     [html.I(className="fa-solid fa-magnifying-glass me-2"), "Search"],
#                     id="apply-custom-search",
#                     color="primary",
#                     className="btn-lg"
#                 )
#             ],
#             className="mb-3"
#         )
#         time_disabled = True
#         time_value = None
#         category_disabled = True
#         category_value = None
#         search_mode = 'custom'
#     elif triggered_id == "default-search-button":
#         pass

#     return input_group, time_disabled, time_value, category_disabled, category_value, offcanvas_open, search_mode


# @app.callback(
#     Output('keyword-table', 'data'),
#     Input('clear-table-button', 'n_clicks'),
#     prevent_initial_call=True
# )
# def clear_keyword_table(n_clicks):
#     if n_clicks:
#         return []
#     return dash.no_update


# @app.callback(
#     Output("custom-search-output", "children"),
#     Output("last-searched-query-store", "data"),
#     Output('keyword-table', 'data'),
#     Output('sentiment-line-graph', 'figure'),
#     Output('sentiment-pie-chart', 'figure'),
#     Output('news-bar', 'children'),
#     Output('alert-visibility-store', 'data'),
#     Output('alert-interval', 'disabled'),
#     Output('alert-interval', 'n_intervals'),
#     Input("apply-custom-search", "n_clicks"),
#     State("custom-search-query-input", "value"),
#     State("last-searched-query-store", "data"),
#     State('country-dropdown', 'value'),
#     prevent_initial_call=True,
#     running=[
#         (Output("apply-custom-search", "disabled"), True, False),
#         (Output("custom-search-output", "children"),
#          html.Div(dbc.Alert("Searching...", color="success", className="mt-3"), style={'text-align': 'center'}),
#          None)
#     ]
# )
# def perform_custom_search(n_clicks, current_search_query, last_searched_query, selected_country):
#     if n_clicks is None:
#         raise dash.exceptions.PreventUpdate

#     cleaned_current_query = current_search_query.strip() if current_search_query else ''

#     output_alert = dash.no_update
#     output_last_query = dash.no_update
#     output_keyword_table = dash.no_update
#     output_line_graph = dash.no_update
#     output_pie_chart = dash.no_update
#     output_news_bar = dash.no_update
#     output_alert_store = dash.no_update
#     output_interval_disabled = dash.no_update
#     output_interval_n_intervals = dash.no_update

#     country_params = COUNTRY_CODES.get(selected_country, COUNTRY_CODES['United States'])


#     if cleaned_current_query and cleaned_current_query != last_searched_query:
#         try:
#             # Use the new get_data_from_cache_or_generate
#             df_line, pie_data, keyword_table_data, news_articles = get_data_from_cache_or_generate(
#                 cleaned_current_query,
#                 country_params['gl'],
#                 country_params['hl'],
#                 country_params['ceid']
#             )

#             fig_line = px.line(df_line, x="Timestamp", y="Sentiment Score", title="Overall Sentiment Trend (Your Data)",
#                                markers=True, line_shape="linear")
#             fig_line.update_layout(hovermode="x unified", template="plotly_white", xaxis_title="Date and Time")

#             all_sentiments = pd.DataFrame({
#                 "Sentiment": ["Positive", "Neutral", "Negative"],
#                 "Count": 0
#             })
#             current_pie_data = pd.DataFrame({
#                 "Sentiment": ["Positive", "Neutral", "Negative"],
#                 "Count": pie_data
#             })
#             df_pie_final = pd.merge(all_sentiments, current_pie_data, on="Sentiment", how="left", suffixes=('_initial', '_actual'))
#             df_pie_final["Count"] = df_pie_final["Count_actual"].fillna(0).astype(int)
#             df_pie_final = df_pie_final[["Sentiment", "Count"]]

#             fig_pie = px.pie(df_pie_final, names="Sentiment", values="Count", title="Sentiment Distribution",
#                              color_discrete_map={'Positive': '#28a745', 'Neutral': '#ffc107', 'Negative': '#dc3545'},
#                              category_orders={"Sentiment": ["Positive", "Neutral", "Negative"]})
#             fig_pie.update_traces(textposition='inside', textinfo='percent+label')
#             fig_pie.update_layout(showlegend=True, title_x=0.5)

#             news_elements = [create_news_item_component(article['title'], article['link']) for article in news_articles]

#             output_alert = None
#             output_last_query = cleaned_current_query
#             output_keyword_table = keyword_table_data
#             output_line_graph = fig_line
#             output_pie_chart = fig_pie
#             output_news_bar = news_elements
#             output_alert_store = {'show': False, 'timestamp': None}
#             output_interval_disabled = True
#             output_interval_n_intervals = 0

#         except Exception as e:
#             print(f"Error in perform_custom_search: {e}")
#             output_alert = html.Div(
#                 dbc.Alert(f"An error occurred while fetching custom search data: {str(e)}", color="danger", className="mt-3"),
#                 style={'text-align': 'center'}
#             )
#             output_alert_store = {'show': True, 'timestamp': time.time()}
#             output_interval_disabled = False
#             output_interval_n_intervals = 0

#     elif not cleaned_current_query:
#         output_alert = html.Div(
#             dbc.Alert("Please enter a search query.", color="warning", className="mt-3"),
#             style={'text-align': 'center'}
#         )
#         output_last_query = dash.no_update
#         output_alert_store = {'show': True, 'timestamp': time.time()}
#         output_interval_disabled = False
#         output_interval_n_intervals = 0

#     else:
#         output_alert = html.Div(
#             dbc.Alert(f"'{cleaned_current_query}' was last searched. No new action.",
#                       color="info", className="mt-3"),
#             style={'text-align': 'center'}
#         )
#         output_last_query = dash.no_update
#         output_alert_store = {'show': True, 'timestamp': time.time()}
#         output_interval_disabled = False
#         output_interval_n_intervals = 0

#     return (
#         output_alert,
#         output_last_query,
#         output_keyword_table,
#         output_line_graph,
#         output_pie_chart,
#         output_news_bar,
#         output_alert_store,
#         output_interval_disabled,
#         output_interval_n_intervals
#     )


# @app.callback(
#     Output("custom-search-output", "children", allow_duplicate=True),
#     Output('alert-visibility-store', 'data', allow_duplicate=True),
#     Output('alert-interval', 'disabled', allow_duplicate=True),
#     Input('alert-interval', 'n_intervals'),
#     State('alert-visibility-store', 'data'),
#     prevent_initial_call=True
# )
# def hide_alert_after_delay(n_intervals, alert_store_data):
#     if alert_store_data and alert_store_data['show'] and alert_store_data['timestamp'] is not None:
#         elapsed_time = time.time() - alert_store_data['timestamp']
#         if elapsed_time >= 3:
#             return None, {'show': False, 'timestamp': None}, True
#     raise dash.exceptions.PreventUpdate


# @app.callback(
#     Output('news-bar', 'children', allow_duplicate=True),
#     Output('sentiment-line-graph', 'figure', allow_duplicate=True),
#     Output('sentiment-pie-chart', 'figure', allow_duplicate=True),
#     Output('keyword-table', 'data', allow_duplicate=True),
#     Input('country-dropdown', 'value'),
#     State('search-mode-store', 'data'),
#     State('last-searched-query-store', 'data'),
#     State('time-dropdown', 'value'), # Not used yet, but kept for future expansion
#     State('category-dropdown', 'value'), # Not used yet, but kept for future expansion
#     prevent_initial_call=True
# )
# def handle_country_change(selected_country_value, current_search_mode, last_searched_query, default_time_period, default_category):
#     output_news_bar = dash.no_update
#     output_line_graph = dash.no_update
#     output_pie_chart = dash.no_update
#     output_keyword_table = dash.no_update

#     country_params = COUNTRY_CODES.get(selected_country_value, COUNTRY_CODES['United States'])
#     gl = country_params['gl']
#     hl = country_params['hl']
#     ceid = country_params['ceid']

#     # query_to
