import pandas as pd
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '')))
from src.service import Service
from datetime import timezone, timedelta

if __name__ == "__main__":
  service = Service()
  cndl_size = 5
  data = service.take_polygon_gold_historical_data(
    from_="2025-01-01",
    to="2025-03-01",
    limit=50000,
    candle_size=cndl_size,
    tz=timezone.utc
  )

  with open(f"backtesting/tests/testing_data_{cndl_size}.csv", "w") as fp:
    data.to_csv(fp)


  print("Success!")
  # print(sys.path)