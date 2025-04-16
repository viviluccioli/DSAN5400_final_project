import pandas as pd
from half_life import estimate_half_life

def test_half_life_basic_decay():
    # Create fake decaying topic counts
    df = pd.DataFrame({
        "source": ["test"] * 10,
        "V2Themes": ["synthetic_topic"] * 10,
        "parsed_date": pd.date_range("2020-01-01", periods=10, freq="D"),
        "count": [100, 80, 64, 51, 41, 33, 26, 21, 17, 14],
        "tone": [0.1] * 10,
        "first_date": pd.to_datetime("2020-01-01")
    })
    df["days_since"] = (df["parsed_date"] - df["first_date"]).dt.days

    result = estimate_half_life(df)

    assert not result.empty, "Half-life result should not be empty"
    assert "half_life_days" in result.columns, "Result should contain half_life_days"
    assert result.iloc[0]["half_life_days"] > 0, "Half-life should be positive"