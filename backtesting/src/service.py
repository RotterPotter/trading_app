
from polygon import RESTClient
import pandas as pd
import datetime
from config import settings
from typing import Union, Optional
from datetime import date, datetime, timedelta, timezone
from typing import List


class Service:
    def __init__(self):
        self.sessions_schedule_utc0 = {
            "Sydney": [-2, 7], # "-" means previous day
            "Tokyo": [0, 9],
            "London": [8, 17],
            "New York": [13, 22]
        }

    def take_polygon_gold_historical_data(
            self, 
            from_: Union[str, int, datetime, date],
            to: Union[str, int, datetime, date],
            candle_size: int,
            limit: Optional[int] = None,
            tz: timezone = timezone.utc
    ) -> pd.DataFrame:
        client = RESTClient(api_key=settings.POLYGON_API_KEY)
        aggs = []
        for a in client.list_aggs(ticker="C:XAUUSD", multiplier=candle_size, timespan="minute", from_=from_, to=to, limit=limit):
            data = {
                "Time": datetime.fromtimestamp(a.timestamp / 1000, tz=tz),
                "Open": a.open,
                "High": a.high,
                "Low": a.low,
                "Close": a.close,
                "Volume": a.volume
            }
            aggs.append(data)
        
        df = pd.DataFrame(aggs)
        
        # Convert 'Time' column to string with timezone using apply
        # df['Time'] = df['Time'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S%z'))
        
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
        
    def utc_offset_in_hours(self, tz):
        """
        Returns the difference in hours between UTC and the given timezone.
        
        Parameters:
            tz (timezone): A timezone object (from zoneinfo, pytz, etc.)
        
        Returns:
            float: UTC offset in hours
        """
        now_utc = datetime.now(timezone.utc)
        offset = tz.utcoffset(now_utc)
        return offset.total_seconds() / 3600
        
    def take_candle_sessions(self, candle_datetime:datetime) -> List[str]:
        candle_datetime_utc = candle_datetime.astimezone(timezone.utc)
        
        candle_sessions = []
        candle_hour = candle_datetime_utc.hour

        if candle_hour >= 22:
            candle_hour -= 24

        for session_name, session_schedule in self.sessions_schedule_utc0.items():
            session_start_hour = session_schedule[0]
            session_end_hour = session_schedule[1]
            if session_start_hour <= candle_hour < session_end_hour:
                candle_sessions.append(session_name)

        return candle_sessions
    
    def slice_data_from_session_start_to_candle(self, session_name: str, candle_datetime:datetime, data: pd.DataFrame, tz: timezone) -> pd.DataFrame:
        """
            1. Takes session start hour  in utc0.
            2. Converts session start in timezone of the program.
            3. Creates a datetime object with candle date and start session hour
            4. If this datetime object > then candle date object, dicrease it by 1 day
            5. Filters dataframe
        """
        session_start_hour_utc = self.sessions_schedule_utc0[session_name][0]
        if session_start_hour_utc < 0:
            session_start_hour_utc += 24

        tz_utc_offset = int(self.utc_offset_in_hours(tz))

        session_start_hour_converted = session_start_hour_utc + tz_utc_offset
        session_start_datetime = datetime(
            year=candle_datetime.year,
            month=candle_datetime.month,
            day=candle_datetime.day,
            hour=session_start_hour_converted,
            tzinfo=tz
        )

        if session_start_datetime > candle_datetime:
            session_start_datetime -= timedelta(days=1)
        
        return data[(data['Time'] >= session_start_datetime) & (data['Time'] <= candle_datetime)]
    
    def find_imbalance_zone(self, candle_1_data, candle_2_data, candle_3_data):
        # 1. Check if three candles market structure is bullish or bearish
        if candle_1_data.Close < candle_2_data.Close < candle_3_data.Close:
            # bullish
            # Check if 1st candle high is lower than 3rd candle low
            if candle_1_data.High <= candle_3_data.Low:
                # return gap between them (imbalance zone)
                return (candle_1_data.High, candle_3_data.Low) # (small, big)
        elif candle_1_data.Close > candle_2_data.Close > candle_3_data.Close:
            # bearish
            # Check if 1st candle low >= 3rd canlde high
            if candle_1_data.Low >= candle_3_data.High:
                return (candle_3_data.High, candle_1_data.Low) # (small, big)
        
        
