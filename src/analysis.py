
import json
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_DIR / "data" / "raw"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"

# Dismissals that are not credited to the bowler.
# Stumped IS credited to the bowler.
NON_BOWLER_WICKETS = {
    "run out",
    "retired hurt",
    "retired out",
    "obstructing the field",
    "hit the ball twice",
    "handled the ball",
}


def load_matches():
    """Load men's T20 match JSON files from the raw data folder."""
    matches = []

    if not RAW_DIR.exists():
        print(f"Raw data folder not found: {RAW_DIR}")
        return matches

    for file_path in sorted(RAW_DIR.glob("*.json")):
        try:
            with file_path.open("r", encoding="utf-8") as file:
                match = json.load(file)

            info = match.get("info", {})

            # The raw folder should contain the IPL dataset.
            if info.get("gender") != "male":
                continue

            if info.get("match_type") != "T20":
                continue

            matches.append((file_path.stem, match))

        except (json.JSONDecodeError, OSError, KeyError) as error:
            print(f"Skipping {file_path.name}: {error}")

    print(f"Loaded {len(matches)} matches.")
    return matches


def extract_deliveries(matches):
    """Convert every delivery into exactly one row."""
    rows = []

    for match_id, match in matches:
        info = match.get("info", {})
        season = info.get("season", "Unknown")

        if isinstance(season, list):
            season = season[0] if season else "Unknown"

        date_values = info.get("dates", [])
        date = date_values[0] if date_values else None
        teams = info.get("teams", [])
        winner = info.get("outcome", {}).get("winner")

        for innings_no, innings in enumerate(
            match.get("innings", []), start=1
        ):
            batting_team = innings.get("team")

            # Standard IPL innings have two competing teams.
            bowling_team = next(
                (team for team in teams if team != batting_team),
                None,
            )

            for over in innings.get("overs", []):
                over_number = over.get("over")

                for delivery_index, delivery in enumerate(
                    over.get("deliveries", [])
                ):
                    runs = delivery.get("runs", {})
                    extras = delivery.get("extras", {})
                    wickets = delivery.get("wickets", [])

                    batter_runs = runs.get("batter", 0)
                    total_runs = runs.get("total", 0)

                    # Wides do not count as balls faced.
                    # No-balls generally do count as balls faced.
                    balls_faced = int("wides" not in extras)

                    # Wides and no-balls are not legal deliveries.
                    legal_ball = int(
                        "wides" not in extras
                        and "noballs" not in extras
                    )

                    # Runs charged to the bowler exclude byes,
                    # leg-byes and penalty runs.
                    bowler_runs = total_runs - (
                        extras.get("byes", 0)
                        + extras.get("legbyes", 0)
                        + extras.get("penalty", 0)
                    )

                    bowler_wickets = sum(
                        1
                        for wicket in wickets
                        if wicket.get("kind") not in NON_BOWLER_WICKETS
                    )

                    # Record every delivery, not only wicket deliveries.
                    rows.append({
                        "match_id": match_id,
                        "date": date,
                        "season": season,
                        "venue": info.get("venue", "Unknown"),
                        "innings": innings_no,
                        "over": over_number,
                        "delivery": delivery_index + 1,
                        "batting_team": batting_team,
                        "bowling_team": bowling_team,
                        "winner": winner,
                        "batter": delivery.get("batter"),
                        "bowler": delivery.get("bowler"),
                        "non_striker": delivery.get("non_striker"),
                        "batter_runs": batter_runs,
                        "total_runs": total_runs,
                        "bowler_runs": bowler_runs,
                        "legal_ball": legal_ball,
                        "balls_faced": balls_faced,
                        "is_four": int(batter_runs == 4),
                        "is_six": int(batter_runs == 6),
                        "is_wicket": int(bool(wickets)),
                        "bowler_wicket": bowler_wickets,
                        "wickets": wickets,
                        "extras": extras,
                    })

    columns = [
        "match_id", "date", "season", "venue", "innings", "over",
        "delivery", "batting_team", "bowling_team", "winner",
        "batter", "bowler", "non_striker", "batter_runs",
        "total_runs", "bowler_runs", "legal_ball", "balls_faced",
        "is_four", "is_six", "is_wicket", "bowler_wicket",
        "wickets", "extras",
    ]

    deliveries = pd.DataFrame(rows, columns=columns)

    if deliveries.empty:
        print("No delivery records were extracted.")
        return deliveries

    print(f"Total delivery records: {len(deliveries):,}")
    print(f"Unique batters: {deliveries['batter'].nunique():,}")
    print(f"Total batter runs: {deliveries['batter_runs'].sum():,}")
    print(f"Total wickets recorded: {deliveries['is_wicket'].sum():,}")
    print("\nSample delivery records:")
    print(
        deliveries[
            ["match_id", "batter", "bowler", "batter_runs", "total_runs"]
        ].head(10).to_string(index=False)
    )

    return deliveries


