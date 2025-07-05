"""
Tests for data fetcher module.

Following TDD approach: Red-Green-Refactor
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from trading_strategy_framework.data.fetcher import DataFetcher


class TestDataFetcher:
    """Test class for DataFetcher functionality."""

    def test_init_creates_fetcher_with_default_symbol(self):
        """Test that DataFetcher initializes with default Nifty 50 symbol."""
        fetcher = DataFetcher()
        assert fetcher.symbol == "^NSEI"
        assert fetcher.interval == "1h"

    def test_init_creates_fetcher_with_custom_parameters(self):
        """Test that DataFetcher initializes with custom parameters."""
        fetcher = DataFetcher(symbol="AAPL", interval="1d")
        assert fetcher.symbol == "AAPL"
        assert fetcher.interval == "1d"

    def test_validate_symbol_accepts_valid_symbols(self):
        """Test that valid symbols are accepted."""
        fetcher = DataFetcher()
        # Should not raise exception
        fetcher._validate_symbol("^NSEI")
        fetcher._validate_symbol("AAPL")
        fetcher._validate_symbol("MSFT")

    def test_validate_symbol_rejects_invalid_symbols(self):
        """Test that invalid symbols are rejected."""
        fetcher = DataFetcher()
        with pytest.raises(ValueError):
            fetcher._validate_symbol("")
        with pytest.raises(ValueError):
            fetcher._validate_symbol(None)

    def test_validate_interval_accepts_valid_intervals(self):
        """Test that valid intervals are accepted."""
        fetcher = DataFetcher()
        valid_intervals = ["1h", "1d", "1wk", "1mo"]
        for interval in valid_intervals:
            fetcher._validate_interval(interval)

    def test_validate_interval_rejects_invalid_intervals(self):
        """Test that invalid intervals are rejected."""
        fetcher = DataFetcher()
        with pytest.raises(ValueError):
            fetcher._validate_interval("invalid")
        with pytest.raises(ValueError):
            fetcher._validate_interval("")
        with pytest.raises(ValueError):
            fetcher._validate_interval(None)

    def test_validate_date_range_accepts_valid_dates(self):
        """Test that valid date ranges are accepted."""
        fetcher = DataFetcher()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2024, 1, 1)
        fetcher._validate_date_range(start_date, end_date)

    def test_validate_date_range_rejects_invalid_dates(self):
        """Test that invalid date ranges are rejected."""
        fetcher = DataFetcher()
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2023, 1, 1)
        with pytest.raises(ValueError):
            fetcher._validate_date_range(start_date, end_date)

    def test_fetch_data_returns_list_with_correct_structure(self):
        """Test that fetch_data returns list with required fields."""
        fetcher = DataFetcher()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 2)
        
        result = fetcher.fetch_data(start_date, end_date)
        
        # Verify result
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Check first item structure
        first_item = result[0]
        required_fields = ['Open', 'High', 'Low', 'Close', 'Volume', 'Timestamp']
        assert all(field in first_item for field in required_fields)

    def test_fetch_data_handles_invalid_date_range(self):
        """Test that fetch_data handles invalid date ranges."""
        fetcher = DataFetcher()
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2023, 1, 1)
        
        with pytest.raises(ValueError):
            fetcher.fetch_data(start_date, end_date)

    def test_generate_mock_data_creates_valid_ohlcv(self):
        """Test that generated mock data has valid OHLCV relationships."""
        fetcher = DataFetcher()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 1, 5)  # 5 hours of data
        
        result = fetcher._generate_mock_data(start_date, end_date)
        
        assert len(result) == 5  # Should have 5 hourly data points
        
        for item in result:
            # Check OHLC relationships
            assert item['Low'] <= item['Open'] <= item['High']
            assert item['Low'] <= item['Close'] <= item['High']
            assert item['Volume'] > 0

    def test_get_default_date_range_returns_one_year_period(self):
        """Test that get_default_date_range returns appropriate date range."""
        fetcher = DataFetcher()
        start_date, end_date = fetcher.get_default_date_range()
        
        assert isinstance(start_date, datetime)
        assert isinstance(end_date, datetime)
        assert end_date > start_date
        # Should be approximately one year
        assert (end_date - start_date).days >= 350
        assert (end_date - start_date).days <= 370

    def test_fetch_data_with_different_intervals(self):
        """Test fetch_data works with different intervals."""
        fetcher_hourly = DataFetcher(interval="1h")
        fetcher_daily = DataFetcher(interval="1d")
        
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 3)
        
        hourly_data = fetcher_hourly.fetch_data(start_date, end_date)
        daily_data = fetcher_daily.fetch_data(start_date, end_date)
        
        # Hourly should have more data points than daily
        assert len(hourly_data) > len(daily_data)