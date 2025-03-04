# tests/test_spot_price_analyzer.py

from config import CONFIG
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from db.models.spot_prices import SpotPrice
from utils.spot_price_analyzer import SpotPriceAnalyzer
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
import pytest

# Add project root to path
project_root = Path(__file__).parents[1]
sys.path.append(str(project_root))


@pytest.fixture
def sample_data():
    """Create sample data for testing the SpotPriceAnalyzer"""
    # Create a date range for the past year
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    date_range = pd.date_range(start=start_date, end=end_date, freq='H')

    # Create sample prices (using a simple pattern for predictability)
    prices = [100 + (i % 50) for i in range(len(date_range))]

    # Create DataFrame
    df = pd.DataFrame({'timestamp': date_range, 'price': prices})
    return df


def test_average_price_analysis(sample_data):
    """Test the average_price_analysis method of SpotPriceAnalyzer"""
    # Initialize analyzer with sample data
    analyzer = SpotPriceAnalyzer(sample_data)

    # Get analysis results
    result = analyzer.average_price_analysis()

    # Check that the result has the expected structure
    assert isinstance(result, dict)
    assert "all_time_average" in result
    assert "selected_range_average" in result
    assert "monthly_averages" in result
    assert "last_month_average" in result
    assert "last_week_average" in result

    # Check that values are within expected range
    assert 100 <= result["all_time_average"] <= 150
    assert 100 <= result["last_month_average"] <= 150
    assert 100 <= result["last_week_average"] <= 150

    # Check that monthly averages are present for the last 12 months
    assert len(result["monthly_averages"]) <= 12

    # Test with custom date range
    now = datetime.now()
    three_months_ago = now - timedelta(days=90)
    custom_result = analyzer.average_price_analysis(
        start_date=three_months_ago,
        end_date=now
    )

    # Verify custom range results
    assert custom_result["selected_range_average"] != result["all_time_average"]
    assert 100 <= custom_result["selected_range_average"] <= 150


def test_with_db_data():
    """Test the analyzer with actual data from the database (if available)"""
    try:
        # Connect to the database
        db_file = CONFIG['db_path'] / CONFIG['db_file']
        engine = create_engine(f'sqlite:///{db_file}')

        with Session(engine) as session:
            # Get database first and last day
            first_price = (session.query(SpotPrice)
                           .order_by(SpotPrice.start_timestamp)
                           .first())
            last_price = (session.query(SpotPrice)
                          .order_by(SpotPrice.start_timestamp.desc())
                          .first())

            if first_price and last_price:
                first_day = datetime.fromtimestamp(first_price.start_timestamp)
                last_day = datetime.fromtimestamp(last_price.start_timestamp)
                print(
                    f"\nDatabase contains data from {first_day.strftime('%Y-%m-%d')} to {last_day.strftime('%Y-%m-%d')}")

                # Query ALL prices for the complete analysis
                all_prices = (session.query(SpotPrice)
                              .order_by(SpotPrice.start_timestamp)
                              .all())

                # Convert to DataFrame
                data = pd.DataFrame([
                    {
                        'timestamp': datetime.fromtimestamp(p.start_timestamp),
                        'price': p.price
                    } for p in all_prices
                ])

                # Test analyzer with complete data
                analyzer = SpotPriceAnalyzer(data)
                result = analyzer.average_price_analysis()

                print(f"\nAnalysis using complete dataset:")
                print(
                    f"All-time average price: {result['all_time_average']} EUR/MWh")
                print(
                    f"Last month average: {result['last_month_average']} EUR/MWh")
                print(
                    f"Last week average: {result['last_week_average']} EUR/MWh")

                # Print some additional information
                print(f"\nTotal number of price points: {len(data)}")
                print(
                    f"Date range in analysis: {data.index.min().strftime('%Y-%m-%d')} to {data.index.max().strftime('%Y-%m-%d')}")

    except Exception as e:
        pytest.skip(f"Database test skipped: {str(e)}")


if __name__ == "__main__":
    # Create sample data manually when running the file directly
    def create_sample_data():
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        date_range = pd.date_range(start=start_date, end=end_date, freq='h')
        prices = [100 + (i % 50) for i in range(len(date_range))]
        return pd.DataFrame({'timestamp': date_range, 'price': prices})

    # Run tests manually
    sample_df = create_sample_data()
    test_average_price_analysis(sample_df)
    test_with_db_data()
    print("All tests passed!")
