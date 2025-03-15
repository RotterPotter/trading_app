from typing import List, Union, Optional, Tuple, Dict
from abc import ABC, abstractmethod
import pandas as pd
from service import Service
from datetime import time, datetime
from checkers import Checker
import json
from config import settings
from fractions import Fraction

class BacktestingPorgram:
  def __init__(
      self, 
      historical_data: pd.DataFrame,
      checker: Checker

  ):
    self.historical_data = historical_data
    self.executed_trades: Dict[int, Trade] = {}
    self.checker_logger = pd.DataFrame([], columns=["CandleTime", "TriggeredChecker", "TakenAction"], )
    self.checker = checker
    self.summary = None
    self.opened_trade = None

  def start(self): 
    self.on_start_program()
    
    for candle_data in self.historical_data.itertuples(index=False): # iteration through candles and their data
      trade_is_opened = False if self.opened_trade is None else True # check if any trade is currently opened
      opened_trade_type = self.opened_trade.trade_type if trade_is_opened else None

      action, triggered_checker_name = self.checker.check(candle_data, trade_is_opened=trade_is_opened, opened_trade_type=opened_trade_type)  # uses all active checkers to check candle data
      
      # loggs an action and triggered_checker_name, candle gmt
      self.checker_log(candle_data.GmtTime, action, triggered_checker_name)

      if action in ["SKIP", None]:
        continue

      if action.split(" ")[0] in ["SELL", "BUY"]:
        position_in_percantage = float(action.split(" ")[1][:-1])
        #  initializes Trade object, adds trade to a self.opened_trade
        self.open_trade(trade_type=action, candle_data=candle_data, position_in_percantage=position_in_percantage, opening_checker_name=triggered_checker_name)
    
      elif action.startswith("CLOSE"):
        part_to_close = float(action.split(" ")[1][:-1])
        
        if part_to_close == 100:
          self.close_trade(candle_data=candle_data, triggered_checker=triggered_checker_name)
        else:
          self.close_trade_part(candle_data=candle_data, triggered_checker=triggered_checker_name, part=part_to_close)

    self.on_finish_program()

  def open_trade(self, trade_type:str, candle_data, position_in_percantage:float, opening_checker_name:str):
    service = Service()
    stop_loss = service.calculate_stop_loss(candle_data, trade_type, self.historical_data)
    take_profit = service.calculate_take_profit(candle_data, trade_type, self.historical_data)
    new_trade = Trade(trade_type=trade_type, candle_data=candle_data, position_in_percantage=position_in_percantage, triggered_opening_checker=opening_checker_name, stop_loss=stop_loss, take_profit=take_profit)
    self.opened_trade = new_trade
    self.checker.opened_trade = new_trade

  def close_trade(self, candle_data, triggered_checker:str):
    self.opened_trade.close(candle_data=candle_data, triggered_checker=triggered_checker)
    # add trade into executed trades
    self.add_to_executed_trades(self.opened_trade)
    self.opened_trade = None
    self.checker.opened_trade = None

  def close_trade_part(self, candle_data, triggered_checker, part:float):
    # this funciton returns True if trade was closed completely, False otherwise
    trade_was_closed = self.opened_trade.close_part(candle_data=candle_data, triggered_checker=triggered_checker, part_amount_perctage=part)
    if trade_was_closed:
      self.add_to_executed_trades(self.opened_trade)
      self.opened_trade = None
      self.checker.opened_trade = None

  def checker_log(self, candle_gmt, action:Optional[str], triggered_checker_name:Optional[str]):
    new_data = pd.DataFrame([[candle_gmt, triggered_checker_name, action]], columns=["CandleTime", "TriggeredChecker", "TakenAction"])
    self.checker_logger = pd.concat([self.checker_logger, new_data], ignore_index=True)

  def add_to_executed_trades(self, trade):
    self.executed_trades[self.opened_trade.id] = trade
    with open(settings.EXECUTED_TRADES_FILE_PATH, "w") as fp:
      data_to_serialize = []
      for trade in self.executed_trades.values():
        data_to_serialize.append(trade.to_dict())
      json.dump(data_to_serialize, fp)

  def on_finish_program(self):
    with open(settings.LOGS_FILE_PATH, 'w') as fp:
      self.checker_logger.to_csv(fp)
    self.summary = self.generate_summary()
    self.print_executed_trades()

  def on_start_program(self):
    with open(settings.EXECUTED_TRADES_FILE_PATH, "w") as fp:
      json.dump([], fp)

  # TODO
  def generate_summary(self) -> pd.DataFrame:
    data = {
    "Opened Trades": [self.calculate_opened_trades()],
    "Win Ratio": [self.calculate_win_ratio()],
    # "Win Ratio incl.BE": [self.calculate_win_ratio_incl_be()],
    "Average R:R": [self.calculate_average_rr()],
    "P/L": [self.calculate_pl()],
    # "Max Drop Down": [self.calculate_max_drop_down()],
    "Consecutive Losses": [self.calculate_consecutive_losses()],
    "Losses Quantity": [self.calculate_losses_quantity()],
    "BE Quantity": [self.calculate_be_quantity()],
    "Win Quantity": [self.calculate_win_quanity()]
    }
    return pd.DataFrame(data)
  
  def calculate_opened_trades(self):
    return len(self.executed_trades.keys())
  
  def calculate_win_ratio(self):
    quantity_of_all_trades = len(self.executed_trades)
    return f'{self.calculate_win_quanity() / quantity_of_all_trades * 100}%'

  def calculate_win_ratio_incl_be(self):
    quantity_of_all_trades = len(self.executed_trades)
    return f'{(self.calculate_win_quanity() + self.calculate_be_quantity()) / quantity_of_all_trades * 100}%'

  def calculate_pl(self):
    pl_sum = 0
    for trade in self.executed_trades.values():
      pl_sum += trade.pl
    return f'{round(pl_sum, 2)}%'

  def calculate_average_rr(self):
    rr_sum = 0
    for trade in self.executed_trades.values():
        rr_sum += trade.r_r
    average_rr = round(rr_sum / len(self.executed_trades.keys()), 2)
    chis = 1
    znamen = round((1 / average_rr), 2)
    return  f'{chis}:{znamen}'

  def calculate_max_drop_down(self):
    return None

  def calculate_consecutive_losses(self):
    consecutive_losses = 0
    n = 0
    for trade in self.executed_trades.values():
      if trade.result == "LOSS":
        n += 1
      elif trade.result in ["WIN", "BE"]:
        n = 0
      consecutive_losses = n if n > consecutive_losses else consecutive_losses
    return consecutive_losses

  # TODO
  def calculate_losses_quantity(self):
    quantity_of_lose_trades = 0
    for trade in self.executed_trades.values():
      if trade.result == "LOSS":
        quantity_of_lose_trades += 1
    return quantity_of_lose_trades

  # TODO
  def calculate_be_quantity(self):
    quantity_of_be_trades = 0
    for trade in self.executed_trades.values():
      if trade.result == "BE":
        quantity_of_be_trades += 1
    return quantity_of_be_trades

  # TODO
  def calculate_win_quanity(self):
    quantity_of_win_trades = 0
    for trade in self.executed_trades.values():
      if trade.result == "WIN":
        quantity_of_win_trades += 1
    return quantity_of_win_trades

  
  def print_executed_trades(self):
    for key, value in self.executed_trades.items():
      print(f'ID: {key} | {str(value)}')

