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
    # filter dataframe to have a dataframe with 3 candles (in a row) that we need.
    new_df = 
    result = self.service.find_imbalance_zone()


if __name__ == '__main__':
  unittest.main()