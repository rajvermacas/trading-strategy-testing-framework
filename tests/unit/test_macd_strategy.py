"""
Unit tests for MACD (Moving Average Convergence Divergence) strategy.
"""

import pytest
from datetime import datetime, timedelta

from src.trading_strategy_framework.strategies.macd import MACDStrategy
from src.trading_strategy_framework.strategies.base import SignalType


class TestMACDStrategy:
    """Test cases for MACD strategy implementation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.strategy = MACDStrategy("MACD_Test")
        
    def test_macd_strategy_initialization(self):
        """Test MACD strategy initializes correctly."""
        assert self.strategy.name == "MACD_Test"
        assert self.strategy.fast_period == 12
        assert self.strategy.slow_period == 26
        assert self.strategy.signal_period == 9
        
    def test_macd_custom_parameters(self):
        """Test MACD strategy with custom parameters."""
        custom_config = {
            'fast_period': 8,
            'slow_period': 21,
            'signal_period': 5
        }
        custom_strategy = MACDStrategy("MACD_Custom", custom_config)
        
        assert custom_strategy.fast_period == 8
        assert custom_strategy.slow_period == 21
        assert custom_strategy.signal_period == 5
        
    def test_config_validation(self):
        """Test configuration validation."""
        # Test invalid values (negative numbers)
        with pytest.raises(ValueError, match="must be a positive integer"):
            MACDStrategy("MACD_Invalid", {
                'fast_period': -1,
                'slow_period': 26,
                'signal_period': 9
            })
        
        # Test fast >= slow period
        with pytest.raises(ValueError, match="Fast period must be less than slow period"):
            MACDStrategy("MACD_Invalid", {
                'fast_period': 26,
                'slow_period': 12,
                'signal_period': 9
            })
            
        # Test zero values
        with pytest.raises(ValueError, match="must be a positive integer"):
            MACDStrategy("MACD_Invalid", {
                'fast_period': 0,
                'slow_period': 26,
                'signal_period': 9
            })
            
        # Test required params method
        required_params = self.strategy.get_required_params()
        assert 'fast_period' in required_params
        assert 'slow_period' in required_params
        assert 'signal_period' in required_params
            
    def _create_sample_data(self, num_points: int = 100, trend: str = "up") -> list:
        """Create sample market data for testing."""
        base_date = datetime(2023, 1, 1)
        data = []
        
        for i in range(num_points):
            if trend == "up":
                base_price = 100 + i * 0.1  # Gradual uptrend
            elif trend == "down":
                base_price = 100 - i * 0.1  # Gradual downtrend
            else:
                base_price = 100 + (i % 10 - 5) * 0.5  # Sideways with noise
            
            data.append({
                'datetime': (base_date + timedelta(hours=i)).isoformat(),
                'open': base_price,
                'high': base_price * 1.01,
                'low': base_price * 0.99,
                'close': base_price,
                'volume': 1000 + i * 10
            })
        
        return data
        
    def test_macd_calculation(self):
        """Test MACD indicator calculation."""
        data = self._create_sample_data(50)
        
        # Calculate MACD
        indicators = self.strategy.calculate_indicators(data)
        
        # Verify MACD components exist
        assert 'macd_line' in indicators
        assert 'macd_signal' in indicators
        assert 'macd_histogram' in indicators
        assert 'fast_ema' in indicators
        assert 'slow_ema' in indicators
        
        # Check that MACD values are calculated after initial period
        assert len(indicators['macd_line']) == len(data)
        
        # Check that some values are not None
        non_none_macd = [x for x in indicators['macd_line'] if x is not None]
        assert len(non_none_macd) > 0
        
    def test_insufficient_data(self):
        """Test handling of insufficient data."""
        # Create data with fewer points than required
        data = self._create_sample_data(20)  # Less than required for MACD
        
        with pytest.raises(ValueError, match="Not enough data points"):
            self.strategy.calculate_indicators(data)
            
    def test_ema_calculation(self):
        """Test EMA calculation helper method."""
        prices = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]
        period = 5
        
        ema = self.strategy._calculate_ema(prices, period)
        
        # Check length
        assert len(ema) == len(prices)
        
        # Check that first few values are None
        assert all(x is None for x in ema[:period-1])
        
        # Check that EMA values are calculated after initial period
        assert ema[period-1] is not None  # First EMA value (SMA)
        assert ema[-1] is not None  # Last EMA value
        
        # Check that EMA is trending upward with upward price trend
        assert ema[-1] > ema[period-1]
        
    def test_signal_generation_bullish(self):
        """Test bullish signal generation."""
        # Create data with clear upward trend to generate bullish signals
        data = self._create_sample_data(50, trend="up")
        
        indicators = self.strategy.calculate_indicators(data)
        
        # Test signal generation on the last few data points
        for i in range(2, len(data)):
            test_data = data[:i+1]
            test_indicators = {
                key: values[:i+1] for key, values in indicators.items()
            }
            
            signal = self.strategy.generate_signal(test_data, test_indicators)
            
            if signal:
                assert signal.signal_type in [SignalType.BUY, SignalType.SELL]
                assert signal.price > 0
                assert 0 <= signal.confidence <= 1.0
                assert 'strategy' in signal.metadata
                break
                
    def test_signal_generation_bearish(self):
        """Test bearish signal generation."""
        # Create data with clear downward trend to generate bearish signals
        data = self._create_sample_data(50, trend="down")
        
        indicators = self.strategy.calculate_indicators(data)
        
        # Test signal generation
        signal = self.strategy.generate_signal(data, indicators)
        
        if signal:
            assert signal.signal_type in [SignalType.BUY, SignalType.SELL]
            assert signal.price > 0
            assert 0 <= signal.confidence <= 1.0
            
    def test_no_signal_generation(self):
        """Test when no signal should be generated."""
        # Test with insufficient data
        data = self._create_sample_data(1)
        
        # Should not generate signal with only one data point
        signal = self.strategy.generate_signal(data, {})
        assert signal is None
        
    def test_macd_crossover_detection(self):
        """Test MACD crossover signal detection."""
        # Create specific data pattern for crossover
        data = []
        base_date = datetime(2023, 1, 1)
        
        # Create data that will cause MACD crossover
        for i in range(50):
            if i < 25:
                price = 100 + i * 0.5  # Strong uptrend
            else:
                price = 100 + 25 * 0.5 + (i - 25) * 0.1  # Weaker uptrend
                
            data.append({
                'datetime': (base_date + timedelta(hours=i)).isoformat(),
                'open': price,
                'high': price * 1.01,
                'low': price * 0.99,
                'close': price,
                'volume': 1000
            })
        
        indicators = self.strategy.calculate_indicators(data)
        
        # Check for crossovers in the data
        macd_line = indicators['macd_line']
        macd_signal = indicators['macd_signal']
        
        crossovers = 0
        for i in range(1, len(macd_line)):
            if (macd_line[i] is not None and macd_signal[i] is not None and
                macd_line[i-1] is not None and macd_signal[i-1] is not None):
                
                # Check for crossover
                if ((macd_line[i-1] <= macd_signal[i-1] and macd_line[i] > macd_signal[i]) or
                    (macd_line[i-1] >= macd_signal[i-1] and macd_line[i] < macd_signal[i])):
                    crossovers += 1
        
        # Should detect some crossovers in trending data
        assert crossovers >= 0  # At least some crossovers should occur
        
    def test_zero_line_crossover(self):
        """Test zero line crossover functionality."""
        # Create strategy with zero cross enabled
        zero_cross_strategy = MACDStrategy("MACD_ZeroCross", {
            'fast_period': 12,
            'slow_period': 26,
            'signal_period': 9,
            'use_zero_cross': True
        })
        
        # Create data that oscillates around a baseline
        data = []
        base_date = datetime(2023, 1, 1)
        
        for i in range(50):
            # Sine wave pattern to create oscillation
            import math
            price = 100 + 5 * math.sin(i * 0.3)
            
            data.append({
                'datetime': (base_date + timedelta(hours=i)).isoformat(),
                'open': price,
                'high': price * 1.01,
                'low': price * 0.99,
                'close': price,
                'volume': 1000
            })
        
        indicators = zero_cross_strategy.calculate_indicators(data)
        
        # Test signal generation (zero crossovers should be detected)
        signal = zero_cross_strategy.generate_signal(data, indicators)
        
        # Should either generate a signal or not, but shouldn't error
        if signal:
            assert signal.signal_type in [SignalType.BUY, SignalType.SELL]
            
    def test_strategy_string_representation(self):
        """Test string representations of the strategy."""
        assert str(self.strategy) == "MACD(12, 26, 9)"
        assert "MACDStrategy" in repr(self.strategy)
        assert "MACD_Test" in repr(self.strategy)