# Section 1: Import libraries
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, State, dash_table

# Section 2: Load dataset
CSV_FILE = "rainfall_tel_hr_odisha_od_2021_2025.csv"
df = pd.read_csv(CSV_FILE)

# Section 3: Clean and prepare dataset
time_col = "Data Acquisition Time"
rainfall_col = "Telemetry Hourly Rainfall (mm)"

df[time_col] = pd.to_datetime(
    df[time_col],
    format="%d-%m-%Y %H:%M",
    errors="coerce"
)

df[rainfall_col] = pd.to_numeric(
    df[rainfall_col],
    errors="coerce"
)

df = df.dropna(subset=[time_col, rainfall_col]).copy()

df = df.drop_duplicates(
    subset=[col for col in df.columns if col != "SlNo"],
    keep="first"
).copy()

df["Year"] = df[time_col].dt.year
df["Month"] = df[time_col].dt.month
df["Hour"] = df[time_col].dt.hour

df = df[df["Year"].between(2022, 2025)].copy()

# Exclude negative readings from rainfall analysis
valid_rain_df = df[df[rainfall_col] >= 0].copy()

print("Dataset loaded successfully!")
print("Total records:", len(df))
print("Available years:", sorted(df["Year"].unique()))
print("Available districts:", df["District"].nunique())

# Section 4: Initialize Dash
app = Dash(__name__)

# Section 5: Black dashboard colours
COLORS = {
    "background": "#000000",
    "panel": "#111827",
    "primary": "#3B82F6",
    "highlight": "#F59E0B",
    "line": "#2DD4BF",
    "text": "#FFFFFF",
    "muted": "#D1D5DB",
    "border": "#374151"
}

years = sorted(df["Year"].dropna().unique())
districts = sorted(df["District"].dropna().astype(str).unique())

month_names = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]


# Common dark styling for all charts
def darken_figure(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=COLORS["background"],
        plot_bgcolor=COLORS["panel"],
        font=dict(color=COLORS["text"]),
        title_font=dict(color=COLORS["text"]),
        margin=dict(l=40, r=25, t=70, b=45)
    )

    fig.update_xaxes(gridcolor="#374151")
    fig.update_yaxes(gridcolor="#374151")

    return fig


# Section 6: Dashboard layout
app.layout = html.Div(
    style={
        "backgroundColor": COLORS["background"],
        "color": COLORS["text"],
        "minHeight": "100vh",
        "padding": "25px",
        "fontFamily": "Arial, sans-serif"
    },

    children=[

        html.H1(
            "Rainfall Insights Odisha",
            style={
                "color": COLORS["text"],
                "textAlign": "center"
            }
        ),

        html.P(
            "Hourly Rainfall Pattern Analysis (2022–2025)",
            style={
                "textAlign": "center",
                "color": COLORS["muted"]
            }
        ),

        # Year dropdown
        html.Label("Select Year:"),

        dcc.Dropdown(
            id="year-dropdown",
            options=[
                {"label": str(y), "value": int(y)}
                for y in years
            ],
            value=int(max(years)),
            clearable=False,
            style={"color": "#111827", "maxWidth": "400px"}
        ),

        html.Br(),

        # District dropdown
        html.Label("Select District:"),

        dcc.Dropdown(
            id="district-dropdown",
            options=[
                {"label": d, "value": d}
                for d in districts
            ],
            value=districts[0] if districts else None,
            clearable=False,
            style={"color": "#111827", "maxWidth": "400px"}
        ),

        html.Br(),

        # KPI cards
        html.Div(
            id="kpi-cards",
            style={
                "display": "grid",
                "gridTemplateColumns":
                    "repeat(auto-fit, minmax(200px, 1fr))",
                "gap": "16px",
                "margin": "20px 0"
            }
        ),

        # Existing charts
        dcc.Graph(id="yearly-chart"),
        dcc.Graph(id="monthly-chart"),
        dcc.Graph(id="heatmap-chart"),

        # New Box Plot
        dcc.Graph(id="boxplot-chart"),

        # New Pair Plot
        dcc.Graph(id="pairplot-chart"),

        # DataFrame table
        html.H3(
            "Rainfall DataFrame",
            style={"marginTop": "30px"}
        ),

        html.P(
            "Data for the selected year and district.",
            style={"color": COLORS["muted"]}
        ),

        dash_table.DataTable(
            id="data-table",
            page_size=20,
            page_action="native",
            sort_action="native",
            filter_action="native",

            style_table={
                "overflowX": "auto",
                "border": f"1px solid {COLORS['border']}"
            },

            style_header={
                "backgroundColor": "#1F2937",
                "color": "white",
                "fontWeight": "bold",
                "border": f"1px solid {COLORS['border']}"
            },

            style_cell={
                "backgroundColor": COLORS["panel"],
                "color": "white",
                "textAlign": "left",
                "padding": "8px",
                "minWidth": "110px",
                "maxWidth": "240px",
                "whiteSpace": "normal",
                "border": f"1px solid {COLORS['border']}"
            }
        ),

        # Download button
        html.Button(
            "Download Filtered Data (CSV)",
            id="download-button",
            n_clicks=0,
            style={
                "backgroundColor": COLORS["primary"],
                "color": "white",
                "padding": "12px 20px",
                "border": "none",
                "borderRadius": "6px",
                "cursor": "pointer",
                "marginTop": "20px"
            }
        ),

        dcc.Download(id="download-data")
    ]
)


