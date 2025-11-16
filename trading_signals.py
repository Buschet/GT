"""
Sistema di segnali di trading
Combina AI predictions con analisi tecnica tradizionale
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime


class TradingSignals:
    """
    Generatore di segnali di trading che combina:
    - Predizioni AI
    - Analisi tecnica tradizionale
    - Gestione del rischio
    """

    def __init__(self):
        self.signals_history = []

    def analyze_rsi(self, rsi: float) -> Dict:
        """
        Analizza RSI per condizioni di overbought/oversold

        Args:
            rsi: Valore RSI corrente

        Returns:
            Dict con segnale e forza
        """
        if rsi < 30:
            return {'signal': 'BUY', 'strength': 'strong', 'reason': f'RSI oversold ({rsi:.1f})'}
        elif rsi < 40:
            return {'signal': 'BUY', 'strength': 'moderate', 'reason': f'RSI basso ({rsi:.1f})'}
        elif rsi > 70:
            return {'signal': 'SELL', 'strength': 'strong', 'reason': f'RSI overbought ({rsi:.1f})'}
        elif rsi > 60:
            return {'signal': 'SELL', 'strength': 'moderate', 'reason': f'RSI alto ({rsi:.1f})'}
        else:
            return {'signal': 'HOLD', 'strength': 'neutral', 'reason': f'RSI neutrale ({rsi:.1f})'}

    def analyze_macd(self, macd: float, macd_signal: float, macd_diff: float) -> Dict:
        """
        Analizza MACD per crossover e divergenze

        Args:
            macd: Valore MACD
            macd_signal: Linea segnale MACD
            macd_diff: Differenza (istogramma)

        Returns:
            Dict con segnale e forza
        """
        if macd_diff > 0 and macd > macd_signal:
            strength = 'strong' if abs(macd_diff) > abs(macd) * 0.1 else 'moderate'
            return {'signal': 'BUY', 'strength': strength, 'reason': 'MACD bullish crossover'}
        elif macd_diff < 0 and macd < macd_signal:
            strength = 'strong' if abs(macd_diff) > abs(macd) * 0.1 else 'moderate'
            return {'signal': 'SELL', 'strength': strength, 'reason': 'MACD bearish crossover'}
        else:
            return {'signal': 'HOLD', 'strength': 'neutral', 'reason': 'MACD neutrale'}

    def analyze_bollinger_bands(self, close: float, bb_lower: float, bb_upper: float, bb_pband: float) -> Dict:
        """
        Analizza posizione del prezzo rispetto alle Bollinger Bands

        Args:
            close: Prezzo di chiusura
            bb_lower: Banda inferiore
            bb_upper: Banda superiore
            bb_pband: Percentuale banda

        Returns:
            Dict con segnale e forza
        """
        if close <= bb_lower or bb_pband < 0.1:
            return {'signal': 'BUY', 'strength': 'strong', 'reason': f'Prezzo su banda inferiore (pband: {bb_pband:.2f})'}
        elif bb_pband < 0.3:
            return {'signal': 'BUY', 'strength': 'moderate', 'reason': f'Prezzo vicino a banda inferiore (pband: {bb_pband:.2f})'}
        elif close >= bb_upper or bb_pband > 0.9:
            return {'signal': 'SELL', 'strength': 'strong', 'reason': f'Prezzo su banda superiore (pband: {bb_pband:.2f})'}
        elif bb_pband > 0.7:
            return {'signal': 'SELL', 'strength': 'moderate', 'reason': f'Prezzo vicino a banda superiore (pband: {bb_pband:.2f})'}
        else:
            return {'signal': 'HOLD', 'strength': 'neutral', 'reason': 'Prezzo in mezzo alle bande'}

    def analyze_moving_averages(self, close: float, sma_50: float, sma_200: float, ema_21: float) -> Dict:
        """
        Analizza medie mobili per trend e crossover

        Args:
            close: Prezzo corrente
            sma_50: SMA 50
            sma_200: SMA 200
            ema_21: EMA 21

        Returns:
            Dict con segnale e forza
        """
        signals = []

        # Golden Cross / Death Cross
        if sma_50 > sma_200:
            if close > sma_50:
                signals.append({'signal': 'BUY', 'strength': 'strong', 'reason': 'Golden cross + prezzo sopra SMA50'})
            else:
                signals.append({'signal': 'BUY', 'strength': 'moderate', 'reason': 'Golden cross'})
        elif sma_50 < sma_200:
            if close < sma_50:
                signals.append({'signal': 'SELL', 'strength': 'strong', 'reason': 'Death cross + prezzo sotto SMA50'})
            else:
                signals.append({'signal': 'SELL', 'strength': 'moderate', 'reason': 'Death cross'})

        # Prezzo vs EMA 21
        if close > ema_21 * 1.02:
            signals.append({'signal': 'BUY', 'strength': 'moderate', 'reason': 'Prezzo sopra EMA21'})
        elif close < ema_21 * 0.98:
            signals.append({'signal': 'SELL', 'strength': 'moderate', 'reason': 'Prezzo sotto EMA21'})

        if not signals:
            return {'signal': 'HOLD', 'strength': 'neutral', 'reason': 'Medie mobili neutre'}

        # Restituisci il segnale più forte
        return max(signals, key=lambda x: 1 if x['strength'] == 'strong' else 0.5)

    def analyze_volume(self, volume_ratio: float, volume_trend: float) -> Dict:
        """
        Analizza il volume per confermare i movimenti

        Args:
            volume_ratio: Rapporto volume corrente / media
            volume_trend: Trend del volume

        Returns:
            Dict con segnale e forza
        """
        if volume_ratio > 2 and volume_trend > 20:
            return {'signal': 'CONFIRM', 'strength': 'strong', 'reason': f'Volume molto alto (ratio: {volume_ratio:.1f})'}
        elif volume_ratio > 1.5:
            return {'signal': 'CONFIRM', 'strength': 'moderate', 'reason': f'Volume alto (ratio: {volume_ratio:.1f})'}
        elif volume_ratio < 0.5:
            return {'signal': 'WEAK', 'strength': 'weak', 'reason': f'Volume basso (ratio: {volume_ratio:.1f})'}
        else:
            return {'signal': 'NEUTRAL', 'strength': 'neutral', 'reason': 'Volume normale'}

    def generate_signal(self,
                       df: pd.DataFrame,
                       ai_prediction: Dict,
                       symbol: str,
                       timeframe: str) -> Dict:
        """
        Genera un segnale di trading completo combinando AI e analisi tecnica

        Args:
            df: DataFrame con dati e indicatori
            ai_prediction: Predizione del modello AI
            symbol: Simbolo della coppia
            timeframe: Timeframe dei dati

        Returns:
            Dict con segnale completo e dettagli
        """
        # Prendi l'ultimo record
        last = df.iloc[-1]

        # Analisi tecnica
        rsi_analysis = self.analyze_rsi(last['rsi'])
        macd_analysis = self.analyze_macd(last['macd'], last['macd_signal'], last['macd_diff'])
        bb_analysis = self.analyze_bollinger_bands(last['close'], last['bb_lower'], last['bb_upper'], last['bb_pband'])
        ma_analysis = self.analyze_moving_averages(last['close'], last['sma_50'], last['sma_200'], last['ema_21'])
        vol_analysis = self.analyze_volume(last['volume_ratio'], last['volume_trend'])

        # Raccogli tutti i segnali
        technical_signals = [rsi_analysis, macd_analysis, bb_analysis, ma_analysis]

        # Conta i segnali buy/sell/hold
        buy_count = sum(1 for s in technical_signals if s['signal'] == 'BUY')
        sell_count = sum(1 for s in technical_signals if s['signal'] == 'SELL')
        hold_count = sum(1 for s in technical_signals if s['signal'] == 'HOLD')

        # Conta la forza
        strong_buy = sum(1 for s in technical_signals if s['signal'] == 'BUY' and s['strength'] == 'strong')
        strong_sell = sum(1 for s in technical_signals if s['signal'] == 'SELL' and s['strength'] == 'strong')

        # Determina il segnale tecnico finale
        if buy_count > sell_count and buy_count >= 2:
            technical_action = 'BUY'
            technical_confidence = (buy_count / len(technical_signals)) * (1 + strong_buy * 0.2)
        elif sell_count > buy_count and sell_count >= 2:
            technical_action = 'SELL'
            technical_confidence = (sell_count / len(technical_signals)) * (1 + strong_sell * 0.2)
        else:
            technical_action = 'HOLD'
            technical_confidence = hold_count / len(technical_signals)

        # Combina AI e analisi tecnica
        ai_action = ai_prediction['action']
        ai_confidence = ai_prediction['confidence']

        # Calcola consenso
        if ai_action == technical_action:
            final_action = ai_action
            final_confidence = (ai_confidence + technical_confidence) / 2 * 1.2  # Boost per consenso
            consensus = 'STRONG'
        elif ai_action == 'HOLD' or technical_action == 'HOLD':
            final_action = ai_action if ai_action != 'HOLD' else technical_action
            final_confidence = max(ai_confidence, technical_confidence) * 0.7
            consensus = 'MODERATE'
        else:
            final_action = 'HOLD'  # In caso di conflitto
            final_confidence = 0.3
            consensus = 'CONFLICT'

        # Applica filtro volume
        if vol_analysis['signal'] == 'WEAK' and final_action != 'HOLD':
            final_confidence *= 0.7  # Riduci confidence se volume è basso

        # Cap confidence a 1.0
        final_confidence = min(final_confidence, 1.0)

        # Determina forza del segnale
        if final_confidence >= 0.7:
            signal_strength = 'FORTE'
        elif final_confidence >= 0.5:
            signal_strength = 'MODERATO'
        else:
            signal_strength = 'DEBOLE'

        # Costruisci il risultato
        result = {
            'symbol': symbol,
            'timeframe': timeframe,
            'timestamp': datetime.now().isoformat(),
            'price': float(last['close']),
            'action': final_action,
            'confidence': float(final_confidence),
            'signal_strength': signal_strength,
            'consensus': consensus,
            'ai': {
                'action': ai_action,
                'confidence': float(ai_confidence),
                'probabilities': ai_prediction['probabilities']
            },
            'technical': {
                'action': technical_action,
                'confidence': float(technical_confidence),
                'buy_signals': buy_count,
                'sell_signals': sell_count,
                'hold_signals': hold_count
            },
            'indicators': {
                'rsi': float(last['rsi']),
                'macd_diff': float(last['macd_diff']),
                'bb_position': float(last['bb_pband']),
                'volume_ratio': float(last['volume_ratio'])
            },
            'analysis_details': {
                'rsi': rsi_analysis,
                'macd': macd_analysis,
                'bollinger': bb_analysis,
                'moving_averages': ma_analysis,
                'volume': vol_analysis
            }
        }

        # Salva nella storia
        self.signals_history.append(result)

        return result

    def get_signal_summary(self, signal: Dict) -> str:
        """
        Genera un riassunto testuale del segnale

        Args:
            signal: Segnale generato

        Returns:
            Stringa con riassunto formattato
        """
        summary = f"""
{'=' * 70}
SEGNALE DI TRADING - {signal['symbol']} ({signal['timeframe']})
{'=' * 70}

