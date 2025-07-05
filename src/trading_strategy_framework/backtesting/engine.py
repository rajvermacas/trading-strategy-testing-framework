"""
Backtesting engine for trading strategy framework.

This module provides the core backtesting functionality to simulate trading
strategies on historical market data with realistic costs and constraints.
"""

from enum import Enum
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass

from ..strategies.base import BaseStrategy, Signal, SignalType


class TradeType(Enum):
    """Enumeration for different types of trades."""
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class Trade:
    """
    Represents a single trade executed during backtesting.
    
    Attributes:
        timestamp: When the trade was executed
        trade_type: Type of trade (BUY or SELL)
        quantity: Number of shares traded
        price: Price per share
        commission: Commission paid for the trade
        slippage: Slippage cost for the trade
    """
    timestamp: datetime
    trade_type: TradeType
    quantity: int
    price: float
    commission: float = 0.0
    slippage: float = 0.0
    
    @property
    def total_cost(self) -> float:
        """
        Calculate total cost of the trade including commission and slippage.
        
        Returns:
            Total cost (positive for buys, negative for sells)
        """
        if self.trade_type == TradeType.BUY:
            return (self.quantity * (self.price + self.slippage)) + self.commission
        else:  # SELL
            return -((self.quantity * (self.price + self.slippage)) - self.commission)
    
    def __str__(self) -> str:
        """String representation of the trade."""
        return f"Trade({self.trade_type.value} {self.quantity} @ {self.price:.2f})"


