import pandas as pd
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '')))
from src.service import Service
from datetime import timezone, timedelta, datetime
import json

if __name__ == "__main__":
  service = Service()
  # cndls_size = 30
  # df = service.take_polygon_gold_historical_data(
  #   from_="2025-01-01",
  #   to="2025-03-01",
  #   limit=500000000,
  #   candle_size=cndls_size,
  #   tz=timezone.utc
  # )

  # with open(f"backtesting/data/data_{cndls_size}min_candles.csv", 'w') as fp:
  #   df.to_csv(fp)
  with open('backtesting/patterns/dates.json', 'r') as fp:
    dates = json.load(fp)

  cndls_size = 0
  while cndls_size <= 330:
    cndls_size += 1
    data_file_path = f'backtesting/data/data_{cndls_size}min_candles.csv'

    if not os.path.isfile(data_file_path):
      continue

    with open (data_file_path, 'r') as fp:
      df = pd.read_csv(fp, parse_dates=["Time"])

    
    
    for entry_model_name, values in dates.items():
      for variant_number, dates_dict in values.items():
        dt_start_str = dates_dict["start"]
        dt_end_str = dates_dict["end"]

        dt_start = datetime.strptime(dt_start_str, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        dt_end = datetime.strptime(dt_end_str, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)

        
        filtered_df = service.filter_df_by_datetime(df, dt_start, dt_end)
        if not filtered_df.empty:
          combo = service.build_relative_candles_combo([candle_data for candle_data in filtered_df.itertuples()])
          combo_name = entry_model_name
          combo_variant = variant_number
          directory_path = f'backtesting/patterns/{combo_name}/{combo_variant}'
          os.makedirs(directory_path, exist_ok=True)
          with open(f'{directory_path}/{len(combo)}candles.json', "w") as fp:
            json.dump(combo, fp)


    # dt_start = datetime(year=2025, month=2, day=21, hour=1, minute=15,  tzinfo=timezone.utc)
    # dt_end = datetime(year=2025, month=2, day=21, hour=18, minute=45, tzinfo=timezone.utc)

    # df = service.filter_df_by_datetime(df, dt_start, dt_end)
    
    # # create a combo from this df
    # combo = service.build_relative_candles_combo([candle_data for candle_data in df.itertuples()])
    # combo_name = 'trend_reversal_1_bullish'
    # combo_variant = 2
    # directory_path = f'backtesting/patterns/{combo_name}/{combo_variant}'
    # os.makedirs(directory_path, exist_ok=True)
    # with open(f'{directory_path}/{len(combo)}candles.json', "w") as fp:
    #   json.dump(combo, fp)

    print("Success!")


  