"""
MACD (Moving Average Convergence Divergence) Strategy Implementation.

The MACD strategy uses the Moving Average Convergence Divergence indicator to generate
trading signals based on the convergence and divergence of moving averages.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np

from .base import BaseStrategy, Signal, SignalType


class MACDStrategy(BaseStrategy):
    """
    MACD (Moving Average Convergence Divergence) Strategy.
    
    The MACD strategy generates signals based on:
    1. MACD line crossing above/below signal line
    2. MACD line crossing above/below zero line
    3. MACD histogram changes (momentum)
    """
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        """
        Initialize MACD strategy.
        
        Args:
            name: Strategy name
            config: Configuration with 'fast_period', 'slow_period', 'signal_period'
        """
        # Set default configuration
        default_config = {
            'fast_period': 12,
            'slow_period': 26,
            'signal_period': 9,
            'use_divergence': True,
            'use_zero_cross': True
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(name, default_config)
        
        # Extract configuration values for easy access
        self.fast_period = self.config['fast_period']
        self.slow_period = self.config['slow_period']
        self.signal_period = self.config['signal_period']
        self.use_divergence = self.config['use_divergence']
        self.use_zero_cross = self.config['use_zero_cross']
        
    def calculate_indicators(self, market_data: List[Dict[str, Any]]) -> Dict[str, List[float]]:
        """
        Calculate MACD indicators.
        
        Args:
            market_data: List of OHLCV data points
            
        Returns:
            Dictionary containing MACD indicators
        """
        if len(market_data) < max(self.fast_period, self.slow_period) + self.signal_period:
            raise ValueError(f"Not enough data points. Need at least {max(self.fast_period, self.slow_period) + self.signal_period}")
        
        # Extract close prices
        close_prices = [float(data['close']) for data in market_data]
        
        # Calculate EMAs
        fast_ema = self._calculate_ema(close_prices, self.fast_period)
        slow_ema = self._calculate_ema(close_prices, self.slow_period)
        
        # Calculate MACD line
        macd_line = [fast - slow if fast is not None and slow is not None else None 
                     for fast, slow in zip(fast_ema, slow_ema)]
        
        # Calculate signal line
        macd_signal = self._calculate_ema([x for x in macd_line if x is not None], self.signal_period)
        
        # Pad signal line to match length
        signal_padded = [None] * (len(macd_line) - len(macd_signal)) + macd_signal
        
        # Calculate histogram
        macd_histogram = [line - signal if line is not None and signal is not None else None
                         for line, signal in zip(macd_line, signal_padded)]
        
        return {
            'macd_line': macd_line,
            'macd_signal': signal_padded,
            'macd_histogram': macd_histogram,
            'fast_ema': fast_ema,
            'slow_ema': slow_ema
        }
        
    def _calculate_ema(self, prices: List[float], period: int) -> List[float]:
        """
        Calculate Exponential Moving Average.
        
        Args:
            prices: List of price values
            period: EMA period
            
        Returns:
            List of EMA values
        """
        if len(prices) < period:
            return [None] * len(prices)
        
        ema = [None] * (period - 1)
        multiplier = 2 / (period + 1)
        
        # First EMA value is SMA
        sma = sum(prices[:period]) / period
        ema.append(sma)
        
        # Calculate subsequent EMA values
        for i in range(period, len(prices)):
            ema_value = (prices[i] * multiplier) + (ema[-1] * (1 - multiplier))
            ema.append(ema_value)
            
        return ema
        
    def generate_signal(self, market_data: List[Dict[str, Any]], 
                       indicators: Dict[str, List[float]]) -> Optional[Signal]:
        """
        Generate trading signal based on MACD indicators.
        
        Args:
            market_data: List of OHLCV data points
            indicators: Calculated MACD indicators
            
        Returns:
            Signal object if a signal is generated, None otherwise
        """
        if len(market_data) < 2:
            return None
            
        current_data = market_data[-1]
        previous_data = market_data[-2]
        
        current_macd = indicators['macd_line'][-1]
        current_signal = indicators['macd_signal'][-1]
        previous_macd = indicators['macd_line'][-2] if len(indicators['macd_line']) > 1 else None
        previous_signal = indicators['macd_signal'][-2] if len(indicators['macd_signal']) > 1 else None
        
        if any(x is None for x in [current_macd, current_signal, previous_macd, previous_signal]):
            return None
        
        current_price = float(current_data['close'])
        timestamp = datetime.fromisoformat(current_data['datetime'])
        
        # MACD line crosses above signal line (bullish)
        if previous_macd <= previous_signal and current_macd > current_signal:
            confidence = min(abs(current_macd - current_signal) / current_price * 1000, 1.0)
            return Signal(
                timestamp=timestamp,
                signal_type=SignalType.BUY,
                price=current_price,
                confidence=confidence,
                metadata={
                    'strategy': self.name,
                    'macd_line': current_macd,
                    'macd_signal': current_signal,
                    'crossover_type': 'bullish'
                }
            )
        
        # MACD line crosses below signal line (bearish)
        elif previous_macd >= previous_signal and current_macd < current_signal:
            confidence = min(abs(current_macd - current_signal) / current_price * 1000, 1.0)
            return Signal(
                timestamp=timestamp,
                signal_type=SignalType.SELL,
                price=current_price,
                confidence=confidence,
                metadata={
                    'strategy': self.name,
                    'macd_line': current_macd,
                    'macd_signal': current_signal,
                    'crossover_type': 'bearish'
                }
            )
        
        # Zero line crossovers if enabled
        if self.use_zero_cross:
            # MACD crosses above zero (additional bullish confirmation)
            if previous_macd <= 0 and current_macd > 0:
                confidence = min(abs(current_macd) / current_price * 1000, 0.8)
                return Signal(
                    timestamp=timestamp,
                    signal_type=SignalType.BUY,
                    price=current_price,
                    confidence=confidence,
                    metadata={
                        'strategy': self.name,
                        'macd_line': current_macd,
                        'crossover_type': 'zero_line_bullish'
                    }
                )
            
            # MACD crosses below zero (additional bearish confirmation)
            elif previous_macd >= 0 and current_macd < 0:
                confidence = min(abs(current_macd) / current_price * 1000, 0.8)
                return Signal(
                    timestamp=timestamp,
                    signal_type=SignalType.SELL,
                    price=current_price,
                    confidence=confidence,
                    metadata={
                        'strategy': self.name,
                        'macd_line': current_macd,
                        'crossover_type': 'zero_line_bearish'
                    }
                )
        
        return None
        
    def validate_config(self, config: Dict[str, Any]) -> None:
        """
        Validate strategy configuration.
        
        Args:
            config: Configuration dictionary
            
        Raises:
            ValueError: If configuration is invalid
        """
        required_keys = self.get_required_params()
        
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required configuration key: {key}")
            if not isinstance(config[key], int) or config[key] <= 0:
                raise ValueError(f"Configuration key {key} must be a positive integer")
        
        if config['fast_period'] >= config['slow_period']:
            raise ValueError("Fast period must be less than slow period")
            
    def get_required_params(self) -> List[str]:
        """
        Get list of required configuration parameters.
        
        Returns:
            List of required parameter names
        """
        return ['fast_period', 'slow_period', 'signal_period']
        
    def __str__(self) -> str:
        """String representation of the strategy."""
        return f"MACD({self.fast_period}, {self.slow_period}, {self.signal_period})"
        
    def __repr__(self) -> str:
        """Detailed representation of the strategy."""
        return f"MACDStrategy(name='{self.name}', config={self.config})"