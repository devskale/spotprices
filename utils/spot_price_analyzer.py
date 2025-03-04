import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from functools import lru_cache


class SpotPriceAnalyzer:
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
        self.data.set_index('timestamp', inplace=True)
        self.data.sort_index(inplace=True)

    @lru_cache(maxsize=32)
    def average_price_analysis(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        if start_date is None:
            start_date = self.data.index.min()
        if end_date is None:
            end_date = self.data.index.max()

        data_range = self.data.loc[start_date:end_date]

        result = {
            "all_time_average": round(self.data['price'].mean(), 2),
            "selected_range_average": round(data_range['price'].mean(), 2),
            "monthly_averages": {},
            "last_month_average": 0,
            "last_week_average": 0
        }

        # Monthly averages for the past 12 months
        last_12_months = pd.date_range(end=end_date, periods=12, freq='ME')
        for month in last_12_months:
            month_data = self.data[self.data.index.to_period(
                'M') == month.to_period('M')]
            result["monthly_averages"][month.strftime(
                "%Y-%m")] = round(month_data['price'].mean(), 2)

        # Last month average
        last_month_start = end_date - timedelta(days=30)
        result["last_month_average"] = round(
            self.data.loc[last_month_start:end_date, 'price'].mean(), 2)

        # Last week average
        last_week_start = end_date - timedelta(days=7)
        result["last_week_average"] = round(
            self.data.loc[last_week_start:end_date, 'price'].mean(), 2)

        return result
