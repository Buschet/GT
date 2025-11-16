#!/usr/bin/env python3
"""
Script principale per l'analisi trading con AI
Analizza coppie di trading da Binance e genera segnali buy/sell
"""

import argparse
import sys
from typing import List, Optional
from binance_data_loader import BinanceDataLoader
from technical_indicators import TechnicalIndicators
from ai_trading_model import TradingAIModel
from trading_signals import TradingSignals
import os


def analyze_symbol(symbol: str,
                   timeframes: List[str],
                   days_back: int,
                   model: Optional[TradingAIModel] = None,
                   train_model: bool = True) -> dict:
    """
    Analizza un simbolo su multipli timeframe

    Args:
        symbol: Coppia di trading (es. 'BTCUSDT')
        timeframes: Lista di timeframe da analizzare
        days_back: Giorni di dati storici
        model: Modello AI pre-addestrato (opzionale)
        train_model: Se True, addestra un nuovo modello

    Returns:
        Dict con risultati per ogni timeframe
    """
    loader = BinanceDataLoader()
    signal_generator = TradingSignals()
    results = {}

    print(f"\n{'=' * 70}")
    print(f"ANALISI: {symbol}")
    print(f"{'=' * 70}\n")

    for timeframe in timeframes:
        print(f"\n--- Analisi Timeframe: {timeframe} ---")

        try:
            # Carica dati
            df = loader.get_historical_klines(symbol, timeframe, days_back=days_back)

            if len(df) < 200:  # Servono abbastanza dati per indicatori
                print(f"⚠️  Dati insufficienti per {timeframe} (solo {len(df)} candelieri)")
                continue

            # Calcola indicatori
            indicators = TechnicalIndicators(df)
            df_with_indicators = indicators.add_all_indicators()
            indicators.add_price_patterns()
            df_clean = indicators.get_features_dataframe()

            if len(df_clean) < 100:
                print(f"⚠️  Dati puliti insufficienti per {timeframe}")
                continue

            # Prepara feature per AI
            feature_cols = indicators.get_feature_names()

            # Addestra o usa modello esistente
            if model is None or train_model:
                print("Addestramento modello AI...")
                ai_model = TradingAIModel()
                ai_model.train(
                    df_clean,
                    feature_cols,
                    forward_periods=5,
                    threshold=0.015
                )
            else:
                ai_model = model

            # Predizione AI
            ai_prediction = ai_model.predict(df_clean, feature_cols)

            # Genera segnale
            signal = signal_generator.generate_signal(
                df_clean,
                ai_prediction,
                symbol,
                timeframe
            )

            # Salva risultati
            results[timeframe] = {
                'signal': signal,
                'model': ai_model
            }

            # Stampa riassunto
            print(signal_generator.get_signal_summary(signal))

        except Exception as e:
            print(f"❌ Errore nell'analisi di {symbol} ({timeframe}): {str(e)}")
            continue

    return results


def analyze_multiple_symbols(symbols: List[str],
                            timeframe: str,
                            days_back: int = 30) -> List[dict]:
    """
    Analizza multiple coppie su un singolo timeframe

    Args:
        symbols: Lista di simboli da analizzare
        timeframe: Timeframe da usare
        days_back: Giorni di dati storici

    Returns:
        Lista di segnali ordinati per confidence
    """
    all_signals = []

    for symbol in symbols:
        print(f"\n{'#' * 70}")
        print(f"Analisi: {symbol}")
        print(f"{'#' * 70}")

        results = analyze_symbol(
            symbol,
            [timeframe],
            days_back,
            train_model=True
        )

        if timeframe in results:
            all_signals.append(results[timeframe]['signal'])

    # Ordina per confidence
    all_signals.sort(key=lambda x: x['confidence'], reverse=True)

    return all_signals


