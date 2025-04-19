import unittest
import sys
import os
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '')))
from src.service import Service
import pandas as pd
import json
from datetime import timezone, timedelta

class TestFindCombosInCandlesDatasList(unittest.TestCase):
  def setUp(self):
    self.service = Service()

  def test1(self): # find trend reversal 1
    with open("backtesting/tests/testing_data_5.csv", "r") as fp:
      data = pd.read_csv(fp, parse_dates=['Time'])

    with open("backtesting/patterns/trend_reversal_1_bearish_278candles_1.json", "r") as fp:
      combo = json.load(fp)
    
    candles_datas = [cndl_data for cndl_data in data.itertuples()]
    result = self.service.find_combos_in_candles_datas_list(combo, candles_datas, threshold=2)
    print(result)



if __name__ == '__main__':
  unittest.main()