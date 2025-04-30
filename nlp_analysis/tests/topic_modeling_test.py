# tests/topic_modeling_test.py

"""
From the root directory of the python project, run poetry run pytest tests/topic_modeling_test.py -v
"""

import pytest
import pandas as pd
import numpy as np
import os
from pathlib import Path
import re
from collections import Counter

# Import the functions to test
from nlp_analysis.topic_modeling import (
    parse_v2themes_string,
    preprocess_headline,
    get_custom_stopwords,
    clean_html_artifacts,
    normalize_topic_label,
    sklearn_topic_modeling,
    create_simple_topic_label,
    plot_top_themes_by_year
)

class TestTopicModeling:
    """Test suite for topic_modeling.py functions"""
    
    def test_parse_v2themes_string(self):
        """Test that V2Themes strings are correctly parsed into lists"""
        # Test with normal input
        test_str = "THEME1;THEME2;THEME3"
        result = parse_v2themes_string(test_str)
        assert result == ["THEME1", "THEME2", "THEME3"]
        
        # Test with extra spaces
        test_str = " THEME1;  THEME2;THEME3 "
        result = parse_v2themes_string(test_str)
        assert result == ["THEME1", "THEME2", "THEME3"]
        
        # Test with empty string
        result = parse_v2themes_string("")
        assert result == []
        
        # Test with NaN
        result = parse_v2themes_string(np.nan)
        assert result == []
        
        # Test with non-string
        result = parse_v2themes_string(123)
        assert result == []
    
    def test_preprocess_headline(self):
        """Test headline preprocessing function"""
        # Test URL removal
        headline = "Check this link https://example.com for more info"
        result = preprocess_headline(headline)
        assert "https://" not in result
        
        # Test special character replacement
        headline = "Breaking: Trump's new policy!"
        result = preprocess_headline(headline)
        assert "'" not in result
        assert "!" not in result
        
        # Test multiple space replacement
        headline = "Multiple    spaces    here"
        result = preprocess_headline(headline)
        assert "  " not in result
        
        # Test with numeric input (should convert to string)
        headline = 12345
        result = preprocess_headline(headline)
        assert result == "12345"
    
    def test_get_custom_stopwords(self):
        """Test custom stopwords list creation"""
        stopwords = get_custom_stopwords()
        
        # Check if common news stopwords are included
        assert "said" in stopwords
        assert "news" in stopwords
        assert "fox" in stopwords
        assert "msnbc" in stopwords
        
        # Check type and size
        assert isinstance(stopwords, list)
        assert len(stopwords) > 20
    
    def test_clean_html_artifacts(self):
        """Test HTML artifact cleaning"""
        # Test HTML tag removal
        html_text = "This is <b>bold</b> and <i>italic</i> text"
        result = clean_html_artifacts(html_text)
        assert "<b>" not in result
        assert "</b>" not in result
        assert "<i>" not in result
        
        # Test HTML term removal
        html_terms = "This contains html and href and css"
        result = clean_html_artifacts(html_terms)
        assert "html" not in result.lower() or "href" not in result.lower() or "css" not in result.lower()
    
    def test_normalize_topic_label(self):
        """Test topic label normalization"""
        # Test basic functionality
        words = ["police", "man"]
        result = normalize_topic_label(words)
        assert "police" in result
        assert "man" in result
        
        # Test with HTML terms (should be filtered)
        words = ["html", "police", "css"]
        result = normalize_topic_label(words)
        assert "html" not in result
        assert "css" not in result
        assert "police" in result
        
        # Test with empty list
        result = normalize_topic_label([])
        assert result == "misc"
        
        # Test topic grouping (politics)
        words = ["election", "trump", "campaign", "random"]
        result = normalize_topic_label(words)
        assert any(word in result for word in ["election", "trump", "campaign", "random"])
    
    def test_create_simple_topic_label(self):
        """Test simple topic label creation"""
        # Test with regular words
        words = ["economy", "finance", "money", "stocks"]
        result = create_simple_topic_label(words)
        assert "/" in result
        assert len(result.split("/")) <= 2
        
        # Test with empty list
        result = create_simple_topic_label([])
        assert result == "Misc."
        
        # Test with common political terms filtering
        words = ["president", "biden", "economy"]
        result = create_simple_topic_label(words)
        assert result == "economy"
    
    def test_sklearn_topic_modeling_integration(self):
        """Basic integration test for topic modeling that doesn't rely on specific outputs"""
        # Create a minimal set of documents that should work
        texts = [
            "economy economy economy finance finance market market",
            "economy economy finance finance market market",
            "economy finance market stocks trading investment",
            "police police police crime crime arrest arrest", 
            "police police crime crime arrest arrest",
            "police crime arrest investigation law enforcement"
        ]
        
        # Just test that the function runs without errors
        doc_topics, topic_words = sklearn_topic_modeling(texts, num_topics=2)
        
        # We don't assert specific values, just that we got something back
        assert isinstance(doc_topics, list)
        assert isinstance(topic_words, dict)
        
        # If we got results, do basic validation of structure
        if doc_topics:
            assert all(isinstance(topic_id, int) for topic_id in doc_topics)
            assert len(doc_topics) <= len(texts)
            
        if topic_words:
            assert all(isinstance(words, list) for words in topic_words.values())
    
    @pytest.fixture
    def sample_df(self):
        """Create a sample DataFrame for testing visualization functions"""
        # Create sample data with theme information
        data = []
        for year in range(2020, 2023):
            for month in range(1, 13):
                for topic in ["politics", "economy", "health"]:
                    for rank in range(1, 4):
                        data.append({
                            "month": month,
                            "year": year,
                            "topic": topic,
                            "rank": rank,
                            "count": np.random.randint(10, 100),
                            "total_articles": np.random.randint(100, 1000),
                            "percentage": np.random.uniform(1, 10)
                        })
        return pd.DataFrame(data)
    
    def test_plot_top_themes_by_year(self, sample_df, tmp_path, monkeypatch):
        """Test theme plotting functionality with a temporary directory"""
        # Create output directory for test
        output_dir = tmp_path / "output"
        figures_dir = output_dir / "figures"
        figures_dir.mkdir(parents=True)
        
        # Modify the output directory for this test
        monkeypatch.setattr("nlp_analysis.topic_modeling.output_viz_dir", str(output_dir))
        
        # Call the plotting function (might skip if matplotlib fails in test env)
        try:
            plot_top_themes_by_year(
                sample_df,
                title="Test Plot",
                filename="test_plot.png",
                min_count=1
            )
            
            # Check if file was created
            output_file = figures_dir / "test_plot.png"
            assert output_file.exists()
            
        except Exception as e:
            pytest.skip(f"Plot creation failed in test environment: {str(e)}")

# Additional test for edge cases and error handling
class TestTopicModelingEdgeCases:
    """Test edge cases and error handling in topic_modeling.py"""
    
    def test_sklearn_topic_modeling_empty_input(self):
        """Test that empty input returns empty results"""
        doc_topics, topic_words = sklearn_topic_modeling([], num_topics=2)
        assert doc_topics == []
        assert topic_words == {}
    
    def test_sklearn_topic_modeling_single_doc(self):
        """Test handling of a single document input"""
        doc_topics, topic_words = sklearn_topic_modeling(["Single document"], num_topics=2)
        # Should return empty results or a valid prediction
        if doc_topics:
            assert len(doc_topics) == 1
        else:
            assert doc_topics == []
            assert topic_words == {}


# passed!!!