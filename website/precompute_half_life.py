# precompute_half_life.py

import pandas as pd
import glob
import numpy as np
from sklearn.linear_model import LinearRegression

# Load your data
sources = {
    "Fox News": glob.glob("../data/fox/fox*.csv"),
    "ABC News": glob.glob("../data/abc/abc*.csv"),
    "MSNBC": glob.glob("../data/msnbc/msnbc*.csv"),
}


def load_and_label_data(source_paths: dict) -> pd.DataFrame:
    df_list = []
    for source_name, file_list in source_paths.items():
        for file in file_list:
            df = pd.read_csv(file, encoding="latin1")
            df["source"] = source_name
            df_list.append(df)
    return pd.concat(df_list, ignore_index=True)


def preprocess_combined_df(df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "parsed_date",
        "url",
        "headline_from_url",
        "V2Themes",
        "V2Locations",
        "V2Persons",
        "V2Organizations",
        "V2Tone",
        "source",
    ]
    df = df.loc[:, columns].copy()
    df["parsed_date"] = pd.to_datetime(
        df["parsed_date"].astype(str).str.replace(" UTC", "", regex=False),
        errors="coerce",
    )
    df = df.dropna(subset=["parsed_date", "V2Themes"])
    df["V2Themes"] = df["V2Themes"].str.split(";")
    df = df.explode("V2Themes").assign(V2Themes=lambda x: x["V2Themes"].str.strip())
    df["V2Tone"] = pd.to_numeric(df["V2Tone"], errors="coerce")
    return df


def get_topic_daily(df: pd.DataFrame) -> pd.DataFrame:
    topic_daily = (
        df.groupby(["source", "V2Themes", "parsed_date"])
        .agg(count=("headline_from_url", "count"), tone=("V2Tone", "mean"))
        .reset_index()
    )
    topic_daily["parsed_date"] = pd.to_datetime(topic_daily["parsed_date"])
    first_dates = (
        topic_daily.groupby(["source", "V2Themes"])["parsed_date"]
        .min()
        .reset_index()
        .rename(columns={"parsed_date": "first_date"})
    )
    topic_daily = topic_daily.merge(first_dates, on=["source", "V2Themes"])
    topic_daily["days_since"] = (
        topic_daily["parsed_date"] - topic_daily["first_date"]
    ).dt.days
    return topic_daily


def estimate_half_life(topic_daily: pd.DataFrame) -> pd.DataFrame:
    decay_results = []
    for (source, topic), group in topic_daily.groupby(["source", "V2Themes"]):
        if len(group) < 2:
            continue
        X = group["days_since"].values.reshape(-1, 1)
        y = np.log1p(group["count"].values)
        model = LinearRegression().fit(X, y)
        lambda_ = -model.coef_[0]
        if lambda_ <= 0 or lambda_ < 1e-5:
            continue
        half_life = np.log(2) / lambda_
        decay_results.append(
            {
                "source": source,
                "topic": topic,
                "decay_rate": lambda_,
                "half_life_days": half_life,
                "r2": model.score(X, y),
                "n_obs": len(group),
                "avg_tone": group["tone"].mean(),
                "first_date": group["parsed_date"].min(),
            }
        )
    return pd.DataFrame(decay_results)


# Run the full process
print("Loading and processing data...")
raw_df = load_and_label_data(sources)
clean_df = preprocess_combined_df(raw_df)
topic_df = get_topic_daily(clean_df)
half_life_df = estimate_half_life(topic_df)

# Save output
half_life_df.to_csv("data/half_life_summary.csv", index=False)
