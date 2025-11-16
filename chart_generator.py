"""
Modulo per generare grafici del sistema di trading
Visualizza output rete neurale, indicatori tecnici e segnali
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import pandas as pd
import numpy as np
from typing import Dict, Optional, List
import os


class TradingChartGenerator:
    """
    Generatore di grafici per analisi trading
    """

    def __init__(self, output_dir: str = 'charts'):
        """
        Inizializza il generatore di grafici

        Args:
            output_dir: Directory dove salvare i grafici
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Stile grafici
        plt.style.use('seaborn-v0_8-darkgrid')

    def plot_neural_network_analysis(
        self,
        results: Dict[str, pd.DataFrame],
        signals: Dict,
        symbol: str,
        save: bool = True,
        show: bool = True
    ) -> Optional[str]:
        """
        Crea grafico completo dell'analisi rete neurale multi-timeframe

        Args:
            results: Risultati dall'analisi multi-timeframe
            signals: Segnali generati
            symbol: Simbolo della coppia
            save: Se True, salva il grafico
            show: Se True, mostra il grafico

        Returns:
            Path del file salvato (se save=True)
        """
        # Crea figura con subplots
        fig = plt.figure(figsize=(16, 12))
        gs = fig.add_gridspec(4, 1, height_ratios=[3, 1, 1, 1], hspace=0.3)

        # Usa i dati del timeframe medio (Squali) come riferimento
        df = results['sharks'].copy()

        # Subplot 1: Prezzo + Crossover
        ax1 = fig.add_subplot(gs[0])
        self._plot_price_with_crossovers(ax1, df, signals, symbol)

        # Subplot 2: Output Rete Neurale
        ax2 = fig.add_subplot(gs[1], sharex=ax1)
        self._plot_nn_outputs(ax2, results)

        # Subplot 3: Combined Signal
        ax3 = fig.add_subplot(gs[2], sharex=ax1)
        self._plot_combined_signal(ax3, results)

        # Subplot 4: Volume
        ax4 = fig.add_subplot(gs[3], sharex=ax1)
        self._plot_volume(ax4, df)

        # Titolo generale
        fig.suptitle(
            f'Analisi Rete Neurale Multi-Timeframe - {symbol}\n'
            f'Trend: {signals["trend"]} | Azione: {signals["action"]} | '
            f'Combined: {signals["combined_output"]:.4f}',
            fontsize=16,
            fontweight='bold'
        )

        plt.tight_layout()

        # Salva
        filepath = None
        if save:
            filename = f'{symbol}_nn_analysis.png'
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            print(f"✅ Grafico salvato: {filepath}")

        # Mostra
        if show:
            plt.show()
        else:
            plt.close()

        return filepath

    def _plot_price_with_crossovers(self, ax, df, signals, symbol):
        """Plotta prezzo con evidenziati i crossover"""
        # Prezzo
        ax.plot(df.index, df['close'], label='Prezzo', linewidth=2, color='blue')

        # EMA per contesto
        if 'ema_21' in df.columns:
            ax.plot(df.index, df['ema_21'], label='EMA 21', alpha=0.5, linestyle='--', color='orange')

        # Bollinger Bands se disponibili
        if 'bb_upper' in df.columns and 'bb_lower' in df.columns:
            ax.fill_between(
                df.index,
                df['bb_upper'],
                df['bb_lower'],
                alpha=0.1,
                color='gray',
                label='Bollinger Bands'
            )

        # Evidenzia crossover
        if signals.get('crossovers'):
            for cross in signals['crossovers'][-10:]:  # Ultimi 10
                idx = cross['index']
                if idx < len(df):
                    timestamp = df.index[idx]
                    price = cross['price']

                    if cross['type'] == 'BULLISH_CROSS':
                        ax.scatter(timestamp, price, color='green', s=200, marker='^',
                                 zorder=5, edgecolors='darkgreen', linewidths=2)
                        ax.annotate('BUY', xy=(timestamp, price),
                                  xytext=(0, 20), textcoords='offset points',
                                  fontsize=10, color='green', fontweight='bold',
                                  ha='center')
                    else:
                        ax.scatter(timestamp, price, color='red', s=200, marker='v',
                                 zorder=5, edgecolors='darkred', linewidths=2)
                        ax.annotate('SELL', xy=(timestamp, price),
                                  xytext=(0, -30), textcoords='offset points',
                                  fontsize=10, color='red', fontweight='bold',
                                  ha='center')

        ax.set_ylabel('Prezzo (USD)', fontsize=12, fontweight='bold')
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        ax.set_title(f'{symbol} - Prezzo con Segnali Entry/Exit', fontsize=14)

    def _plot_nn_outputs(self, ax, results):
        """Plotta gli output delle 3 reti neurali"""
        # Sincronizza gli indici (usa il più corto)
        min_len = min(len(results['dolphins']), len(results['sharks']), len(results['whales']))

        df_d = results['dolphins'].iloc[-min_len:]
        df_s = results['sharks'].iloc[-min_len:]
        df_w = results['whales'].iloc[-min_len:]

        # Plotta
        ax.plot(df_d.index, df_d['nn_output'], label='🐬 Delfini', linewidth=2, color='cyan')
        ax.plot(df_s.index, df_s['nn_output'], label='🦈 Squali', linewidth=2, color='blue')
        ax.plot(df_w.index, df_w['nn_output'], label='🐋 Balene', linewidth=2, color='navy')

        # Linea zero
        ax.axhline(y=0, color='black', linestyle='-', linewidth=1, alpha=0.5)

        # Zone di overbought/oversold
        ax.axhline(y=0.5, color='green', linestyle='--', linewidth=1, alpha=0.3)
        ax.axhline(y=-0.5, color='red', linestyle='--', linewidth=1, alpha=0.3)

        # Riempi zone
        ax.fill_between(df_d.index, 0, 1, where=(df_d['nn_output'] > 0),
                       alpha=0.1, color='green', interpolate=True)
        ax.fill_between(df_d.index, 0, -1, where=(df_d['nn_output'] < 0),
                       alpha=0.1, color='red', interpolate=True)

        ax.set_ylabel('Output NN', fontsize=12, fontweight='bold')
        ax.set_ylim(-1.1, 1.1)
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        ax.set_title('Output Reti Neurali (Delfini/Squali/Balene)', fontsize=14)

    def _plot_combined_signal(self, ax, results):
        """Plotta il segnale combinato"""
        min_len = min(len(results['dolphins']), len(results['sharks']), len(results['whales']))

        df_d = results['dolphins'].iloc[-min_len:]
        df_s = results['sharks'].iloc[-min_len:]
        df_w = results['whales'].iloc[-min_len:]

        # Calcola combined
        combined = df_d['nn_output'] + df_s['nn_output'] + df_w['nn_output']

        # Plotta
        ax.plot(df_d.index, combined, label='Combined', linewidth=2.5, color='purple')

        # Linea zero
        ax.axhline(y=0, color='black', linestyle='-', linewidth=1, alpha=0.5)

        # Soglie
        ax.axhline(y=0.3, color='green', linestyle='--', linewidth=1, alpha=0.5, label='Soglia BUY')
        ax.axhline(y=-0.3, color='red', linestyle='--', linewidth=1, alpha=0.5, label='Soglia SELL')

        # Riempi zone
        ax.fill_between(df_d.index, 0, 3, where=(combined > 0.3),
                       alpha=0.2, color='green', interpolate=True, label='Zona BUY')
        ax.fill_between(df_d.index, 0, -3, where=(combined < -0.3),
                       alpha=0.2, color='red', interpolate=True, label='Zona SELL')

        ax.set_ylabel('Combined Output', fontsize=12, fontweight='bold')
        ax.set_ylim(-3.5, 3.5)
        ax.legend(loc='upper left', fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.set_title('Segnale Combinato (Somma 3 NN)', fontsize=14)

    def _plot_volume(self, ax, df):
        """Plotta il volume"""
        colors = ['green' if df['close'].iloc[i] >= df['open'].iloc[i] else 'red'
                 for i in range(len(df))]

        ax.bar(df.index, df['volume'], color=colors, alpha=0.5, width=0.8)
        ax.set_ylabel('Volume', fontsize=12, fontweight='bold')
        ax.set_xlabel('Data', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_title('Volume', fontsize=14)

        # Formatta asse x
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    def plot_indicators_analysis(
        self,
        df: pd.DataFrame,
        symbol: str,
        save: bool = True,
        show: bool = True
    ) -> Optional[str]:
        """
        Crea grafico con indicatori tecnici

        Args:
            df: DataFrame con indicatori calcolati
            symbol: Simbolo della coppia
            save: Se True, salva il grafico
            show: Se True, mostra il grafico

        Returns:
            Path del file salvato
        """
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(3, 1, height_ratios=[2, 1, 1], hspace=0.3)

        # Subplot 1: Prezzo + Bollinger Bands + MA
        ax1 = fig.add_subplot(gs[0])
        ax1.plot(df.index, df['close'], label='Prezzo', linewidth=2, color='blue')

        if 'bb_upper' in df.columns:
            ax1.plot(df.index, df['bb_upper'], label='BB Superior', linestyle='--', color='red', alpha=0.5)
            ax1.plot(df.index, df['bb_middle'], label='BB Media', linestyle='--', color='gray', alpha=0.5)
            ax1.plot(df.index, df['bb_lower'], label='BB Inferior', linestyle='--', color='green', alpha=0.5)
            ax1.fill_between(df.index, df['bb_upper'], df['bb_lower'], alpha=0.1, color='gray')

        if 'ema_21' in df.columns:
            ax1.plot(df.index, df['ema_21'], label='EMA 21', linestyle='--', color='orange')

        if 'sma_50' in df.columns:
            ax1.plot(df.index, df['sma_50'], label='SMA 50', linestyle='--', color='purple')

        ax1.set_ylabel('Prezzo (USD)', fontsize=12, fontweight='bold')
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)
        ax1.set_title(f'{symbol} - Prezzo e Medie Mobili', fontsize=14)

        # Subplot 2: RSI
        ax2 = fig.add_subplot(gs[1], sharex=ax1)
        if 'rsi' in df.columns:
            ax2.plot(df.index, df['rsi'], label='RSI', linewidth=2, color='purple')
            ax2.axhline(y=70, color='red', linestyle='--', linewidth=1, alpha=0.5, label='Overbought')
            ax2.axhline(y=30, color='green', linestyle='--', linewidth=1, alpha=0.5, label='Oversold')
            ax2.fill_between(df.index, 70, 100, alpha=0.1, color='red')
            ax2.fill_between(df.index, 0, 30, alpha=0.1, color='green')

        ax2.set_ylabel('RSI', fontsize=12, fontweight='bold')
        ax2.set_ylim(0, 100)
        ax2.legend(loc='upper left')
        ax2.grid(True, alpha=0.3)
        ax2.set_title('Relative Strength Index (RSI)', fontsize=14)

        # Subplot 3: MACD
        ax3 = fig.add_subplot(gs[2], sharex=ax1)
        if 'macd' in df.columns and 'macd_signal' in df.columns:
            ax3.plot(df.index, df['macd'], label='MACD', linewidth=2, color='blue')
            ax3.plot(df.index, df['macd_signal'], label='Signal', linewidth=2, color='red')

            if 'macd_diff' in df.columns:
                colors = ['green' if x > 0 else 'red' for x in df['macd_diff']]
                ax3.bar(df.index, df['macd_diff'], color=colors, alpha=0.3, label='Histogram')

            ax3.axhline(y=0, color='black', linestyle='-', linewidth=1, alpha=0.5)

        ax3.set_ylabel('MACD', fontsize=12, fontweight='bold')
        ax3.set_xlabel('Data', fontsize=12, fontweight='bold')
        ax3.legend(loc='upper left')
        ax3.grid(True, alpha=0.3)
        ax3.set_title('MACD', fontsize=14)

        # Formatta asse x
        ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right')

        fig.suptitle(f'Indicatori Tecnici - {symbol}', fontsize=16, fontweight='bold')
        plt.tight_layout()

        filepath = None
        if save:
            filename = f'{symbol}_indicators.png'
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            print(f"✅ Grafico indicatori salvato: {filepath}")

        if show:
            plt.show()
        else:
            plt.close()

        return filepath

    def plot_screening_results(
        self,
        screening_results: List[Dict],
        save: bool = True,
        show: bool = True
    ) -> Optional[str]:
        """
        Crea grafico con risultati dello screening

        Args:
            screening_results: Lista di risultati screening
            save: Se True, salva il grafico
            show: Se True, mostra il grafico

        Returns:
            Path del file salvato
        """
        if not screening_results:
            print("⚠️  Nessun risultato da visualizzare")
            return None

        # Prepara dati
        symbols = [r['symbol'] for r in screening_results[:20]]  # Top 20
        combined = [r['combined_output'] for r in screening_results[:20]]
        actions = [r['action'] for r in screening_results[:20]]

        # Colori basati sull'azione
        colors = ['green' if a == 'BUY' else 'red' if a == 'SELL' else 'gray' for a in actions]

        # Crea figura
        fig, ax = plt.subplots(figsize=(14, 8))

        # Barre orizzontali
        y_pos = np.arange(len(symbols))
        bars = ax.barh(y_pos, combined, color=colors, alpha=0.7)

        # Linea zero
        ax.axvline(x=0, color='black', linestyle='-', linewidth=2)
        ax.axvline(x=0.3, color='green', linestyle='--', linewidth=1, alpha=0.5, label='Soglia BUY')
        ax.axvline(x=-0.3, color='red', linestyle='--', linewidth=1, alpha=0.5, label='Soglia SELL')

        # Etichette
        ax.set_yticks(y_pos)
        ax.set_yticklabels(symbols)
        ax.set_xlabel('Combined NN Output', fontsize=12, fontweight='bold')
        ax.set_ylabel('Simbolo', fontsize=12, fontweight='bold')
        ax.set_title('Screening Multi-Coppia - Top Opportunità', fontsize=16, fontweight='bold')

        # Aggiungi valori sulle barre
        for i, (bar, val, action) in enumerate(zip(bars, combined, actions)):
            label = f'{val:.2f} ({action})'
            x_pos = val + (0.1 if val > 0 else -0.1)
            ha = 'left' if val > 0 else 'right'
            ax.text(x_pos, bar.get_y() + bar.get_height()/2, label,
                   ha=ha, va='center', fontsize=9, fontweight='bold')

        ax.legend()
        ax.grid(True, alpha=0.3, axis='x')
        plt.tight_layout()

        filepath = None
        if save:
            filename = 'screening_results.png'
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            print(f"✅ Grafico screening salvato: {filepath}")

        if show:
            plt.show()
        else:
            plt.close()

        return filepath


# Test del modulo
if __name__ == '__main__':
    from binance_data_loader import BinanceDataLoader
    from neural_network_trader import MultiTimeframeNNTrader
    from technical_indicators import TechnicalIndicators

    print("=" * 80)
    print("TEST: Generazione Grafici")
    print("=" * 80)

    # Carica dati
    loader = BinanceDataLoader()
    trader = MultiTimeframeNNTrader()

    # Analizza BTC
    results = trader.analyze_multi_timeframe('BTCUSDT', days_back=30)
    signals = trader.generate_signals(results)

    # Genera grafici
    chart_gen = TradingChartGenerator()

    # Grafico rete neurale
    chart_gen.plot_neural_network_analysis(results, signals, 'BTCUSDT', show=False)

    # Grafico indicatori
    df = results['sharks']
    indicators = TechnicalIndicators(df)
    df_with_ind = indicators.add_all_indicators()
    chart_gen.plot_indicators_analysis(df_with_ind, 'BTCUSDT', show=False)

    print("\n✅ Grafici generati con successo nella cartella 'charts/'")
