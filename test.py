"""
  RUN 

  1. Execute checker to check conditions for the opening of the buy trade.
    - Check 70% of fibonacci # 1
    - 

When our program decides to open a trade (buy/sell), one of the next steps is set to stop loss.
Can we change a value of stop loss. Example:
If we are openin a buy trade at the price level of 200$, our stop loss will be 2.5$ lower (197.5$).

1. 

candle 21
"when_trade_is_opened" : {
      "global": [
        ....
      ],
      "to_close_sell": [
        1. To check if time after 23.00. None
        2 TO check if time after 20:00 None
        3 Checker3 None
        4 Checker. Set stop loss of the opened trade to 200$ + 2.5$ None. "SKIP" our candle number :20
        5 Checker. If the weather is good. "CLOSE 20%"
        6 Checker. Takes parameters of the actual opened trade. And If opened part of the trade is == 80% check some logic. if not None
        ...
        ..
        ...
      ],
      "to_close_buy": [
        Checker. (None) Set stop loss of the opened trade to 200$ - 2.5$
        ...
      ]
    },
"when_trade_is_not_opened" : {
        ...
      ],
      "to_open_sell": [
       ...
      ],
      "to_open_buy": [
        ...
        7. Checks the condition to open buy trade. If price == 200$ - "BUY 1%"
        ...
      ]
    }
"""