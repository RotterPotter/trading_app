import unittest
import sys
import os
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '')))
from src.service import Service
import pandas as pd
from datetime import timezone, timedelta

class TestSliceDataFromSessionStartToCandleTest(unittest.TestCase):
  def setUp(self):
    self.service = Service()

    with open("backtesting/tests/testing_data.csv", "r") as fp:
      data = pd.read_csv(fp, parse_dates=['Time'])
    self.data = data
  
  def test1(self):
    candle_time_str = "2025-01-06 13:30:00-0500"
    candle_time_datetime = datetime.strptime(candle_time_str, "%Y-%m-%d %H:%M:%S%z")
    tz = timezone(timedelta(hours=-5))

    result = self.service.slice_data_from_session_start_to_candle("New York", candle_time_datetime, self.data, tz=tz)
    candles_data = [candle_data for candle_data in result.itertuples()]

    self.assertEqual(candles_data[0].Time, datetime(
      year=candle_time_datetime.year,
      month=candle_time_datetime.month,
      day=candle_time_datetime.day,
      hour=8,
      tzinfo=tz
    ))
    self.assertEqual(candles_data[-1].Time, candle_time_datetime)


if __name__ == '__main__':
  unittest.main()