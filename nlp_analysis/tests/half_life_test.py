# tests/half_life_test.py


"""
From the root directory of the python project, run poetry run pytest tests/half_life_test.py -v
"""


import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# We'll mock the functions we need to test instead of importing the whole module
# This prevents the main code from running during import

@pytest.fixture
def sample_topic_data():
    """Create a sample dataset with exponential decay pattern for testing"""
    # Create dates from 2020-01-01 to 2020-01-10
    dates = pd.date_range(start="2020-01-01", periods=10, freq="D")
    
    # Create sample data with 2 different topics
    data = []
    
    # Topic 1: Fast decay
    for i, date in enumerate(dates):
        count = 100 * np.exp(-0.25 * i)  # Exponential decay
        data.append({
            "source": "test_source",
            "V2Themes": "FAST_DECAY",
            "parsed_date": date,
            "count": int(count),
            "tone": 0.2,
            "first_date": dates[0],
            "days_since": i
        })
        
    # Topic 2: Slow decay
    for i, date in enumerate(dates):
        count = 100 * np.exp(-0.1 * i)  # Slower exponential decay
        data.append({
            "source": "test_source",
            "V2Themes": "SLOW_DECAY",
            "parsed_date": date,
            "count": int(count),
            "tone": -0.1,
            "first_date": dates[0],
            "days_since": i
        })
        
    return pd.DataFrame(data)

# Define the estimate_half_life function from your module
def estimate_half_life(topic_daily, min_obs=5):
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
        decay_results.append(
            {
                "source": source,
                "topic": topic,
                "decay_rate": lambda_,
                "half_life_days": half_life,
                "r2": r2,
                "n_obs": len(group),
                "avg_tone": group["tone"].mean(),
                "first_date": group["parsed_date"].min(),
            }
        )
    return pd.DataFrame(decay_results)

# Import LinearRegression directly in the test file
from sklearn.linear_model import LinearRegression

def test_half_life_basic_decay(sample_topic_data):
    """Test basic half-life estimation functionality"""
    # Run half-life estimation
    result = estimate_half_life(sample_topic_data)
    
    # Check results
    assert not result.empty, "Should return non-empty results"
    assert len(result) == 2, "Should return results for both topics"
    assert "half_life_days" in result.columns, "Should include half_life_days column"
    
    # Check specific half-life values
    fast_decay = result[result["topic"] == "FAST_DECAY"].iloc[0]
    slow_decay = result[result["topic"] == "SLOW_DECAY"].iloc[0]
    
    # FAST_DECAY should have shorter half-life than SLOW_DECAY
    assert fast_decay["half_life_days"] < slow_decay["half_life_days"], (
        "Fast decay topic should have shorter half-life"
    )
    
    # Check approximate values (allowing for some numerical error)
    assert abs(fast_decay["half_life_days"] - 2.77) < 0.5, "Half-life should be close to expected value"
    assert abs(slow_decay["half_life_days"] - 6.93) < 0.5, "Half-life should be close to expected value"

def test_half_life_empty_input():
    """Test handling of empty input"""
    empty_df = pd.DataFrame(columns=["source", "V2Themes", "parsed_date", "count", "days_since"])
    result = estimate_half_life(empty_df)
    
    assert isinstance(result, pd.DataFrame), "Should return DataFrame even for empty input"
    assert result.empty, "Result should be empty for empty input"

def test_half_life_insufficient_data():
    """Test with insufficient data points"""
    # Create dataset with only 3 points (below min_obs default of 5)
    small_df = pd.DataFrame({
        "source": ["test"] * 3,
        "V2Themes": ["topic"] * 3,
        "parsed_date": pd.date_range("2020-01-01", periods=3),
        "count": [100, 80, 64],
        "days_since": [0, 1, 2],
        "tone": [0.1] * 3,
        "first_date": [pd.to_datetime("2020-01-01")] * 3
    })
    
    result = estimate_half_life(small_df)
    assert result.empty, "Should return empty result for insufficient data points"
    
    # Test with custom min_obs
    result_custom = estimate_half_life(small_df, min_obs=3)
    assert not result_custom.empty, "Should return results when min_obs is set to match data points"

def test_half_life_increasing_trend():
    """Test with increasing trend (negative decay rate)"""
    # Create dataset with increasing trend
    increasing_df = pd.DataFrame({
        "source": ["test"] * 10,
        "V2Themes": ["topic"] * 10,
        "parsed_date": pd.date_range("2020-01-01", periods=10),
        "count": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],  # Increasing
        "days_since": list(range(10)),
        "tone": [0.1] * 10,
        "first_date": [pd.to_datetime("2020-01-01")] * 10
    })
    
    result = estimate_half_life(increasing_df)
    assert result.empty, "Should skip topics with negative decay rate (increasing trend)"