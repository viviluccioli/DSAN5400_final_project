import pandas as pd
import glob
import numpy as np
from sklearn.linear_model import LinearRegression

def load_and_label_data(source_paths: dict) -> pd.DataFrame:
    """Load CSV files and label them by source."""
    df_list = []
    for source_name, file_list in source_paths.items():
        for file in file_list:
            df = pd.read_csv(file)
            df['source'] = source_name
            df_list.append(df)
    return pd.concat(df_list, ignore_index=True)

def preprocess_combined_df(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and structure the dataset."""
    columns = [
        "parsed_date", "url", "headline_from_url",
        "V2Themes", "V2Locations", "V2Persons",
        "V2Organizations", "V2Tone", "source"
    ]
    df = df[columns]
    df["parsed_date"] = pd.to_datetime(df["parsed_date"], errors="coerce").dt.tz_localize(None)
    df = df.dropna(subset=["parsed_date", "V2Themes"])
    df["V2Themes"] = df["V2Themes"].str.split(";").explode().str.strip()
    df["V2Tone"] = pd.to_numeric(df["V2Tone"], errors="coerce")
    return df

def get_topic_daily(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate article counts and average tone by source, theme, and date."""
    topic_daily = (
        df.groupby(["source", "V2Themes", "parsed_date"])
        .agg(count=("headline_from_url", "count"), tone=("V2Tone", "mean"))
        .reset_index()
    )
    topic_daily["parsed_date"] = pd.to_datetime(topic_daily["parsed_date"])
    first_dates = (
        topic_daily.groupby(["source", "V2Themes"])["parsed_date"]
        .min().reset_index().rename(columns={"parsed_date": "first_date"})
    )
    topic_daily = topic_daily.merge(first_dates, on=["source", "V2Themes"])
    topic_daily["first_date"] = pd.to_datetime(topic_daily["first_date"])
    topic_daily["days_since"] = (topic_daily["parsed_date"] - topic_daily["first_date"]).dt.days
    return topic_daily

def estimate_half_life(topic_daily: pd.DataFrame, min_obs: int = 5) -> pd.DataFrame:
    """Estimate topic half-life via exponential decay."""
    decay_results = []
    for (source, topic), group in topic_daily.groupby(["source", "V2Themes"]):
        if len(group) < min_obs:
            continue
        X = group["days_since"].values.reshape(-1, 1)
        y = np.log1p(group["count"].values)
        model = LinearRegression().fit(X, y)
        lambda_ = -model.coef_[0]
        r2 = model.score(X, y)
        if lambda_ <= 0:
            continue
        half_life = np.log(2) / lambda_
        decay_results.append({
            "source": source,
            "topic": topic,
            "decay_rate": lambda_,
            "half_life_days": half_life,
            "r2": r2,
            "n_obs": len(group),
            "avg_tone": group["tone"].mean(),
            "first_date": group["parsed_date"].min()
        })
    return pd.DataFrame(decay_results)

def average_half_life_by_source(half_life_df: pd.DataFrame) -> pd.Series:
    """Compute average half-life per source."""
    return half_life_df.groupby("source")["half_life_days"].mean().sort_values()

def get_yearly_trends(half_life_df: pd.DataFrame) -> pd.DataFrame:
    """Return average half-life by source per year."""
    half_life_df["year"] = half_life_df["first_date"].dt.year
    return half_life_df.groupby(["source", "year"])["half_life_days"].mean().unstack()

def filter_topic(half_life_df: pd.DataFrame, keyword: str) -> pd.DataFrame:
    """Return subset of topics matching keyword prefix."""
    return half_life_df[half_life_df["topic"].str.startswith(keyword)]

def categorize_by_tone(half_life_df: pd.DataFrame, tone_threshold: float = 0.0) -> pd.DataFrame:
    """Add tone category column (positive/negative/neutral)."""
    def tone_label(t):
        if pd.isna(t):
            return "unknown"
        elif t > tone_threshold:
            return "positive"
        elif t < -tone_threshold:
            return "negative"
        else:
            return "neutral"
    half_life_df["tone_category"] = half_life_df["avg_tone"].apply(tone_label)
    return half_life_df

#sample script for site
""" from half_life import (
    load_and_label_data, preprocess_combined_df,
    get_topic_daily, estimate_half_life,
    average_half_life_by_source, get_yearly_trends,
    filter_topic, categorize_by_tone
)

sources = {
    'msnbc': glob.glob("../data/msnbc/msnbc*.csv"),
    'abc': glob.glob("../data/abc/abc*.csv"),
    'fox': glob.glob("../data/fox/fox*.csv"),
}

raw_df = load_and_label_data(sources)
clean_df = preprocess_combined_df(raw_df)
topic_df = get_topic_daily(clean_df)
half_life_df = estimate_half_life(topic_df) """
