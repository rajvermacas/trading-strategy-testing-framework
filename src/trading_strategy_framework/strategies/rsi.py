"""
RSI (Relative Strength Index) Strategy Implementation.

The RSI strategy uses the Relative Strength Index indicator to identify
overbought and oversold conditions in the market.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np

from .base import BaseStrategy, Signal, SignalType


class RSIStrategy(BaseStrategy):
    """
    RSI (Relative Strength Index) Strategy.
    
    The RSI strategy generates signals based on:
    1. RSI crossing above overbought threshold (sell signal)
    2. RSI crossing below oversold threshold (buy signal)
    3. RSI divergence patterns (optional)
    """
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        """
        Initialize RSI strategy.
        
        Args:
            name: Strategy name
            config: Configuration with 'period', 'overbought', 'oversold'
        """
        # Set default configuration
        default_config = {
            'period': 14,
            'overbought': 70,
            'oversold': 30,
            'use_divergence': False
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(name, default_config)
        
        # Extract configuration values for easy access
        self.period = self.config['period']
        self.overbought = self.config['overbought']
        self.oversold = self.config['oversold']
        self.use_divergence = self.config['use_divergence']
        
    def calculate_indicators(self, market_data: List[Dict[str, Any]]) -> Dict[str, List[float]]:
        """
        Calculate RSI indicators.
        
        Args:
            market_data: List of OHLCV data points
            
        Returns:
            Dictionary containing RSI indicators
        """
        if len(market_data) < self.period + 1:
            raise ValueError(f"Not enough data points. Need at least {self.period + 1}")
        
        # Extract close prices
        close_prices = [float(data['close']) for data in market_data]
        
        # Calculate price changes
        price_changes = []
        for i in range(1, len(close_prices)):
            price_changes.append(close_prices[i] - close_prices[i-1])
        
        # Separate gains and losses
        gains = [max(change, 0) for change in price_changes]
        losses = [abs(min(change, 0)) for change in price_changes]
        
        # Calculate RSI
        rsi_values = self._calculate_rsi(gains, losses)
        
        # Pad RSI values to match original data length
        # We need period + 1 None values (one for the first price, period for RSI calculation)
        padding_needed = len(close_prices) - len(rsi_values)
        rsi_padded = [None] * padding_needed + rsi_values
        
        # Calculate average gain and loss for analysis
        avg_gains = self._calculate_smoothed_average(gains)
        avg_losses = self._calculate_smoothed_average(losses)
        
        # Pad average values
        avg_gains_padded = [None] * padding_needed + avg_gains
        avg_losses_padded = [None] * padding_needed + avg_losses
        
        indicators = {
            'rsi': rsi_padded,
            'avg_gain': avg_gains_padded,
            'avg_loss': avg_losses_padded
        }
        
        # Add divergence calculation if enabled
        if self.use_divergence:
            indicators['divergence'] = self._calculate_divergence(
                close_prices, rsi_padded
            )
        
        return indicators
        
    def _calculate_rsi(self, gains: List[float], losses: List[float]) -> List[float]:
        """
        Calculate RSI values using the standard formula.
        
        Args:
            gains: List of price gains
            losses: List of price losses
            
        Returns:
            List of RSI values
        """
        if len(gains) < self.period:
            return []
        
        rsi_values = []
        
        # Calculate initial SMA for gains and losses
        avg_gain = sum(gains[:self.period]) / self.period
        avg_loss = sum(losses[:self.period]) / self.period
        
        # Calculate first RSI value
        if avg_loss == 0:
            rsi = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        rsi_values.append(rsi)
        
        # Calculate subsequent RSI values using smoothed averages
        for i in range(self.period, len(gains)):
            # Wilder's smoothing method
            avg_gain = ((avg_gain * (self.period - 1)) + gains[i]) / self.period
            avg_loss = ((avg_loss * (self.period - 1)) + losses[i]) / self.period
            
            if avg_loss == 0:
                rsi = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            rsi_values.append(rsi)
        
        return rsi_values
        
    def _calculate_smoothed_average(self, values: List[float]) -> List[float]:
        """
        Calculate smoothed average values (for analysis).
        
        Args:
            values: List of values to smooth
            
        Returns:
            List of smoothed averages
        """
        if len(values) < self.period:
            return []
        
        smoothed = []
        
        # Initial average
        avg = sum(values[:self.period]) / self.period
        smoothed.append(avg)
        
        # Subsequent smoothed values
        for i in range(self.period, len(values)):
            avg = ((avg * (self.period - 1)) + values[i]) / self.period
            smoothed.append(avg)
        
        return smoothed
        
    def _calculate_divergence(self, prices: List[float], rsi_values: List[float]) -> List[int]:
        """
        Calculate RSI divergence patterns.
        
        Args:
            prices: Close prices
            rsi_values: RSI values
            
        Returns:
            List of divergence signals (1 for bullish, -1 for bearish, 0 for none)
        """
        divergence = [0] * len(prices)
        
        # Simple divergence detection
        window = 10
        for i in range(window, len(prices) - window):
            if rsi_values[i] is None:
                continue
                
            # Look for local highs and lows in both price and RSI
            price_window = prices[i-window:i+window]
            rsi_window = [x for x in rsi_values[i-window:i+window] if x is not None]
            
            if len(rsi_window) < window:
                continue
            
            # Check if current point is a local extremum
            if prices[i] == max(price_window) and rsi_values[i] < max(rsi_window):
                # Bearish divergence: price high but RSI not at high
                divergence[i] = -1
            elif prices[i] == min(price_window) and rsi_values[i] > min(rsi_window):
                # Bullish divergence: price low but RSI not at low
                divergence[i] = 1
        
        return divergence
        
    def generate_signal(self, market_data: List[Dict[str, Any]], 
                       indicators: Dict[str, List[float]]) -> Optional[Signal]:
        """
        Generate trading signal based on RSI indicators.
        
        Args:
            market_data: List of OHLCV data points
            indicators: Calculated RSI indicators
            
        Returns:
            Signal object if a signal is generated, None otherwise
        """
        if len(market_data) < 2:
            return None
            
        current_data = market_data[-1]
        previous_data = market_data[-2] if len(market_data) > 1 else None
        
        current_rsi = indicators['rsi'][-1]
        previous_rsi = indicators['rsi'][-2] if len(indicators['rsi']) > 1 else None
        
        if current_rsi is None or previous_rsi is None:
            return None
        
        current_price = float(current_data['close'])
        timestamp = datetime.fromisoformat(current_data['datetime'])
        
        # RSI crosses below oversold threshold (bullish signal)
        if previous_rsi >= self.oversold and current_rsi < self.oversold:
            confidence = min((self.oversold - current_rsi) / self.oversold, 1.0)
            return Signal(
                timestamp=timestamp,
                signal_type=SignalType.BUY,
                price=current_price,
                confidence=confidence,
                metadata={
                    'strategy': self.name,
                    'rsi': current_rsi,
                    'threshold': self.oversold,
                    'signal_type': 'oversold_entry'
                }
            )
        
        # RSI crosses above overbought threshold (bearish signal)
        elif previous_rsi <= self.overbought and current_rsi > self.overbought:
            confidence = min((current_rsi - self.overbought) / (100 - self.overbought), 1.0)
            return Signal(
                timestamp=timestamp,
                signal_type=SignalType.SELL,
                price=current_price,
                confidence=confidence,
                metadata={
                    'strategy': self.name,
                    'rsi': current_rsi,
                    'threshold': self.overbought,
                    'signal_type': 'overbought_entry'
                }
            )
        
        # Check for divergence signals if enabled
        if self.use_divergence and 'divergence' in indicators:
            current_divergence = indicators['divergence'][-1]
            
            if current_divergence == 1:  # Bullish divergence
                return Signal(
                    timestamp=timestamp,
                    signal_type=SignalType.BUY,
                    price=current_price,
                    confidence=0.7,
                    metadata={
                        'strategy': self.name,
                        'rsi': current_rsi,
                        'signal_type': 'bullish_divergence'
                    }
                )
            elif current_divergence == -1:  # Bearish divergence
                return Signal(
                    timestamp=timestamp,
                    signal_type=SignalType.SELL,
                    price=current_price,
                    confidence=0.7,
                    metadata={
                        'strategy': self.name,
                        'rsi': current_rsi,
                        'signal_type': 'bearish_divergence'
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
            
        # Validate period
        if not isinstance(config['period'], int) or config['period'] <= 0:
            raise ValueError("Period must be a positive integer")
            
        # Validate thresholds
        if not (0 < config['overbought'] <= 100):
            raise ValueError("Overbought threshold must be between 0 and 100")
            
        if not (0 <= config['oversold'] < 100):
            raise ValueError("Oversold threshold must be between 0 and 100")
            
        if config['overbought'] <= config['oversold']:
            raise ValueError("Overbought must be greater than oversold")
            
    def get_required_params(self) -> List[str]:
        """
        Get list of required configuration parameters.
        
        Returns:
            List of required parameter names
        """
        return ['period', 'overbought', 'oversold']
        
    def __str__(self) -> str:
        """String representation of the strategy."""
        return f"RSI({self.period}, {self.overbought}, {self.oversold})"
        
    def __repr__(self) -> str:
        """Detailed representation of the strategy."""
        return f"RSIStrategy(name='{self.name}', config={self.config})"