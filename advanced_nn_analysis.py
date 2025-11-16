#!/usr/bin/env python3
"""
Analisi Avanzata combinando:
- Rete Neurale Multi-Timeframe (Delfini/Squali/Balene)
- AI Trading Model (Random Forest + Gradient Boosting)
- Indicatori Tecnici Tradizionali

Sistema completo per identificare trend e punti di ingresso/uscita
"""

import argparse
from binance_data_loader import BinanceDataLoader
from neural_network_trader import MultiTimeframeNNTrader
from technical_indicators import TechnicalIndicators
from ai_trading_model import TradingAIModel
from trading_signals import TradingSignals


class AdvancedNeuralAnalyzer:
    """
    Combina analisi da rete neurale, AI ML e indicatori tecnici
    """

    def __init__(self):
        self.nn_trader = MultiTimeframeNNTrader()
        self.loader = BinanceDataLoader()

    def analyze_symbol_complete(
        self,
        symbol: str,
        tf_short: str = '15m',
        tf_medium: str = '1h',
        tf_long: str = '4h',
        days_back: int = 30
    ):
        """
        Analisi completa di un simbolo combinando tutti i metodi

        Args:
            symbol: Coppia di trading
            tf_short: Timeframe corto (Delfini)
            tf_medium: Timeframe medio (Squali)
            tf_long: Timeframe lungo (Balene)
            days_back: Giorni di storico
        """
        print("\n" + "🚀 " * 40)
        print(f"ANALISI AVANZATA MULTI-SISTEMA: {symbol}")
        print("🚀 " * 40)

        # ===============================================
        # 1. RETE NEURALE MULTI-TIMEFRAME
        # ===============================================
        print("\n" + "=" * 80)
        print("1️⃣  RETE NEURALE MULTI-TIMEFRAME (Delfini/Squali/Balene)")
        print("=" * 80)

        nn_results = self.nn_trader.analyze_multi_timeframe(
            symbol,
            tf_dolphins=tf_short,
            tf_sharks=tf_medium,
            tf_whales=tf_long,
            days_back=days_back
        )

        nn_signals = self.nn_trader.generate_signals(nn_results, lookback=30)
        self.nn_trader.print_analysis_report(symbol, nn_signals)

        # ===============================================
        # 2. AI MACHINE LEARNING
        # ===============================================
        print("\n" + "=" * 80)
        print("2️⃣  AI MACHINE LEARNING (Random Forest + Gradient Boosting)")
        print("=" * 80)

        # Usa il timeframe medio per l'analisi AI
        df_ai = self.loader.get_historical_klines(symbol, tf_medium, days_back=60)

        # Calcola indicatori tecnici
        indicators = TechnicalIndicators(df_ai)
        df_with_indicators = indicators.add_all_indicators()
        indicators.add_price_patterns()
        df_clean = indicators.get_features_dataframe()

        # Addestra modello AI
        print("\n🤖 Training AI model...")
        ai_model = TradingAIModel()
        feature_cols = indicators.get_feature_names()
        ai_metrics = ai_model.train(
            df_clean,
            feature_cols,
            forward_periods=5,
            threshold=0.015
        )

        # Predizione AI
        ai_prediction = ai_model.predict(df_clean, feature_cols)

        # Genera segnale combinato AI + tecnica
        signal_gen = TradingSignals()
        ai_signal = signal_gen.generate_signal(
            df_clean,
            ai_prediction,
            symbol,
            tf_medium
        )

        print(signal_gen.get_signal_summary(ai_signal))

        # ===============================================
        # 3. CONSENSO FINALE TRA I SISTEMI
        # ===============================================
        print("\n" + "=" * 80)
        print("3️⃣  CONSENSO TRA TUTTI I SISTEMI")
        print("=" * 80)

        # Raccogli segnali
        nn_action = nn_signals['action']
        ai_action = ai_signal['action']
        nn_confidence = abs(nn_signals['combined_output']) / 3  # Normalizza a 0-1
        ai_confidence = ai_signal['confidence']

        print(f"\n📊 COMPARAZIONE SEGNALI:")
        print(f"   🧠 Rete Neurale:     {nn_action:<6} (confidence: {nn_confidence:.1%})")
        print(f"   🤖 AI ML:            {ai_action:<6} (confidence: {ai_confidence:.1%})")

        # Determina consenso
        if nn_action == ai_action:
            final_action = nn_action
            consensus_strength = "FORTISSIMO"
            final_confidence = (nn_confidence + ai_confidence) / 2 * 1.3  # Boost per consenso
        elif nn_action == 'HOLD' or ai_action == 'HOLD':
            # Uno dei due dice HOLD
            final_action = nn_action if nn_action != 'HOLD' else ai_action
            consensus_strength = "MODERATO"
            final_confidence = max(nn_confidence, ai_confidence) * 0.7
        else:
            # Conflitto
            final_action = 'HOLD'
            consensus_strength = "CONFLITTO"
            final_confidence = 0.3

        final_confidence = min(final_confidence, 1.0)  # Cap a 1.0

        print(f"\n🎯 RACCOMANDAZIONE FINALE:")
        print(f"   Azione:            {final_action}")
        print(f"   Consenso:          {consensus_strength}")
        print(f"   Confidence Finale: {final_confidence:.1%}")

        # ===============================================
        # 4. PUNTI DI INGRESSO/USCITA
        # ===============================================
        print(f"\n" + "=" * 80)
        print("4️⃣  PUNTI DI INGRESSO/USCITA")
        print("=" * 80)

        current_price = nn_signals['current_price']

        if nn_signals['entry_exit_signal']:
            print(f"\n{nn_signals['entry_exit_signal']}")

        # Calcola livelli chiave basati su indicatori tecnici
        last_row = df_clean.iloc[-1]

        print(f"\n📍 LIVELLI CHIAVE:")
        print(f"   Prezzo Corrente:   ${current_price:,.2f}")
        print(f"   Bollinger Superior: ${last_row['bb_upper']:,.2f}")
        print(f"   Bollinger Medio:   ${last_row['bb_middle']:,.2f}")
        print(f"   Bollinger Inferior: ${last_row['bb_lower']:,.2f}")
        print(f"   EMA 21:            ${last_row['ema_21']:,.2f}")
        print(f"   SMA 50:            ${last_row['sma_50']:,.2f}")

        # Suggerisci livelli di ingresso/uscita
        if final_action == 'BUY':
            entry_price = current_price
            stop_loss = entry_price * 0.97  # 3% sotto
            take_profit_1 = entry_price * 1.02  # 2% sopra
            take_profit_2 = entry_price * 1.05  # 5% sopra

            print(f"\n🟢 SETUP LONG:")
            print(f"   Ingresso:       ${entry_price:,.2f}")
            print(f"   Stop Loss:     ${stop_loss:,.2f} (-3%)")
            print(f"   Take Profit 1: ${take_profit_1:,.2f} (+2%)")
            print(f"   Take Profit 2: ${take_profit_2:,.2f} (+5%)")
            print(f"   Risk/Reward:   1:1.67")

        elif final_action == 'SELL':
            entry_price = current_price
            stop_loss = entry_price * 1.03  # 3% sopra
            take_profit_1 = entry_price * 0.98  # 2% sotto
            take_profit_2 = entry_price * 0.95  # 5% sotto

            print(f"\n🔴 SETUP SHORT:")
            print(f"   Ingresso:       ${entry_price:,.2f}")
            print(f"   Stop Loss:     ${stop_loss:,.2f} (+3%)")
            print(f"   Take Profit 1: ${take_profit_1:,.2f} (-2%)")
            print(f"   Take Profit 2: ${take_profit_2:,.2f} (-5%)")
            print(f"   Risk/Reward:   1:1.67")

        else:
            print(f"\n⏸️  NESSUNA POSIZIONE RACCOMANDATA")
            print(f"   Attendere segnale più chiaro da entrambi i sistemi")

        # ===============================================
        # 5. INDICATORI TECNICI DI SUPPORTO
        # ===============================================
        print(f"\n" + "=" * 80)
        print("5️⃣  INDICATORI TECNICI CHIAVE")
        print("=" * 80)

        print(f"\n📊 MOMENTUM:")
        print(f"   RSI(14):        {last_row['rsi']:.2f}")
        if last_row['rsi'] < 30:
            print(f"   └─ Oversold - Possibile rimbalzo")
        elif last_row['rsi'] > 70:
            print(f"   └─ Overbought - Possibile correzione")
        else:
            print(f"   └─ Zona neutra")

        print(f"\n   MACD:          {last_row['macd']:.4f}")
        print(f"   MACD Signal:   {last_row['macd_signal']:.4f}")
        print(f"   MACD Diff:     {last_row['macd_diff']:.4f}")
        if last_row['macd_diff'] > 0:
            print(f"   └─ Momentum rialzista")
        else:
            print(f"   └─ Momentum ribassista")

        print(f"\n   Stochastic K:  {last_row['stoch_k']:.2f}")
        print(f"   Stochastic D:  {last_row['stoch_d']:.2f}")

        print(f"\n📊 VOLATILITÀ:")
        print(f"   ATR:           {last_row['atr']:.2f}")
        print(f"   BB Width:      {last_row['bb_width']:.4f}")
        print(f"   BB Position:   {last_row['bb_pband']:.2f}")

        print(f"\n📊 VOLUME:")
        print(f"   Volume Ratio:  {last_row['volume_ratio']:.2f}x")
        if last_row['volume_ratio'] > 1.5:
            print(f"   └─ Volume alto - Conferma movimento")
        elif last_row['volume_ratio'] < 0.7:
            print(f"   └─ Volume basso - Segnale debole")

        # ===============================================
        # 6. RIASSUNTO FINALE
        # ===============================================
        print(f"\n" + "=" * 80)
        print("📋 RIASSUNTO ESECUTIVO")
        print("=" * 80)

        # Emoji per il trend
        trend_emoji = {
            'BUY': '🟢 📈',
            'SELL': '🔴 📉',
            'HOLD': '🟡 ➡️'
        }

        print(f"\nSimbolo: {symbol}")
        print(f"Prezzo: ${current_price:,.2f}")
        print(f"\n{trend_emoji.get(final_action, '⚪')} RACCOMANDAZIONE: {final_action}")
        print(f"Consenso: {consensus_strength}")
        print(f"Confidence: {final_confidence:.1%}")

        if consensus_strength == "FORTISSIMO" and final_confidence > 0.7:
            print(f"\n✅ SEGNALE MOLTO FORTE - Alta probabilità di successo")
            print(f"✅ Tutti i sistemi sono allineati")
            print(f"✅ Considerare fortemente questa opportunità")

        elif consensus_strength == "MODERATO":
            print(f"\n⚠️  SEGNALE MODERATO - Cautela raccomandata")
            print(f"⚠️  I sistemi non sono completamente allineati")
            print(f"⚠️  Ridurre size posizione o attendere")

        else:
            print(f"\n❌ SEGNALE DEBOLE O CONFLITTO - Non tradare")
            print(f"❌ I sistemi sono in disaccordo")
            print(f"❌ Attendere segnale più chiaro")

        print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description='Analisi Avanzata Multi-Sistema con Rete Neurale e AI'
    )

    parser.add_argument(
        '--symbol',
        default='BTCUSDT',
        help='Simbolo da analizzare (default: BTCUSDT)'
    )

    parser.add_argument(
        '--tf-short',
        default='15m',
        help='Timeframe corto per Delfini (default: 15m)'
    )

    parser.add_argument(
        '--tf-medium',
        default='1h',
        help='Timeframe medio per Squali (default: 1h)'
    )

    parser.add_argument(
        '--tf-long',
        default='4h',
        help='Timeframe lungo per Balene (default: 4h)'
    )

    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Giorni di storico (default: 30)'
    )

    args = parser.parse_args()

    analyzer = AdvancedNeuralAnalyzer()
    analyzer.analyze_symbol_complete(
        args.symbol,
        args.tf_short,
        args.tf_medium,
        args.tf_long,
        args.days
    )


if __name__ == '__main__':
    main()
