from typing import List, Tuple, Optional, Dict
from datetime import datetime, timezone, timedelta, time
from src.service import Service
from config import settings
import json

class VariableRequired(Exception):
  def __init__(self, message):
    super().__init__(message)

class Checker:
  def __init__(self, active_checkers:Dict[str, List[str]], data, params: dict, tz_offset:int):
    self.CHECKERS = {
      "start_time_checker": self.start_time_checker,
      "end_time_checker": self.end_time_checker,
      "no_more_trades_time_checker": self.no_more_trades_time_checker,
      "to_sell_order_1_checker": self.to_sell_order_1_checker,
      "to_buy_order_1_checker": self.to_buy_order_1_checker,
      "if_sell_was_executed_once_this_day": self.if_sell_was_executed_once_this_day,
      "if_buy_was_executed_once_this_day" : self.if_buy_was_executed_once_this_day,
      "updating_sell_stop_loss_checker": self.updating_sell_stop_loss_checker,
      "updating_buy_stop_loss_checker": self.updating_buy_stop_loss_checker,
      "to_close_sell_trade_1_checker": self.to_close_sell_trade_1_checker,
      "to_close_buy_trade_1_checker": self.to_close_buy_trade_1_checker,
      "to_close_sell_trade_2_checker": self.to_close_sell_trade_2_checker,
      "to_close_buy_trade_2_checker": self.to_close_buy_trade_2_checker,
      "to_close_sell_trade_3_checker": self.to_close_sell_trade_3_checker,
      "to_close_buy_trade_3_checker": self.to_close_buy_trade_3_checker,
      # sniping checkers
      "is_new_york_session_checker": self.is_new_york_session_checker,
    }
    self.REQUIRED_PARAMS = {
      "start_time_checker": ["start_time",],
      "end_time_checker": ["end_time", ],
      "no_more_trades_time_checker" : ["no_more_trades_time",],
      "is_new_york_session_checker": ["new_york_session_start_time", "new_york_session_end_time"] # format: "HH:MM"
    }
    self.data = data
    self.params = params
    self.active_checkers = active_checkers
    self.opened_trade = None
    self.timezone = timezone(timedelta(hours=tz_offset)) 
    self.service = Service()

    # check if required params for checkers are passed. if not, raise ParamsRequired custom error
    try:
      for active_checker in self.active_checkers:
        if self.REQUIRED_PARAMS.get(active_checker, None) is None:
          continue
        required_params = self.REQUIRED_PARAMS[active_checker]
        for param in required_params:
          if not param in self.params.keys():
            raise VariableRequired(f"Parameter {param} is required for checker {active_checker}.")
    except VariableRequired as e:
      print(f"Error: {e}")

  # TODO test
  def check(self, candle_data, trade_is_opened:bool, opened_trade_type:Optional[str]=None) -> Tuple[Optional[str], Optional[str]]: # returns an action to take (or None) and name of the triggered checker (or None)
    """
      Serves as a router to checkers. 
      1. Looks on the variable "trade_is_opened" and take list of available checkers for one of two scenarious (when_trade_is_opened, when_trade_is_not_opened).
      2. Iterates through the list of active checkers and check candle data with each checker.
      3. The first triggered checker will break an iteration.
      4. If checker was triggered, function returns Tuple[action:str, checker_name:str].
      5. If checker wasn't triggered, function returns Tuple[None, None].
    """
    
    if trade_is_opened == True:
      # check global checkers
      for checker_name in self.active_checkers["when_trade_is_opened"]["global"]:
        action = self.CHECKERS[checker_name](candle_data)
        if action is not None:
          return action, checker_name
      
    # check specified checkers based on type of opened
    if trade_is_opened and opened_trade_type.startswith("SELL"):
      for checker_name in self.active_checkers["when_trade_is_opened"]["to_close_sell"]:
        action = self.CHECKERS[checker_name](candle_data)
        if action is not None:
          return action, checker_name
        
    elif trade_is_opened and opened_trade_type.startswith("BUY"):
      for checker_name in self.active_checkers["when_trade_is_opened"]["to_close_buy"]:
        action = self.CHECKERS[checker_name](candle_data)
        if action is not None:
          return action, checker_name

    elif trade_is_opened == False:
      # check global checkers
      for checker_name in self.active_checkers["when_trade_is_not_opened"]["global"]: 
        action = self.CHECKERS[checker_name](candle_data)
        if action is not None:
          return action, checker_name
      
      # check to_open_sell
      for checker_name in self.active_checkers["when_trade_is_not_opened"]["to_open_sell"]:
        action = self.CHECKERS[checker_name](candle_data)
        if action is not None:
          # skips all sell checkers to go to buy checkers
          if action == "SKIP":
            break
          return action, checker_name

      for checker_name in self.active_checkers["when_trade_is_not_opened"]["to_open_buy"]: 
        action = self.CHECKERS[checker_name](candle_data)
        if action is not None:
          return action, checker_name

    return None, None
  
  # TODO test
  def start_time_checker(self, candle_data) -> Optional[str]:
    """
      Purpose: 
        To prevent executing any trade before start time
      Description:
        Returns "SKIP" if candle_time < start_time(specified in params).
        Returns None otherwise.
      Note:
        "SKIP" action means, that no more checkers should be checked for this candle.
        None tells to the program to execute the next available checker.
    """
    start_time = datetime.strptime(self.params["start_time"], "%H:%M").time()
    candle_time = datetime.strptime(str(candle_data.Time).split(" ")[1][:5], "%H:%M").time()
    if candle_time < start_time:
      return "SKIP"
    return None
    
  def end_time_checker(self, candle_data) -> Optional[str]:
    """
      Purpose: 
        To tell the program to CLOSE opened trade, if candle_time >= end_time (time when we should close all opened trades)
      Description:
        Returns "CLOSE" action if time variable of candle >= than time when we shouldn't open any trade (specified in Checker config)
        Returns "None" if not triggered. That means for a program that next checkers in the available list should be executed.
        "CLOSE" action means that program should close the trade.
    """
    end_time = datetime.strptime(self.params["end_time"], "%H:%M").time()
    candle_time = datetime.strptime(str(candle_data.Time).split(" ")[1][:5], "%H:%M").time()
    if candle_time >= end_time:
      return "CLOSE 100%"
    return None
  
  def no_more_trades_time_checker(self, candle_data) -> Optional[str]:
    """
      Purpose:
        To prevent opening new trades on current candle after no more trades time.
      Desctiption: 
        Check if candle time is >= than no_more_trades_time (specified in checker config). If so, returns "SKIP" action.
        "SKIP" action means, that no more checkers should be checked for this candle.
        Returns None if checker wasn't triggered ( in this case, if candle_time < no_more_trades_time).
        None tells to the program to go through the next available checker.

    """
    candle_time = datetime.strptime(str(candle_data.Time).split(" ")[1][:5], "%H:%M").time()
    no_more_trades_time = datetime.strptime(self.params["no_more_trades_time"], "%H:%M").time()
    if candle_time >= no_more_trades_time:
      return "SKIP"
    return None

  # TODO test 
  def to_sell_order_1_checker(self, candle_data):
    """
      Purpose:
        To check candle's conditions to open sell trade. (candle_data.High >= sell_price)
      Desctiption: 
        1. Uses custom functions from the service.Service object to find required variables (pdLSH, adL) for the step 3.
        2. If required variables for step 3 weren't found (in case of data missing), returns None.
        3. Calculates sell price using custom function from the service.Service object.
        4. Returns "SELL" action, if candle_data.High >= sell_price.
        5. Returns None, if candle_data.High < sell_price.
      Notes:
        None tells to the program to move to the next checker.
        "SELL" tells to the program to execute sell trade.
    """
    service = Service()
    pdLSH = service.find_pdLSH(candle_data, self.data) # previous day london session's low
    adL = service.find_adL(candle_data, self.data) # actual day low

    if pdLSH is None or adL is None:
      return None
    
    sell_price = service.calculate_sell_price(pdLSH, adL)
    if candle_data.High >= sell_price:
      return "SELL 1%"
    return None

  # TODO test
  def to_buy_order_1_checker(self, candle_data):
    """
      Purpose:
        To check candle's conditions to open sell trade. (candle_data.Low <= buy_price)
      Desctiption: 
        1. Uses custom functions from the service.Service object to find required variables (pdLSl, adH) for the step 3.
        2. If required variables for step 3 weren't found (in case of data missing), returns None.
        3. Calculates buy price using custom function from the service.Service object.
        4. Returns "BUY" action, if candle_data.Low <= buy_price.
        5. Returns None, if candle_data.Low > buy_price.
      Notes:
        None tells to the program to move to the next checker.
        "BUY" tells to the program to execute buy trade.
    """
    service = Service()
    adH = service.find_adH(candle_data, self.data)
    pdLSL = service.find_pdLSL(candle_data, self.data)

    if pdLSL is None or adH is None:
      return None
    
    buy_price = service.calculate_buy_price(pdLSL, adH)
    if candle_data.Low <= buy_price:
      return "BUY 1%"
    return None

  def if_sell_was_executed_once_this_day(self, candle_data):
    with open(settings.EXECUTED_TRADES_FILE_PATH, "r") as fp:
      executed_trades = json.load(fp)

    service = Service()
    candle_data_date = service.get_datetime_from_iso_string(str(candle_data.Time)).date()
    for trade in executed_trades:
      if trade["trade_type"].startswith("SELL"):
        executed_trade_date = service.get_datetime_from_iso_string(trade["opening_time"]).date()
        if candle_data_date == executed_trade_date:
          return "SKIP"
      
    return None
  
  def if_buy_was_executed_once_this_day(self, candle_data):
    with open(settings.EXECUTED_TRADES_FILE_PATH, "r") as fp:
      executed_trades = json.load(fp)
    
    service = Service()
    candle_data_date = service.get_datetime_from_iso_string(str(candle_data.Time)).date()
    for trade in executed_trades:
      if trade["trade_type"].startswith("BUY"):
        executed_trade_date = service.get_datetime_from_iso_string(trade["opening_time"]).date()
        if candle_data_date == executed_trade_date:
          return "SKIP"
        
    return None
  
  def updating_sell_stop_loss_checker(self, candle_data):
    service = Service()
    pdLSH = service.find_pdLSH(candle_data, self.data)
    adL = service.find_adL(candle_data, self.data)
    if pdLSH is None or adL is None:
      return None
    
    stop_loss_is_sell_price = True if "updating_sell_stop_loss_checker" in self.opened_trade.triggered_checkers else False
    
    if not stop_loss_is_sell_price and candle_data.Low <= service.calculate_half_fib_sell(pdLSH, adL):
      trade_opening_candle_data = service.take_candle_data_by_iso(self.opened_trade.opening_time, self.data)
      op_pdLSH = service.find_pdLSH(trade_opening_candle_data, self.data)
      op_adL = service.find_adL(trade_opening_candle_data, self.data)
      trade_sell_price_on_opening = service.calculate_sell_price(op_pdLSH, op_adL)
      self.opened_trade.update_stop_loss(candle_data=candle_data, new_stop_loss=trade_sell_price_on_opening, triggered_checker="updating_sell_stop_loss_checker")
    return None
  
  def updating_buy_stop_loss_checker(self, candle_data):
    service = Service()
    pdLSL = service.find_pdLSL(candle_data, self.data)
    adH = service.find_adH(candle_data, self.data)
    if pdLSL is None or adH is None:
      return None
    
    stop_loss_is_buy_price = True if "updating_buy_stop_loss_checker" in self.opened_trade.triggered_checkers else False
    if not stop_loss_is_buy_price and candle_data.High >= service.calculate_half_fib_buy(pdLSL, adH):
      trade_opening_candle_data = service.take_candle_data_by_iso(self.opened_trade.opening_time, self.data)
      op_pdLSL = service.find_pdLSL(trade_opening_candle_data, self.data)
      op_adH = service.find_adH(trade_opening_candle_data, self.data)
      trade_buy_price_on_opening = service.calculate_buy_price(op_pdLSL, op_adH)
      self.opened_trade.update_stop_loss(candle_data=candle_data, new_stop_loss=trade_buy_price_on_opening, triggered_checker="updating_buy_stop_loss_checker")
    return None
  
  def to_close_sell_trade_1_checker(self, candle_data):
    stop_loss_is_sell_price = True if "updating_sell_stop_loss_checker" in self.opened_trade.triggered_checkers else False
    if candle_data.High >= self.opened_trade.stop_loss and stop_loss_is_sell_price == True:
      return "CLOSE 100%"

  def to_close_buy_trade_1_checker(self, candle_data):
    stop_loss_is_buy_price = True if "updating_buy_stop_loss_checker" in self.opened_trade.triggered_checkers else False
    if candle_data.High >= self.opened_trade.stop_loss and stop_loss_is_buy_price == True:
      return "CLOSE 100%"
    
  def to_close_sell_trade_2_checker(self, candle_data):
    service = Service()
    stop_loss = self.opened_trade.stop_loss
    stop_loss_is_sell_price = True if "updating_sell_stop_loss_checker" in self.opened_trade.triggered_checkers else False
    adL = service.find_adL(candle_data, self.data)
    pdLSH = service.find_pdLSH(candle_data, self.data)
    sell_price = service.calculate_sell_price(pdLSH, adL)
    if pdLSH is None or adL is None:
      return None

    if candle_data.High >= stop_loss and stop_loss_is_sell_price == False and stop_loss > sell_price:
      return "CLOSE 100%"
    return None
  
  def to_close_buy_trade_2_checker(self, candle_data):
    service = Service()
    stop_loss = self.opened_trade.stop_loss
    stop_loss_is_buy_price = True if "updating_buy_stop_loss_checker" in self.opened_trade.triggered_checkers else False
    adH = service.find_adH(candle_data, self.data)
    pdLSL = service.find_pdLSL(candle_data, self.data)
    if pdLSL is None or adH is None:
      return None
    buy_price = service.calculate_buy_price(pdLSL, adH)

    if candle_data.Low <= stop_loss and stop_loss_is_buy_price == False and stop_loss < buy_price:
      return "CLOSE 100%"
    return None
  
  def to_close_sell_trade_3_checker(self, candle_data):
    if candle_data.Low <= self.opened_trade.take_profit:
      return "CLOSE 100%"
    
  def to_close_buy_trade_3_checker(self, candle_data):
    if candle_data.High >= self.opened_trade.take_profit:
      return "CLOSE 100%"


  """
  -------------------------------------------------------------------------------------------------------------------------------------------------------------
    Sniping strategy checkers
  """
 
  def is_new_york_session_checker(self, candle_data):
    """
      -surname:
        "sniping_checker_0"
      -purpose:
        Check if observed candle is in new york session
    """
    candle_sessions_list = self.service.take_candle_sessions(candle_data.Time)

    if "New York" in candle_sessions_list:
      return None
    else:
      return "SKIP"
    
  
  def sniping_strategy_entry_checker(self, candle_data):
    # Check previous 3 days data availability
    dt_end = candle_data.Time
    dt_start = dt_end - timedelta(days=3)
    last_3_days_df = self.service.filter_df_by_datetime(self.data, dt_start, dt_end)
    if not last_3_days_df:
      return None
    
    # Take last 1 day df
    dt_end = candle_data.Time
    dt_start = dt_end - timedelta(days=1)
    last_1_day_df = self.service.filter_df_by_datetime(self.data, dt_start, dt_end)
    
    # Check if price in some entry model
    entry_model_tuple = self.service.detect_price_entry_model(last_1_day_df)
    if not entry_model_tuple:
      return None
    entry_model_name, entry_model_df = entry_model_tuple
    
    # Check if price in a good entering position of an entry model
    if not self.service.price_in_good_entry_position_of_the_model(candle_data, entry_model_name, entry_model_df):
      return None
    
    # Take consolidation within entry model df
    consolidation_df = self.service.find_consolidation(entry_model_df)
    if not consolidation_df:
      return None
    
    # Take entry model's swing cndl ( to trace fib)
    swing_cndl = self.service.find_entry_model_swing_candle(entry_model_df)
    if not swing_cndl:
      return None
    
    # Identify last 3 days market structure
    last_3days_market_structure:str = self.service.identify_market_structure(last_3_days_df)

    # Identify entry model structure
    consolidation_low, consolidation_high = consolidation_df.min(consolidation_df["Low"]), consolidation_df.max(consolidation_df["High"])
    model_structure = "bullish" if consolidation_high < swing_cndl.High else "bearish"

    # Check if entry model market structure alligns with last 3 days market structure
    if not last_3days_market_structure != model_structure:
      return None
    
    # Calculate 0.764fib level price
    if model_structure == "bullish":
      fib_level_price = self.service.calculate_fibonacci_level(fib=0.764, from_=consolidation_low, to=swing_cndl.High)
    elif model_structure == "bearish":
      fib_level_price = self.service.calculate_fibonacci_level(fib=0.764, from_=consolidation_high, to=swing_cndl.Low)
    
    # Check if fib level is in a consolidation zone
    if not consolidation_low <= fib_level_price <= consolidation_high:
      return None
    
    # Identify premium area dataframe
    premium_area_df = self.service.find_premium_area_df(consolidation_df, fib_level_price, model_structure)

    # Find supply & demand in a premium area
    supply_demand_df = self.service.find_supply_demand(premium_area_df)
    if not supply_demand_df:
      return None
    
    # Find internal & external liquidities
    internal_liquidity = self.service.find_liquidity(consolidation_df)
    external_liquidity = self.service.find_liquidity(entry_model_df)
    if not internal_liquidity or not external_liquidity:
      return None
    
    # Check if last day p.o.c in a consolidation zone
    poc_level = self.service.calculate_poc_level(last_1_day_df)
    if not consolidation_low <= poc_level <= consolidation_high:
      return None
    
    # Find imbalance in a consolidation zone
    imbalance = self.service.find_imbalance(consolidation_df)
    if not imbalance:
      return None
    
    # TODO checked something with session liquidity 

    # Set entry price
    entry_price = fib_level_price

    # Set stop loss
    stop_loss = consolidation_low if model_structure == "bullish" else consolidation_high

    # Set target 
    target = swing_cndl.High if model_structure == "bullish" else swing_cndl.Low

    # Set order type
    order_type = "BUY" if model_structure == "bullish" else "SELL"

    # Execute an order
    return f"{order_type} 1%; ENTER_ON {entry_price}; STOP_LOSS {stop_loss}; TARGET {target}"

  """
  -------------------------------------------------------------------------------------------------------------------------------------------------------------
  """


  

