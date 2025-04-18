import unittest
import sys
import os
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '')))
from src.service import Service
import pandas as pd
from datetime import timezone, timedelta

class TestFindCombosInCandlesDatasList(unittest.TestCase):
  def setUp(self):
    self.service = Service()

    with open("backtesting/tests/testing_data.csv", "r") as fp:
      data = pd.read_csv(fp, parse_dates=['Time'])
    self.data = data

  def test1(self):
    candles_datas = [candle_data for candle_data in self.data.itertuples()]
    combo = self.service.build_relative_candles_combo(candles_datas[:5])
    result = self.service.find_combos_in_candles_datas_list(combo, candles_datas, threshold=32)
    self.assertEqual(len(result), 2)

  def test2(self): # find trend reversal 1
    
    trend_reversal_1_combo = self.service.build_relative_candles_combo()

if __name__ == '__main__':
  unittest.main()