
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from dash import Dash, dcc, html, Input, Output
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

app = Dash(__name__)
server = app.server

app.layout = html.Div([
    html.Div([
        html.H1("AI Shockwave Index",
                style={"color": "white", "margin": "0", "fontSize": "32px"}),
        html.P("Measuring the Economic Blast Radius of Major AI Events",
               style={"color": "#aaaaaa", "margin": "5px 0 0 0"})
    ], style={"backgroundColor": "#1a1a2e", "padding": "30px", "marginBottom": "20px"}),

    html.Div([
        html.H2("Market Impact Heatmap", style={"color": "#333"}),
        html.P("Green = stock gained | Red = stock dropped | Around each AI event",
               style={"color": "#666"}),
        dcc.Graph(id="heatmap", figure=px.imshow(
            impact_df.pivot(index="ticker", columns="event", values="impact_pct"),
            color_continuous_scale="RdYlGn",
            color_continuous_midpoint=0,
            labels=dict(color="Impact %"),
            aspect="auto",
            height=400
        )),

        html.Hr(style={"margin": "30px 0"}),

        html.H2("Event Impact Timeline", style={"color": "#333"}),
        html.P("Select a company and event to see day-by-day price movement",
               style={"color": "#666"}),
        html.Div([
            html.Div([
                html.Label("Select Company:", style={"fontWeight": "bold"}),
                dcc.Dropdown(
                    id="ticker-dropdown",
                    options=[{"label": t, "value": t} for t in ticker_list],
                    value="NVDA",
                    clearable=False
                )
            ], style={"width": "45%", "display": "inline-block", "marginRight": "5%"}),
            html.Div([
                html.Label("Select AI Event:", style={"fontWeight": "bold"}),
                dcc.Dropdown(
                    id="event-dropdown",
                    options=[{"label": e, "value": e} for e in event_list],
                    value="DeepSeek R1 Launch",
                    clearable=False
                )
            ], style={"width": "45%", "display": "inline-block"})
        ], style={"marginBottom": "15px"}),
        dcc.Graph(id="timeline-chart"),

        html.Hr(style={"margin": "30px 0"}),

        html.H2("Category Impact Comparison", style={"color": "#333"}),
        html.P("How each company category responded across all AI events",
               style={"color": "#666"}),
        dcc.Graph(id="category-chart", figure=px.bar(
            impact_df.groupby(["event", "category"])["impact_pct"].mean().reset_index(),
            x="event", y="impact_pct", color="category", barmode="group",
            labels={"impact_pct": "Avg Price Impact %", "event": "AI Event", "category": "Category"},
            color_discrete_map={"AI Winners": "royalblue", "Disrupted": "crimson", "Infrastructure": "green"},
            height=450
        )),

    ], style={"maxWidth": "1200px", "margin": "0 auto", "padding": "0 20px"}),

    html.Div([
        html.P("Built by Arbab Jabbar | Business Economics | Data: Yahoo Finance",
               style={"color": "#aaaaaa", "textAlign": "center", "margin": "0"})
    ], style={"backgroundColor": "#1a1a2e", "padding": "20px", "marginTop": "40px"})
])

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
        line=dict(color="royalblue", width=2)
    ))
    fig.add_vline(
        x=0, line_dash="dash", line_color="red",
        annotation_text=event_name, annotation_position="top left"
    )
    fig.update_layout(
        title=f"{ticker} — 30 Days Before & After {event_name}",
        xaxis_title="Days From Event (0 = Event Date)",
        yaxis_title="Stock Price (USD)",
        height=450
    )
    return fig

if __name__ == "__main__":
    app.run(debug=False)
