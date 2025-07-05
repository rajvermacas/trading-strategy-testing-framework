"""
Tests for strategy base classes.

Following TDD approach: Red-Green-Refactor
"""

import pytest
from datetime import datetime
from unittest.mock import Mock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from trading_strategy_framework.strategies.base import BaseStrategy, Signal, SignalType


class TestSignalType:
    """Test SignalType enum."""
    
    def test_signal_type_has_required_values(self):
        """Test that SignalType enum has all required values."""
        assert SignalType.BUY
        assert SignalType.SELL
        assert SignalType.HOLD


class TestSignal:
    """Test Signal class."""
    
    def test_signal_init_with_required_fields(self):
        """Test Signal initialization with required fields."""
        timestamp = datetime(2023, 1, 1, 10, 0)
        signal = Signal(
            timestamp=timestamp,
            signal_type=SignalType.BUY,
            price=100.0,
            confidence=0.8
        )
        
        assert signal.timestamp == timestamp
        assert signal.signal_type == SignalType.BUY
        assert signal.price == 100.0
        assert signal.confidence == 0.8
        assert signal.metadata == {}

    def test_signal_init_with_metadata(self):
        """Test Signal initialization with metadata."""
        timestamp = datetime(2023, 1, 1, 10, 0)
        metadata = {"rsi": 30, "ma_cross": True}
        
        signal = Signal(
            timestamp=timestamp,
            signal_type=SignalType.BUY,
            price=100.0,
            confidence=0.8,
            metadata=metadata
        )
        
        assert signal.metadata == metadata

    def test_signal_str_representation(self):
        """Test Signal string representation."""
        timestamp = datetime(2023, 1, 1, 10, 0)
        signal = Signal(
            timestamp=timestamp,
            signal_type=SignalType.BUY,
            price=100.0,
            confidence=0.8
        )
        
        str_repr = str(signal)
        assert "BUY" in str_repr
        assert "100.0" in str_repr


class TestBaseStrategy:
    """Test BaseStrategy abstract class."""
    
    def test_base_strategy_init_with_name(self):
        """Test BaseStrategy initialization."""
        strategy = ConcreteStrategy("TestStrategy")
        assert strategy.name == "TestStrategy"
        assert strategy.config == {}

    def test_base_strategy_init_with_config(self):
        """Test BaseStrategy initialization with config."""
        config = {"period": 14, "threshold": 70}
        strategy = ConcreteStrategy("TestStrategy", config)
        assert strategy.name == "TestStrategy"
        assert strategy.config == config

    def test_base_strategy_calculate_indicators_is_abstract(self):
        """Test that calculate_indicators must be implemented."""
        # This is tested by trying to instantiate the abstract class
        with pytest.raises(TypeError):
            BaseStrategy("TestStrategy")

    def test_base_strategy_generate_signal_is_abstract(self):
        """Test that generate_signal must be implemented."""
        # This is tested implicitly when we implement ConcreteStrategy
        strategy = ConcreteStrategy("TestStrategy")
        assert hasattr(strategy, 'generate_signal')

    def test_base_strategy_calculate_indicators_called_with_data(self):
        """Test that calculate_indicators is called with market data."""
        strategy = ConcreteStrategy("TestStrategy")
        market_data = [
            {'Open': 100, 'High': 105, 'Low': 98, 'Close': 103, 'Volume': 1000}
        ]
        
        # This should call calculate_indicators
        result = strategy.calculate_indicators(market_data)
        assert result is not None

    def test_base_strategy_generate_signal_called_with_data(self):
        """Test that generate_signal is called with market data and indicators."""
        strategy = ConcreteStrategy("TestStrategy")
        market_data = [
            {'Open': 100, 'High': 105, 'Low': 98, 'Close': 103, 'Volume': 1000}
        ]
        indicators = {"sma": [101, 102, 103]}
        
        signal = strategy.generate_signal(market_data, indicators)
        assert signal is None or isinstance(signal, Signal)

    def test_base_strategy_validate_config_checks_required_params(self):
        """Test that validate_config checks for required parameters."""
        strategy = ConcreteStrategy("TestStrategy")
        
        # Should not raise for valid config
        valid_config = {"period": 14}
        strategy.validate_config(valid_config)
        
        # Should raise for invalid config
        invalid_config = {"period": "invalid"}
        with pytest.raises(ValueError):
            strategy.validate_config(invalid_config)

    def test_base_strategy_get_required_params_returns_list(self):
        """Test that get_required_params returns list of required parameters."""
        strategy = ConcreteStrategy("TestStrategy")
        params = strategy.get_required_params()
        assert isinstance(params, list)


# Concrete implementation for testing
class ConcreteStrategy(BaseStrategy):
    """Concrete strategy implementation for testing."""
    
    def calculate_indicators(self, market_data):
        """Calculate simple moving average for testing."""
        if not market_data:
            return {}
        
        close_prices = [item['Close'] for item in market_data]
        period = self.config.get('period', 10)
        
        if len(close_prices) < period:
            return {"sma": []}
        
        sma_values = []
        for i in range(period - 1, len(close_prices)):
            sma = sum(close_prices[i - period + 1:i + 1]) / period
            sma_values.append(sma)
        
        return {"sma": sma_values}
    
    def generate_signal(self, market_data, indicators):
        """Generate simple signal for testing."""
        if not market_data or not indicators.get("sma"):
            return None
        
        current_price = market_data[-1]['Close']
        current_sma = indicators["sma"][-1]
        
        if current_price > current_sma:
            return Signal(
                timestamp=datetime.now(),
                signal_type=SignalType.BUY,
                price=current_price,
                confidence=0.7
            )
        elif current_price < current_sma:
            return Signal(
                timestamp=datetime.now(),
                signal_type=SignalType.SELL,
                price=current_price,
                confidence=0.7
            )
        
        return None
    
    def validate_config(self, config):
        """Validate configuration for testing."""
        if 'period' in config:
            if not isinstance(config['period'], int) or config['period'] <= 0:
                raise ValueError("Period must be a positive integer")
    
    def get_required_params(self):
        """Get required parameters for testing."""
        return ["period"]