# Section 7: Dashboard callback
@app.callback(
    Output("kpi-cards", "children"),
    Output("yearly-chart", "figure"),
    Output("monthly-chart", "figure"),
    Output("heatmap-chart", "figure"),
    Output("boxplot-chart", "figure"),
    Output("pairplot-chart", "figure"),
    Output("data-table", "data"),
    Output("data-table", "columns"),

    Input("year-dropdown", "value"),
    Input("district-dropdown", "value")
)
def update_dashboard(selected_year, selected_district):

    district_df = df[
        df["District"].astype(str) == str(selected_district)
    ].copy()

    filtered_df = district_df[
        district_df["Year"] == selected_year
    ].copy()

    valid_district_df = valid_rain_df[
        valid_rain_df["District"].astype(str)
        == str(selected_district)
    ].copy()

    valid_filtered_df = valid_district_df[
        valid_district_df["Year"] == selected_year
    ].copy()

    # KPI cards
    total_records = len(filtered_df)

    mean_rainfall = valid_filtered_df[rainfall_col].mean()
    max_rainfall = valid_filtered_df[rainfall_col].max()

    mean_text = (
        f"{mean_rainfall:.2f} mm"
        if pd.notna(mean_rainfall) else "No data"
    )

    max_text = (
        f"{max_rainfall:.2f} mm"
        if pd.notna(max_rainfall) else "No data"
    )

    card_style = {
        "backgroundColor": COLORS["panel"],
        "color": "white",
        "padding": "18px",
        "borderRadius": "10px",
        "textAlign": "center",
        "border": f"1px solid {COLORS['border']}"
    }

    cards = [
        html.Div([
            html.H4("Total Records"),
            html.H2(f"{total_records:,}")
        ], style=card_style),

        html.Div([
            html.H4("Mean Valid Rainfall"),
            html.H2(mean_text)
        ], style=card_style),

        html.Div([
            html.H4("Maximum Valid Rainfall"),
            html.H2(max_text)
        ], style=card_style)
    ]

    # 1. Year-wise bar chart
    yearly_data = (
        valid_district_df.groupby("Year")[rainfall_col]
        .mean()
        .reindex(years)
        .rename_axis("Year")
        .reset_index(name=rainfall_col)
    )

    bar_fig = px.bar(
        yearly_data,
        x="Year",
        y=rainfall_col,
        title=f"Year-wise Mean Rainfall — {selected_district}",
        labels={
            "Year": "Year",
            rainfall_col: "Mean Rainfall (mm)"
        },
        color_discrete_sequence=[COLORS["primary"]]
    )

    bar_fig.update_traces(
        marker_color=[
            COLORS["highlight"]
            if int(y) == int(selected_year)
            else COLORS["primary"]
            for y in yearly_data["Year"]
        ]
    )

    bar_fig.update_xaxes(
        tickmode="array",
        tickvals=years,
        ticktext=[str(y) for y in years]
    )

    darken_figure(bar_fig)

    # 2. Monthly line chart
    monthly_data = (
        valid_filtered_df.groupby("Month")[rainfall_col]
        .mean()
        .reindex(range(1, 13))
        .rename_axis("Month")
        .reset_index(name=rainfall_col)
    )

    line_fig = px.line(
        monthly_data,
        x="Month",
        y=rainfall_col,
        markers=True,
        title=(
            f"Monthly Mean Rainfall — "
            f"{selected_district}, {selected_year}"
        ),
        labels={
            "Month": "Month",
            rainfall_col: "Mean Rainfall (mm)"
        },
        color_discrete_sequence=[COLORS["line"]]
    )

    line_fig.update_xaxes(
        tickmode="array",
        tickvals=list(range(1, 13)),
        ticktext=month_names
    )

    darken_figure(line_fig)

    # 3. Heatmap
    heatmap_data = (
        valid_district_df.groupby(["Year", "Month"])[rainfall_col]
        .mean()
        .reset_index()
        .pivot(
            index="Year",
            columns="Month",
            values=rainfall_col
        )
        .reindex(index=years, columns=range(1, 13))
    )

    heatmap_fig = px.imshow(
        heatmap_data,
        labels={
            "x": "Month",
            "y": "Year",
            "color": "Mean Rainfall (mm)"
        },
        x=month_names,
        y=[str(y) for y in heatmap_data.index],
        aspect="auto",
        color_continuous_scale="YlGnBu",
        title=f"Monthly Rainfall Heatmap — {selected_district}"
    )

    darken_figure(heatmap_fig)

    # 4. Box plot
    box_fig = px.box(
        valid_district_df,
        x="Year",
        y=rainfall_col,
        color="Year",
        points="outliers",
        title=f"Rainfall Distribution by Year — {selected_district}",
        labels={
            "Year": "Year",
            rainfall_col: "Hourly Rainfall (mm)"
        }
    )

    darken_figure(box_fig)

    # 5. Pair plot / scatter matrix
    pair_df = valid_filtered_df[
        [rainfall_col, "Year", "Month", "Hour"]
    ].dropna().copy()

    # Sample rows to keep the dashboard responsive
    if len(pair_df) > 2000:
        pair_df = pair_df.sample(
            2000,
            random_state=42
        )

    pair_fig = px.scatter_matrix(
        pair_df,
        dimensions=[
            rainfall_col,
            "Year",
            "Month",
            "Hour"
        ],
        color="Month",
        title=(
            f"Pair Plot: Rainfall and Time Variables — "
            f"{selected_district}, {selected_year}"
        ),
        labels={
            rainfall_col: "Hourly Rainfall (mm)",
            "Year": "Year",
            "Month": "Month",
            "Hour": "Hour"
        },
        color_continuous_scale="Turbo"
    )

    pair_fig.update_traces(
        diagonal_visible=False,
        showupperhalf=False
    )

    darken_figure(pair_fig)

    # 6. DataFrame table
    table_df = filtered_df.drop(
        columns=["Year", "Month", "Hour"],
        errors="ignore"
    ).head(500)

    table_df = table_df.astype(object).where(
        pd.notna(table_df),
        None
    )

    table_data = table_df.to_dict("records")

    table_columns = [
        {"name": col, "id": col}
        for col in table_df.columns
    ]

    return (
        cards,
        bar_fig,
        line_fig,
        heatmap_fig,
        box_fig,
        pair_fig,
        table_data,
        table_columns
    )


# Section 8: Download filtered CSV
@app.callback(
    Output("download-data", "data"),
    Input("download-button", "n_clicks"),
    State("year-dropdown", "value"),
    State("district-dropdown", "value"),
    prevent_initial_call=True
)
def download_filtered_data(
    n_clicks,
    selected_year,
    selected_district
):

    filtered_data = df[
        (df["Year"] == selected_year)
        & (
            df["District"].astype(str)
            == str(selected_district)
        )
    ].copy()

    filtered_data = filtered_data.drop(
        columns=["Year", "Month", "Hour"],
        errors="ignore"
    )

    filename = (
        f"rainfall_{selected_district}_{selected_year}.csv"
    )

    return dcc.send_data_frame(
        filtered_data.to_csv,
        filename,
        index=False
    )


# Section 9: Run dashboard
if __name__ == "__main__":
    app.run(debug=True)