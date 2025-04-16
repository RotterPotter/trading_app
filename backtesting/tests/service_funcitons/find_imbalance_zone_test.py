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
  
  def test_bearish(self):
    # filter dataframe to have a dataframe with 3 candles (in a row) that we need.
    tz = timezone(timedelta(hours=-5))
    cndl_1_dt = datetime(year=2025, month=2, day=27, hour=9, minute=15, tzinfo=tz)
    cndl_3_dt = datetime(year=2025, month=2, day=27, hour=9, minute=45, tzinfo=tz)

    df = self.data
    filtered_df = df[(df["Time"] >= cndl_1_dt) & (df["Time"] <= cndl_3_dt)]
    candles = [candle_data for candle_data in filtered_df.itertuples()]
    result = self.service.find_imbalance_zone(candles[0], candles[1], candles[2])

    self.assertEqual(result, (2881.24, 2889.19))

  def test_bullish(self):
    # filter dataframe to have a dataframe with 3 candles (in a row) that we need.
    tz = timezone(timedelta(hours=-5))
    cndl_1_dt = datetime(year=2025, month=2, day=26, hour=9, minute=30, tzinfo=tz)
    cndl_3_dt = datetime(year=2025, month=2, day=26, hour=10, minute=00, tzinfo=tz)

    df = self.data
    filtered_df = df[(df["Time"] >= cndl_1_dt) & (df["Time"] <= cndl_3_dt)]
    candles = [candle_data for candle_data in filtered_df.itertuples()]
    result = self.service.find_imbalance_zone(candles[0], candles[1], candles[2])

    print(result)
    self.assertEqual(result, (2896.37, 2898.5))

if __name__ == '__main__':
  unittest.main()