class Trade():
  _id_counter = 0

  def __init__(
      self,
      trade_type: str, # SELL/BUY
      position_in_percantage:float, # part of the balance that we are risking
      triggered_opening_checker,
      candle_data,
      stop_loss:float,
      take_profit:float
    ):
    Trade._id_counter += 1
    self.id = Trade._id_counter
    self.opening_gmt_time = candle_data.GmtTime
    self.closing_gmt_time = None
    self.trade_type = trade_type
    self.entering_price = candle_data.Close
    self.closing_price = None

    
    


    self.position_in_percantage:float = position_in_percantage
    self.active_part = 100
    self.result = None
    self.pl = None
    self.logs = pd.DataFrame([], columns=["GmtTime", "Log"])
    self.triggered_opening_checker = triggered_opening_checker

    # define stop loss and take profit
    self.stop_loss = stop_loss
    self.take_profit = take_profit

    if self.trade_type.startswith("SELL"):
      self.potential_reward = self.entering_price - self.take_profit 
      self.potential_risk = abs(self.entering_price - self.stop_loss)

    elif self.trade_type.startswith("BUY"):
        self.potential_reward = self.take_profit - self.entering_price
        self.potential_risk = abs(self.entering_price - self.stop_loss)

    self.r_r = self.potential_risk / self.potential_reward 



    self.triggered_checkers = [triggered_opening_checker]


    
    # logging of the trade opening
    self.log(self.opening_gmt_time, f"Trade {self.trade_type} was opened on the price {self.entering_price}.\nAction triggered by checker: {self.triggered_opening_checker}.\nStop loss:{self.stop_loss}\nTake profit:{self.take_profit}")

  def log(self, gmt_time:str, message:str):
    new_data = pd.DataFrame([[gmt_time, message]], columns=["GmtTime", "Log"])
    self.logs = pd.concat([self.logs, new_data], ignore_index=True)
  
  def close(self, candle_data, triggered_checker):
    self.closing_price = candle_data.Close
    # on close should calculate parameters that will be used in summary. (result, pl,)
    if self.trade_type.startswith("SELL"):
      if self.entering_price > candle_data.Close:
          self.result = "WIN"  
      elif self.entering_price < candle_data.Close:
          self.result = "LOSS"  
      elif self.entering_price == candle_data.Close:
          self.result = "BE"  

      self.pl = ((self.entering_price - self.closing_price) / self.entering_price) * self.position_in_percantage * 100

    elif self.trade_type.startswith("BUY"):
      if self.entering_price < candle_data.Close:
          self.result = "WIN"  
      elif self.entering_price > candle_data.Close:
          self.result = "LOSS"  
      elif self.entering_price == candle_data.Close:
          self.result = "BE"

      self.pl = ((self.closing_price - self.entering_price) / self.entering_price) * self.position_in_percantage * 100


    self.closing_gmt_time = candle_data.GmtTime
    self.active_part = 0
    self.log(candle_data.GmtTime, f"Trade {self.trade_type} was closed on the price {candle_data.Close}.\nAction triggered by checker: {triggered_checker}.\nResult: {self.result}\nP/L: {self.pl}%.")
    if triggered_checker:
      self.triggered_checkers.append(triggered_checker)

  def update_stop_loss(self, candle_data, new_stop_loss:float, triggered_checker):
    self.stop_loss = new_stop_loss
    self.log(candle_data.GmtTime, f"Stop loss was updated by {triggered_checker}.\nNew stop loss:{new_stop_loss}")
    if triggered_checker:
      self.triggered_checkers.append(triggered_checker)

  def close_part(self, candle_data, part_amount_perctage:float, triggered_checker: Optional[str] = None) -> bool:
    if (self.active_part - part_amount_perctage) < 0:
      self.active_part = 0
      self.log(candle_data.GmtTime, f"Trade was partially closed on the price{candle_data.Close}.\nAction triggered by checker: {triggered_checker}.\nClosed by: {part_amount_perctage}%.\nRemaining position part: {self.active_part}%.\nInitializing closing trade process...")
      if triggered_checker:
        self.triggered_checkers.append(triggered_checker)
      self.close(candle_data=candle_data)
      return True
    else:
      self.active_part -= part_amount_perctage
      self.log(candle_data.GmtTime, f"Trade was partially closed on the price{candle_data.Close}.\nAction triggered by checker: {triggered_checker}.\nClosed by: {part_amount_perctage}%.\nRemaining position part: {self.active_part}%.")
      if triggered_checker:
        self.triggered_checkers.append(triggered_checker)
      return False
  
  def __str__(self):
    return f'{self.trade_type} trade ({self.opening_gmt_time}) - ({self.closing_gmt_time})'
  
  def to_dict(self):
    return {
        **self.__dict__,
        "logs": self.logs.to_dict(orient="records"),  # Convert DataFrame to list of dicts
    }
  
