from src.checker import Checker
from src.backtesting_program import BacktestingPorgram
import pandas as pd

if __name__ == "__main__":
  # reading our data
  data = pd.read_csv("backtesting/data.csv")
  
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

  # Printing useful info (optional)
  program.print_executed_trades()
  print(program.summary)

# Commands that can be told to the program from the checker:
# 1. SELL n% - % of the balance, how much we want to risk
# 2. BUY n% - % of the balance, how much we want to risk
# 3. CLOSE n% - % what part of the position we want to close
# 4. SKIP - tells to the program to stop
# 5. None
