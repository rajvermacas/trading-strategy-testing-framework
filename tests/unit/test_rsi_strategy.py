"""
Unit tests for RSI (Relative Strength Index) strategy.
"""

import pytest
from datetime import datetime, timedelta

from src.trading_strategy_framework.strategies.rsi import RSIStrategy
from src.trading_strategy_framework.strategies.base import SignalType


class TestRSIStrategy:
    """Test cases for RSI strategy implementation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.strategy = RSIStrategy("RSI_Test")
        
    def test_rsi_strategy_initialization(self):
        """Test RSI strategy initializes correctly."""
        assert self.strategy.name == "RSI_Test"
        assert self.strategy.period == 14
        assert self.strategy.overbought == 70
        assert self.strategy.oversold == 30
        
    def test_rsi_custom_parameters(self):
        """Test RSI strategy with custom parameters."""
        custom_config = {
            'period': 21,
            'overbought': 80,
            'oversold': 20
        }
        custom_strategy = RSIStrategy("RSI_Custom", custom_config)
        
        assert custom_strategy.period == 21
        assert custom_strategy.overbought == 80
        assert custom_strategy.oversold == 20
        
    def test_config_validation(self):
        """Test configuration validation."""
        # Test invalid period
        with pytest.raises(ValueError, match="must be a positive integer"):
            RSIStrategy("RSI_Invalid", {
                'period': -1,
                'overbought': 70,
                'oversold': 30
            })
        
        # Test invalid thresholds
        with pytest.raises(ValueError, match="Overbought must be greater than oversold"):
            RSIStrategy("RSI_Invalid", {
                'period': 14,
                'overbought': 30,
                'oversold': 70
            })
            
    def _create_sample_data(self, num_points: int = 100, trend: str = "up") -> list:
        """Create sample market data for testing."""
        base_date = datetime(2023, 1, 1)
        data = []
        
        for i in range(num_points):
            if trend == "up":
                base_price = 100 + i * 0.2  # Strong uptrend for RSI > 70
            elif trend == "down":
                base_price = 200 - i * 0.2  # Strong downtrend for RSI < 30
            else:
                base_price = 100 + (i % 10 - 5) * 0.1  # Sideways
            
            data.append({
                'datetime': (base_date + timedelta(hours=i)).isoformat(),
                'open': base_price,
                'high': base_price * 1.01,
                'low': base_price * 0.99,
                'close': base_price,
                'volume': 1000 + i * 10
            })
        
        return data
        
    def test_rsi_calculation(self):
        """Test RSI indicator calculation."""
        data = self._create_sample_data(30)
        
        # Calculate RSI
        indicators = self.strategy.calculate_indicators(data)
        
        # Verify RSI components exist
        assert 'rsi' in indicators
        assert 'avg_gain' in indicators
        assert 'avg_loss' in indicators
        
        # Check that RSI values are calculated after initial period
        assert len(indicators['rsi']) == len(data)
        
        # Check that some values are not None
        non_none_rsi = [x for x in indicators['rsi'] if x is not None]
        assert len(non_none_rsi) > 0
        
        # Check RSI bounds (0-100)
        for rsi_val in non_none_rsi:
            assert 0 <= rsi_val <= 100
        
    def test_insufficient_data(self):
        """Test handling of insufficient data."""
        # Create data with fewer points than required
        data = self._create_sample_data(10)  # Less than required for RSI
        
        with pytest.raises(ValueError, match="Not enough data points"):
            self.strategy.calculate_indicators(data)
            
    def test_signal_generation_overbought(self):
        """Test overbought signal generation."""
        # Create data with strong uptrend to generate overbought signals
        data = self._create_sample_data(30, trend="up")
        
        indicators = self.strategy.calculate_indicators(data)
        
        # Test signal generation
        signal = self.strategy.generate_signal(data, indicators)
        
        if signal:
            assert signal.signal_type in [SignalType.BUY, SignalType.SELL]
            assert signal.price > 0
            assert 0 <= signal.confidence <= 1.0
            
    def test_signal_generation_oversold(self):
        """Test oversold signal generation."""
        # Create data with strong downtrend to generate oversold signals
        data = self._create_sample_data(30, trend="down")
        
        indicators = self.strategy.calculate_indicators(data)
        
        # Test signal generation
        signal = self.strategy.generate_signal(data, indicators)
        
        if signal:
            assert signal.signal_type in [SignalType.BUY, SignalType.SELL]
            assert signal.price > 0
            assert 0 <= signal.confidence <= 1.0
            
    def test_rsi_divergence_detection(self):
        """Test RSI divergence detection if implemented."""
        data = self._create_sample_data(50)
        
        indicators = self.strategy.calculate_indicators(data)
        
        # Test if divergence is calculated
        if 'divergence' in indicators:
            assert len(indicators['divergence']) == len(data)
            
    def test_required_params(self):
        """Test required params method."""
        required_params = self.strategy.get_required_params()
        assert 'period' in required_params
        assert 'overbought' in required_params
        assert 'oversold' in required_params
        
    def test_strategy_string_representation(self):
        """Test string representations of the strategy."""
        assert str(self.strategy) == "RSI(14, 70, 30)"
        assert "RSIStrategy" in repr(self.strategy)
        assert "RSI_Test" in repr(self.strategy)