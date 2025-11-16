"""
Modulo per caricare dati di trading da Binance
Supporta multipli timeframe e coppie di trading
"""

import pandas as pd
import numpy as np
from binance.client import Client
from datetime import datetime, timedelta
import time
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

load_dotenv()


class BinanceDataLoader:
    """
    Classe per caricare dati storici da Binance
    """

    # Timeframe disponibili su Binance
    TIMEFRAMES = {
        '1m': Client.KLINE_INTERVAL_1MINUTE,
        '3m': Client.KLINE_INTERVAL_3MINUTE,
        '5m': Client.KLINE_INTERVAL_5MINUTE,
        '15m': Client.KLINE_INTERVAL_15MINUTE,
        '30m': Client.KLINE_INTERVAL_30MINUTE,
        '1h': Client.KLINE_INTERVAL_1HOUR,
        '2h': Client.KLINE_INTERVAL_2HOUR,
        '4h': Client.KLINE_INTERVAL_4HOUR,
        '6h': Client.KLINE_INTERVAL_6HOUR,
        '8h': Client.KLINE_INTERVAL_8HOUR,
        '12h': Client.KLINE_INTERVAL_12HOUR,
        '1d': Client.KLINE_INTERVAL_1DAY,
        '3d': Client.KLINE_INTERVAL_3DAY,
        '1w': Client.KLINE_INTERVAL_1WEEK,
        '1M': Client.KLINE_INTERVAL_1MONTH
    }

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """
        Inizializza il client Binance

        Args:
            api_key: API key di Binance (opzionale per dati pubblici)
            api_secret: API secret di Binance (opzionale per dati pubblici)
        """
        # Se non forniti, prova a caricare dalle variabili d'ambiente
        if api_key is None:
            api_key = os.getenv('BINANCE_API_KEY', '')
        if api_secret is None:
            api_secret = os.getenv('BINANCE_API_SECRET', '')

        # Anche senza credenziali, possiamo accedere ai dati pubblici
        self.client = Client(api_key, api_secret)

    def get_historical_klines(self,
                             symbol: str,
                             timeframe: str,
                             days_back: int = 30,
                             start_date: Optional[str] = None,
                             end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Scarica dati storici OHLCV per una coppia di trading

        Args:
            symbol: Coppia di trading (es. 'BTCUSDT')
            timeframe: Timeframe ('1m', '5m', '15m', '1h', '4h', '1d')
            days_back: Numero di giorni da scaricare (default: 30)
            start_date: Data inizio (formato: 'YYYY-MM-DD') - opzionale
            end_date: Data fine (formato: 'YYYY-MM-DD') - opzionale

        Returns:
            DataFrame con colonne: timestamp, open, high, low, close, volume
        """
        if timeframe not in self.TIMEFRAMES:
            raise ValueError(f"Timeframe {timeframe} non valido. Usa: {list(self.TIMEFRAMES.keys())}")

        interval = self.TIMEFRAMES[timeframe]

        # Calcola date
        if start_date:
            start_ts = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp() * 1000)
        else:
            start_ts = int((datetime.now() - timedelta(days=days_back)).timestamp() * 1000)

        if end_date:
            end_ts = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp() * 1000)
        else:
            end_ts = int(datetime.now().timestamp() * 1000)

        print(f"Scaricamento dati per {symbol} - Timeframe: {timeframe}")
        print(f"Periodo: {datetime.fromtimestamp(start_ts/1000)} - {datetime.fromtimestamp(end_ts/1000)}")

        # Scarica i dati
        klines = self.client.get_historical_klines(
            symbol=symbol,
            interval=interval,
            start_str=start_ts,
            end_str=end_ts
        )

        # Converti in DataFrame
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])

        # Seleziona solo le colonne necessarie
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

        # Converti i tipi
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)

        # Imposta timestamp come indice
        df.set_index('timestamp', inplace=True)

        print(f"Scaricati {len(df)} candelieri")

        return df

    def get_multiple_timeframes(self,
                               symbol: str,
                               timeframes: List[str],
                               days_back: int = 30) -> Dict[str, pd.DataFrame]:
        """
        Scarica dati per multipli timeframe contemporaneamente

        Args:
            symbol: Coppia di trading (es. 'BTCUSDT')
            timeframes: Lista di timeframe da scaricare
            days_back: Numero di giorni da scaricare

        Returns:
            Dizionario {timeframe: DataFrame}
        """
        data = {}

        for tf in timeframes:
            print(f"\n--- Timeframe: {tf} ---")
            df = self.get_historical_klines(symbol, tf, days_back)
            data[tf] = df
            time.sleep(0.5)  # Pausa per evitare rate limiting

        return data

    def get_current_price(self, symbol: str) -> float:
        """
        Ottiene il prezzo corrente per una coppia

        Args:
            symbol: Coppia di trading (es. 'BTCUSDT')

        Returns:
            Prezzo corrente
        """
        ticker = self.client.get_symbol_ticker(symbol=symbol)
        return float(ticker['price'])

    def get_top_symbols(self, quote_asset: str = 'USDT', limit: int = 20) -> List[str]:
        """
        Ottiene i simboli più scambiati per un quote asset

        Args:
            quote_asset: Asset di quotazione (default: 'USDT')
            limit: Numero di simboli da restituire

        Returns:
            Lista di simboli ordinati per volume
        """
        tickers = self.client.get_ticker()

        # Filtra per quote asset e ordina per volume
        filtered = [
            t for t in tickers
            if t['symbol'].endswith(quote_asset)
        ]

        # Ordina per volume (quote volume)
        sorted_tickers = sorted(
            filtered,
            key=lambda x: float(x['quoteVolume']),
            reverse=True
        )

        return [t['symbol'] for t in sorted_tickers[:limit]]


# Test del modulo
if __name__ == '__main__':
    loader = BinanceDataLoader()

    # Test 1: Scarica dati BTC
    print("=" * 60)
    print("TEST 1: Scaricamento dati BTCUSDT")
    print("=" * 60)
    btc_data = loader.get_historical_klines('BTCUSDT', '1h', days_back=7)
    print(f"\nPrime 5 righe:\n{btc_data.head()}")
    print(f"\nUltime 5 righe:\n{btc_data.tail()}")

    # Test 2: Multiple timeframes
    print("\n" + "=" * 60)
    print("TEST 2: Multiple timeframes per ETHUSDT")
    print("=" * 60)
    eth_data = loader.get_multiple_timeframes('ETHUSDT', ['15m', '1h', '4h'], days_back=7)
    for tf, df in eth_data.items():
        print(f"\n{tf}: {len(df)} candelieri")

    # Test 3: Prezzo corrente
    print("\n" + "=" * 60)
    print("TEST 3: Prezzi correnti")
    print("=" * 60)
    btc_price = loader.get_current_price('BTCUSDT')
    eth_price = loader.get_current_price('ETHUSDT')
    print(f"BTC: ${btc_price:,.2f}")
    print(f"ETH: ${eth_price:,.2f}")

    # Test 4: Top symbols
    print("\n" + "=" * 60)
    print("TEST 4: Top 10 simboli per volume")
    print("=" * 60)
    top_symbols = loader.get_top_symbols(limit=10)
    for i, symbol in enumerate(top_symbols, 1):
        print(f"{i}. {symbol}")
