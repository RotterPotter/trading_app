import unittest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '')))
from src.checker import Checker
import pandas as pd

class TestIsNewYorkSessionChecker(unittest.TestCase):
  def setUp(self):
    with open("backtesting/tests/testing_data.csv", "r") as fp:
      data = pd.read_csv(fp, parse_dates=['Time'])
    self.data = data  
    self.checker = Checker(
      active_checkers={
      "when_trade_is_opened" : {
        "global": [
          "is_new_york_session_checker"
        ],
        "to_close_sell": [
        ],
        "to_close_buy": [
        ]
      },
      "when_trade_is_not_opened" : {
        "global": [
        "is_new_york_session_checker",
        ],
        "to_open_sell": [

        ],
        "to_open_buy": [

        ]
      }
    },
    data=data,
    params={"new_york_session_start_time": "08:00", "new_york_session_end_time": "17:00"}, 
    tz_offset=-5
  )
    
  def test_before_ny_session(self):
    candle_datas = [candle_data for candle_data in self.data.itertuples()]
    candle_data = candle_datas[50] # candle with Time: 2025-01-02 06:30:00-0500

    result = self.checker.is_new_york_session_checker(candle_data=candle_data)
    self.assertEqual(result, "SKIP")

  def test_during_ny_sessin(self):
    candle_datas = [candle_data for candle_data in self.data.itertuples()]
    candle_data = candle_datas[80] # candle with Time: 2025-01-02 14:00:00-0500

    result = self.checker.is_new_york_session_checker(candle_data=candle_data)
    self.assertEqual(result, None)

  def test_after_ny_session(self):
    candle_datas = [candle_data for candle_data in self.data.itertuples()]
    candle_data = candle_datas[100] # candle with Time: 2025-01-02 19:45:00-0500

    result = self.checker.is_new_york_session_checker(candle_data=candle_data)
    self.assertEqual(result, "SKIP")
  
if __name__ == '__main__':
  unittest.main()