def build_batting_stats(deliveries):
    """Build player-level batting statistics."""
    if deliveries.empty:
        return pd.DataFrame()

    # Calculate each player's statistics in each innings.
    innings_stats = deliveries.groupby(
        ["match_id", "innings", "batter"],
        as_index=False,
    ).agg(
        runs=("batter_runs", "sum"),
        balls_faced=("balls_faced", "sum"),
        fours=("is_four", "sum"),
        sixes=("is_six", "sum"),
    )

    # Identify dismissals from the wickets list.
    # A player is out if listed as player_out, except retired hurt.
    dismissal_rows = []

    for row in deliveries[
        ["match_id", "innings", "wickets"]
    ].itertuples(index=False):
        for wicket in row.wickets:
            player_out = wicket.get("player_out")
            kind = wicket.get("kind")

            if player_out and kind != "retired hurt":
                dismissal_rows.append({
                    "match_id": row.match_id,
                    "innings": row.innings,
                    "batter": player_out,
                })

    dismissals = pd.DataFrame(
        dismissal_rows,
        columns=["match_id", "innings", "batter"],
    ).drop_duplicates()

    if not dismissals.empty:
        dismissals["out"] = 1
        innings_stats = innings_stats.merge(
            dismissals,
            on=["match_id", "innings", "batter"],
            how="left",
        )
        innings_stats["out"] = innings_stats["out"].fillna(0).astype(int)
    else:
        innings_stats["out"] = 0

    batting = innings_stats.groupby("batter", as_index=False).agg(
        runs=("runs", "sum"),
        innings=("innings", "size"),
        outs=("out", "sum"),
        balls_faced=("balls_faced", "sum"),
        fours=("fours", "sum"),
        sixes=("sixes", "sum"),
        matches=("match_id", "nunique"),
    )

    batting["not_outs"] = batting["innings"] - batting["outs"]

    batting["batting_average"] = (
        batting["runs"] / batting["outs"].replace(0, float("nan"))
    ).round(2)

    batting["strike_rate"] = (
        batting["runs"] * 100
        / batting["balls_faced"].replace(0, float("nan"))
    ).round(2)

    return batting.sort_values(
        ["runs", "strike_rate"],
        ascending=[False, False],
    ).reset_index(drop=True)


def build_bowling_stats(deliveries):
    """Build player-level bowling statistics."""
    if deliveries.empty:
        return pd.DataFrame()

    bowling = deliveries.groupby("bowler", as_index=False).agg(
        runs_conceded=("bowler_runs", "sum"),
        legal_balls=("legal_ball", "sum"),
        wickets=("bowler_wicket", "sum"),
        matches=("match_id", "nunique"),
    )

    bowling["overs"] = (
        (bowling["legal_balls"] // 6).astype(str)
        + "."
        + (bowling["legal_balls"] % 6).astype(str)
    )

    bowling["economy"] = (
        bowling["runs_conceded"] * 6
        / bowling["legal_balls"].replace(0, float("nan"))
    ).round(2)

    bowling["bowling_average"] = (
        bowling["runs_conceded"]
        / bowling["wickets"].replace(0, float("nan"))
    ).round(2)

    bowling["bowling_strike_rate"] = (
        bowling["legal_balls"]
        / bowling["wickets"].replace(0, float("nan"))
    ).round(2)

    return bowling.sort_values(
        ["wickets", "economy"],
        ascending=[False, True],
    ).reset_index(drop=True)


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    matches = load_matches()

    if not matches:
        print("No eligible matches found. Check data/raw/ and the dataset.")
        return

    deliveries = extract_deliveries(matches)

    if deliveries.empty:
        print("No delivery data found.")
        return

    batting = build_batting_stats(deliveries)
    bowling = build_bowling_stats(deliveries)

    deliveries.to_csv(
        PROCESSED_DIR / "deliveries.csv",
        index=False,
    )
    batting.to_csv(
        PROCESSED_DIR / "batting_stats.csv",
        index=False,
    )
    bowling.to_csv(
        PROCESSED_DIR / "bowling_stats.csv",
        index=False,
    )

    print("\nTop 10 run scorers:")
    print(batting.head(10).to_string(index=False))

    print("\nTop 10 wicket takers:")
    print(bowling.head(10).to_string(index=False))

    print(f"\nProcessed CSV files saved to: {PROCESSED_DIR}")


if __name__ == "__main__":
    main()
