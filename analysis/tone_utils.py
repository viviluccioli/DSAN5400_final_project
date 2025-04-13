
import pandas as pd
from transformers import pipeline
from afinn import Afinn
import os

afinn = Afinn()

def load_data(base_dir, media_sources, year, election_day, period):
    all_data = []
    for source in media_sources:
        file_path = os.path.join(base_dir, source, f"{source}{year}.csv")
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            df["media"] = source
            df["year"] = year
            df["parsed_date"] = pd.to_datetime(df["parsed_date"], errors='coerce')
            df = df.dropna(subset=["parsed_date"])
            election_day = pd.to_datetime(election_day)
            if election_day.tzinfo is None:
                election_day = election_day.tz_localize("UTC")
            if period == "before":
                mask = (df["parsed_date"] >= (election_day - pd.Timedelta(days=30))) & \
                       (df["parsed_date"] < election_day)
            elif period == "after":
                mask = (df["parsed_date"] > election_day) & \
                       (df["parsed_date"] <= (election_day + pd.Timedelta(days=30)))
            df_filtered = df.loc[mask]
            all_data.append(df_filtered)
    if not all_data:
        return pd.DataFrame()
    df_all = pd.concat(all_data, ignore_index=True)
    df_all["headline"] = df_all["headline_from_url"].astype(str).fillna("")
    df_all["gdelt_tone"] = pd.to_numeric(df_all["V2Tone"].str.split(",", expand=True)[0], errors="coerce")
    return df_all

def compute_afinn_tone(text):
    words = text.split()
    score = afinn.score(text)
    return (score / len(words)) * 100 if words else 0.0

def run_sentiment(df, output_csv_path=None):
    sentiment_model = pipeline("sentiment-analysis", model="mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis")
    texts = df["headline"].tolist()
    results = sentiment_model(texts, batch_size=32, truncation=True)

    # 手动映射 label（统一为大写）
    label_map = {
        "positive": "POSITIVE",
        "neutral": "NEUTRAL",
        "negative": "NEGATIVE"
    }
    df["sentiment_label"] = [label_map.get(x.get("label", "").lower(), "UNKNOWN") for x in results]
    df["sentiment_score"] = [x.get("score", 0.0) for x in results]

    df["signed_score"] = df["sentiment_score"].where(
        df["sentiment_label"] == "POSITIVE",
        -df["sentiment_score"]
    )
    df["afinn_tone"] = df["headline"].apply(compute_afinn_tone)

    if output_csv_path:
        df.to_csv(output_csv_path, index=False)
    return df
