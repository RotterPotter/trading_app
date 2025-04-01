
from polygon import RESTClient
import pandas as pd
import datetime
from config import settings
from typing import Union, Optional
from datetime import date, datetime, timedelta


class Service:
    def take_polygon_gold_historical_data(
            self, 
            from_: Union[str, int, datetime, date],
            to: Union[str, int, datetime, date],
            candle_size: int,
            limit: Optional[int] = None,
            tz_convert: Optional[str] = None
    ) -> pd.DataFrame:
        client = RESTClient(api_key=settings.POLYGON_API_KEY)
        aggs = []
        for a in client.list_aggs(ticker="C:XAUUSD", multiplier=candle_size, timespan="minute", from_=from_, to=to, limit=limit):
            data = {
                "Time": pd.to_datetime(a.ti3mestamp, unit='ms', utc=True) if tz_convert is None else pd.to_datetime(a.timestamp, unit='ms', utc=True).tz_convert(tz_convert),
                "Open": a.open,
                "High": a.high,
                "Low": a.low,
                "Close": a.close,
                "Volume": a.volume
            }
            aggs.append(data)
        
        df = pd.DataFrame(aggs)
        
        # Convert 'Time' column to string with timezone using apply
        df['Time'] = df['Time'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S%z'))
        
        return df
    
    def calculate_sell_price(self, pdLSH: float, adL: float) -> float:
        return adL + ((pdLSH - adL) * 0.764)

    def calculate_buy_price(self, pdLSL: float, adH: float) -> float:
        return adH - ((adH - pdLSL) * 0.764)

    def calculate_rr(self, entry_point, stop_loss, profit_target, trade_type="BUY"):
        if trade_type.upper() == "BUY":
            # For BUY: risk is entry - stop_loss, reward is profit_target - entry.
            risk = entry_point - stop_loss
            reward = profit_target - entry_point
        elif trade_type.upper() == "SELL":
            # For SELL: risk is stop_loss - entry, reward is entry - profit_target.
            risk = stop_loss - entry_point
            reward = entry_point - profit_target
        k = reward / risk
        return f"1:{round(k, 2)}"

    def calculate_half_fib_sell(self, pdLSH: float, adL: float) -> float:
        return adL + ((pdLSH - adL) * 0.5)

    def calculate_half_fib_buy(self, pdLSL: float, adH: float) -> float:
        return adH - ((adH - pdLSL) * 0.5)
    
    def find_pdLSH(self, candle_data, data: pd.DataFrame) -> Optional[float]:
        """
            1. Takes candle date from candle_data.
            2. Filters data dataframe to include only series with previous day date.
            3. Returns None if previous date dataframe is empty.
            4. Returns Max value in "High" column of the previous date dataframe.
        """
        candle_date_datetime = self.get_datetime_from_iso_string(candle_data.Time)
        previous_day_date_datetime = candle_date_datetime - timedelta(days=1)
        previous_day_date_string = str(previous_day_date_datetime.date())
        filtered_df = data[data['Time'].str.startswith(previous_day_date_string)]

        if filtered_df.empty:
            return None
        
        return filtered_df["High"].max()

    def find_pdLSL(self, candle_data, data: pd.DataFrame) -> Optional[float]:
        """
            1. Takes candle date from candle_data.
            2. Filters data dataframe to include only series with previous day date.
            3. Returns None if previous date dataframe is empty.
            4. Returns Min value in "Low" column of the previous date dataframe.
        """
        candle_date_datetime = self.get_datetime_from_iso_string(candle_data.Time)
        previous_day_date_datetime = candle_date_datetime - timedelta(days=1)
        previous_day_date_string = str(previous_day_date_datetime.date())
        filtered_df = data[data['Time'].str.startswith(previous_day_date_string)]

        if filtered_df.empty:
            return None
        
        return filtered_df["Low"].min()
    
    def find_adH(self, candle_data, data: pd.DataFrame) -> Optional[float]:
        """
            1. Takes candle date from candle_data.
            2. Filters data dataframe to include only series with actual day date.
            3. Returns None if actual date dataframe is empty.
            4. Returns Max value in "High" column of the actual date dataframe.
        """
        candle_date_datetime = self.get_datetime_from_iso_string(candle_data.Time)
        candle_date_string = str(candle_date_datetime.date())
        filtered_df = data[data['Time'].str.startswith(candle_date_string)]

        if filtered_df.empty:
            return None
        
        return filtered_df["High"].max()

    def find_adL(self, candle_data, data: pd.DataFrame) -> Optional[float]:
        """
            1. Takes candle date from candle_data.
            2. Filters data dataframe to include only series with actual day date.
            3. Returns None if actual date dataframe is empty.
            4. Returns Min value in "Low" column of the actual date dataframe.
        """
        candle_date_datetime = self.get_datetime_from_iso_string(candle_data.Time)
        candle_date_string = str(candle_date_datetime.date())
        filtered_df = data[data['Time'].str.startswith(candle_date_string)]

        if filtered_df.empty:
            return None
        
        return filtered_df["Low"].min()
    
    def get_datetime_from_iso_string(self, iso_string:str) -> datetime:
        return datetime.strptime(iso_string.split(" ")[0], "%Y-%m-%d")
    
    def calculate_stop_loss(self, candle_data, trade_type:str, data) -> float:
        if trade_type.startswith("SELL"):
            return self.find_pdLSH(candle_data, data) 
        elif trade_type.startswith("BUY"):
            return self.find_pdLSL(candle_data, data)
    
    def calculate_take_profit(self, candle_data, trade_type:str, data) -> float:
        if trade_type.startswith("SELL"):
            return self.find_adL(candle_data, data)  
        elif trade_type.startswith("BUY"):
            return self.find_adH(candle_data, data)

    def take_candle_data_by_iso(self, iso_string:str, data):
        filtered_df = data[data['Time'].str.startswith(iso_string)]
        for el in filtered_df.itertuples():
            return el

