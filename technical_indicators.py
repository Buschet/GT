"""
Modulo per calcolare indicatori tecnici
Fornisce feature per l'analisi AI
"""

import pandas as pd
import numpy as np
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator, VolumeWeightedAveragePrice


class TechnicalIndicators:
    """
    Classe per calcolare indicatori tecnici su dati OHLCV
    """

    def __init__(self, df: pd.DataFrame):
        """
        Inizializza con un DataFrame OHLCV

        Args:
            df: DataFrame con colonne: open, high, low, close, volume
        """
        self.df = df.copy()

    def add_all_indicators(self) -> pd.DataFrame:
        """
        Aggiunge tutti gli indicatori tecnici al DataFrame

        Returns:
            DataFrame con tutti gli indicatori aggiunti
        """
        self.add_moving_averages()
        self.add_rsi()
        self.add_macd()
        self.add_bollinger_bands()
        self.add_stochastic()
        self.add_atr()
        self.add_obv()
        self.add_price_momentum()
        self.add_volume_indicators()

        return self.df

    def add_moving_averages(self, periods: list = [7, 14, 21, 50, 100, 200]):
        """
        Aggiunge medie mobili semplici ed esponenziali

        Args:
            periods: Lista di periodi per le medie mobili
        """
        for period in periods:
            # SMA
            sma = SMAIndicator(close=self.df['close'], window=period)
            self.df[f'sma_{period}'] = sma.sma_indicator()

            # EMA
            ema = EMAIndicator(close=self.df['close'], window=period)
            self.df[f'ema_{period}'] = ema.ema_indicator()

    def add_rsi(self, period: int = 14):
        """
        Aggiunge Relative Strength Index

        Args:
            period: Periodo per il calcolo RSI
        """
        rsi = RSIIndicator(close=self.df['close'], window=period)
        self.df['rsi'] = rsi.rsi()

    def add_macd(self, fast: int = 12, slow: int = 26, signal: int = 9):
        """
        Aggiunge MACD (Moving Average Convergence Divergence)

        Args:
            fast: Periodo EMA veloce
            slow: Periodo EMA lento
            signal: Periodo linea segnale
        """
        macd = MACD(
            close=self.df['close'],
            window_fast=fast,
            window_slow=slow,
            window_sign=signal
        )
        self.df['macd'] = macd.macd()
        self.df['macd_signal'] = macd.macd_signal()
        self.df['macd_diff'] = macd.macd_diff()

    def add_bollinger_bands(self, period: int = 20, std_dev: int = 2):
        """
        Aggiunge Bollinger Bands

        Args:
            period: Periodo per la media mobile
            std_dev: Numero di deviazioni standard
        """
        bb = BollingerBands(
            close=self.df['close'],
            window=period,
            window_dev=std_dev
        )
        self.df['bb_upper'] = bb.bollinger_hband()
        self.df['bb_middle'] = bb.bollinger_mavg()
        self.df['bb_lower'] = bb.bollinger_lband()
        self.df['bb_width'] = bb.bollinger_wband()
        self.df['bb_pband'] = bb.bollinger_pband()

    def add_stochastic(self, k_period: int = 14, d_period: int = 3):
        """
        Aggiunge Stochastic Oscillator

        Args:
            k_period: Periodo per %K
            d_period: Periodo per %D (media mobile di %K)
        """
        stoch = StochasticOscillator(
            high=self.df['high'],
            low=self.df['low'],
            close=self.df['close'],
            window=k_period,
            smooth_window=d_period
        )
        self.df['stoch_k'] = stoch.stoch()
        self.df['stoch_d'] = stoch.stoch_signal()

    def add_atr(self, period: int = 14):
        """
        Aggiunge Average True Range (volatilità)

        Args:
            period: Periodo per il calcolo ATR
        """
        atr = AverageTrueRange(
            high=self.df['high'],
            low=self.df['low'],
            close=self.df['close'],
            window=period
        )
        self.df['atr'] = atr.average_true_range()

    def add_obv(self):
        """
        Aggiunge On-Balance Volume
        """
        obv = OnBalanceVolumeIndicator(
            close=self.df['close'],
            volume=self.df['volume']
        )
        self.df['obv'] = obv.on_balance_volume()

    def add_price_momentum(self, periods: list = [1, 3, 5, 10]):
        """
        Aggiunge momentum del prezzo (variazione percentuale)

        Args:
            periods: Lista di periodi per calcolare il momentum
        """
        for period in periods:
            self.df[f'momentum_{period}'] = self.df['close'].pct_change(period) * 100

    def add_volume_indicators(self):
        """
        Aggiunge indicatori basati sul volume
        """
        # Volume ratio (volume corrente / media mobile volume)
        vol_sma = self.df['volume'].rolling(window=20).mean()
        self.df['volume_ratio'] = self.df['volume'] / vol_sma

        # Volume trend
        self.df['volume_trend'] = self.df['volume'].pct_change(5) * 100

    def add_price_patterns(self):
        """
        Aggiunge pattern di prezzo riconosciuti
        """
        # Candles verdi/rosse
        self.df['is_green'] = (self.df['close'] > self.df['open']).astype(int)

        # Range del candle
        self.df['candle_range'] = (self.df['high'] - self.df['low']) / self.df['close'] * 100

        # Body del candle
        self.df['candle_body'] = abs(self.df['close'] - self.df['open']) / self.df['close'] * 100

        # Upper/Lower shadow
        self.df['upper_shadow'] = (self.df['high'] - self.df[['close', 'open']].max(axis=1)) / self.df['close'] * 100
        self.df['lower_shadow'] = (self.df[['close', 'open']].min(axis=1) - self.df['low']) / self.df['close'] * 100

    def get_features_dataframe(self) -> pd.DataFrame:
        """
        Restituisce DataFrame con tutte le feature calcolate, rimuovendo righe con NaN

        Returns:
            DataFrame pulito con tutte le feature
        """
        # Rimuovi righe con NaN (generate dai calcoli degli indicatori)
        df_clean = self.df.dropna()
        return df_clean

    def get_feature_names(self) -> list:
        """
        Restituisce lista dei nomi delle feature (escludendo OHLCV originali)

        Returns:
            Lista di nomi delle colonne feature
        """
        base_cols = ['open', 'high', 'low', 'close', 'volume']
        return [col for col in self.df.columns if col not in base_cols]


