from typing import  Optional, Dict
import pandas as pd
from src.service import Service
from src.checker import Checker
import json
from config import settings
from src.trade import Trade


class BacktestingPorgram:
  def __init__(
      self, 
      historical_data: pd.DataFrame,
      checker: Checker,
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
      self.checker_log(candle_data.Time, action, triggered_checker_name)

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

  def on_start_program(self):
    with open(settings.EXECUTED_TRADES_FILE_PATH, "w") as fp:
      json.dump([], fp)


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

  def calculate_be_quantity(self):
    quantity_of_be_trades = 0
    for trade in self.executed_trades.values():
      if trade.result == "BE":
        quantity_of_be_trades += 1
    return quantity_of_be_trades

  def calculate_win_quanity(self):
    quantity_of_win_trades = 0
    for trade in self.executed_trades.values():
      if trade.result == "WIN":
        quantity_of_win_trades += 1
    return quantity_of_win_trades

  
  def print_executed_trades(self):
    for key, value in self.executed_trades.items():
      print(f'ID: {key} | {str(value)}')
