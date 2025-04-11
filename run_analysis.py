import os
import logging
import pandas as pd
from analysis.tone_utils import load_data, run_sentiment

logging.basicConfig(filename="logs/tone_analysis.log", level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def analyze_year(year, election_day):
    for period in ["before", "after"]:
        label = f"{year} - {period.title()}"
        logging.info(f"Processing: {label}")
        df = load_data("data", ["abc", "msnbc", "fox"], year, election_day, period)
        if df.empty:
            logging.warning(f"No data found for {label}")
            continue

        df = run_sentiment(df)

        for media in df["media"].unique():
            df_media = df[df["media"] == media]
            file_path = os.path.join("data", media, f"{media}{year}.csv")
            try:
                if os.path.exists(file_path):
                    original_df = pd.read_csv(file_path)

                    if "afinn_tone_score" not in original_df.columns:
                        original_df["afinn_tone_score"] = None
                    tone_map = dict(zip(df_media["headline_from_url"], df_media["afinn_tone"]))
                    original_df["afinn_tone_score"] = original_df["headline_from_url"].map(tone_map)
                    original_df.to_csv(file_path, index=False)
                    logging.info(f"✅ Updated file with afinn tone: {file_path}")
            except Exception as e:
                logging.error(f"❌ Failed to update {file_path}: {str(e)}")

        summary = {
            "total": len(df),
            "positive": (df["sentiment_label"] == "POSITIVE").sum(),
            "negative": (df["sentiment_label"] == "NEGATIVE").sum(),
            "neutral": len(df) - ((df["sentiment_label"] == "POSITIVE") | (df["sentiment_label"] == "NEGATIVE")).sum(),
            "avg_gdelt": df["gdelt_tone"].mean(),
            "avg_model": df["signed_score"].mean(),
            "avg_afinn": df["afinn_tone"].mean()
        }

        print(f"\n {label} Election Stats:")
        for k, v in summary.items():
            print(f"{k.capitalize()}: {v}")
        logging.info(f"Finished {label}: {summary}")

if __name__ == "__main__":
    elections = {
        2016: "2016-11-08",
        2020: "2020-11-03",
        2024: "2024-11-05"
    }
    for year, date in elections.items():
        analyze_year(year, date)
