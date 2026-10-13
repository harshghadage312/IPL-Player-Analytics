from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data" / "processed"

st.set_page_config(
    page_title="IPL Performance Lab",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Premium dark theme ----------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --bg: #080d18;
        --panel: #101827;
        --panel-2: #141f31;
        --line: rgba(148, 163, 184, .18);
        --muted: #9aa9bd;
        --text: #f2f6fc;
        --lime: #c8f169;
        --cyan: #57d6e8;
        --orange: #ff9b54;
    }

    .stApp {
        background:
            radial-gradient(ellipse at 85% 0%, rgba(42, 83, 107, .22), transparent 34%),
            radial-gradient(ellipse at 0% 20%, rgba(111, 140, 52, .10), transparent 28%),
            var(--bg);
        color: var(--text);
        font-family: 'Inter', sans-serif;
    }

    [data-testid="stHeader"] { background: rgba(8, 13, 24, .86); }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #101827 0%, #0b1220 100%);
        border-right: 1px solid var(--line);
    }
    [data-testid="stSidebar"] * { color: var(--text); }

    h1, h2, h3 {
        font-family: 'Barlow Condensed', sans-serif !important;
        letter-spacing: .3px;
        color: var(--text) !important;
    }
    h1 { font-size: clamp(2.5rem, 5vw, 4rem) !important; line-height: 1.0 !important; }
    h2 { font-size: 2rem !important; }
    h3 { font-size: 1.5rem !important; }

    .hero {
        border: 1px solid rgba(200, 241, 105, .22);
        border-radius: 22px;
        padding: 28px 30px;
        margin: 4px 0 22px 0;
        background:
            linear-gradient(115deg, rgba(200,241,105,.10), transparent 40%),
            linear-gradient(135deg, #172438 0%, #101827 58%, #132331 100%);
        box-shadow: 0 18px 55px rgba(0,0,0,.18);
    }
    .eyebrow {
        color: var(--lime);
        font-size: .75rem;
        font-weight: 800;
        letter-spacing: 2.5px;
        text-transform: uppercase;
        margin-bottom: 9px;
    }
    .hero-sub {
        color: #b5c2d3;
        font-size: .98rem;
        max-width: 760px;
        line-height: 1.6;
        margin-top: 12px;
    }
    .section-kicker {
        color: var(--lime);
        font-size: .72rem;
        letter-spacing: 2px;
        font-weight: 800;
        text-transform: uppercase;
        margin: 0 0 3px 0;
    }
    .section-note { color: var(--muted); font-size: .9rem; margin-bottom: 12px; }

    [data-testid="stMetric"] {
        background: linear-gradient(145deg, #152136, #101827);
        border: 1px solid var(--line);
        padding: 17px 18px;
        border-radius: 16px;
        min-height: 112px;
    }
    [data-testid="stMetricLabel"] p {
        color: #a9b8cb !important;
        font-size: .78rem !important;
        font-weight: 600 !important;
    }
    [data-testid="stMetricValue"] {
        color: var(--lime) !important;
        font-family: 'Barlow Condensed', sans-serif !important;
        font-size: 2rem !important;
    }

    div[data-testid="stPlotlyChart"] {
        border: 1px solid var(--line);
        border-radius: 16px;
        background: rgba(16, 24, 39, .55);
        padding: 8px 8px 0 8px;
    }
    [data-testid="stDataFrame"] {
        border: 1px solid var(--line);
        border-radius: 14px;
        overflow: hidden;
    }
    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
        background-color: #111c2c;
        border-color: #344258;
        border-radius: 10px;
    }
    .stButton button {
        background: var(--lime);
        color: #101827;
        border: 0;
        border-radius: 10px;
        font-weight: 800;
    }
    hr { border-color: var(--line); }
    .footer {
        color: #77879d;
        font-size: .78rem;
        border-top: 1px solid var(--line);
        margin-top: 30px;
        padding-top: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Plotly styling ----------
PLOT_TEMPLATE = "plotly_dark"
LIME = "#c8f169"
CYAN = "#57d6e8"
ORANGE = "#ff9b54"
PURPLE = "#b6a0ff"


def style_figure(fig, height=390):
    fig.update_layout(
        template=PLOT_TEMPLATE,
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#dce6f2", size=12),
        title=dict(font=dict(size=17, color="#f2f6fc"), x=0.02, xanchor="left"),
        margin=dict(l=20, r=20, t=65, b=25),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        xaxis=dict(gridcolor="rgba(148,163,184,.12)", zerolinecolor="rgba(148,163,184,.15)"),
        yaxis=dict(gridcolor="rgba(148,163,184,.12)", zerolinecolor="rgba(148,163,184,.15)"),
    )
    return fig


@st.cache_data
def load_data():
    deliveries = pd.read_csv(
        DATA_DIR / "deliveries.csv",
        low_memory=False,
        dtype={"season": str},
    )
    batting = pd.read_csv(DATA_DIR / "batting_stats.csv")
    bowling = pd.read_csv(DATA_DIR / "bowling_stats.csv")

    for column in ["season", "batter", "bowler"]:
        if column in deliveries.columns:
            deliveries[column] = deliveries[column].astype(str).str.strip()

    return deliveries, batting, bowling


def section(title, note=None):
    st.markdown(f'<div class="section-kicker">Performance Centre</div>', unsafe_allow_html=True)
    st.subheader(title)
    if note:
        st.markdown(f'<div class="section-note">{note}</div>', unsafe_allow_html=True)


def get_batter_stats(player_name, data):
    player_data = data[data["batter"] == player_name].copy()
    runs = int(player_data["batter_runs"].sum())
    balls = int(player_data["balls_faced"].sum())
    matches = int(player_data["match_id"].nunique())
    fours = int(player_data["is_four"].sum())
    sixes = int(player_data["is_six"].sum())
    strike_rate = round(runs * 100 / balls, 2) if balls else 0

    season_data = (
        player_data.groupby("season", as_index=False)
        .agg(
            runs=("batter_runs", "sum"),
            matches=("match_id", "nunique"),
            balls_faced=("balls_faced", "sum"),
            fours=("is_four", "sum"),
            sixes=("is_six", "sum"),
        )
    )
    season_data["strike_rate"] = (
        season_data["runs"] * 100
        / season_data["balls_faced"].replace(0, float("nan"))
    ).round(2)
    season_data["season"] = season_data["season"].astype(str)
    season_data = season_data.sort_values("season")

    return {
        "Player": player_name,
        "Runs": runs,
        "Matches": matches,
        "Balls Faced": balls,
        "Strike Rate": strike_rate,
        "Fours": fours,
        "Sixes": sixes,
        "season_data": season_data,
    }


# ---------- Load ----------
try:
    deliveries, batting, bowling = load_data()
except FileNotFoundError:
    st.error("Processed CSV files not found. Run `python src/analysis.py` first.")
    st.stop()
except (pd.errors.EmptyDataError, pd.errors.ParserError) as exc:
    st.error(f"Could not read a processed CSV file: {exc}")
    st.stop()

required_columns = {
    "season", "match_id", "batter", "bowler", "batter_runs",
    "balls_faced", "is_four", "is_six", "is_wicket",
    "bowler_runs", "legal_ball", "bowler_wicket",
}
missing = required_columns.difference(deliveries.columns)
if missing:
    st.error(
        "deliveries.csv is missing required columns: "
        + ", ".join(sorted(missing))
        + ". Please rerun `python src/analysis.py` and check the output."
    )
    st.stop()

# ---------- Hero ----------
st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">Cricket intelligence • IPL data lab</div>
        <h1>IPL PERFORMANCE<br>ANALYTICS</h1>
        <div class="hero-sub">
            Explore the numbers behind the game — discover elite batters,
            wicket-taking bowlers, season trends and head-to-head player battles.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- Sidebar ----------
st.sidebar.markdown("## 🏏 IPL DATA LAB")
st.sidebar.caption("FILTER YOUR MATCH DATA")
seasons = sorted(deliveries["season"].dropna().unique().tolist(), reverse=True)

selected_seasons = st.sidebar.multiselect(
    "IPL season",
    options=seasons,
    default=seasons,
)
players = sorted(deliveries["batter"].dropna().unique().tolist())

selected_player = st.sidebar.selectbox(
    "Individual batter explorer",
    options=["All players"] + players,
)
st.sidebar.markdown("---")
st.sidebar.caption("Premium Cricket Analytics · Built with Streamlit")

filtered = deliveries[deliveries["season"].isin(selected_seasons)].copy()
if filtered.empty:
    st.warning("No data for the selected seasons. Select at least one season in the sidebar.")
    st.stop()

# ---------- Overview KPIs ----------
total_matches = filtered["match_id"].nunique()
total_runs = int(filtered["batter_runs"].sum())
total_wickets = int(filtered["is_wicket"].sum())
total_players = pd.concat([filtered["batter"], filtered["bowler"]]).nunique()

k1, k2, k3, k4 = st.columns(4)
k1.metric("MATCHES COVERED", f"{total_matches:,}")
k2.metric("BATTER RUNS", f"{total_runs:,}")
k3.metric("WICKETS RECORDED", f"{total_wickets:,}")
k4.metric("PLAYERS FEATURED", f"{total_players:,}")

st.divider()

# ---------- Batting leaderboard ----------
section("🏆 Top Run Scorers", "The leading run-makers across your selected IPL seasons.")

batting_filtered = (
    filtered.groupby("batter", as_index=False)
    .agg(
        runs=("batter_runs", "sum"),
        balls_faced=("balls_faced", "sum"),
        fours=("is_four", "sum"),
        sixes=("is_six", "sum"),
        matches=("match_id", "nunique"),
    )
)
batting_filtered["strike_rate"] = (
    batting_filtered["runs"] * 100
    / batting_filtered["balls_faced"].replace(0, float("nan"))
).round(2)
top_batters = batting_filtered.nlargest(10, "runs")

left, right = st.columns(2)
with left:
    fig = px.bar(
        top_batters.sort_values("runs"),
        x="runs",
        y="batter",
        orientation="h",
        title="Top 10 batters · runs",
        labels={"runs": "Runs", "batter": "Player"},
        hover_data=["matches", "strike_rate", "fours", "sixes"],
        color_discrete_sequence=[LIME],
    )
    fig.update_traces(marker_line_width=0, opacity=0.95)
    fig.update_layout(yaxis_title="", xaxis_title="Runs")
    st.plotly_chart(style_figure(fig), width="stretch")

with right:
    fig = px.scatter(
        batting_filtered,
        x="balls_faced",
        y="strike_rate",
        size="runs",
        hover_name="batter",
        title="Strike rate vs balls faced",
        labels={"balls_faced": "Balls faced", "strike_rate": "Strike rate"},
        color="runs",
        color_continuous_scale=[[0, "#34516a"], [0.55, CYAN], [1, LIME]],
    )
    st.plotly_chart(style_figure(fig), width="stretch")

with st.expander("View top batting leaderboard"):
    st.dataframe(
        top_batters.sort_values("runs", ascending=False),
        width="stretch",
        hide_index=True,
    )

st.divider()

# ---------- Bowling leaderboard ----------
section("🎯 Top Wicket Takers", "Compare wicket hauls and bowling economy in the selected seasons.")

bowling_filtered = (
    filtered.groupby("bowler", as_index=False)
    .agg(
        wickets=("bowler_wicket", "sum"),
        runs_conceded=("bowler_runs", "sum"),
        legal_balls=("legal_ball", "sum"),
        matches=("match_id", "nunique"),
    )
)
bowling_filtered["economy"] = (
    bowling_filtered["runs_conceded"] * 6
    / bowling_filtered["legal_balls"].replace(0, float("nan"))
).round(2)
bowling_filtered["overs"] = (
    (bowling_filtered["legal_balls"] // 6).astype(int).astype(str)
    + "."
    + (bowling_filtered["legal_balls"] % 6).astype(str)
)
top_bowlers = bowling_filtered.nlargest(10, "wickets")

left, right = st.columns(2)
with left:
    fig = px.bar(
        top_bowlers.sort_values("wickets"),
        x="wickets",
        y="bowler",
        orientation="h",
        title="Top 10 bowlers · wickets",
        labels={"wickets": "Wickets", "bowler": "Bowler"},
        hover_data=["economy", "runs_conceded", "matches", "overs"],
        color_discrete_sequence=[CYAN],
    )
    fig.update_layout(yaxis_title="", xaxis_title="Wickets")
    st.plotly_chart(style_figure(fig), width="stretch")

with right:
    fig = px.scatter(
        bowling_filtered,
        x="economy",
        y="wickets",
        hover_name="bowler",
        title="Economy vs wickets",
        labels={"economy": "Economy rate", "wickets": "Wickets"},
        color="wickets",
        color_continuous_scale=[[0, "#34516a"], [0.55, CYAN], [1, ORANGE]],
    )
    st.plotly_chart(style_figure(fig), width="stretch")

with st.expander("View top bowling leaderboard"):
    st.dataframe(
        top_bowlers.sort_values("wickets", ascending=False),
        width="stretch",
        hide_index=True,
    )

st.divider()

# ---------- Season trends ----------
section("📈 Season Run Trends", "Track total batter runs in the matches available for each season.")

season_trends = (
    filtered.groupby("season", as_index=False)
    .agg(
        runs=("batter_runs", "sum"),
        matches=("match_id", "nunique"),
    )
    .sort_values("season")
)
fig = px.line(
    season_trends,
    x="season",
    y="runs",
    markers=True,
    title="Total batter runs by season",
    labels={"season": "IPL season", "runs": "Batter runs"},
)
fig.update_traces(line=dict(color=LIME, width=3), marker=dict(size=8, color=LIME))
fig.update_xaxes(type="category")
st.plotly_chart(style_figure(fig, height=360), width="stretch")

with st.expander("View season summary table"):
    st.dataframe(season_trends, width="stretch", hide_index=True)

# ---------- Individual batter explorer ----------
st.divider()
section(
    "🔎 Individual Batter Explorer",
    "Choose a batter in the sidebar to explore their available season-by-season record.",
)

if selected_player == "All players":
    st.info("Choose a batter from the sidebar to display their individual performance.")
else:
    # Intentionally use all available dataset seasons, independent of the dashboard filter.
    stats = get_batter_stats(selected_player, deliveries)
    player_summary = stats["season_data"]

    if player_summary.empty:
        st.warning("No records found for this batter.")
    else:
        st.markdown(f"### {selected_player}")
        a, b, c, d, e = st.columns(5)
        a.metric("CAREER RUNS", f'{stats["Runs"]:,}')
        b.metric("MATCHES", f'{stats["Matches"]:,}')
        c.metric("STRIKE RATE", f'{stats["Strike Rate"]:.2f}')
        d.metric("FOURS", f'{stats["Fours"]:,}')
        e.metric("SIXES", f'{stats["Sixes"]:,}')

        st.dataframe(
            player_summary[
                ["season", "matches", "runs", "balls_faced", "fours", "sixes", "strike_rate"]
            ],
            width="stretch",
            hide_index=True,
        )

        left, right = st.columns(2)
        with left:
            fig = px.bar(
                player_summary,
                x="season",
                y="runs",
                text="runs",
                title=f"{selected_player} · runs by season",
                labels={"season": "Season", "runs": "Runs"},
                color_discrete_sequence=[LIME],
            )
            fig.update_traces(textposition="outside")
            fig.update_xaxes(type="category")
            st.plotly_chart(style_figure(fig), width="stretch")

        with right:
            fig = px.line(
                player_summary,
                x="season",
                y="strike_rate",
                markers=True,
                title=f"{selected_player} · strike rate by season",
                labels={"season": "Season", "strike_rate": "Strike rate"},
            )
            fig.update_traces(line=dict(color=CYAN, width=3), marker=dict(size=8))
            fig.update_xaxes(type="category")
            st.plotly_chart(style_figure(fig), width="stretch")

# ---------- Player comparison ----------
st.divider()
section(
    "⚔️ Head-to-Head Player Comparison",
    "Compare two batters using career totals and season-by-season run production.",
)

col1, col2 = st.columns(2)
default1 = players.index("V Kohli") if "V Kohli" in players else 0
default2 = players.index("RG Sharma") if "RG Sharma" in players else min(1, len(players) - 1)

with col1:
    batter1 = st.selectbox(
        "First batter",
        options=players,
        index=default1,
        key="comparison_batter1",
    )
with col2:
    batter2 = st.selectbox(
        "Second batter",
        options=players,
        index=default2,
        key="comparison_batter2",
    )

if batter1 == batter2:
    st.warning("Select two different batters to compare their performance.")
else:
    stats1 = get_batter_stats(batter1, deliveries)
    stats2 = get_batter_stats(batter2, deliveries)

    comparison_df = pd.DataFrame([
        {k: v for k, v in stats1.items() if k != "season_data"},
        {k: v for k, v in stats2.items() if k != "season_data"},
    ])
    st.dataframe(comparison_df, width="stretch", hide_index=True)

    fig = px.bar(
        comparison_df,
        x="Player",
        y="Runs",
        color="Player",
        text="Runs",
        title="Career runs comparison",
        color_discrete_sequence=[LIME, CYAN],
    )
    fig.update_traces(textposition="outside")
    st.plotly_chart(style_figure(fig, height=330), width="stretch")

    season1 = stats1["season_data"][["season", "runs"]].rename(
        columns={"runs": batter1}
    )
    season2 = stats2["season_data"][["season", "runs"]].rename(
        columns={"runs": batter2}
    )
    season_comparison = pd.merge(
        season1, season2, on="season", how="outer"
    ).fillna(0).sort_values("season")

    fig = px.line(
        season_comparison,
        x="season",
        y=[batter1, batter2],
        markers=True,
        title="Season-by-season runs comparison",
        labels={"season": "IPL season", "value": "Runs", "variable": "Player"},
        color_discrete_sequence=[LIME, CYAN],
    )
    fig.update_xaxes(type="category")
    st.plotly_chart(style_figure(fig), width="stretch")

# ---------- Footer ----------
st.markdown(
    """
    <div class="footer">
        IPL PERFORMANCE ANALYTICS · Built with Streamlit, Pandas and Plotly<br>
        Source: locally processed Cricsheet match files. Figures reflect the available
        dataset and should be validated against official scorecards before publication.
    </div>
    """,
    unsafe_allow_html=True,
)