if __name__ == "__main__":
  # reading our data
  data = pd.read_csv("data.csv")
  
  checker = Checker(
    active_checkers={
      "when_trade_is_opened" : {
        "global": [
          "end_time_checker"
        ],
        "to_close_sell": [
          "updating_sell_stop_loss_checker",
          "to_close_sell_trade_1_checker",
          "to_close_sell_trade_2_checker",
          "to_close_sell_trade_3_checker"
        ],
        "to_close_buy": [
          "updating_buy_stop_loss_checker",
          "to_close_buy_trade_1_checker",
          "to_close_buy_trade_2_checker",
          "to_close_buy_trade_3_checker"
        ]
      },
      "when_trade_is_not_opened" : {
        "global": [
        "start_time_checker",
        "no_more_trades_time_checker",
        ],
        # if checker returns "SKIP", program skips all "to_open_sell" checkers and goes to "to_open_buy" checkers
        "to_open_sell": [
          "if_sell_was_executed_once_this_day",
          "to_sell_order_1_checker",
        ],
        "to_open_buy": [
        "if_buy_was_executed_once_this_day",
        "to_buy_order_1_checker",
        ]
      }
    },
    data=data,
    params={"start_time": "06:00", "end_time": "23:00", "no_more_trades_time": "21:30"}
  )

  program = BacktestingPorgram(historical_data=data, checker=checker)
  program.start()

  with open(settings.LOGS_FILE_PATH, 'w') as fp:
    program.checker_logger.to_csv(fp)

# Commands that can be told to the program from the checker:
# 1. SELL n% - % of the balance, how much we want to risk
# 2. BUY n% - % of the balance, how much we want to risk
# 3. CLOSE n% - % what part of the position we want to close
# 4. SKIP - tells to the program to stop
# 5. None
