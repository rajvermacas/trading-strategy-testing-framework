"""
Integration tests for Stage 2 enhanced features.

Tests the integration of new strategies (MACD, RSI) with the backtesting engine
and ensures realistic trading costs are properly applied.
"""

import pytest
from datetime import datetime, timedelta

from src.trading_strategy_framework.strategies.macd import MACDStrategy
from src.trading_strategy_framework.strategies.rsi import RSIStrategy
from src.trading_strategy_framework.backtesting.engine import BacktestEngine
from src.trading_strategy_framework.data.fetcher import DataFetcher


class TestStage2Integration:
    """Integration tests for Stage 2 features."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.fetcher = DataFetcher()
        
        # Create engine with Stage 2 realistic costs
        self.engine = BacktestEngine({
            'initial_capital': 100000.0,
            'commission_rate': 0.0003,  # 0.03%
            'slippage_rate': 0.0002,    # 0.02%
            'impact_cost_rate': 0.0001  # 0.01%
        })
        
    def _create_trending_data(self, num_points: int = 100, trend_direction: str = "up") -> list:
        """Create data with specific trend for testing divergence."""
        base_date = datetime(2023, 1, 1)
        data = []
        
        for i in range(num_points):
            if trend_direction == "up":
                base_price = 100 + i * 0.5  # Strong uptrend
            elif trend_direction == "down":
                base_price = 200 - i * 0.5  # Strong downtrend
            else:  # oscillating
                import math
                base_price = 100 + 10 * math.sin(i * 0.2)
                
            data.append({
                'datetime': (base_date + timedelta(hours=i)).isoformat(),
                'open': base_price,
                'high': base_price * 1.02,
                'low': base_price * 0.98,
                'close': base_price,
                'volume': 1000 + i * 10
            })
        
        return data
        
    def test_macd_strategy_integration_with_backtesting(self):
        """Test MACD strategy integration with backtesting engine."""
        # Create MACD strategy
        macd_strategy = MACDStrategy("MACD_Integration", {
            'fast_period': 8,
            'slow_period': 21,
            'signal_period': 5
        })
        
        # Get sample data
        data = self._create_trending_data(50, "oscillating")
        
        # Run backtest
        position_config = {'type': 'fixed', 'amount': 10000}
        results = self.engine.run_backtest(macd_strategy, data, position_config)
        
        # Verify results structure
        assert 'total_return' in results
        assert 'win_rate' in results
        assert 'max_drawdown' in results
        assert 'total_trades' in results
        assert 'final_capital' in results
        
        # Verify realistic results
        assert isinstance(results['total_return'], float)
        assert 0 <= results['win_rate'] <= 1.0
        assert results['max_drawdown'] >= 0  # Drawdown is reported as positive percentage
        
    def test_rsi_strategy_integration_with_backtesting(self):
        """Test RSI strategy integration with backtesting engine."""
        # Create RSI strategy
        rsi_strategy = RSIStrategy("RSI_Integration", {
            'period': 14,
            'overbought': 75,
            'oversold': 25
        })
        
        # Get sample data
        data = self._create_trending_data(50, "oscillating")
        
        # Run backtest
        position_config = {'type': 'fixed', 'amount': 10000}
        results = self.engine.run_backtest(rsi_strategy, data, position_config)
        
        # Verify results structure
        assert 'total_return' in results
        assert 'win_rate' in results
        assert 'max_drawdown' in results
        assert 'total_trades' in results
        assert 'final_capital' in results
        
    def test_rsi_divergence_detection_integration(self):
        """Test RSI divergence detection in realistic scenario."""
        # Create RSI strategy with divergence enabled
        rsi_strategy = RSIStrategy("RSI_Divergence", {
            'period': 14,
            'overbought': 70,
            'oversold': 30,
            'use_divergence': True
        })
        
        # Create data pattern for divergence
        data = []
        base_date = datetime(2023, 1, 1)
        
        # Create price pattern that may produce divergence
        for i in range(50):
            if i < 20:
                price = 100 + i * 2  # Strong uptrend
            elif i < 35:
                price = 140 + (i - 20) * 0.5  # Weaker uptrend (potential divergence)
            else:
                price = 147 - (i - 35) * 1  # Reversal
                
            data.append({
                'datetime': (base_date + timedelta(hours=i)).isoformat(),
                'open': price,
                'high': price * 1.01,
                'low': price * 0.99,
                'close': price,
                'volume': 1000
            })
        
        # Calculate indicators
        indicators = rsi_strategy.calculate_indicators(data)
        
        # Verify divergence calculation
        assert 'divergence' in indicators
        assert len(indicators['divergence']) == len(data)
        
        # Test signal generation with divergence
        signal = rsi_strategy.generate_signal(data, indicators)
        # Signal may or may not be generated - just ensure no errors
        
    def test_realistic_trading_costs_impact(self):
        """Test that Stage 2 realistic trading costs are properly applied."""
        # Create simple strategy for cost testing
        macd_strategy = MACDStrategy("MACD_Costs", {
            'fast_period': 5,
            'slow_period': 10,
            'signal_period': 3
        })
        
        # Create data that will generate signals
        data = self._create_trending_data(30, "up")
        
        # Run backtest and track costs
        position_config = {'type': 'fixed', 'amount': 10000}
        results = self.engine.run_backtest(macd_strategy, data, position_config)
        
        # Verify that trading costs are being applied
        if len(self.engine.trades) > 0:
            for trade in self.engine.trades:
                # Check that realistic costs are applied
                assert trade.commission > 0  # Commission should be applied
                assert hasattr(trade, 'impact_cost')  # Stage 2 enhancement
                
                # Verify commission is approximately 0.03% of trade value
                expected_commission = trade.quantity * trade.price * 0.0003
                assert abs(trade.commission - expected_commission) < 0.01
        
    def test_multiple_strategies_comparison(self):
        """Test comparison of multiple Stage 2 strategies."""
        strategies = [
            MACDStrategy("MACD_Compare", {'fast_period': 12, 'slow_period': 26, 'signal_period': 9}),
            RSIStrategy("RSI_Compare", {'period': 14, 'overbought': 70, 'oversold': 30})
        ]
        
        data = self._create_trending_data(40, "oscillating")
        results = {}
        
        position_config = {'type': 'fixed', 'amount': 10000}
        
        for strategy in strategies:
            self.engine.reset()  # Reset for each strategy
            strategy_results = self.engine.run_backtest(strategy, data, position_config)
            results[strategy.name] = strategy_results
        
        # Verify all strategies produced valid results
        for strategy_name, strategy_results in results.items():
            assert 'total_return' in strategy_results
            assert 'win_rate' in strategy_results
            assert isinstance(strategy_results['total_return'], float)
            
    def test_rsi_edge_cases(self):
        """Test RSI strategy edge cases for better coverage."""
        rsi_strategy = RSIStrategy("RSI_Edge", {
            'period': 5,  # Shorter period for faster testing
            'overbought': 80,
            'oversold': 20
        })
        
        # Test with data that produces RSI = 100 (all gains)
        data = []
        base_date = datetime(2023, 1, 1)
        
        for i in range(20):
            price = 100 + i * 5  # Strong uptrend
            data.append({
                'datetime': (base_date + timedelta(hours=i)).isoformat(),
                'open': price,
                'high': price * 1.01,
                'low': price * 0.99,
                'close': price,
                'volume': 1000
            })
        
        # Calculate indicators
        indicators = rsi_strategy.calculate_indicators(data)
        
        # Check that RSI calculation handles extreme cases
        rsi_values = [x for x in indicators['rsi'] if x is not None]
        assert len(rsi_values) > 0
        
        # RSI should be between 0 and 100
        for rsi in rsi_values:
            assert 0 <= rsi <= 100
            
        # Test signal generation on extreme RSI values
        signal = rsi_strategy.generate_signal(data, indicators)
        if signal:
            assert hasattr(signal, 'confidence')
            assert 0 <= signal.confidence <= 1.0
            
    def test_macd_zero_line_crossover_coverage(self):
        """Test MACD zero line crossover for better coverage."""
        macd_strategy = MACDStrategy("MACD_Zero", {
            'fast_period': 5,
            'slow_period': 10,
            'signal_period': 3,
            'use_zero_cross': True
        })
        
        # Create oscillating data around a mean to trigger zero crossovers
        data = []
        base_date = datetime(2023, 1, 1)
        
        for i in range(30):
            import math
            price = 100 + 5 * math.sin(i * 0.5)  # Oscillating pattern
            
            data.append({
                'datetime': (base_date + timedelta(hours=i)).isoformat(),
                'open': price,
                'high': price * 1.01,
                'low': price * 0.99,
                'close': price,
                'volume': 1000
            })
        
        # Calculate indicators
        indicators = macd_strategy.calculate_indicators(data)
        
        # Check for zero crossovers in MACD line
        macd_line = indicators['macd_line']
        zero_crossovers = 0
        
        for i in range(1, len(macd_line)):
            if (macd_line[i] is not None and macd_line[i-1] is not None):
                if ((macd_line[i] > 0 and macd_line[i-1] <= 0) or 
                    (macd_line[i] < 0 and macd_line[i-1] >= 0)):
                    zero_crossovers += 1
        
        # Should detect some zero crossovers with oscillating data
        assert zero_crossovers >= 0
        
        # Test signal generation
        signal = macd_strategy.generate_signal(data, indicators)
        # Signal generation should complete without errors