#!/usr/bin/env python3
"""
Demo script for Trading Strategy Testing Framework MVP.

This script demonstrates the core functionality of the framework:
1. Data fetching
2. Strategy implementation
3. Backtesting
4. Performance reporting
"""

import sys
import os
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from trading_strategy_framework.data.fetcher import DataFetcher
from trading_strategy_framework.data.validator import DataValidator
from trading_strategy_framework.strategies.simple_ma import SimpleMAStrategy
from trading_strategy_framework.backtesting.engine import BacktestEngine


def print_header(title):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)


def print_results(results):
    """Print backtest results in a formatted way."""
    print(f"Initial Capital:     ${results['initial_capital']:,.2f}")
    print(f"Final Capital:       ${results['final_capital']:,.2f}")
    print(f"Total Return:        {results['total_return']:.2%}")
    print(f"Total Trades:        {results['total_trades']}")
    print(f"Winning Trades:      {results['winning_trades']}")
    print(f"Losing Trades:       {results['losing_trades']}")
    print(f"Win Rate:            {results['win_rate']:.2%}")
    print(f"Max Drawdown:        {results['max_drawdown']:.2%}")
    print(f"Current Position:    {results['current_position']}")


def main():
    """Run the MVP demonstration."""
    print_header("Trading Strategy Testing Framework - MVP Demo")
    
    # 1. Data Fetching
    print_header("1. Data Fetching")
    print("Initializing data fetcher for Nifty 50...")
    
    data_fetcher = DataFetcher("^NSEI", "1h")
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 2, 1)  # 1 month of data
    
    print(f"Fetching data from {start_date.date()} to {end_date.date()}...")
    market_data = data_fetcher.fetch_data(start_date, end_date)
    
    print(f"✓ Successfully fetched {len(market_data)} data points")
    print(f"  First data point: {market_data[0]['Timestamp']} - Close: ₹{market_data[0]['Close']:,.2f}")
    print(f"  Last data point:  {market_data[-1]['Timestamp']} - Close: ₹{market_data[-1]['Close']:,.2f}")
    
    # 2. Data Validation
    print_header("2. Data Validation")
    validator = DataValidator()
    
    print("Validating market data quality...")
    valid_data_points = 0
    for data_point in market_data:
        if validator.validate_ohlcv_data(data_point):
            valid_data_points += 1
    
    print(f"✓ {valid_data_points}/{len(market_data)} data points are valid ({valid_data_points/len(market_data)*100:.1f}%)")
    
    # Check for gaps
    timestamps = [item['Timestamp'] for item in market_data]
    gaps = validator.detect_gaps(timestamps)
    print(f"✓ Found {len(gaps)} gaps in the time series")
    
    # 3. Strategy Testing
    print_header("3. Strategy Testing")
    
    # Test multiple strategy configurations
    strategies = [
        SimpleMAStrategy("SMA_Conservative", {'fast_period': 10, 'slow_period': 20}),
        SimpleMAStrategy("SMA_Aggressive", {'fast_period': 5, 'slow_period': 10}),
        SimpleMAStrategy("SMA_Long_Term", {'fast_period': 20, 'slow_period': 50})
    ]
    
    position_configs = [
        {'type': 'fixed', 'amount': 50000},
        {'type': 'percentage', 'percentage': 0.1}
    ]
    
    all_results = []
    
    for strategy in strategies:
        print(f"\nTesting strategy: {strategy.name}")
        print(f"  Configuration: Fast={strategy.config['fast_period']}, Slow={strategy.config['slow_period']}")
        
        # Calculate indicators first to show some statistics
        indicators = strategy.calculate_indicators(market_data)
        print(f"  Fast SMA values: {len(indicators['fast_sma'])}")
        print(f"  Slow SMA values: {len(indicators['slow_sma'])}")
        
        for i, pos_config in enumerate(position_configs):
            config_name = "Fixed ₹50K" if pos_config['type'] == 'fixed' else "10% Capital"
            print(f"\n  Position sizing: {config_name}")
            
            # Initialize backtest engine
            engine = BacktestEngine({
                'initial_capital': 500000,  # ₹5 Lakh
                'commission_rate': 0.0003,   # 0.03%
                'slippage_rate': 0.0001      # 0.01%
            })
            
            # Run backtest
            results = engine.run_backtest(strategy, market_data, pos_config)
            
            # Store results
            result_entry = {
                'strategy': strategy.name,
                'position_config': config_name,
                'results': results
            }
            all_results.append(result_entry)
            
            # Print summary
            print(f"    Return: {results['total_return']:.2%}")
            print(f"    Trades: {results['total_trades']}")
            print(f"    Win Rate: {results['win_rate']:.2%}")
    
    # 4. Results Summary
    print_header("4. Detailed Results")
    
    for i, result_entry in enumerate(all_results):
        print(f"\nStrategy {i+1}: {result_entry['strategy']} - {result_entry['position_config']}")
        print("-" * 50)
        print_results(result_entry['results'])
    
    # 5. Best Strategy
    print_header("5. Best Performing Strategy")
    
    if all_results:
        best_result = max(all_results, key=lambda x: x['results']['total_return'])
        print(f"Best Strategy: {best_result['strategy']} with {best_result['position_config']}")
        print_results(best_result['results'])
    else:
        print("No strategies generated trades in this period.")
    
    # 6. Framework Summary
    print_header("6. Framework Capabilities Demonstrated")
    print("✓ Data Fetching: Mock data generation for Nifty 50")
    print("✓ Data Validation: OHLCV validation and gap detection")
    print("✓ Strategy Framework: Simple Moving Average crossover strategy")
    print("✓ Backtesting Engine: Trade execution with realistic costs")
    print("✓ Performance Metrics: Return, win rate, drawdown calculation")
    print("✓ Multiple Configurations: Different strategies and position sizing")
    
    print_header("MVP Demo Complete!")
    print("The Trading Strategy Testing Framework MVP is working successfully!")
    print("Next steps would include:")
    print("- Adding more technical indicators")
    print("- Implementing real data sources")
    print("- Creating HTML reports")
    print("- Adding optimization capabilities")


if __name__ == "__main__":
    main()