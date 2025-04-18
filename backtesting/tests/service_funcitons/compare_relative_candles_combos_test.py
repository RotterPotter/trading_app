import unittest
import sys
import os
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '')))
from src.service import Service
import pandas as pd
from datetime import timezone, timedelta

class TestCompareRelativeCandlesCombos(unittest.TestCase):
  def setUp(self):
    self.service = Service()

    with open("backtesting/tests/testing_data.csv", "r") as fp:
      data = pd.read_csv(fp, parse_dates=['Time'])
    self.data = data

  def test1(self): # equal combos
    candles_datas_list = [candle_data for candle_data in self.data.itertuples()]
    
    combo1 = self.service.build_relative_candles_combo(candles_datas_list[:10])
    combo2 = self.service.build_relative_candles_combo(candles_datas_list[:10])

    result = self.service.compare_relative_candles_combos(combo1, combo2, threshold=1)
    self.assertEqual(result, True)

  def test2(self): # different len
    candles_datas_list = [candle_data for candle_data in self.data.itertuples()]

    combo1 = self.service.build_relative_candles_combo(candles_datas_list[:10])
    combo2 = self.service.build_relative_candles_combo(candles_datas_list[:11])

    result = self.service.compare_relative_candles_combos(combo1, combo2, threshold=1)
    self.assertEqual(result, False)

  def test3(self):
    pass

if __name__ == '__main__':
  unittest.main()