
from polygon import RESTClient
import pandas as pd
import datetime
from config import settings
from typing import Union, Optional, Dict
from datetime import date, datetime, timedelta, timezone
from typing import List
import decimal


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

    def identify_market_structure(self, data: pd.DataFrame, min_swing_diff=0.1, recent_swing_limit=20, range_threshold=0.02):
        """
        Identifies the market structure (bullish, bearish, or ranging) based on price action.

        Improvements added:
        - Ignores swing highs/lows that are too close in price (to reduce noise)
        - Considers only the last N swings (to focus on recent structure)
        - Detects ranging market if overall price movement is compressed within a small range

        Parameters:
            data (pd.DataFrame): OHLCV dataframe with ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
            min_swing_diff (float): Minimum price difference between swings (to ignore small fluctuations)
            recent_swing_limit (int): How many recent swings to use for structure analysis
            range_threshold (float): % threshold of High-Low range relative to average price for "ranging" detection

        Returns:
            dict: {
                'structure': str,  # 'bullish', 'bearish', or 'ranging'
                'swings': List[Tuple[str, float, Any]],
                'trend_sequence': List[str]
            }
        """
        swings = []
        data = data.sort_values("Time").reset_index(drop=True)

        highs = data["High"].values
        lows = data["Low"].values
        times = data["Time"].values

        # Detect swing highs and lows
        for i in range(1, len(data) - 1):
            prev = data.iloc[i - 1]
            curr = data.iloc[i]
            next = data.iloc[i + 1]

            # Swing High
            if curr.High > prev.High and curr.High > next.High:
                if not swings or abs(curr.High - swings[-1][1]) > min_swing_diff:
                    swings.append(("SH", curr.High, curr.Time))

            # Swing Low
            elif curr.Low < prev.Low and curr.Low < next.Low:
                if not swings or abs(curr.Low - swings[-1][1]) > min_swing_diff:
                    swings.append(("SL", curr.Low, curr.Time))

        # Use only the last N swings
        swings = swings[-recent_swing_limit:]

        structure = None
        trend = []

        for i in range(1, len(swings)):
            prev_type, prev_price, _ = swings[i - 1]
            curr_type, curr_price, _ = swings[i]

            if prev_type == "SH" and curr_type == "SH":
                if curr_price > prev_price:
                    trend.append("HH")
                elif curr_price < prev_price:
                    trend.append("LH")
            elif prev_type == "SL" and curr_type == "SL":
                if curr_price > prev_price:
                    trend.append("HL")
                elif curr_price < prev_price:
                    trend.append("LL")

        hh = trend.count("HH")
        hl = trend.count("HL")
        lh = trend.count("LH")
        ll = trend.count("LL")

        # Check if price is within a tight range -> ranging
        max_price = data["High"].max()
        min_price = data["Low"].min()
        avg_price = data["Close"].mean()
        # Only say it's ranging if there's no clear trend AND it's within a tight range
        if (hh + hl == 0 and ll + lh == 0) and (max_price - min_price) / avg_price < range_threshold:
            structure = "ranging"
        elif hh >= 1 and hl >= 1 and hh + hl > lh + ll:
            structure = "bullish"
        elif ll >= 1 and lh >= 1 and ll + lh > hh + hl:
            structure = "bearish"
        else:
            structure = "ranging"

        return {
            "structure": structure,
            "swings": swings,
            "trend_sequence": trend
        }
    
    """
    -----------------------------------------------
        Sniping checker's functions
    """

    def detect_price_entry_model(self, df:pd.DataFrame) -> Optional[tuple]: # (entry_model_name, entry_model_df)
        """
        How to detect price entry model within a dataframe?
        FIrst of all, we should to create relative patterns for the shapes
        # 1. Trend continuation bullish ( only works if general market structure is bullish)
            [-50%, +97%, -110%, +200%, -40%, +80%, -200%, +300%]

        Let's try to find all mathes with this entry model in a given dataframe on 15min/candle time frame
        """
        candle_datas = [candle_data for candle_data in df.itertuples()]
        trend_continuation = []
        df_price_relations = []
        for i, candle_data in enumerate(candle_datas):
            if i > 1: # skip first two candles
                continue
            
            if candle_data.Close > candle_datas[i - 1].Close:
                # take difference for bullish ( from cndl2.High to cndl1.Low )
                price_difference = candle_data.High - candle_datas[i-1].Low
                pass
            else:
                pass
                # take difference for bearish ( from cndl1.High to cndl2.Low)
            

    def relatively_describe_candle(self, cndl_data) -> List[float]:
        decimal.getcontext().prec = 100

        cndl_close = decimal.Decimal(cndl_data.Close)
        cndl_open = decimal.Decimal(cndl_data.Open)
        cndl_high = decimal.Decimal(cndl_data.High)
        cndl_low = decimal.Decimal(cndl_data.Low)
        
        a = cndl_close - cndl_open 
        b = cndl_high - cndl_open 
        c = cndl_low - cndl_open 
        
        a = a if a != decimal.Decimal(0) else decimal.Decimal(0.0000001)
        b = b if b != decimal.Decimal(0) else decimal.Decimal(0.0000001)
        c = c if c != decimal.Decimal(0) else decimal.Decimal(0.0000001)
        
        return [float(round(a / b, 2)), float(round(a / c, 2)), float(round(b / c, 2))]

    def build_relative_candles_combo(self, candles_datas_list: list) -> List[List[float]]:
        return [self.relatively_describe_candle(candle_data) for candle_data in candles_datas_list]
    

    def compare_relative_candles_combos(self, combo1: List[List[float]], combo2: List[List[float]], threshold: float):
        if not len(combo1) == len(combo2):
            return False
        
        for i, described_candle in enumerate(combo1):
            for j, relative_change in enumerate(described_candle):
                if not (relative_change - threshold) <= combo2[i][j] <= (relative_change + threshold):
                    return False
        return True
    
    def find_combos_in_candles_datas_list(self, combo: List[List[float]], candles_datas_list: list, threshold: float) -> List[pd.DataFrame]:
        to_return = []
        for i in range(len(candles_datas_list)):
            slice_start_indx = i
            slice_end_indx = slice_start_indx + len(combo)

            if slice_end_indx >= len(candles_datas_list):
                break

            combo_to_compare = self.build_relative_candles_combo(candles_datas_list[slice_start_indx: slice_end_indx])
            if self.compare_relative_candles_combos(combo, combo_to_compare, threshold):
                found_combo_start_datetime = candles_datas_list[slice_start_indx].Time
                found_combo_end_datetime = candles_datas_list[slice_end_indx].Time
                to_return.append([found_combo_start_datetime, found_combo_end_datetime])
        
        return to_return

    def find_consolidation(self, df: pd.DataFrame) -> Optional[pd.DataFrame]: # dataframe of the consolidation zone
        pass

    def find_entry_model_swing_candle(self, entry_model_df: pd.DataFrame) -> Optional[pd.DataFrame]:
        pass

    def calculate_fibonacci_level(self, fib:float, from_:float, to:float) -> float: # return level price
        pass

    def find_premium_area_df(self, consolidation_df: pd.DataFrame, fib_level_price:float, model_structure:str) -> pd.DataFrame:
        pass

    def find_supply_demand(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        pass

    def find_liquidity(self, df:pd.DataFrame) -> Optional[pd.DataFrame]:
        pass


    def filter_df_by_datetime(self, df: pd.DataFrame, dt_start: datetime, dt_end: datetime) -> Optional[pd.DataFrame]:
        mask = (df['Time'] >= dt_start) & (df['Time'] <= dt_end)
        filtered_df = df.loc[mask]

        return filtered_df 


    def calculate_poc_level(self, df:pd.DataFrame) -> float:
        pass

    def find_imbalance_zone_in_df(self, df:pd.DataFrame) -> Optional[tuple]: # (zone start price, zone end price)
        pass

    def identify_market_structure(self, df:pd.DataFrame) -> str: # bullish/bearish/ranging
        pass


    """
    -----------------------------------------------
    """