import os
import logging
import pandas as pd
from analysis.tone_utils import run_sentiment

logging.basicConfig(filename="logs/tone_analysis.log", level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def analyze_year(year, election_day):
    label = f"{year} - Combined 60 Day Window"
    logging.info(f"Processing: {label}")

    df_list = []
    for source in ["abc", "msnbc", "fox"]:
        file_path = os.path.join("data", source, f"{source}{year}.csv")
        if os.path.exists(file_path):
            df = pd.read_csv(file_path, on_bad_lines="skip")
            df["media"] = source
            df["year"] = year
            df["parsed_date"] = pd.to_datetime(df["parsed_date"], errors='coerce')
            df = df.dropna(subset=["parsed_date"])
            df["url"] = df.get("url", "")  # fallback
            df_list.append(df)
    if not df_list:
        logging.warning(f"No data found for {label}")
        return

    df_all = pd.concat(df_list, ignore_index=True)
    election_day = pd.to_datetime(election_day)

    window_mask = (df_all["parsed_date"] >= (election_day - pd.Timedelta(days=30))) & \
                  (df_all["parsed_date"] <= (election_day + pd.Timedelta(days=30)))
    df_filtered = df_all.loc[window_mask].copy()

    df_filtered = run_sentiment(df_filtered)

    for media in df_filtered["media"].unique():
        df_media = df_filtered[df_filtered["media"] == media]
        file_path = os.path.join("data", media, f"{media}{year}.csv")
        if os.path.exists(file_path):
            original_df = pd.read_csv(file_path)

            vader_sentiment_map = dict(zip(df_media["url"], df_media["vader_sentiment_analysis"]))
            vader_score_map = dict(zip(df_media["url"], df_media["vader_tone_score"]))
            afinn_map = dict(zip(df_media["url"], df_media["afinn_tone_score"]))
            label_map = dict(zip(df_media["url"], df_media["RoBERTa_sentiment_label"]))

            original_df["vader_sentiment_analysis"] = original_df["url"].map(vader_sentiment_map)
            original_df["vader_tone_score"] = original_df["url"].map(vader_score_map)
            original_df["afinn_tone_score"] = original_df["url"].map(afinn_map)
            original_df["RoBERTa_sentiment_label"] = original_df["url"].map(label_map)

            original_df.to_csv(file_path, index=False)
            logging.info(f"Updated file: {file_path}")

    # 极化度计算
    df_filtered["is_extreme"] = df_filtered["RoBERTa_sentiment_label"].isin(["POSITIVE", "NEGATIVE"])
    polarization = df_filtered["is_extreme"].mean()

    print(f"\n{label} Election Stats:")
    print(f"Total articles: {len(df_filtered)}")
    print(f"Positive (VADER): {(df_filtered['vader_sentiment_analysis'] == 1).sum()}")
    print(f"Negative (VADER): {(df_filtered['vader_sentiment_analysis'] == 0).sum()}")
    print(f"Avg VADER Score: {df_filtered['vader_tone_score'].mean():.4f}")
    print(f"Avg AFINN Score: {df_filtered['afinn_tone_score'].mean():.4f}")
    print(f"Polarization (RoBERTa-based): {polarization:.2%}")
    logging.info(f"Finished {label} with {len(df_filtered)} rows")

if __name__ == "__main__":
    elections = {
        2016: "2016-11-08",
        2020: "2020-11-03",
        2024: "2024-11-05"
    }
    for year, date in elections.items():
        analyze_year(year, date)
