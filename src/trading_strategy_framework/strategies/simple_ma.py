"""
Simple Moving Average (SMA) crossover strategy.

This module implements a basic moving average crossover strategy that generates
BUY signals when the fast MA crosses above the slow MA and SELL signals when
the fast MA crosses below the slow MA.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional

from .base import BaseStrategy, Signal, SignalType


class SimpleMAStrategy(BaseStrategy):
    """
    Simple Moving Average crossover strategy.
    
    This strategy uses two moving averages (fast and slow) and generates:
    - BUY signal when fast MA crosses above slow MA
    - SELL signal when fast MA crosses below slow MA
    - No signal when there's no crossover
    """
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        """
        Initialize SimpleMAStrategy.
        
        Args:
            name: Strategy name
            config: Configuration with 'fast_period' and 'slow_period'
        """
        # Set default configuration
        default_config = {
            'fast_period': 10,
            'slow_period': 20
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(name, default_config)
    
    def calculate_indicators(self, market_data: List[Dict[str, Any]]) -> Dict[str, List[float]]:
        """
        Calculate fast and slow simple moving averages.
        
        Args:
            market_data: List of OHLCV data points
            
        Returns:
            Dictionary containing 'fast_sma' and 'slow_sma' lists
        """
        if not market_data:
            return {'fast_sma': [], 'slow_sma': []}
        
        close_prices = [float(item['Close']) for item in market_data]
        
        fast_period = self.config['fast_period']
        slow_period = self.config['slow_period']
        
        fast_sma = self._calculate_sma(close_prices, fast_period)
        slow_sma = self._calculate_sma(close_prices, slow_period)
        
        return {
            'fast_sma': fast_sma,
            'slow_sma': slow_sma
        }
    
    def generate_signal(self, market_data: List[Dict[str, Any]], 
                       indicators: Dict[str, List[float]]) -> Optional[Signal]:
        """
        Generate trading signal based on MA crossover.
        
        Args:
            market_data: List of OHLCV data points
            indicators: Calculated indicators with 'fast_sma' and 'slow_sma'
            
        Returns:
            Signal object if crossover detected, None otherwise
        """
        if not market_data or not indicators.get('fast_sma') or not indicators.get('slow_sma'):
            return None
        
        fast_sma = indicators['fast_sma']
        slow_sma = indicators['slow_sma']
        
        # Need at least 2 data points to detect crossover
        if len(fast_sma) < 2 or len(slow_sma) < 2:
            return None
        
        # Current values
        current_fast = fast_sma[-1]
        current_slow = slow_sma[-1]
        
        # Previous values
        prev_fast = fast_sma[-2]
        prev_slow = slow_sma[-2]
        
        current_price = float(market_data[-1]['Close'])
        timestamp = market_data[-1].get('Timestamp', datetime.now())
        
        # Check for crossover
        if prev_fast <= prev_slow and current_fast > current_slow:
            # Fast MA crosses above slow MA - BUY signal
            confidence = min(abs(current_fast - current_slow) / current_slow, 1.0)
            return Signal(
                timestamp=timestamp,
                signal_type=SignalType.BUY,
                price=current_price,
                confidence=confidence,
                metadata={
                    'fast_sma': current_fast,
                    'slow_sma': current_slow,
                    'crossover_type': 'bullish'
                }
            )
        elif prev_fast >= prev_slow and current_fast < current_slow:
            # Fast MA crosses below slow MA - SELL signal
            confidence = min(abs(current_slow - current_fast) / current_slow, 1.0)
            return Signal(
                timestamp=timestamp,
                signal_type=SignalType.SELL,
                price=current_price,
                confidence=confidence,
                metadata={
                    'fast_sma': current_fast,
                    'slow_sma': current_slow,
                    'crossover_type': 'bearish'
                }
            )
        
        return None
    
    def validate_config(self, config: Dict[str, Any]) -> None:
        """
        Validate strategy configuration.
        
        Args:
            config: Configuration to validate
            
        Raises:
            ValueError: If configuration is invalid
        """
        required_params = self.get_required_params()
        
        for param in required_params:
            if param not in config:
                raise ValueError(f"Missing required parameter: {param}")
            
            value = config[param]
            if not isinstance(value, int) or value <= 0:
                raise ValueError(f"Parameter {param} must be a positive integer")
        
        # Ensure fast period is less than slow period
        if config.get('fast_period', 0) >= config.get('slow_period', 0):
            raise ValueError("fast_period must be less than slow_period")
    
    def get_required_params(self) -> List[str]:
        """
        Get list of required configuration parameters.
        
        Returns:
            List of required parameter names
        """
        return ['fast_period', 'slow_period']
    
    def _calculate_sma(self, prices: List[float], period: int) -> List[float]:
        """
        Calculate Simple Moving Average for given prices and period.
        
        Args:
            prices: List of price values
            period: Number of periods for moving average
            
        Returns:
            List of SMA values
        """
        if len(prices) < period:
            return []
        
        sma_values = []
        for i in range(period - 1, len(prices)):
            sma = sum(prices[i - period + 1:i + 1]) / period
            sma_values.append(sma)
        
        return sma_values