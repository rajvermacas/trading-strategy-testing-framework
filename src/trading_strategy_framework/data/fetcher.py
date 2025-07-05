"""
Data fetcher module for trading strategy framework.

This module provides functionality to fetch historical market data
from various sources with validation and error handling.
"""

import re
from datetime import datetime, timedelta
from typing import Tuple, Optional, List, Dict, Any


class DataFetcher:
    """
    Fetches historical market data from external sources.
    
    This class provides a clean interface for fetching historical market data
    with built-in validation, error handling, and caching capabilities.
    """
    
    def __init__(self, symbol: str = "^NSEI", interval: str = "1h"):
        """
        Initialize DataFetcher with symbol and interval.
        
        Args:
            symbol: Stock symbol to fetch data for (default: ^NSEI for Nifty 50)
            interval: Data interval (default: 1h)
        """
        self._validate_symbol(symbol)
        self._validate_interval(interval)
        
        self.symbol = symbol
        self.interval = interval
    
    def _validate_symbol(self, symbol: str) -> None:
        """
        Validate trading symbol format.
        
        Args:
            symbol: Trading symbol to validate
            
        Raises:
            ValueError: If symbol is invalid
        """
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        
        # Basic symbol validation - alphanumeric characters, hyphens, dots, and carets
        if not re.match(r'^[A-Za-z0-9\.\-\^]+$', symbol):
            raise ValueError(f"Invalid symbol format: {symbol}")
    
    def _validate_interval(self, interval: str) -> None:
        """
        Validate data interval.
        
        Args:
            interval: Data interval to validate
            
        Raises:
            ValueError: If interval is invalid
        """
        valid_intervals = ["1h", "1d", "1wk", "1mo", "2m", "5m", "15m", "30m", "60m", "90m", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
        
        if not interval or not isinstance(interval, str):
            raise ValueError("Interval must be a non-empty string")
        
        if interval not in valid_intervals:
            raise ValueError(f"Invalid interval: {interval}. Valid intervals: {valid_intervals}")
    
    def _validate_date_range(self, start_date: datetime, end_date: datetime) -> None:
        """
        Validate date range for data fetching.
        
        Args:
            start_date: Start date for data fetching
            end_date: End date for data fetching
            
        Raises:
            ValueError: If date range is invalid
        """
        if not isinstance(start_date, datetime):
            raise ValueError("Start date must be a datetime object")
        
        if not isinstance(end_date, datetime):
            raise ValueError("End date must be a datetime object")
        
        if start_date >= end_date:
            raise ValueError("Start date must be before end date")
    
    def fetch_data(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Fetch historical market data for the specified date range.
        
        Args:
            start_date: Start date for data fetching
            end_date: End date for data fetching
            
        Returns:
            List of dictionaries with OHLCV data
            
        Raises:
            ValueError: If no data is received or dates are invalid
            Exception: If data fetching fails
        """
        self._validate_date_range(start_date, end_date)
        
        try:
            # For MVP, generate mock data - will be replaced with real API integration
            data = self._generate_mock_data(start_date, end_date)
            
            if not data:
                raise ValueError(f"No data received for {self.symbol} from {start_date} to {end_date}")
            
            return data
            
        except Exception as e:
            raise Exception(f"Failed to fetch data: {str(e)}")
    
    def _generate_mock_data(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Generate mock market data for testing purposes.
        
        Args:
            start_date: Start date for data generation
            end_date: End date for data generation
            
        Returns:
            List of mock OHLCV data points
        """
        data = []
        current_date = start_date
        base_price = 18000.0  # Base price for Nifty 50
        
        while current_date < end_date:
            # Simple price simulation
            open_price = base_price + (hash(str(current_date)) % 200 - 100)
            high_price = open_price + (hash(str(current_date + timedelta(minutes=1))) % 50)
            low_price = open_price - (hash(str(current_date + timedelta(minutes=2))) % 50)
            close_price = open_price + (hash(str(current_date + timedelta(minutes=3))) % 100 - 50)
            volume = 1000000 + (hash(str(current_date + timedelta(minutes=4))) % 500000)
            
            # Ensure OHLC relationships are valid
            high_price = max(high_price, open_price, close_price)
            low_price = min(low_price, open_price, close_price)
            
            data.append({
                'Open': float(open_price),
                'High': float(high_price), 
                'Low': float(low_price),
                'Close': float(close_price),
                'Volume': int(volume),
                'Timestamp': current_date
            })
            
            # Move to next hour
            if self.interval == "1h":
                current_date += timedelta(hours=1)
            elif self.interval == "1d":
                current_date += timedelta(days=1)
            else:
                current_date += timedelta(hours=1)  # Default to hourly
                
            base_price = close_price  # Use previous close as next base
        
        return data
    
    def get_default_date_range(self) -> Tuple[datetime, datetime]:
        """
        Get default date range for backtesting (approximately 1 year).
        
        Returns:
            Tuple of (start_date, end_date)
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        return start_date, end_date