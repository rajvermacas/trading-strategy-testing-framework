"""
Tests for data validator module.

Following TDD approach: Red-Green-Refactor
"""

import pytest
from datetime import datetime, timedelta
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from trading_strategy_framework.data.validator import DataValidator


class TestDataValidator:
    """Test class for DataValidator functionality."""

    def test_init_creates_validator(self):
        """Test that DataValidator initializes successfully."""
        validator = DataValidator()
        assert validator is not None

    def test_validate_ohlcv_data_accepts_valid_data(self):
        """Test that valid OHLCV data is accepted."""
        validator = DataValidator()
        valid_data = {
            'Open': 100.0,
            'High': 105.0,
            'Low': 98.0,
            'Close': 103.0,
            'Volume': 1000000
        }
        
        result = validator.validate_ohlcv_data(valid_data)
        assert result is True

    def test_validate_ohlcv_data_rejects_missing_fields(self):
        """Test that data missing required fields is rejected."""
        validator = DataValidator()
        invalid_data = {
            'Open': 100.0,
            'High': 105.0,
            'Low': 98.0
            # Missing Close and Volume
        }
        
        result = validator.validate_ohlcv_data(invalid_data)
        assert result is False

    def test_validate_ohlcv_data_rejects_negative_values(self):
        """Test that negative values are rejected."""
        validator = DataValidator()
        invalid_data = {
            'Open': 100.0,
            'High': 105.0,
            'Low': -98.0,  # Negative value
            'Close': 103.0,
            'Volume': 1000000
        }
        
        result = validator.validate_ohlcv_data(invalid_data)
        assert result is False

    def test_validate_ohlcv_data_rejects_invalid_ohlc_relationships(self):
        """Test that invalid OHLC relationships are rejected."""
        validator = DataValidator()
        invalid_data = {
            'Open': 100.0,
            'High': 95.0,  # High less than Open
            'Low': 98.0,
            'Close': 103.0,
            'Volume': 1000000
        }
        
        result = validator.validate_ohlcv_data(invalid_data)
        assert result is False

    def test_clean_data_filters_invalid_rows(self):
        """Test that clean_data removes invalid rows."""
        validator = DataValidator()
        
        data = [
            {'Open': 100.0, 'High': 105.0, 'Low': 98.0, 'Close': 103.0, 'Volume': 1000000},  # Valid
            {'Open': 100.0, 'High': 95.0, 'Low': 98.0, 'Close': 103.0, 'Volume': 1000000},   # Invalid
            {'Open': 101.0, 'High': 106.0, 'Low': 99.0, 'Close': 104.0, 'Volume': 1100000},  # Valid
        ]
        
        result = validator.clean_data(data)
        assert len(result) == 2  # Only valid rows should remain

    def test_detect_gaps_finds_time_gaps(self):
        """Test that detect_gaps identifies time series gaps."""
        validator = DataValidator()
        
        # Create timestamps with a gap
        base_time = datetime(2023, 1, 1, 9, 0)
        timestamps = [
            base_time,
            base_time + timedelta(hours=1),
            base_time + timedelta(hours=2),
            base_time + timedelta(hours=5),  # 3-hour gap here
            base_time + timedelta(hours=6),
        ]
        
        gaps = validator.detect_gaps(timestamps, expected_interval_minutes=60)
        assert len(gaps) == 1
        assert gaps[0] == 3  # Gap at index 3

    def test_detect_gaps_returns_empty_for_continuous_data(self):
        """Test that detect_gaps returns empty list for continuous data."""
        validator = DataValidator()
        
        # Create continuous timestamps
        base_time = datetime(2023, 1, 1, 9, 0)
        timestamps = [
            base_time + timedelta(hours=i) for i in range(5)
        ]
        
        gaps = validator.detect_gaps(timestamps, expected_interval_minutes=60)
        assert len(gaps) == 0