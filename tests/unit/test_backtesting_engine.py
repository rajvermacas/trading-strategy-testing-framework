"""
Tests for backtesting engine.

Following TDD approach: Red-Green-Refactor
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from trading_strategy_framework.backtesting.engine import BacktestEngine, Trade, TradeType
from trading_strategy_framework.strategies.base import Signal, SignalType


class TestTradeType:
    """Test TradeType enum."""
    
    def test_trade_type_has_required_values(self):
        """Test that TradeType enum has all required values."""
        assert TradeType.BUY
        assert TradeType.SELL


class TestTrade:
    """Test Trade class."""
    
    def test_trade_init_buy_order(self):
        """Test Trade initialization for buy order."""
        timestamp = datetime(2023, 1, 1, 10, 0)
        trade = Trade(
            timestamp=timestamp,
            trade_type=TradeType.BUY,
            quantity=100,
            price=1000.0,
            commission=10.0
        )
        
        assert trade.timestamp == timestamp
        assert trade.trade_type == TradeType.BUY
        assert trade.quantity == 100
        assert trade.price == 1000.0
        assert trade.commission == 10.0
        assert trade.total_cost == 100010.0  # 100 * 1000 + 10 (slippage is 0)

    def test_trade_init_sell_order(self):
        """Test Trade initialization for sell order."""
        timestamp = datetime(2023, 1, 1, 10, 0)
        trade = Trade(
            timestamp=timestamp,
            trade_type=TradeType.SELL,
            quantity=100,
            price=1100.0,
            commission=11.0
        )
        
        assert trade.total_cost == -109989.0  # -(100 * 1100 - 11)

    def test_trade_str_representation(self):
        """Test Trade string representation."""
        timestamp = datetime(2023, 1, 1, 10, 0)
        trade = Trade(
            timestamp=timestamp,
            trade_type=TradeType.BUY,
            quantity=100,
            price=1000.0
        )
        
        str_repr = str(trade)
        assert "BUY" in str_repr
        assert "100" in str_repr
        assert "1000.0" in str_repr


class TestBacktestEngine:
    """Test BacktestEngine functionality."""
    
    def test_init_creates_engine_with_default_config(self):
        """Test BacktestEngine initialization with default configuration."""
        engine = BacktestEngine()
        assert engine.initial_capital == 100000.0
        assert engine.commission_rate == 0.001
        assert engine.slippage_rate == 0.0001
        assert engine.current_capital == 100000.0
        assert engine.current_position == 0
        assert engine.trades == []

    def test_init_creates_engine_with_custom_config(self):
        """Test BacktestEngine initialization with custom configuration."""
        config = {
            'initial_capital': 50000.0,
            'commission_rate': 0.002,
            'slippage_rate': 0.0005
        }
        engine = BacktestEngine(config)
        assert engine.initial_capital == 50000.0
        assert engine.commission_rate == 0.002
        assert engine.slippage_rate == 0.0005

    def test_calculate_commission_with_fixed_rate(self):
        """Test commission calculation with fixed rate."""
        engine = BacktestEngine({'commission_rate': 0.001})
        commission = engine._calculate_commission(100, 1000.0)
        assert commission == 100.0  # 100 * 1000 * 0.001

    def test_calculate_slippage_with_fixed_rate(self):
        """Test slippage calculation with fixed rate."""
        engine = BacktestEngine({'slippage_rate': 0.0001})
        
        # Buy order - slippage increases price
        slippage_buy = engine._calculate_slippage(1000.0, TradeType.BUY)
        assert slippage_buy == 0.1  # 1000 * 0.0001
        
        # Sell order - slippage decreases price
        slippage_sell = engine._calculate_slippage(1000.0, TradeType.SELL)
        assert slippage_sell == -0.1  # -1000 * 0.0001

    def test_calculate_position_size_fixed_amount(self):
        """Test position size calculation with fixed amount."""
        engine = BacktestEngine()
        quantity = engine._calculate_position_size(1000.0, 'fixed', {'amount': 10000})
        assert quantity == 10  # 10000 / 1000

    def test_calculate_position_size_percentage(self):
        """Test position size calculation with percentage of capital."""
        engine = BacktestEngine({'initial_capital': 100000})
        quantity = engine._calculate_position_size(1000.0, 'percentage', {'percentage': 0.1})
        assert quantity == 10  # (100000 * 0.1) / 1000

    def test_execute_buy_signal_successful(self):
        """Test successful execution of buy signal."""
        engine = BacktestEngine({'initial_capital': 100000})
        signal = Signal(
            timestamp=datetime(2023, 1, 1, 10, 0),
            signal_type=SignalType.BUY,
            price=1000.0,
            confidence=0.8
        )
        position_config = {'type': 'fixed', 'amount': 10000}
        
        result = engine.execute_signal(signal, position_config)
        
        assert result is True
        assert len(engine.trades) == 1
        assert engine.current_position == 10
        assert engine.current_capital < 100000  # Capital reduced by trade cost

    def test_execute_sell_signal_with_position(self):
        """Test successful execution of sell signal when having position."""
        engine = BacktestEngine({'initial_capital': 100000})
        engine.current_position = 20  # Already have position
        
        signal = Signal(
            timestamp=datetime(2023, 1, 1, 10, 0),
            signal_type=SignalType.SELL,
            price=1100.0,
            confidence=0.8
        )
        position_config = {'type': 'fixed', 'amount': 10000}
        
        result = engine.execute_signal(signal, position_config)
        
        assert result is True
        assert len(engine.trades) == 1
        assert engine.current_position == 11  # 20 - 9 (9 shares sold based on 10000/1100)
        assert engine.current_capital > 100000  # Capital increased by sale

    def test_execute_sell_signal_without_position(self):
        """Test sell signal execution fails when no position available."""
        engine = BacktestEngine()
        signal = Signal(
            timestamp=datetime(2023, 1, 1, 10, 0),
            signal_type=SignalType.SELL,
            price=1100.0,
            confidence=0.8
        )
        position_config = {'type': 'fixed', 'amount': 10000}
        
        result = engine.execute_signal(signal, position_config)
        
        assert result is False
        assert len(engine.trades) == 0
        assert engine.current_position == 0

    def test_execute_buy_signal_insufficient_capital(self):
        """Test buy signal execution fails with insufficient capital."""
        engine = BacktestEngine({'initial_capital': 1000})  # Low capital
        signal = Signal(
            timestamp=datetime(2023, 1, 1, 10, 0),
            signal_type=SignalType.BUY,
            price=1000.0,
            confidence=0.8
        )
        position_config = {'type': 'fixed', 'amount': 50000}  # More than available
        
        result = engine.execute_signal(signal, position_config)
        
        assert result is False
        assert len(engine.trades) == 0
        assert engine.current_position == 0

    def test_run_backtest_with_strategy_and_data(self):
        """Test running complete backtest with strategy and market data."""
        engine = BacktestEngine()
        
        # Mock strategy
        mock_strategy = Mock()
        mock_strategy.calculate_indicators.return_value = {'sma': [1000, 1010, 1020]}
        
        # First call returns BUY signal, second returns None
        mock_strategy.generate_signal.side_effect = [
            Signal(datetime(2023, 1, 1, 10, 0), SignalType.BUY, 1000.0, 0.8),
            None,
            Signal(datetime(2023, 1, 1, 12, 0), SignalType.SELL, 1100.0, 0.7)
        ]
        
        market_data = [
            {'Close': 1000, 'Timestamp': datetime(2023, 1, 1, 10, 0)},
            {'Close': 1050, 'Timestamp': datetime(2023, 1, 1, 11, 0)},
            {'Close': 1100, 'Timestamp': datetime(2023, 1, 1, 12, 0)}
        ]
        
        position_config = {'type': 'fixed', 'amount': 10000}
        
        result = engine.run_backtest(mock_strategy, market_data, position_config)
        
        assert result is not None
        assert 'total_trades' in result
        assert 'final_capital' in result
        assert 'total_return' in result
        assert result['total_trades'] == 2  # One buy, one sell

    def test_calculate_performance_metrics(self):
        """Test performance metrics calculation."""
        engine = BacktestEngine({'initial_capital': 100000})
        
        # Add some trades
        engine.trades = [
            Trade(datetime(2023, 1, 1), TradeType.BUY, 10, 1000.0, 10.0),
            Trade(datetime(2023, 1, 2), TradeType.SELL, 10, 1100.0, 11.0),
        ]
        engine.current_capital = 101000.0
        
        metrics = engine.calculate_performance_metrics()
        
        assert 'total_return' in metrics
        assert 'total_trades' in metrics
        assert 'winning_trades' in metrics
        assert 'losing_trades' in metrics
        assert 'win_rate' in metrics
        assert 'final_capital' in metrics

    def test_reset_engine_state(self):
        """Test resetting engine to initial state."""
        engine = BacktestEngine({'initial_capital': 50000})
        
        # Modify engine state
        engine.current_capital = 40000
        engine.current_position = 10
        engine.trades = [Mock()]
        
        engine.reset()
        
        assert engine.current_capital == 50000
        assert engine.current_position == 0
        assert engine.trades == []