RACCOMANDAZIONE: {signal['action']}
Confidence: {signal['confidence']:.1%} ({signal['signal_strength']})
Consenso: {signal['consensus']}
Prezzo attuale: ${signal['price']:,.2f}

AI PREDICTION:
  Azione: {signal['ai']['action']} (confidence: {signal['ai']['confidence']:.1%})
  Probabilità BUY:  {signal['ai']['probabilities']['buy']:.1%}
  Probabilità HOLD: {signal['ai']['probabilities']['hold']:.1%}
  Probabilità SELL: {signal['ai']['probabilities']['sell']:.1%}

ANALISI TECNICA:
  Azione: {signal['technical']['action']} (confidence: {signal['technical']['confidence']:.1%})
  Segnali BUY:  {signal['technical']['buy_signals']}
  Segnali HOLD: {signal['technical']['hold_signals']}
  Segnali SELL: {signal['technical']['sell_signals']}

INDICATORI CHIAVE:
  RSI: {signal['indicators']['rsi']:.1f} - {signal['analysis_details']['rsi']['reason']}
  MACD: {signal['analysis_details']['macd']['reason']}
  Bollinger: {signal['analysis_details']['bollinger']['reason']}
  Medie Mobili: {signal['analysis_details']['moving_averages']['reason']}
  Volume: {signal['analysis_details']['volume']['reason']}

