#!/usr/bin/env python3
"""
Sistema di Screening Automatico Multi-Coppia
Scansiona le top coppie e identifica le migliori opportunità di trading
"""

import argparse
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime
from binance_data_loader import BinanceDataLoader
from neural_network_trader import MultiTimeframeNNTrader
from chart_generator import TradingChartGenerator
import time


class TradingScreener:
    """
    Scanner automatico per identificare opportunità di trading
    """

    def __init__(self):
        self.loader = BinanceDataLoader()
        self.nn_trader = MultiTimeframeNNTrader()
        self.chart_gen = TradingChartGenerator()

    def screen_top_pairs(
        self,
        n_pairs: int = 20,
        quote_asset: str = 'USDT',
        tf_short: str = '15m',
        tf_medium: str = '1h',
        tf_long: str = '4h',
        days_back: int = 30,
        min_confidence: float = 0.0,
        actions_filter: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Scansiona le top N coppie per volume

        Args:
            n_pairs: Numero di coppie da scansionare
            quote_asset: Asset di quotazione (default: USDT)
            tf_short: Timeframe corto
            tf_medium: Timeframe medio
            tf_long: Timeframe lungo
            days_back: Giorni di storico
            min_confidence: Confidence minima (0-3)
            actions_filter: Lista azioni da includere ['BUY', 'SELL', 'HOLD']

        Returns:
            Lista di risultati ordinati per confidence
        """
        print("\n" + "🔍 " * 40)
        print("SCREENING AUTOMATICO COPPIE")
        print("🔍 " * 40)

        # Ottieni top simboli
        print(f"\n📊 Ottenimento top {n_pairs} simboli per volume...")
        symbols = self.loader.get_top_symbols(quote_asset=quote_asset, limit=n_pairs)
        print(f"✅ Simboli ottenuti: {len(symbols)}")

        results = []
        total = len(symbols)

        for idx, symbol in enumerate(symbols, 1):
            print(f"\n{'=' * 80}")
            print(f"[{idx}/{total}] Analizzando: {symbol}")
            print(f"{'=' * 80}")

            try:
                # Analizza con rete neurale
                nn_results = self.nn_trader.analyze_multi_timeframe(
                    symbol,
                    tf_dolphins=tf_short,
                    tf_sharks=tf_medium,
                    tf_whales=tf_long,
                    days_back=days_back
                )

                # Genera segnali
                signals = self.nn_trader.generate_signals(nn_results, lookback=30)

                # Aggiungi a risultati
                result = {
                    'symbol': symbol,
                    'combined_output': signals['combined_output'],
                    'nn_dolphins': signals['nn_dolphins'],
                    'nn_sharks': signals['nn_sharks'],
                    'nn_whales': signals['nn_whales'],
                    'trend': signals['trend'],
                    'action': signals['action'],
                    'current_price': signals['current_price'],
                    'crossovers_count': signals['total_crossovers'],
                    'bars_since_last_cross': signals.get('bars_since_last_cross'),
                    'entry_exit_signal': signals.get('entry_exit_signal'),
                    'timestamp': datetime.now()
                }

                results.append(result)

                # Mostra risultato
                action_emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '🟡'}.get(result['action'], '⚪')
                print(f"{action_emoji} {result['action']:<6} | "
                      f"Combined: {result['combined_output']:+.4f} | "
                      f"Prezzo: ${result['current_price']:,.2f}")

                # Pausa per evitare rate limiting
                time.sleep(0.5)

            except Exception as e:
                print(f"❌ Errore nell'analisi di {symbol}: {str(e)}")
                continue

        # Filtra per confidence
        if min_confidence > 0:
            results = [r for r in results if abs(r['combined_output']) >= min_confidence]

        # Filtra per azione
        if actions_filter:
            results = [r for r in results if r['action'] in actions_filter]

        # Ordina per confidence (valore assoluto del combined output)
        results.sort(key=lambda x: abs(x['combined_output']), reverse=True)

        return results

    def print_screening_report(self, results: List[Dict]):
        """
        Stampa report dello screening

        Args:
            results: Lista risultati screening
        """
        if not results:
            print("\n⚠️  Nessun risultato trovato con i filtri specificati")
            return

        print("\n" + "=" * 100)
        print("📋 REPORT SCREENING")
        print("=" * 100)

        print(f"\nTotale coppie analizzate: {len(results)}")

        # Conta azioni
        buy_count = sum(1 for r in results if r['action'] == 'BUY')
        sell_count = sum(1 for r in results if r['action'] == 'SELL')
        hold_count = sum(1 for r in results if r['action'] == 'HOLD')

        print(f"  🟢 BUY:  {buy_count}")
        print(f"  🔴 SELL: {sell_count}")
        print(f"  🟡 HOLD: {hold_count}")

        # Tabella risultati
        print("\n" + "=" * 100)
        print(f"{'#':<4} {'Simbolo':<12} {'Azione':<8} {'Combined':<12} {'🐬 Delfini':<12} "
              f"{'🦈 Squali':<12} {'🐋 Balene':<12} {'Prezzo':<15}")
        print("-" * 100)

        for idx, r in enumerate(results[:30], 1):  # Top 30
            action_emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '🟡'}.get(r['action'], '⚪')

            print(f"{idx:<4} {r['symbol']:<12} "
                  f"{action_emoji} {r['action']:<6} "
                  f"{r['combined_output']:+.4f}      "
                  f"{r['nn_dolphins']:+.4f}      "
                  f"{r['nn_sharks']:+.4f}      "
                  f"{r['nn_whales']:+.4f}      "
                  f"${r['current_price']:>12,.2f}")

        print("=" * 100)

    def print_top_opportunities(self, results: List[Dict], top_n: int = 5):
        """
        Stampa le top N opportunità

        Args:
            results: Lista risultati
            top_n: Numero di opportunità da mostrare
        """
        # Filtra per BUY o SELL (esclude HOLD)
        opportunities = [r for r in results if r['action'] != 'HOLD']

        if not opportunities:
            print("\n⚠️  Nessuna opportunità trovata (tutti HOLD)")
            return

        print("\n" + "🌟 " * 40)
        print(f"TOP {min(top_n, len(opportunities))} OPPORTUNITÀ DI TRADING")
        print("🌟 " * 40)

        for idx, opp in enumerate(opportunities[:top_n], 1):
            action_emoji = '🟢' if opp['action'] == 'BUY' else '🔴'

            print(f"\n{idx}. {action_emoji} {opp['symbol']} - {opp['action']}")
            print(f"   {'=' * 70}")
            print(f"   Combined Output:  {opp['combined_output']:+.4f}")
            print(f"   Prezzo Corrente:  ${opp['current_price']:,.2f}")
            print(f"   Trend:            {opp['trend']}")
            print(f"   Crossovers:       {opp['crossovers_count']}")

            if opp['entry_exit_signal']:
                print(f"   Segnale:          {opp['entry_exit_signal']}")

            if opp['bars_since_last_cross'] is not None:
                print(f"   Ultimo Crossover: {opp['bars_since_last_cross']} bar fa")

            # Calcola livelli entry/stop/target
            price = opp['current_price']
            if opp['action'] == 'BUY':
                stop_loss = price * 0.97
                target1 = price * 1.02
                target2 = price * 1.05
                print(f"\n   📊 SETUP LONG:")
                print(f"      Entry:      ${price:,.2f}")
                print(f"      Stop Loss:  ${stop_loss:,.2f} (-3%)")
                print(f"      Target 1:   ${target1:,.2f} (+2%)")
                print(f"      Target 2:   ${target2:,.2f} (+5%)")
            else:
                stop_loss = price * 1.03
                target1 = price * 0.98
                target2 = price * 0.95
                print(f"\n   📊 SETUP SHORT:")
                print(f"      Entry:      ${price:,.2f}")
                print(f"      Stop Loss:  ${stop_loss:,.2f} (+3%)")
                print(f"      Target 1:   ${target1:,.2f} (-2%)")
                print(f"      Target 2:   ${target2:,.2f} (-5%)")

        print("\n" + "=" * 80)

    def export_to_csv(self, results: List[Dict], filename: str = 'screening_results.csv'):
        """
        Esporta risultati in CSV

        Args:
            results: Lista risultati
            filename: Nome file CSV
        """
        if not results:
            print("⚠️  Nessun risultato da esportare")
            return

        df = pd.DataFrame(results)
        df.to_csv(filename, index=False)
        print(f"✅ Risultati esportati in: {filename}")

    def generate_screening_charts(self, results: List[Dict], top_n: int = 5):
        """
        Genera grafici per le top N opportunità

        Args:
            results: Lista risultati
            top_n: Numero di grafici da generare
        """
        print(f"\n📊 Generazione grafici per top {top_n} opportunità...")

        opportunities = [r for r in results if r['action'] != 'HOLD'][:top_n]

        for idx, opp in enumerate(opportunities, 1):
            print(f"\n[{idx}/{len(opportunities)}] Generando grafico per {opp['symbol']}...")

            try:
                # Rianalizza per ottenere tutti i dati necessari
                nn_results = self.nn_trader.analyze_multi_timeframe(
                    opp['symbol'],
                    days_back=30
                )
                signals = self.nn_trader.generate_signals(nn_results)

                # Genera grafico
                self.chart_gen.plot_neural_network_analysis(
                    nn_results,
                    signals,
                    opp['symbol'],
                    save=True,
                    show=False
                )

            except Exception as e:
                print(f"❌ Errore nella generazione grafico per {opp['symbol']}: {e}")

        print("\n✅ Grafici generati nella cartella 'charts/'")


def main():
    parser = argparse.ArgumentParser(
        description='Screening Automatico Coppie di Trading con Rete Neurale'
    )

    parser.add_argument(
        '--pairs',
        type=int,
        default=20,
        help='Numero di coppie da scansionare (default: 20)'
    )

    parser.add_argument(
        '--quote',
        default='USDT',
        help='Asset di quotazione (default: USDT)'
    )

    parser.add_argument(
        '--tf-short',
        default='15m',
        help='Timeframe corto (default: 15m)'
    )

    parser.add_argument(
        '--tf-medium',
        default='1h',
        help='Timeframe medio (default: 1h)'
    )

    parser.add_argument(
        '--tf-long',
        default='4h',
        help='Timeframe lungo (default: 4h)'
    )

    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Giorni di storico (default: 30)'
    )

    parser.add_argument(
        '--min-confidence',
        type=float,
        default=0.5,
        help='Confidence minima per filtrare (default: 0.5)'
    )

    parser.add_argument(
        '--action',
        choices=['BUY', 'SELL', 'HOLD', 'ALL'],
        default='ALL',
        help='Filtra per azione (default: ALL)'
    )

    parser.add_argument(
        '--export',
        action='store_true',
        help='Esporta risultati in CSV'
    )

    parser.add_argument(
        '--charts',
        type=int,
        default=0,
        help='Numero di grafici da generare per top opportunità (default: 0)'
    )

    parser.add_argument(
        '--chart-all',
        action='store_true',
        help='Genera grafico riassuntivo di tutti i risultati'
    )

    args = parser.parse_args()

    # Inizializza screener
    screener = TradingScreener()

    # Prepara filtro azioni
    actions_filter = None if args.action == 'ALL' else [args.action]

    # Esegui screening
    results = screener.screen_top_pairs(
        n_pairs=args.pairs,
        quote_asset=args.quote,
        tf_short=args.tf_short,
        tf_medium=args.tf_medium,
        tf_long=args.tf_long,
        days_back=args.days,
        min_confidence=args.min_confidence,
        actions_filter=actions_filter
    )

    # Stampa report
    screener.print_screening_report(results)

    # Top opportunità
    screener.print_top_opportunities(results, top_n=5)

    # Esporta CSV
    if args.export:
        screener.export_to_csv(results)

    # Genera grafici
    if args.charts > 0:
        screener.generate_screening_charts(results, top_n=args.charts)

    # Grafico riassuntivo
    if args.chart_all and results:
        screener.chart_gen.plot_screening_results(results, show=False)

    print("\n✅ Screening completato!\n")


if __name__ == '__main__':
    main()
