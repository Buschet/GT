#!/usr/bin/env python3
"""
Script di analisi rapida - Quick Start
Analizza BTC e ETH per segnali di trading veloci
"""

from binance_data_loader import BinanceDataLoader
from technical_indicators import TechnicalIndicators
from ai_trading_model import TradingAIModel
from trading_signals import TradingSignals


def quick_analysis(symbol='BTCUSDT', timeframe='1h', days=30):
    """
    Esegue un'analisi rapida di un simbolo

    Args:
        symbol: Coppia di trading
        timeframe: Timeframe
        days: Giorni di storico
    """
    print(f"\n{'=' * 70}")
    print(f"ANALISI RAPIDA: {symbol} - {timeframe}")
    print(f"{'=' * 70}\n")

    # 1. Scarica dati
    print("📊 Scaricamento dati da Binance...")
    loader = BinanceDataLoader()
    df = loader.get_historical_klines(symbol, timeframe, days_back=days)
    print(f"✓ Scaricati {len(df)} candelieri")

    # 2. Calcola indicatori tecnici
    print("\n📈 Calcolo indicatori tecnici...")
    indicators = TechnicalIndicators(df)
    df_with_indicators = indicators.add_all_indicators()
    indicators.add_price_patterns()
    df_clean = indicators.get_features_dataframe()
    print(f"✓ Calcolati {len(indicators.get_feature_names())} indicatori")

    # 3. Addestra modello AI
    print("\n🤖 Addestramento modello AI...")
    model = TradingAIModel()
    feature_cols = indicators.get_feature_names()
    metrics = model.train(df_clean, feature_cols, forward_periods=5, threshold=0.015)
    print(f"✓ Modello addestrato - Accuracy: {metrics['rf_test_accuracy']:.2%}")

    # 4. Genera predizione
    print("\n🎯 Generazione segnale di trading...")
    ai_prediction = model.predict(df_clean, feature_cols)

    # 5. Analisi completa
    signal_generator = TradingSignals()
    signal = signal_generator.generate_signal(df_clean, ai_prediction, symbol, timeframe)

    # 6. Mostra risultato
    print(signal_generator.get_signal_summary(signal))

    # 7. Raccomandazione finale
    print("\n" + "=" * 70)
    print("RACCOMANDAZIONE FINALE")
    print("=" * 70)

    if signal['action'] == 'BUY' and signal['confidence'] >= 0.6:
        print(f"✅ SEGNALE DI ACQUISTO per {symbol}")
        print(f"   Confidence: {signal['confidence']:.1%} ({signal['signal_strength']})")
        print(f"   Prezzo ingresso suggerito: ${signal['price']:,.2f}")
        print(f"   Consenso AI + Tecnica: {signal['consensus']}")

    elif signal['action'] == 'SELL' and signal['confidence'] >= 0.6:
        print(f"⚠️  SEGNALE DI VENDITA per {symbol}")
        print(f"   Confidence: {signal['confidence']:.1%} ({signal['signal_strength']})")
        print(f"   Prezzo attuale: ${signal['price']:,.2f}")
        print(f"   Consenso AI + Tecnica: {signal['consensus']}")

    else:
        print(f"⏸️  NESSUNA AZIONE RACCOMANDATA per {symbol}")
        print(f"   Meglio attendere un segnale più chiaro")
        print(f"   Confidence attuale: {signal['confidence']:.1%}")

    print("=" * 70)

    return signal


if __name__ == '__main__':
    print("\n" + "🚀 " * 35)
    print("AI TRADING ANALYSIS - QUICK START")
    print("🚀 " * 35)

    # Analizza BTC
    btc_signal = quick_analysis('BTCUSDT', '1h', 30)

    # Analizza ETH
    eth_signal = quick_analysis('ETHUSDT', '1h', 30)

    # Confronto
    print("\n" + "=" * 70)
    print("CONFRONTO BTC vs ETH")
    print("=" * 70)

    signals = [
        ('BTC', btc_signal),
        ('ETH', eth_signal)
    ]

    for name, sig in signals:
        action_emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '🟡'}.get(sig['action'], '⚪')
        print(f"\n{name}:")
        print(f"  {action_emoji} {sig['action']} - Confidence: {sig['confidence']:.1%}")
        print(f"  Prezzo: ${sig['price']:,.2f}")
        print(f"  Consenso: {sig['consensus']}")

    # Migliore opportunità
    best = max(signals, key=lambda x: x[1]['confidence'] if x[1]['action'] != 'HOLD' else 0)

    if best[1]['action'] != 'HOLD':
        print("\n" + "=" * 70)
        print("🏆 MIGLIORE OPPORTUNITÀ")
        print("=" * 70)
        print(f"{best[0]} - {best[1]['action']} con {best[1]['confidence']:.1%} confidence")

    print("\n✅ Analisi completata!\n")