Timestamp: {signal['timestamp']}
{'=' * 70}
"""
        return summary


# Test del modulo
if __name__ == '__main__':
    from binance_data_loader import BinanceDataLoader
    from technical_indicators import TechnicalIndicators
    from ai_trading_model import TradingAIModel

    print("=" * 70)
    print("TEST: Trading Signals System")
    print("=" * 70)

    # Setup
    symbol = 'BTCUSDT'
    timeframe = '1h'

    # Carica dati
    loader = BinanceDataLoader()
    df = loader.get_historical_klines(symbol, timeframe, days_back=60)

    # Calcola indicatori
    indicators = TechnicalIndicators(df)
    df_with_indicators = indicators.add_all_indicators()
    indicators.add_price_patterns()
    df_clean = indicators.get_features_dataframe()

    # Addestra modello AI
    model = TradingAIModel()
    feature_cols = indicators.get_feature_names()
    model.train(df_clean, feature_cols, forward_periods=5, threshold=0.015)

    # Fai predizione AI
    ai_prediction = model.predict(df_clean, feature_cols)

    # Genera segnale
    signal_generator = TradingSignals()
    signal = signal_generator.generate_signal(df_clean, ai_prediction, symbol, timeframe)

    # Mostra risultato
    print(signal_generator.get_signal_summary(signal))
