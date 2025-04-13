import unittest
import sys
import os
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '')))
from src.service import Service

class TestTakeCandleSessions(unittest.TestCase):
  def setUp(self):
    self.service = Service()
  
  def test1(self):
    candle_time = "2025-01-02 22:01:00+0000"
    candle_time = datetime.strptime(candle_time, "%Y-%m-%d %H:%M:%S%z")
    result = self.service.take_candle_sessions(candle_time)

    self.assertListEqual(result, ["Sydney"])

  def test2(self):
    candle_time = "2025-01-02 00:01:00+0000"
    candle_time = datetime.strptime(candle_time, "%Y-%m-%d %H:%M:%S%z")
    result = self.service.take_candle_sessions(candle_time)

    self.assertListEqual(result, ["Sydney", "Tokyo"])

  def test3(self):
    candle_time = "2025-01-02 08:30:00+0000"
    candle_time = datetime.strptime(candle_time, "%Y-%m-%d %H:%M:%S%z")
    result = self.service.take_candle_sessions(candle_time)

    self.assertListEqual(result, ["Tokyo", "London"])

  def test4(self):
    candle_time = "2025-01-02 13:30:00+0000"
    candle_time = datetime.strptime(candle_time, "%Y-%m-%d %H:%M:%S%z")
    result = self.service.take_candle_sessions(candle_time)

    self.assertListEqual(result, ["London", "New York"])

  def test5(self):
    candle_time = "2025-01-02 13:30:00-0500"
    candle_time = datetime.strptime(candle_time, "%Y-%m-%d %H:%M:%S%z")
    result = self.service.take_candle_sessions(candle_time)

    self.assertListEqual(result, ["New York"])

  def test6(self):
    candle_time = "2025-01-02 13:30:00-1200"
    candle_time = datetime.strptime(candle_time, "%Y-%m-%d %H:%M:%S%z")
    result = self.service.take_candle_sessions(candle_time)

    self.assertListEqual(result, ["Sydney", "Tokyo"])
  
  def test7(self):
    candle_time = "2025-01-02 13:30:00+1100"
    candle_time = datetime.strptime(candle_time, "%Y-%m-%d %H:%M:%S%z")
    result = self.service.take_candle_sessions(candle_time)

    self.assertListEqual(result, ["Sydney", "Tokyo"])

  def test8(self):
    candle_time = "2025-01-02 00:30:00+0800"
    candle_time = datetime.strptime(candle_time, "%Y-%m-%d %H:%M:%S%z")
    result = self.service.take_candle_sessions(candle_time)

    self.assertListEqual(result, ["London", "New York"])

if __name__ == '__main__':
  unittest.main()