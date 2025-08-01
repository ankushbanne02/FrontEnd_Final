import dash
from dash import dcc, html, dash_table
import plotly.express as px
import plotly.graph_objects as go 
import requests
import pandas as pd
import dash_bootstrap_components as dbc
import datetime
from dash import Input, Output, State, callback
import numpy as np

# Function to fetch volume data from API
def fetch_volume_data(selected_date):
    try:
        payload = {"date": selected_date}
        response = requests.post("https://backend-vanderlande-1.onrender.com/volume", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API error: {e}")
    except ValueError as e:
        print(f"JSON decoding error: {e}")
    return {"height_distribution": {}, "width_distribution": {}, "length_distribution": {}}

# Function to create bar charts
def generate_bar_chart(data_dict, title, xaxis_label, bin_size=50, max_bin=1200):
    if not data_dict:
        return html.Div(f"No data available for {title}", className="text-danger")

    try:
        # Convert keys to float
        parsed_data = [(float(k), int(v)) for k, v in data_dict.items() if v is not None]

        # Initialize bins
        num_bins = int(max_bin / bin_size)
        bins = {f"{i * bin_size}-{(i + 1) * bin_size}": 0 for i in range(num_bins)}

        # Populate bins
        for value, count in parsed_data:
            bin_index = int(value // bin_size)
            bin_label = f"{bin_index * bin_size}-{(bin_index + 1) * bin_size}"
            if bin_label in bins:
                bins[bin_label] += count

        # Filter out empty bins
        bins = {k: v for k, v in bins.items() if v > 0}

        x = list(bins.keys())
        y = list(bins.values())

        fig = go.Figure([
            go.Bar(x=x, y=y, marker_color='#d63384', name=title)
        ])

        fig.update_layout(
            title=title,
            xaxis_title=xaxis_label,
            yaxis_title="Number of Parcels",
            paper_bgcolor='white',
            plot_bgcolor='white',
            height=350,
            margin=dict(l=30, r=30, t=50, b=30)
        )

        return dcc.Graph(figure=fig, config={"displayModeBar": False})

    except Exception as e:
        print(f"Chart rendering error for {title}: {e}")
        return html.Div(f"Error rendering chart for {title}", className="text-danger")

# Function to compute min, avg, max stats
def compute_stats(data_dict):
    try:
        values = [float(k) for k in data_dict.keys() if float(k) > 0]
        if not values:
            return "N/A", "N/A", "N/A"
        return min(values), round(np.mean(values), 1), max(values)
    except Exception as e:
        print(f"Stats computation error: {e}")
        return "Error", "Error", "Error"

# Function to generate stats table
def generate_stats_table(height_dict, width_dict, length_dict):
    h_min, h_avg, h_max = compute_stats(height_dict)
    w_min, w_avg, w_max = compute_stats(width_dict)
    l_min, l_avg, l_max = compute_stats(length_dict)

    df = pd.DataFrame([
        {"Parameter": "Height", "Min (mm)": h_min, "Avg (mm)": h_avg, "Max (mm)": h_max},
        {"Parameter": "Width", "Min (mm)": w_min, "Avg (mm)": w_avg, "Max (mm)": w_max},
        {"Parameter": "Length", "Min (mm)": l_min, "Avg (mm)": l_avg, "Max (mm)": l_max},
    ])

    return dash_table.DataTable(
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict("records"),
        style_table={"marginTop": "20px"},
        style_cell={"textAlign": "center", "padding": "5px"},
        style_header={"backgroundColor": "#343a40", "color": "white", "fontWeight": "bold"},
        style_data={"backgroundColor": "#f8f9fa", "color": "#212529"}
    )

# Function to calculate length allocation KPIs
def calculate_length_allocation_kpis(length_dict):
    try:
        parsed = [(float(k), int(v)) for k, v in length_dict.items() if float(k) > 0 and v is not None]
        total = sum(v for _, v in parsed)
        under_400 = sum(v for k, v in parsed if k <= 400)
        under_600 = sum(v for k, v in parsed if k <= 600)

        pct_400 = round(100 * under_400 / total, 2) if total else 0
        pct_600 = round(100 * under_600 / total, 2) if total else 0
        return pct_400, pct_600
    except Exception as e:
        print(f"KPI calculation error: {e}")
        return 0, 0

# Function to generate KPI card for length allocated parcels
def generate_kpi_card(title, value):
    return dbc.Card(
        dbc.CardBody([
            html.Div(title, className="kpi-label"),
            html.H2(f"{value:.2f} %", className="kpi-value")
        ]),
        style={
            "backgroundColor": "#f4731c",
            "color": "white",
            "textAlign": "center",
            "height": "120px",
            "fontWeight": "bold"
        },
        className="mb-2"
    )
