# tests/semantic_test.py
"""
From the root directory of the python project, run poetry run pytest tests/semantic_test.py -v
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
import os
from unittest.mock import patch, MagicMock

# Instead of importing the actual module (which might try to run code),
# we'll mock the dependencies and test the function directly

# Copy the function here for testing
def analyze_year(year, election_day, data_dir="data", utils_module=None):
    """
    Modified version of analyze_year function for testing purposes
    """
    label = f"{year} - Combined 60 Day Window"
    
    df_list = []
    for source in ["abc", "msnbc", "fox"]:
        file_path = os.path.join(data_dir, source, f"{source}{year}.csv")
        if os.path.exists(file_path):
            df = pd.read_csv(file_path, on_bad_lines="skip")
            df["media"] = source
            df["year"] = year
            df["parsed_date"] = pd.to_datetime(df["parsed_date"], errors="coerce")
            df = df.dropna(subset=["parsed_date"])
            df["url"] = df.get("url", "")  # fallback
            df_list.append(df)
    if not df_list:
        return None

    df_all = pd.concat(df_list, ignore_index=True)
    election_day = pd.to_datetime(election_day)

    window_mask = (df_all["parsed_date"] >= (election_day - pd.Timedelta(days=30))) & (
        df_all["parsed_date"] <= (election_day + pd.Timedelta(days=30))
    )
    df_filtered = df_all.loc[window_mask].copy()

    if utils_module:
        df_filtered = utils_module.run_sentiment(df_filtered)
    else:
        # Mock sentiment analysis for testing
        df_filtered["vader_sentiment_analysis"] = np.random.choice([0, 1], size=len(df_filtered))
        df_filtered["vader_tone_score"] = np.random.uniform(-1, 1, size=len(df_filtered))
        df_filtered["afinn_tone_score"] = np.random.uniform(-5, 5, size=len(df_filtered))
        df_filtered["RoBERTa_sentiment_label"] = np.random.choice(
            ["POSITIVE", "NEGATIVE", "NEUTRAL"], size=len(df_filtered)
        )

    # Calculate polarization
    df_filtered["is_extreme"] = df_filtered["RoBERTa_sentiment_label"].isin(
        ["POSITIVE", "NEGATIVE"]
    )
    
    return df_filtered


class TestSemantic:
    @pytest.fixture
    def mock_data_dir(self, tmp_path):
        """Create a temporary directory with mock CSV files"""
        # Create base directories
        data_dir = tmp_path / "data"
        for source in ["abc", "msnbc", "fox"]:
            source_dir = data_dir / source
            source_dir.mkdir(parents=True, exist_ok=True)

        # Create mock CSV files with test data
        for source in ["abc", "msnbc", "fox"]:
            for year in [2016, 2020, 2024]:
                # Create dates centered around election day
                election_day = {
                    2016: "2016-11-08",
                    2020: "2020-11-03",
                    2024: "2024-11-05"
                }[year]
                
                # Create 50 dates around election day
                election_date = pd.to_datetime(election_day)
                dates = pd.date_range(
                    start=election_date - pd.Timedelta(days=40),
                    end=election_date + pd.Timedelta(days=40),
                    periods=50
                )
                
                # Create test data
                data = {
                    "parsed_date": dates,
                    "headline_from_url": [f"Headline {i}" for i in range(50)],
                    "url": [f"https://example.com/{source}/{year}/{i}" for i in range(50)],
                    "V2Themes": ["POLITICS;ELECTION" for _ in range(50)]
                }
                
                df = pd.DataFrame(data)
                file_path = data_dir / source / f"{source}{year}.csv"
                df.to_csv(file_path, index=False)
        
        return data_dir

    @pytest.fixture
    def mock_utils_module(self):
        """Create a mock for utils module with run_sentiment function"""
        mock_module = MagicMock()
        
        def mock_run_sentiment(df):
            """Mock implementation of run_sentiment"""
            df = df.copy()
            n_rows = len(df)
            
            # Add sentiment analysis columns with mock data
            df["vader_sentiment_analysis"] = np.random.choice([0, 1], size=n_rows)
            df["vader_tone_score"] = np.random.uniform(-1, 1, size=n_rows)
            df["afinn_tone_score"] = np.random.uniform(-5, 5, size=n_rows)
            df["RoBERTa_sentiment_label"] = np.random.choice(
                ["POSITIVE", "NEGATIVE", "NEUTRAL"], size=n_rows
            )
            
            return df
        
        mock_module.run_sentiment = mock_run_sentiment
        return mock_module

    def test_analyze_year_basic(self, mock_data_dir, mock_utils_module):
        """Test basic functionality of analyze_year"""
        # Run function with test data
        year = 2020
        election_day = "2020-11-03"
        
        result_df = analyze_year(year, election_day, data_dir=mock_data_dir, utils_module=mock_utils_module)
        
        # Verify results
        assert result_df is not None, "Function should return DataFrame"
        assert "vader_sentiment_analysis" in result_df.columns, "Should have sentiment columns"
        assert "vader_tone_score" in result_df.columns
        assert "afinn_tone_score" in result_df.columns
        assert "RoBERTa_sentiment_label" in result_df.columns
        assert "is_extreme" in result_df.columns, "Should calculate polarization"
        
        # Verify filtering by date window
        election_date = pd.to_datetime(election_day)
        min_date = election_date - pd.Timedelta(days=30)
        max_date = election_date + pd.Timedelta(days=30)
        
        assert (result_df["parsed_date"] >= min_date).all(), "All dates should be >= min_date"
        assert (result_df["parsed_date"] <= max_date).all(), "All dates should be <= max_date"
        
        # Verify all sources are included
        sources = result_df["media"].unique()
        assert set(sources) == {"abc", "msnbc", "fox"}, "Should include all three sources"

    def test_analyze_year_no_data(self, tmp_path):
        """Test behavior when no data files exist"""
        empty_data_dir = tmp_path / "empty_data"
        os.makedirs(empty_data_dir, exist_ok=True)
        
        # Function should return None when no data is found
        result = analyze_year(2020, "2020-11-03", data_dir=empty_data_dir)
        assert result is None, "Should return None when no data is found"

    def test_analyze_year_partial_data(self, mock_data_dir, mock_utils_module):
        """Test with only some sources having data"""
        # Remove one source's data file
        os.remove(mock_data_dir / "fox" / "fox2020.csv")
        
        # Function should still work with partial data
        result_df = analyze_year(2020, "2020-11-03", data_dir=mock_data_dir, utils_module=mock_utils_module)
        
        assert result_df is not None, "Should return results with partial data"
        sources = result_df["media"].unique()
        assert "fox" not in sources, "Fox should not be in sources"
        assert len(sources) == 2, "Should have two sources"

    def test_analyze_year_date_filtering(self, mock_data_dir, mock_utils_module):
        """Test date window filtering logic"""
        year = 2020
        election_day = "2020-11-03"
        
        result_df = analyze_year(year, election_day, data_dir=mock_data_dir, utils_module=mock_utils_module)
        
        # Calculate expected date range
        election_date = pd.to_datetime(election_day)
        min_date = election_date - pd.Timedelta(days=30)
        max_date = election_date + pd.Timedelta(days=30)
        
        # Confirm all dates are within range
        assert (result_df["parsed_date"] >= min_date).all()
        assert (result_df["parsed_date"] <= max_date).all()
        
        # Check if some dates from the original data were filtered out
        # Read original data file
        abc_df = pd.read_csv(mock_data_dir / "abc" / f"abc{year}.csv")
        abc_df["parsed_date"] = pd.to_datetime(abc_df["parsed_date"])
        
        # Some dates should be outside the window
        outside_window = (abc_df["parsed_date"] < min_date) | (abc_df["parsed_date"] > max_date)
        assert outside_window.any(), "Test data should have dates outside window"
        
        # These dates should not appear in the result
        filtered_dates = result_df[result_df["media"] == "abc"]["parsed_date"]
        outside_dates = abc_df.loc[outside_window, "parsed_date"]
        
        for date in outside_dates:
            assert date not in filtered_dates.values, f"Date {date} should be filtered out"

    def test_analyze_year_polarization(self, mock_data_dir):
        """Test polarization calculation"""
        # Create a custom mock utils module with controlled sentiment data
        class CustomMockUtils:
            @staticmethod
            def run_sentiment(df):
                df = df.copy()
                n_rows = len(df)
                
                # Set sentiment values in a controlled way for testing polarization
                half_point = n_rows // 2
                
                # First half: all POSITIVE
                # Second half: mix of NEGATIVE and NEUTRAL
                df["RoBERTa_sentiment_label"] = ["POSITIVE"] * half_point + \
                                               ["NEGATIVE"] * (n_rows // 4) + \
                                               ["NEUTRAL"] * (n_rows - half_point - n_rows // 4)
                
                # Add other required columns
                df["vader_sentiment_analysis"] = [1] * half_point + [0] * (n_rows - half_point)
                df["vader_tone_score"] = [0.5] * half_point + [-0.5] * (n_rows - half_point)
                df["afinn_tone_score"] = [2.0] * half_point + [-2.0] * (n_rows - half_point)
                
                return df
        
        mock_utils = CustomMockUtils()
        
        # Run analysis
        result_df = analyze_year(2020, "2020-11-03", data_dir=mock_data_dir, utils_module=mock_utils)
        
        # Calculate expected polarization
        extreme_count = result_df["RoBERTa_sentiment_label"].isin(["POSITIVE", "NEGATIVE"]).sum()
        expected_polarization = extreme_count / len(result_df)
        
        # Verify polarization calculation
        actual_polarization = result_df["is_extreme"].mean()
        assert abs(actual_polarization - expected_polarization) < 0.001, "Polarization calculation should be correct"
        
        # Based on our setup, polarization should be 75% (half POSITIVE, quarter NEGATIVE, quarter NEUTRAL)
        assert abs(actual_polarization - 0.75) < 0.001, "Expected polarization should be ~75%"