"""
Data validation module for trading strategy framework.

This module provides data quality validation and cleaning capabilities.
"""

from typing import Any, List, Dict
from datetime import datetime


class DataValidator:
    """
    Validates and cleans market data for backtesting.
    
    This class provides methods to ensure data quality and consistency
    before using it in trading strategy testing.
    """
    
    def __init__(self):
        """Initialize DataValidator."""
        pass
    
    def validate_ohlcv_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate OHLCV data structure and values.
        
        Args:
            data: Dictionary containing OHLCV data
            
        Returns:
            True if data is valid, False otherwise
        """
        required_fields = ['Open', 'High', 'Low', 'Close', 'Volume']
        
        # Check if all required fields are present
        if not all(field in data for field in required_fields):
            return False
        
        # Check if values are numeric and positive
        for field in required_fields:
            if not isinstance(data[field], (int, float)) or data[field] < 0:
                return False
        
        # Check OHLC relationships
        if not (data['Low'] <= data['Open'] <= data['High'] and 
                data['Low'] <= data['Close'] <= data['High']):
            return False
        
        return True
    
    def clean_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Clean and filter market data.
        
        Args:
            data: List of OHLCV data points
            
        Returns:
            Cleaned data list
        """
        cleaned_data = []
        
        for row in data:
            if self.validate_ohlcv_data(row):
                cleaned_data.append(row)
        
        return cleaned_data
    
    def detect_gaps(self, timestamps: List[datetime], expected_interval_minutes: int = 60) -> List[int]:
        """
        Detect gaps in time series data.
        
        Args:
            timestamps: List of timestamps
            expected_interval_minutes: Expected interval between data points in minutes
            
        Returns:
            List of indices where gaps occur
        """
        gaps = []
        
        for i in range(1, len(timestamps)):
            time_diff = (timestamps[i] - timestamps[i-1]).total_seconds() / 60
            if time_diff > expected_interval_minutes * 1.5:  # Allow 50% tolerance
                gaps.append(i)
        
        return gaps