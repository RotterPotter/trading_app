import unittest
import sys
import os
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '')))
from src.service import Service
import pandas as pd
from datetime import timezone, timedelta

class TestIdentifyMarketStructure(unittest.TestCase):
  def setUp(self):
    self.service = Service()

    with open("backtesting/tests/testing_data.csv", "r") as fp:
      data = pd.read_csv(fp, parse_dates=['Time'])
    self.data = data

  def test_identify_bullish(self):
    tz = timezone(timedelta(hours=-5))
    from_datetime = datetime(year=2025, month=2, day=2, hour=21, tzinfo=tz)
    to_datetime = datetime(year=2025, month=2, day=10, hour=23, tzinfo=tz)

    df = self.data
    filtered_df = df[(df["Time"] >= from_datetime) & (df["Time"] <= to_datetime)]

    result = self.service.identify_market_structure(filtered_df)
    self.assertEqual(result["structure"], "bullish")
  
  def test_identify_ranging(self):
    tz = timezone(timedelta(hours=-5))
    from_datetime = datetime(year=2025, month=2, day=10, hour=21, tzinfo=tz)
    to_datetime = datetime(year=2025, month=2, day=18, hour=15, tzinfo=tz)

    df = self.data
    filtered_df = df[(df["Time"] >= from_datetime) & (df["Time"] <= to_datetime)]

    result = self.service.identify_market_structure(filtered_df)
    self.assertEqual(result["structure"], "ranging")

  def test_identify_ranging_2(self):
    tz = timezone(timedelta(hours=-5))
    from_datetime = datetime(year=2025, month=2, day=20, hour=5, tzinfo=tz)
    to_datetime = datetime(year=2025, month=2, day=24, hour=9, tzinfo=tz)

    df = self.data
    filtered_df = df[(df["Time"] >= from_datetime) & (df["Time"] <= to_datetime)]

    result = self.service.identify_market_structure(filtered_df)
    self.assertEqual(result["structure"], "ranging")

  def test_identify_bullish_long(self):
    tz = timezone(timedelta(hours=-5))
    from_datetime = datetime(year=2025, month=1, day=27, hour=5, tzinfo=tz)
    to_datetime = datetime(year=2025, month=2, day=11, hour=5, tzinfo=tz)

    df = self.data
    filtered_df = df[(df["Time"] >= from_datetime) & (df["Time"] <= to_datetime)]

    result = self.service.identify_market_structure(filtered_df)
    self.assertEqual(result["structure"], "bullish")

  def test_identify_bullish_long_2(self):
    tz = timezone(timedelta(hours=-5))
    from_datetime = datetime(year=2025, month=1, day=2, hour=5, tzinfo=tz)
    to_datetime = datetime(year=2025, month=2, day=20, hour=5, tzinfo=tz)

    df = self.data
    filtered_df = df[(df["Time"] >= from_datetime) & (df["Time"] <= to_datetime)]

    result = self.service.identify_market_structure(filtered_df, recent_swing_limit=10000)
    self.assertEqual(result["structure"], "bullish")

  def test_identify_bearish(self):
    tz = timezone(timedelta(hours=-5))
    from_datetime = datetime(year=2025, month=2, day=24, hour=10, tzinfo=tz)
    to_datetime = datetime(year=2025, month=2, day=28, hour=12, tzinfo=tz)

    df = self.data
    filtered_df = df[(df["Time"] >= from_datetime) & (df["Time"] <= to_datetime)]

    result = self.service.identify_market_structure(filtered_df, recent_swing_limit=10000)
    self.assertEqual(result["structure"], "bearish")

  def test_identify_bearish_2(self):
    tz = timezone(timedelta(hours=-5))
    from_datetime = datetime(year=2025, month=1, day=24, hour=10, tzinfo=tz)
    to_datetime = datetime(year=2025, month=1, day=28, hour=5, tzinfo=tz)

    df = self.data
    filtered_df = df[(df["Time"] >= from_datetime) & (df["Time"] <= to_datetime)]

    result = self.service.identify_market_structure(filtered_df, recent_swing_limit=100)
    self.assertEqual(result["structure"], "bullish")

if __name__ == '__main__':
  unittest.main()