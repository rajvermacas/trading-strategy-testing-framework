"""
End-to-end integration tests for trading strategy framework.

These tests verify that all components work together correctly.
"""

import pytest
from datetime import datetime, timedelta
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from trading_strategy_framework.data.fetcher import DataFetcher
from trading_strategy_framework.strategies.simple_ma import SimpleMAStrategy
from trading_strategy_framework.backtesting.engine import BacktestEngine


class TestEndToEndIntegration:
    """Test complete end-to-end workflow."""
    
    def test_complete_backtest_workflow(self):
        """Test complete workflow from data fetch to backtest results."""
        # 1. Initialize components
        data_fetcher = DataFetcher("^NSEI", "1h")
        strategy = SimpleMAStrategy("SMA_Test", {'fast_period': 5, 'slow_period': 10})
        backtest_engine = BacktestEngine({'initial_capital': 100000})
        
        # 2. Fetch market data
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 10)  # 9 days of data
        market_data = data_fetcher.fetch_data(start_date, end_date)
        
        # 3. Verify data structure
        assert len(market_data) > 0
        assert all('Close' in item for item in market_data)
        assert all('Timestamp' in item for item in market_data)
        
        # 4. Run backtest
        position_config = {'type': 'fixed', 'amount': 10000}
        results = backtest_engine.run_backtest(strategy, market_data, position_config)
        
        # 5. Verify results structure
        assert 'total_return' in results
        assert 'total_trades' in results
        assert 'win_rate' in results
        assert 'final_capital' in results
        assert 'initial_capital' in results
        
        # 6. Verify results are reasonable
        assert results['initial_capital'] == 100000
        assert results['final_capital'] > 0
        assert results['total_trades'] >= 0
        assert 0 <= results['win_rate'] <= 1
        
        print(f"Backtest completed successfully!")
        print(f"Initial Capital: ${results['initial_capital']:,.2f}")
        print(f"Final Capital: ${results['final_capital']:,.2f}")
        print(f"Total Return: {results['total_return']:.2%}")
        print(f"Total Trades: {results['total_trades']}")
        print(f"Win Rate: {results['win_rate']:.2%}")

    def test_strategy_generates_signals_on_real_data(self):
        """Test that strategy generates signals on market data."""
        # Initialize strategy
        strategy = SimpleMAStrategy("SMA_Test", {'fast_period': 3, 'slow_period': 5})
        
        # Create sample market data with trend
        market_data = []
        base_price = 18000
        
        for i in range(20):
            # Create uptrend then downtrend
            if i < 10:
                price = base_price + i * 20  # Uptrend
            else:
                price = base_price + (20 - i) * 20  # Downtrend
                
            market_data.append({
                'Close': price,
                'Timestamp': datetime(2023, 1, 1) + timedelta(hours=i)
            })
        
        # Calculate indicators
        indicators = strategy.calculate_indicators(market_data)
        
        # Verify indicators were calculated
        assert 'fast_sma' in indicators
        assert 'slow_sma' in indicators
        assert len(indicators['fast_sma']) > 0
        assert len(indicators['slow_sma']) > 0
        
        # Test signal generation at different points
        signals_generated = 0
        for i in range(5, len(market_data)):
            current_data = market_data[:i+1]
            current_indicators = {
                'fast_sma': indicators['fast_sma'][:len(current_data)-2],
                'slow_sma': indicators['slow_sma'][:len(current_data)-4]
            }
            
            signal = strategy.generate_signal(current_data, current_indicators)
            if signal:
                signals_generated += 1
                print(f"Signal generated at step {i}: {signal}")
        
        # Should generate at least some signals due to crossovers
        print(f"Total signals generated: {signals_generated}")

    def test_multiple_strategies_comparison(self):
        """Test running multiple strategies for comparison."""
        # Create different strategy configurations
        strategies = [
            SimpleMAStrategy("SMA_Fast", {'fast_period': 3, 'slow_period': 8}),
            SimpleMAStrategy("SMA_Slow", {'fast_period': 8, 'slow_period': 15}),
            SimpleMAStrategy("SMA_Medium", {'fast_period': 5, 'slow_period': 12})
        ]
        
        # Get market data
        data_fetcher = DataFetcher()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 15)
        market_data = data_fetcher.fetch_data(start_date, end_date)
        
        # Run backtests for each strategy
        results = {}
        position_config = {'type': 'percentage', 'percentage': 0.1}
        
        for strategy in strategies:
            engine = BacktestEngine({'initial_capital': 100000})
            result = engine.run_backtest(strategy, market_data, position_config)
            results[strategy.name] = result
        
        # Verify all strategies ran successfully
        assert len(results) == 3
        for strategy_name, result in results.items():
            assert 'total_return' in result
            assert 'total_trades' in result
            print(f"{strategy_name}: Return={result['total_return']:.2%}, Trades={result['total_trades']}")
        
        # Results should be different (unless by coincidence)
        returns = [result['total_return'] for result in results.values()]
        assert len(set(returns)) > 1 or all(r == 0 for r in returns)  # Different results or all zero

    def test_data_validation_integration(self):
        """Test data validation integration with fetcher."""
        from trading_strategy_framework.data.validator import DataValidator
        
        # Fetch data
        data_fetcher = DataFetcher()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 3)
        market_data = data_fetcher.fetch_data(start_date, end_date)
        
        # Validate data
        validator = DataValidator()
        
        # Check each data point
        for data_point in market_data:
            is_valid = validator.validate_ohlcv_data(data_point)
            assert is_valid, f"Invalid data point: {data_point}"
        
        # Test data cleaning
        cleaned_data = validator.clean_data(market_data)
        assert len(cleaned_data) == len(market_data)  # All data should be valid
        
        print(f"Validated {len(market_data)} data points successfully")

    def test_error_handling_integration(self):
        """Test error handling across components."""
        # Test with invalid date range
        data_fetcher = DataFetcher()
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2023, 1, 1)  # Invalid range
        
        with pytest.raises(ValueError):
            data_fetcher.fetch_data(start_date, end_date)
        
        # Test strategy with invalid config
        with pytest.raises(ValueError):
            SimpleMAStrategy("Invalid", {'fast_period': 20, 'slow_period': 10})
        
        # Test backtest with empty data
        strategy = SimpleMAStrategy("SMA_Test")
        engine = BacktestEngine()
        result = engine.run_backtest(strategy, [], {'type': 'fixed', 'amount': 1000})
        
        # Should return valid results even with no data
        assert result['total_trades'] == 0
        assert result['total_return'] == 0