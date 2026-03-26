import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go

ai_events = {
    "ChatGPT Launch":        "2022-11-30",
    "GPT-4 Release":         "2023-03-14",
    "Nvidia $1T Market Cap": "2023-05-30",
    "Sam Altman Fired":      "2023-11-17",
    "DeepSeek R1 Launch":    "2025-01-20",
    "Meta $65B Investment":  "2025-01-24"
}

companies = {
    "AI Winners":    ["NVDA", "MSFT", "GOOGL", "META"],
    "Disrupted":     ["CHGG", "DUOL", "UPWK", "FVRR"],
    "Infrastructure":["AMD", "PLTR", "ORCL", "AMZN"]
}

COLORS = {
    "background":  "#0d1117",
    "card":        "#161b22",
    "border":      "#30363d",
    "text":        "#e6edf3",
    "subtext":     "#8b949e",
    "accent":      "#58a6ff",
    "green":       "#3fb950",
    "red":         "#f85149",
    "yellow":      "#d29922"
}

LOGO_URL = "https://logo.clearbit.com/{domain}"
COMPANY_DOMAINS = {
    "NVDA": "nvidia.com",   "MSFT": "microsoft.com",
    "GOOGL": "google.com",  "META": "meta.com",
    "CHGG": "chegg.com",    "DUOL": "duolingo.com",
    "UPWK": "upwork.com",   "FVRR": "fiverr.com",
    "AMD": "amd.com",       "PLTR": "palantir.com",
    "ORCL": "oracle.com",   "AMZN": "amazon.com"
}

def get_event_data(ticker, event_date, window=30):
    date = datetime.strptime(event_date, "%Y-%m-%d")
    start = date - timedelta(days=window)
    end = date + timedelta(days=window)
    stock = yf.Ticker(ticker)
    df = stock.history(start=start, end=end)
    df["ticker"] = ticker
    df["event_date"] = date
    df["days_from_event"] = (df.index.tz_localize(None) - date).days
    df["pct_change"] = df["Close"].pct_change() * 100
    return df

print("Loading market data...")
all_data = []
for event_name, event_date in ai_events.items():
    for category, tickers in companies.items():
        for ticker in tickers:
            df = get_event_data(ticker, event_date)
            df["event_name"] = event_name
            df["category"] = category
            all_data.append(df)

master_df = pd.concat(all_data)

def calculate_impact(master_df):
    results = []
    for event_name in master_df["event_name"].unique():
        for ticker in master_df["ticker"].unique():
            subset = master_df[
                (master_df["event_name"] == event_name) &
                (master_df["ticker"] == ticker)
            ]
            before = subset[subset["days_from_event"] < 0]["Close"].mean()
            after = subset[subset["days_from_event"] > 0]["Close"].mean()
            impact = ((after - before) / before) * 100
            category = subset["category"].iloc[0]
            results.append({
                "event": event_name,
                "ticker": ticker,
                "category": category,
                "avg_before": round(before, 2),
                "avg_after": round(after, 2),
                "impact_pct": round(impact, 2)
            })
    return pd.DataFrame(results)

impact_df = calculate_impact(master_df)
event_list = list(ai_events.keys())
ticker_list = [t for tickers in companies.values() for t in tickers]

def make_logo_option(ticker):
    domain = COMPANY_DOMAINS.get(ticker, "")
    return {
        "label": html.Span([
            html.Img(
                src=LOGO_URL.format(domain=domain),
                style={"height": "20px", "marginRight": "8px",
                       "borderRadius": "4px"}
            ),
            ticker
        ]),
        "value": ticker
    }

app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
server = app.server

CARD_STYLE = {
    "backgroundColor": COLORS["card"],
    "border": f"1px solid {COLORS['border']}",
    "borderRadius": "12px",
    "padding": "24px",
    "marginBottom": "24px"
}

LABEL_STYLE = {
    "color": COLORS["subtext"],
    "fontSize": "12px",
    "fontWeight": "600",
    "letterSpacing": "0.8px",
    "textTransform": "uppercase",
    "marginBottom": "8px"
}

CHART_TEMPLATE = "plotly_dark"