# Test del modulo
if __name__ == '__main__':
    from binance_data_loader import BinanceDataLoader

    # Carica dati di esempio
    loader = BinanceDataLoader()
    df = loader.get_historical_klines('BTCUSDT', '1h', days_back=30)

    print("=" * 60)
    print("TEST: Calcolo Indicatori Tecnici")
    print("=" * 60)
    print(f"\nDati originali: {len(df)} righe")

    # Calcola indicatori
    indicators = TechnicalIndicators(df)
    df_with_indicators = indicators.add_all_indicators()
    indicators.add_price_patterns()

    print(f"Dati con indicatori: {len(df_with_indicators)} righe")
    print(f"\nColonne totali: {len(df_with_indicators.columns)}")

    # Mostra feature
    features = indicators.get_feature_names()
    print(f"\nFeature calcolate ({len(features)}):")
    for i, feat in enumerate(features, 1):
        print(f"{i}. {feat}")

    # Mostra ultimi dati
    df_clean = indicators.get_features_dataframe()
    print(f"\n\nUltimi 3 record con indicatori:")
    print(df_clean.tail(3).to_string())

    # Statistiche sugli indicatori
    print("\n\nStatistiche indicatori principali:")
    key_indicators = ['rsi', 'macd', 'bb_pband', 'stoch_k', 'atr']
    print(df_clean[key_indicators].describe())
