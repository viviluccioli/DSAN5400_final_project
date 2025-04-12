import os
import logging
import pandas as pd
from analysis.tone_utils import load_data, run_sentiment

logging.basicConfig(filename="logs/tone_analysis.log", level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def analyze_year(year, election_day):
    label = f"{year} - Combined 60 Day Window"
    logging.info(f"Processing: {label}")

    df_list = []
    for source in ["abc", "msnbc", "fox"]:
        file_path = os.path.join("data", source, f"{source}{year}.csv")
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            df["media"] = source
            df["year"] = year
            df["parsed_date"] = pd.to_datetime(df["parsed_date"], errors='coerce')
            df = df.dropna(subset=["parsed_date"])
            df_list.append(df)
    if not df_list:
        logging.warning(f"No data found for {label}")
        return

    df_all = pd.concat(df_list, ignore_index=True)
    election_day = pd.to_datetime(election_day)
    if election_day.tzinfo is None:
        election_day = election_day.tz_localize("UTC")

    window_mask = (df_all["parsed_date"] >= (election_day - pd.Timedelta(days=30))) & \
                  (df_all["parsed_date"] <= (election_day + pd.Timedelta(days=30)))
    df_filtered = df_all.loc[window_mask].copy()
    df_filtered["headline"] = df_filtered["headline_from_url"].astype(str).fillna("")
    df_filtered["gdelt_tone"] = pd.to_numeric(df_filtered["V2Tone"].str.split(",", expand=True)[0], errors="coerce")


    df_filtered = run_sentiment(df_filtered)

    for media in df_filtered["media"].unique():
        df_media = df_filtered[df_filtered["media"] == media]
        file_path = os.path.join("data", media, f"{media}{year}.csv")
        if os.path.exists(file_path):
            original_df = pd.read_csv(file_path)
            if "afinn_tone_score" not in original_df.columns:
                original_df["afinn_tone_score"] = pd.NA
            tone_map = dict(zip(df_media["headline_from_url"], df_media["afinn_tone"]))
            original_df.loc[original_df["headline_from_url"].isin(tone_map.keys()), "afinn_tone_score"] = \
                original_df["headline_from_url"].map(tone_map)
            original_df.to_csv(file_path, index=False)
            logging.info(f"Updated file with afinn tone: {file_path}")

    summary = {
        "total": len(df_filtered),
        "positive": (df_filtered["sentiment_label"] == "POSITIVE").sum(),
        "negative": (df_filtered["sentiment_label"] == "NEGATIVE").sum(),
        "neutral": len(df_filtered) - ((df_filtered["sentiment_label"] == "POSITIVE") | (df_filtered["sentiment_label"] == "NEGATIVE")).sum(),
        "avg_gdelt": df_filtered["gdelt_tone"].mean(),
        "avg_model": df_filtered["signed_score"].mean(),
        "avg_afinn": df_filtered["afinn_tone"].mean()
    }

    print(f"\n{label} Election Stats:")
    for k, v in summary.items():
        print(f"{k.capitalize()}: {v:.4f}" if isinstance(v, float) else f"{k.capitalize()}: {v}")
    logging.info(f"Finished {label}: {summary}")

if __name__ == "__main__":
    elections = {
        2016: "2016-11-08",
        2020: "2020-11-03",
        2024: "2024-11-05"
    }
    for year, date in elections.items():
        analyze_year(year, date)