app.layout = html.Div([

    html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Span("AI", style={
                            "color": COLORS["accent"],
                            "fontWeight": "800",
                            "fontSize": "28px"
                        }),
                        html.Span(" Shockwave Index", style={
                            "color": COLORS["text"],
                            "fontWeight": "800",
                            "fontSize": "28px"
                        })
                    ]),
                    html.P(
                        "Measuring the Economic Blast Radius of Major AI Events",
                        style={"color": COLORS["subtext"],
                               "margin": "4px 0 0 0",
                               "fontSize": "14px"}
                    )
                ], md=8),
                dbc.Col([
                    html.Div([
                        html.Div([
                            html.P("EVENTS TRACKED", style=LABEL_STYLE),
                            html.H3("6", style={"color": COLORS["accent"],
                                                "margin": "0"})
                        ], style={"textAlign": "center", "marginRight": "32px"}),
                        html.Div([
                            html.P("COMPANIES", style=LABEL_STYLE),
                            html.H3("12", style={"color": COLORS["green"],
                                                 "margin": "0"})
                        ], style={"textAlign": "center", "marginRight": "32px"}),
                        html.Div([
                            html.P("DATA POINTS", style=LABEL_STYLE),
                            html.H3("2,892", style={"color": COLORS["yellow"],
                                                    "margin": "0"})
                        ], style={"textAlign": "center"})
                    ], style={"display": "flex", "alignItems": "center",
                              "justifyContent": "flex-end", "height": "100%"})
                ], md=4)
            ])
        ], fluid=True)
    ], style={
        "backgroundColor": COLORS["card"],
        "borderBottom": f"1px solid {COLORS['border']}",
        "padding": "24px 32px",
        "marginBottom": "32px"
    }),

    dbc.Container([

        html.Div([
            html.P("MARKET IMPACT OVERVIEW", style=LABEL_STYLE),
            html.H4("Heatmap — All Events vs All Companies",
                    style={"color": COLORS["text"], "marginBottom": "4px"}),
            html.P("Green = gained | Red = dropped | Measured 30 days around each event",
                   style={"color": COLORS["subtext"], "fontSize": "13px",
                          "marginBottom": "16px"}),
            dcc.Graph(
                id="heatmap",
                figure=px.imshow(
                    impact_df.pivot(index="ticker", columns="event",
                                   values="impact_pct"),
                    color_continuous_scale="RdYlGn",
                    color_continuous_midpoint=0,
                    labels=dict(color="Impact %"),
                    aspect="auto",
                    height=380,
                    template=CHART_TEMPLATE
                ),
                config={"displayModeBar": False}
            )
        ], style=CARD_STYLE),

        html.Div([
            html.P("EVENT DEEP DIVE", style=LABEL_STYLE),
            html.H4("Price Timeline — 30 Days Before & After",
                    style={"color": COLORS["text"], "marginBottom": "4px"}),
            html.P("Select any company and event to see the exact moment of impact",
                   style={"color": COLORS["subtext"], "fontSize": "13px",
                          "marginBottom": "20px"}),
            dbc.Row([
                dbc.Col([
                    html.P("COMPANY", style=LABEL_STYLE),
                    dcc.Dropdown(
                        id="ticker-dropdown",
                        options=[make_logo_option(t) for t in ticker_list],
                        value="NVDA",
                        clearable=False,
                        style={"backgroundColor": COLORS["background"],
                               "color": COLORS["text"]}
                    )
                ], md=6),
                dbc.Col([
                    html.P("AI EVENT", style=LABEL_STYLE),
                    dcc.Dropdown(
                        id="event-dropdown",
                        options=[{"label": e, "value": e} for e in event_list],
                        value="DeepSeek R1 Launch",
                        clearable=False,
                        style={"backgroundColor": COLORS["background"],
                               "color": COLORS["text"]}
                    )
                ], md=6)
            ], style={"marginBottom": "16px"}),
            dcc.Graph(id="timeline-chart", config={"displayModeBar": False})
        ], style=CARD_STYLE),

        html.Div([
            html.P("CATEGORY ANALYSIS", style=LABEL_STYLE),
            html.H4("Average Impact by Company Category",
                    style={"color": COLORS["text"], "marginBottom": "4px"}),
            html.P("Which types of companies win and lose from each AI event",
                   style={"color": COLORS["subtext"], "fontSize": "13px",
                          "marginBottom": "16px"}),
            dcc.Graph(
                id="category-chart",
                figure=px.bar(
                    impact_df.groupby(["event", "category"])["impact_pct"].mean().reset_index(),
                    x="event", y="impact_pct", color="category",
                    barmode="group",
                    labels={"impact_pct": "Avg Price Impact %",
                            "event": "AI Event", "category": "Category"},
                    color_discrete_map={
                        "AI Winners": COLORS["accent"],
                        "Disrupted": COLORS["red"],
                        "Infrastructure": COLORS["green"]
                    },
                    height=420,
                    template=CHART_TEMPLATE
                ),
                config={"displayModeBar": False}
            )
        ], style=CARD_STYLE),

        html.Div([
            html.P(
                "Built by Arbab Jabbar | Business Economics | Data: Yahoo Finance via yfinance",
                style={"color": COLORS["subtext"], "textAlign": "center",
                       "fontSize": "13px", "margin": "0"}
            )
        ], style={"padding": "24px 0 32px 0"})

    ], fluid=True)

], style={"backgroundColor": COLORS["background"],
          "minHeight": "100vh",
          "fontFamily": "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"})


@app.callback(
    Output("timeline-chart", "figure"),
    Input("ticker-dropdown", "value"),
    Input("event-dropdown", "value")
)
def update_timeline(ticker, event_name):
    subset = master_df[
        (master_df["ticker"] == ticker) &
        (master_df["event_name"] == event_name)
    ].copy()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=subset["days_from_event"],
        y=subset["Close"],
        mode="lines+markers",
        name=ticker,
        line=dict(color=COLORS["accent"], width=2),
        marker=dict(size=5)
    ))
    fig.add_vline(
        x=0,
        line_dash="dash",
        line_color=COLORS["red"],
        annotation_text=event_name,
        annotation_font_color=COLORS["red"],
        annotation_position="top left"
    )
    fig.update_layout(
        template=CHART_TEMPLATE,
        paper_bgcolor=COLORS["card"],
        plot_bgcolor=COLORS["card"],
        title=f"{ticker} — {event_name}",
        xaxis_title="Days From Event (0 = Event Date)",
        yaxis_title="Stock Price (USD)",
        height=420
    )
    return fig

if __name__ == "__main__":
    app.run(debug=False)