class BacktestEngine:
    """
    Core backtesting engine for trading strategy simulation.
    
    This class provides functionality to:
    - Execute trades based on strategy signals
    - Track portfolio performance
    - Calculate realistic trading costs
    - Generate performance metrics
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the backtesting engine.
        
        Args:
            config: Configuration dictionary with engine parameters
        """
        self.config = config or {}
        
        # Initialize configuration with defaults
        self.initial_capital = self.config.get('initial_capital', 100000.0)
        self.commission_rate = self.config.get('commission_rate', 0.001)  # 0.1%
        self.slippage_rate = self.config.get('slippage_rate', 0.0001)     # 0.01%
        
        # Initialize state
        self.reset()
    
    def reset(self) -> None:
        """Reset the engine to initial state."""
        self.current_capital = self.initial_capital
        self.current_position = 0
        self.trades: List[Trade] = []
        self.max_capital = self.initial_capital
        self.max_drawdown = 0.0
    
    def execute_signal(self, signal: Signal, position_config: Dict[str, Any]) -> bool:
        """
        Execute a trading signal.
        
        Args:
            signal: Trading signal to execute
            position_config: Position sizing configuration
            
        Returns:
            True if trade was executed successfully, False otherwise
        """
        if signal.signal_type == SignalType.BUY:
            return self._execute_buy(signal, position_config)
        elif signal.signal_type == SignalType.SELL:
            return self._execute_sell(signal, position_config)
        
        return False
    
    def _execute_buy(self, signal: Signal, position_config: Dict[str, Any]) -> bool:
        """Execute a buy order."""
        quantity = self._calculate_position_size(signal.price, 
                                               position_config.get('type', 'fixed'),
                                               position_config)
        
        if quantity <= 0:
            return False
        
        commission = self._calculate_commission(quantity, signal.price)
        slippage = self._calculate_slippage(signal.price, TradeType.BUY)
        
        total_cost = (quantity * (signal.price + slippage)) + commission
        
        # Check if we have enough capital
        if total_cost > self.current_capital:
            return False
        
        # Execute trade
        trade = Trade(
            timestamp=signal.timestamp,
            trade_type=TradeType.BUY,
            quantity=quantity,
            price=signal.price,
            commission=commission,
            slippage=slippage
        )
        
        self.trades.append(trade)
        self.current_capital -= total_cost
        self.current_position += quantity
        
        return True
    
    def _execute_sell(self, signal: Signal, position_config: Dict[str, Any]) -> bool:
        """Execute a sell order."""
        quantity = self._calculate_position_size(signal.price,
                                               position_config.get('type', 'fixed'),
                                               position_config)
        
        # Check if we have enough position to sell
        if quantity <= 0 or quantity > self.current_position:
            return False
        
        commission = self._calculate_commission(quantity, signal.price)
        slippage = self._calculate_slippage(signal.price, TradeType.SELL)
        
        total_proceeds = (quantity * (signal.price + slippage)) - commission
        
        # Execute trade
        trade = Trade(
            timestamp=signal.timestamp,
            trade_type=TradeType.SELL,
            quantity=quantity,
            price=signal.price,
            commission=commission,
            slippage=slippage
        )
        
        self.trades.append(trade)
        self.current_capital += total_proceeds
        self.current_position -= quantity
        
        # Update max capital and drawdown
        if self.current_capital > self.max_capital:
            self.max_capital = self.current_capital
        
        current_drawdown = (self.max_capital - self.current_capital) / self.max_capital
        if current_drawdown > self.max_drawdown:
            self.max_drawdown = current_drawdown
        
        return True
    
    def _calculate_position_size(self, price: float, sizing_type: str, 
                               config: Dict[str, Any]) -> int:
        """Calculate position size based on configuration."""
        if sizing_type == 'fixed':
            amount = config.get('amount', 10000)
            return int(amount // price)
        elif sizing_type == 'percentage':
            percentage = config.get('percentage', 0.1)
            amount = self.current_capital * percentage
            return int(amount // price)
        
        return 0
    
    def _calculate_commission(self, quantity: int, price: float) -> float:
        """Calculate commission for a trade."""
        return quantity * price * self.commission_rate
    
    def _calculate_slippage(self, price: float, trade_type: TradeType) -> float:
        """Calculate slippage for a trade."""
        if trade_type == TradeType.BUY:
            return price * self.slippage_rate  # Increase price for buys
        else:
            return -price * self.slippage_rate  # Decrease price for sells
    
    def run_backtest(self, strategy: BaseStrategy, market_data: List[Dict[str, Any]], 
                    position_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run complete backtest with strategy and market data.
        
        Args:
            strategy: Trading strategy to test
            market_data: Historical market data
            position_config: Position sizing configuration
            
        Returns:
            Dictionary containing backtest results
        """
        self.reset()
        
        # Calculate indicators once for all data
        indicators = strategy.calculate_indicators(market_data)
        
        # Process each data point
        for i, data_point in enumerate(market_data):
            # Get indicators up to current point
            current_indicators = {}
            for indicator_name, values in indicators.items():
                # Only include indicator values up to current time
                end_idx = min(i + 1, len(values))
                current_indicators[indicator_name] = values[:end_idx]
            
            # Generate signal
            signal = strategy.generate_signal(market_data[:i+1], current_indicators)
            
            if signal:
                self.execute_signal(signal, position_config)
        
        # Calculate final performance metrics
        return self.calculate_performance_metrics()
    
    def calculate_performance_metrics(self) -> Dict[str, Any]:
        """
        Calculate comprehensive performance metrics.
        
        Returns:
            Dictionary containing performance metrics
        """
        total_trades = len(self.trades)
        
        # Calculate portfolio value (cash + position value)
        portfolio_value = self.current_capital
        
        # Calculate returns
        total_return = (portfolio_value - self.initial_capital) / self.initial_capital
        
        # Analyze trades
        winning_trades = 0
        losing_trades = 0
        total_profit = 0.0
        total_loss = 0.0
        
        # Group trades into round trips (buy-sell pairs)
        buy_trades = [t for t in self.trades if t.trade_type == TradeType.BUY]
        sell_trades = [t for t in self.trades if t.trade_type == TradeType.SELL]
        
        # Simple P&L calculation for completed trades
        for buy_trade in buy_trades:
            for sell_trade in sell_trades:
                if sell_trade.timestamp > buy_trade.timestamp:
                    # Calculate profit/loss for this trade pair
                    profit = (sell_trade.price - buy_trade.price) * min(buy_trade.quantity, sell_trade.quantity)
                    profit -= (buy_trade.commission + sell_trade.commission)
                    
                    if profit > 0:
                        winning_trades += 1
                        total_profit += profit
                    else:
                        losing_trades += 1
                        total_loss += abs(profit)
                    break
        
        win_rate = winning_trades / max(1, winning_trades + losing_trades)
        
        return {
            'initial_capital': self.initial_capital,
            'final_capital': portfolio_value,
            'total_return': total_return,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_profit': total_profit,
            'total_loss': total_loss,
            'max_drawdown': self.max_drawdown,
            'current_position': self.current_position
        }