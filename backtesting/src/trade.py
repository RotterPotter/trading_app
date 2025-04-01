from typing import Optional
import pandas as pd

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
    self.opening_time = candle_data.Time
    self.closing_time = None
    self.trade_type = trade_type
    self.entering_price = candle_data.Close
    self.closing_price = None

    self.position_in_percantage:float = position_in_percantage
    self.active_part = 100
    self.result = None
    self.pl = None
    self.logs = pd.DataFrame([], columns=["Time", "Log"])
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
    self.log(self.opening_time, f"Trade {self.trade_type} was opened on the price {self.entering_price}.\nAction triggered by checker: {self.triggered_opening_checker}.\nStop loss:{self.stop_loss}\nTake profit:{self.take_profit}")

  def log(self, time:str, message:str):
    new_data = pd.DataFrame([[time, message]], columns=["Time", "Log"])
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


    self.closing_time = candle_data.Time
    self.active_part = 0
    self.log(candle_data.Time, f"Trade {self.trade_type} was closed on the price {candle_data.Close}.\nAction triggered by checker: {triggered_checker}.\nResult: {self.result}\nP/L: {self.pl}%.")
    if triggered_checker:
      self.triggered_checkers.append(triggered_checker)

  def update_stop_loss(self, candle_data, new_stop_loss:float, triggered_checker):
    self.stop_loss = new_stop_loss
    self.log(candle_data.Time, f"Stop loss was updated by {triggered_checker}.\nNew stop loss:{new_stop_loss}")
    if triggered_checker:
      self.triggered_checkers.append(triggered_checker)

  def close_part(self, candle_data, part_amount_perctage:float, triggered_checker: Optional[str] = None) -> bool:
    if (self.active_part - part_amount_perctage) < 0:
      self.active_part = 0
      self.log(candle_data.Time, f"Trade was partially closed on the price{candle_data.Close}.\nAction triggered by checker: {triggered_checker}.\nClosed by: {part_amount_perctage}%.\nRemaining position part: {self.active_part}%.\nInitializing closing trade process...")
      if triggered_checker:
        self.triggered_checkers.append(triggered_checker)
      self.close(candle_data=candle_data)
      return True
    else:
      self.active_part -= part_amount_perctage
      self.log(candle_data.Time, f"Trade was partially closed on the price{candle_data.Close}.\nAction triggered by checker: {triggered_checker}.\nClosed by: {part_amount_perctage}%.\nRemaining position part: {self.active_part}%.")
      if triggered_checker:
        self.triggered_checkers.append(triggered_checker)
      return False
  
  def __str__(self):
    return f'{self.trade_type} trade ({self.opening_time}) - ({self.closing_time})'
  
  def to_dict(self):
    return {
        **self.__dict__,
        "logs": self.logs.to_dict(orient="records"),  # Convert DataFrame to list of dicts
    }