def print_summary_table(signals: List[dict]):
    """
    Stampa una tabella riassuntiva di tutti i segnali

    Args:
        signals: Lista di segnali da visualizzare
    """
    print("\n" + "=" * 100)
    print("RIASSUNTO SEGNALI - TOP OPPORTUNITÀ")
    print("=" * 100)
    print(f"{'Simbolo':<12} {'TF':<6} {'Azione':<6} {'Confidence':<12} {'Forza':<10} {'Consenso':<10} {'Prezzo':<15}")
    print("-" * 100)

    for signal in signals:
        action_emoji = {
            'BUY': '🟢',
            'SELL': '🔴',
            'HOLD': '🟡'
        }.get(signal['action'], '⚪')

        print(f"{signal['symbol']:<12} "
              f"{signal['timeframe']:<6} "
              f"{action_emoji} {signal['action']:<6} "
              f"{signal['confidence']:>6.1%}      "
              f"{signal['signal_strength']:<10} "
              f"{signal['consensus']:<10} "
              f"${signal['price']:>12,.2f}")

    print("=" * 100)


def main():
    parser = argparse.ArgumentParser(
        description='AI Trading Analysis - Analizza coppie Binance con intelligenza artificiale'
    )

    parser.add_argument(
        '--symbols',
        nargs='+',
        default=['BTCUSDT'],
        help='Simboli da analizzare (es: BTCUSDT ETHUSDT BNBUSDT)'
    )

    parser.add_argument(
        '--timeframes',
        nargs='+',
        default=['1h'],
        help='Timeframe da analizzare (es: 15m 1h 4h 1d)'
    )

    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Giorni di dati storici da scaricare (default: 30)'
    )

    parser.add_argument(
        '--top',
        type=int,
        default=None,
        help='Analizza i top N simboli per volume (es: --top 20)'
    )

    parser.add_argument(
        '--mode',
        choices=['single', 'multi'],
        default='single',
        help='Modalità: single (un simbolo multi-TF) o multi (multi simboli single-TF)'
    )

    args = parser.parse_args()

    print("=" * 70)
    print(" AI TRADING ANALYSIS SYSTEM - BINANCE")
    print("=" * 70)
    print(f"Modalità: {args.mode}")
    print(f"Simboli: {args.symbols}")
    print(f"Timeframes: {args.timeframes}")
    print(f"Periodo: {args.days} giorni")
    print("=" * 70)

    try:
        if args.top:
            # Ottieni top simboli
            print(f"\nOttenimento top {args.top} simboli per volume...")
            loader = BinanceDataLoader()
            args.symbols = loader.get_top_symbols(limit=args.top)
            print(f"Simboli selezionati: {', '.join(args.symbols[:10])}{'...' if len(args.symbols) > 10 else ''}")

        if args.mode == 'single':
            # Analizza un simbolo su multipli timeframe
            for symbol in args.symbols:
                results = analyze_symbol(
                    symbol,
                    args.timeframes,
                    args.days
                )

                if results:
                    signals = [r['signal'] for r in results.values()]
                    print_summary_table(signals)

        else:  # multi mode
            # Analizza multipli simboli su un timeframe
            timeframe = args.timeframes[0]
            signals = analyze_multiple_symbols(
                args.symbols,
                timeframe,
                args.days
            )

            if signals:
                print_summary_table(signals)

                # Mostra top 5 opportunità
                print("\n" + "=" * 70)
                print("TOP 5 OPPORTUNITÀ")
                print("=" * 70)

                for i, signal in enumerate(signals[:5], 1):
                    if signal['action'] != 'HOLD':
                        print(f"\n{i}. {signal['symbol']} - {signal['action']}")
                        print(f"   Confidence: {signal['confidence']:.1%}")
                        print(f"   Prezzo: ${signal['price']:,.2f}")
                        print(f"   Consenso: {signal['consensus']}")
                        print(f"   Ragione principale: {signal['analysis_details']['rsi']['reason']}")

    except KeyboardInterrupt:
        print("\n\nInterrotto dall'utente.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Errore: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n✅ Analisi completata!\n")


if __name__ == '__main__':
    main()
