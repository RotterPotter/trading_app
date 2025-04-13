import pandas as pd
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '')))
from src.service import Service

if __name__ == "__main__":
  service = Service()
  data = service.take_polygon_gold_historical_data(
    from_="2025-01-01",
    to="2025-03-01",
    limit=50000,
    candle_size=15,
    tz_convert='America/New_York'
  )

  with open("backtesting/tests/testing_data.csv", "w") as fp:
    data.to_csv(fp)

  print("Success!")
  # print(sys.path)