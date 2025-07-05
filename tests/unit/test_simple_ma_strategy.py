"""
Tests for Simple Moving Average strategy.

Following TDD approach: Red-Green-Refactor
"""

import pytest
from datetime import datetime
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from trading_strategy_framework.strategies.simple_ma import SimpleMAStrategy
from trading_strategy_framework.strategies.base import Signal, SignalType


class TestSimpleMAStrategy:
    """Test SimpleMAStrategy implementation."""
    
    def test_init_with_default_config(self):
        """Test SimpleMAStrategy initialization with default config."""
        strategy = SimpleMAStrategy("SMA_Test")
        assert strategy.name == "SMA_Test"
        assert strategy.config.get('fast_period') == 10
        assert strategy.config.get('slow_period') == 20

    def test_init_with_custom_config(self):
        """Test SimpleMAStrategy initialization with custom config."""
        config = {'fast_period': 5, 'slow_period': 15}
        strategy = SimpleMAStrategy("SMA_Test", config)
        assert strategy.config['fast_period'] == 5
        assert strategy.config['slow_period'] == 15

    def test_validate_config_accepts_valid_config(self):
        """Test that valid configurations are accepted."""
        strategy = SimpleMAStrategy("SMA_Test")
        valid_config = {'fast_period': 10, 'slow_period': 20}
        # Should not raise exception
        strategy.validate_config(valid_config)

    def test_validate_config_rejects_invalid_periods(self):
        """Test that invalid period configurations are rejected."""
        strategy = SimpleMAStrategy("SMA_Test")
        
        # Fast period greater than slow period
        with pytest.raises(ValueError):
            strategy.validate_config({'fast_period': 20, 'slow_period': 10})
        
        # Negative periods
        with pytest.raises(ValueError):
            strategy.validate_config({'fast_period': -5, 'slow_period': 20})
        
        # Non-integer periods
        with pytest.raises(ValueError):
            strategy.validate_config({'fast_period': 'invalid', 'slow_period': 20})

    def test_get_required_params_returns_periods(self):
        """Test that get_required_params returns the required parameters."""
        strategy = SimpleMAStrategy("SMA_Test")
        params = strategy.get_required_params()
        assert 'fast_period' in params
        assert 'slow_period' in params

    def test_calculate_sma_with_sufficient_data(self):
        """Test SMA calculation with sufficient data."""
        strategy = SimpleMAStrategy("SMA_Test")
        prices = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]
        
        result = strategy._calculate_sma(prices, period=5)
        # For period 5: [100,101,102,103,104] = 102, [101,102,103,104,105] = 103, etc.
        expected = [102.0, 103.0, 104.0, 105.0, 106.0, 107.0]  # 6 values for 10 prices with period 5
        
        assert len(result) == 6
        assert result == expected

    def test_calculate_sma_with_insufficient_data(self):
        """Test SMA calculation with insufficient data."""
        strategy = SimpleMAStrategy("SMA_Test")
        prices = [100, 101, 102]  # Only 3 prices
        
        result = strategy._calculate_sma(prices, period=5)
        assert result == []

    def test_calculate_indicators_with_valid_data(self):
        """Test indicator calculation with valid market data."""
        config = {'fast_period': 3, 'slow_period': 5}
        strategy = SimpleMAStrategy("SMA_Test", config)
        
        market_data = [
            {'Close': 100}, {'Close': 101}, {'Close': 102}, {'Close': 103}, 
            {'Close': 104}, {'Close': 105}, {'Close': 106}
        ]
        
        indicators = strategy.calculate_indicators(market_data)
        
        assert 'fast_sma' in indicators
        assert 'slow_sma' in indicators
        assert len(indicators['fast_sma']) == 5  # 7 - 3 + 1
        assert len(indicators['slow_sma']) == 3  # 7 - 5 + 1

    def test_calculate_indicators_with_insufficient_data(self):
        """Test indicator calculation with insufficient data."""
        strategy = SimpleMAStrategy("SMA_Test")
        market_data = [{'Close': 100}, {'Close': 101}]  # Only 2 data points
        
        indicators = strategy.calculate_indicators(market_data)
        
        assert indicators['fast_sma'] == []
        assert indicators['slow_sma'] == []

    def test_generate_signal_buy_when_fast_crosses_above_slow(self):
        """Test BUY signal generation when fast MA crosses above slow MA."""
        config = {'fast_period': 2, 'slow_period': 3}
        strategy = SimpleMAStrategy("SMA_Test", config)
        
        market_data = [
            {'Close': 100, 'Timestamp': datetime(2023, 1, 1, 10, 0)},
            {'Close': 101, 'Timestamp': datetime(2023, 1, 1, 11, 0)},
            {'Close': 102, 'Timestamp': datetime(2023, 1, 1, 12, 0)},
            {'Close': 105, 'Timestamp': datetime(2023, 1, 1, 13, 0)},  # Fast MA jumps above slow MA
        ]
        
        # Create crossover scenario: fast was below, now above
        indicators = {
            'fast_sma': [100.5, 103.5],  # Previous: 100.5, Current: 103.5 (fast crosses up)
            'slow_sma': [101.0, 102.3]   # Previous: 101.0, Current: 102.3 (slow stays lower)
        }
        
        signal = strategy.generate_signal(market_data, indicators)
        
        assert signal is not None
        assert signal.signal_type == SignalType.BUY
        assert signal.price == 105
        assert signal.confidence > 0

    def test_generate_signal_sell_when_fast_crosses_below_slow(self):
        """Test SELL signal generation when fast MA crosses below slow MA."""
        config = {'fast_period': 2, 'slow_period': 3}
        strategy = SimpleMAStrategy("SMA_Test", config)
        
        market_data = [
            {'Close': 105, 'Timestamp': datetime(2023, 1, 1, 10, 0)},
            {'Close': 104, 'Timestamp': datetime(2023, 1, 1, 11, 0)},
            {'Close': 103, 'Timestamp': datetime(2023, 1, 1, 12, 0)},
            {'Close': 100, 'Timestamp': datetime(2023, 1, 1, 13, 0)},  # Fast MA drops below slow MA
        ]
        
        # Create crossover scenario: fast was above, now below
        indicators = {
            'fast_sma': [104.5, 101.5],  # Previous: 104.5, Current: 101.5 (fast crosses down)
            'slow_sma': [104.0, 103.0]   # Previous: 104.0, Current: 103.0 (slow stays higher)
        }
        
        signal = strategy.generate_signal(market_data, indicators)
        
        assert signal is not None
        assert signal.signal_type == SignalType.SELL
        assert signal.price == 100
        assert signal.confidence > 0

    def test_generate_signal_none_when_no_crossover(self):
        """Test no signal generation when there's no crossover."""
        strategy = SimpleMAStrategy("SMA_Test")
        
        market_data = [
            {'Close': 100, 'Timestamp': datetime(2023, 1, 1, 10, 0)}
        ]
        
        indicators = {
            'fast_sma': [100.5, 101.0],
            'slow_sma': [99.5, 100.0]   # Fast consistently above slow
        }
        
        signal = strategy.generate_signal(market_data, indicators)
        assert signal is None

    def test_generate_signal_none_with_insufficient_indicators(self):
        """Test no signal generation with insufficient indicator data."""
        strategy = SimpleMAStrategy("SMA_Test")
        
        market_data = [{'Close': 100, 'Timestamp': datetime(2023, 1, 1, 10, 0)}]
        indicators = {'fast_sma': [], 'slow_sma': []}
        
        signal = strategy.generate_signal(market_data, indicators)
        assert signal is None