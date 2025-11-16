# 📊 Guida allo Screening e Grafici

Guida completa per l'uso del sistema di **screening automatico** e **generazione grafici**.

## 🔍 Screening Automatico

### Uso Base

Scansiona le top 20 coppie per volume:

```bash
python screening_scanner.py
```

### Parametri Disponibili

```bash
python screening_scanner.py \
  --pairs 30 \              # Numero di coppie da scansionare
  --quote USDT \            # Asset di quotazione
  --tf-short 15m \          # Timeframe corto (Delfini)
  --tf-medium 1h \          # Timeframe medio (Squali)
  --tf-long 4h \            # Timeframe lungo (Balene)
  --days 30 \               # Giorni di storico
  --min-confidence 0.5 \    # Confidence minima (0-3)
  --action BUY \            # Filtra solo BUY, SELL o HOLD
  --export \                # Esporta risultati in CSV
  --charts 5 \              # Genera 5 grafici per top opportunità
  --chart-all               # Genera grafico riassuntivo
```

### Esempi Pratici

#### 1. Cerca Solo Opportunità di Acquisto

```bash
python screening_scanner.py --pairs 50 --action BUY --min-confidence 0.8 --charts 3
```

**Cosa fa**:
- Scansiona top 50 coppie
- Filtra solo segnali BUY
- Mostra solo quelli con confidence > 0.8
- Genera grafici per le top 3 opportunità

#### 2. Scan Rapido per Scalping

```bash
python screening_scanner.py \
  --pairs 30 \
  --tf-short 5m \
  --tf-medium 15m \
  --tf-long 1h \
  --days 7 \
  --min-confidence 0.3
```

**Cosa fa**:
- Timeframe corti per scalping
- Solo 7 giorni di dati (più veloce)
- Confidence bassa per più segnali

#### 3. Scan Completo con Export

```bash
python screening_scanner.py \
  --pairs 100 \
  --days 60 \
  --export \
  --chart-all
```

**Cosa fa**:
- Scansiona 100 coppie
- 60 giorni di storico (più accurato)
- Esporta risultati in CSV
- Genera grafico riassuntivo

#### 4. Cerca Opportunità Short

```bash
python screening_scanner.py --pairs 40 --action SELL --charts 5
```

**Cosa fa**:
- Cerca solo segnali SELL (short)
- Genera grafici per top 5

## Output dello Screening

### Report Testuale

```
📋 REPORT SCREENING
================================================================================

Totale coppie analizzate: 20
  🟢 BUY:  7
  🔴 SELL: 4
  🟡 HOLD: 9

================================================================================
#    Simbolo      Azione    Combined    🐬 Delfini   🦈 Squali   🐋 Balene   Prezzo
------------------------------------------------------------------------------------
1    SOLUSDT      🟢 BUY     +1.2341      +0.4521     +0.4103     +0.3717    $98.45
2    ADAUSDT      🟢 BUY     +0.9876      +0.3421     +0.3312     +0.3143    $0.52
3    LINKUSDT     🔴 SELL    -0.8765      -0.3012     -0.2891     -0.2862    $14.23
...
```

### Top Opportunità

```
🌟 TOP 5 OPPORTUNITÀ DI TRADING
================================================================================

1. 🟢 SOLUSDT - BUY
   ======================================================================
   Combined Output:  +1.2341
   Prezzo Corrente:  $98.45
   Trend:            RIALZISTA
   Crossovers:       3
   Segnale:          🟢 INGRESSO LONG - Crossover rialzista 2 bar fa
   Ultimo Crossover: 2 bar fa

   📊 SETUP LONG:
      Entry:      $98.45
      Stop Loss:  $95.50 (-3%)
      Target 1:   $100.42 (+2%)
      Target 2:   $103.37 (+5%)
```

### File CSV

Se usi `--export`, viene generato `screening_results.csv`:

```csv
symbol,combined_output,nn_dolphins,nn_sharks,nn_whales,trend,action,current_price,crossovers_count,bars_since_last_cross,entry_exit_signal,timestamp
SOLUSDT,1.2341,0.4521,0.4103,0.3717,RIALZISTA,BUY,98.45,3,2,🟢 INGRESSO LONG - Crossover rialzista 2 bar fa,2025-11-16 15:30:00
...
```

## 📊 Generazione Grafici

### Grafici Automatici

#### Durante lo Screening

```bash
python screening_scanner.py --pairs 20 --charts 5
```

Genera automaticamente grafici per le top 5 opportunità nella cartella `charts/`.

#### Grafico Riassuntivo

```bash
python screening_scanner.py --chart-all
```

Genera un grafico a barre orizzontali con tutte le coppie ordinate per confidence.

### Grafici Personalizzati

#### Uso Programmatico

```python
from chart_generator import TradingChartGenerator
from neural_network_trader import MultiTimeframeNNTrader

# Setup
trader = MultiTimeframeNNTrader()
chart_gen = TradingChartGenerator()

# Analizza simbolo
results = trader.analyze_multi_timeframe('BTCUSDT', days_back=30)
signals = trader.generate_signals(results)

# Genera grafico rete neurale
chart_gen.plot_neural_network_analysis(
    results,
    signals,
    'BTCUSDT',
    save=True,    # Salva in charts/
    show=True     # Mostra a schermo
)
```

## Tipi di Grafici Generati

### 1. Grafico Rete Neurale Multi-Timeframe

**File**: `{SYMBOL}_nn_analysis.png`

**Contiene**:
- **Panel 1**: Prezzo con crossover evidenziati (frecce verdi/rosse)
- **Panel 2**: Output delle 3 reti neurali (Delfini/Squali/Balene)
- **Panel 3**: Segnale combinato con zone BUY/SELL
- **Panel 4**: Volume

**Quando usarlo**: Per vedere l'analisi completa della rete neurale

### 2. Grafico Indicatori Tecnici

**File**: `{SYMBOL}_indicators.png`

**Contiene**:
- **Panel 1**: Prezzo + Bollinger Bands + Medie Mobili
- **Panel 2**: RSI con zone overbought/oversold
- **Panel 3**: MACD con histogram

**Quando usarlo**: Per confermare i segnali con indicatori tradizionali

### 3. Grafico Screening Riassuntivo

**File**: `screening_results.png`

**Contiene**:
- Barre orizzontali per ogni coppia
- Colore verde (BUY), rosso (SELL), grigio (HOLD)
- Valori combined output e azione

**Quando usarlo**: Per avere una vista d'insieme di tutte le coppie

## 🎯 Strategie di Screening

### Strategia 1: "High Confidence Only"

**Obiettivo**: Solo segnali fortissimi

```bash
python screening_scanner.py \
  --pairs 100 \
  --min-confidence 1.0 \
  --charts 3
```

**Filtri**:
- Combined output > 1.0 o < -1.0
- Solo le coppie con tutti e 3 i timeframe allineati

### Strategia 2: "Quick Scan Intraday"

**Obiettivo**: Opportunità rapide

```bash
python screening_scanner.py \
  --pairs 50 \
  --tf-short 5m \
  --tf-medium 15m \
  --tf-long 1h \
  --days 3 \
  --min-confidence 0.3
```

**Vantaggi**:
- Veloce (solo 3 giorni)
- Timeframe corti per day trading

### Strategia 3: "Deep Swing Scan"

**Obiettivo**: Opportunità swing trading

```bash
python screening_scanner.py \
  --pairs 30 \
  --tf-short 1h \
  --tf-medium 4h \
  --tf-long 1d \
  --days 90 \
  --min-confidence 0.7 \
  --export \
  --chart-all
```

**Vantaggi**:
- Timeframe lunghi per swing
- Storico ampio (90 giorni)
- Export per tracking

### Strategia 4: "Only Fresh Crossovers"

**Obiettivo**: Solo segnali con crossover recente

```python
# Usa Python per filtrare
from screening_scanner import TradingScreener

screener = TradingScreener()
results = screener.screen_top_pairs(n_pairs=50)

# Filtra solo crossover negli ultimi 5 bar
fresh_signals = [
    r for r in results
    if r.get('bars_since_last_cross') is not None
    and r['bars_since_last_cross'] <= 5
]

screener.print_top_opportunities(fresh_signals)
```

## ⚙️ Automazione

### Script Bash per Scan Periodico

Crea `auto_scan.sh`:

```bash
#!/bin/bash

while true; do
    echo "========================================="
    echo "Scan: $(date)"
    echo "========================================="

    python screening_scanner.py \
      --pairs 30 \
      --min-confidence 0.7 \
      --action BUY \
      --export

    echo "Prossimo scan tra 1 ora..."
    sleep 3600
done
```

Esegui:
```bash
chmod +x auto_scan.sh
./auto_scan.sh
```

### Cron Job

Esegui ogni 4 ore:

```bash
# Apri crontab
crontab -e

# Aggiungi
0 */4 * * * cd /path/to/GT && python screening_scanner.py --pairs 50 --export
```

## 📁 Struttura File Generati

```
GT/
├── charts/                    # Grafici generati
│   ├── BTCUSDT_nn_analysis.png
│   ├── ETHUSDT_nn_analysis.png
│   ├── screening_results.png
│   └── ...
├── screening_results.csv      # Export CSV (se --export)
└── ...
```

## 🔧 Tips & Tricks

### 1. Performance

**Problema**: Scan di 100 coppie troppo lento

**Soluzione**:
```bash
# Riduci giorni di storico
python screening_scanner.py --pairs 100 --days 14

# Oppure usa timeframe più lunghi (meno dati)
python screening_scanner.py --pairs 100 --tf-short 1h --tf-medium 4h
```

### 2. Filtrare Risultati

**Problema**: Troppi segnali HOLD

**Soluzione**:
```bash
# Escludi HOLD aumentando confidence minima
python screening_scanner.py --min-confidence 0.5

# Oppure filtra manualmente
python screening_scanner.py --action BUY  # Solo BUY
```

### 3. Grafici Leggibili

**Problema**: Grafici troppo affollati

**Soluzione**:
```bash
# Genera solo per top 3
python screening_scanner.py --charts 3

# Oppure genera solo screening riassuntivo
python screening_scanner.py --chart-all
```

### 4. Export per Excel

```bash
# Genera CSV
python screening_scanner.py --export

# Apri con Excel/Google Sheets
# Ordina per "combined_output" per vedere top opportunità
```

## 📊 Interpretazione Grafici

### Grafico Rete Neurale

**Panel "Output Reti Neurali"**:
- Linee che si muovono insieme → Consensus forte
- Linee divergenti → Timeframe in disaccordo
- Tutte sopra zero → Trend rialzista su tutti TF
- Tutte sotto zero → Trend ribassista su tutti TF

**Panel "Segnale Combinato"**:
- Dentro zona verde (> +0.3) → BUY zone
- Dentro zona rossa (< -0.3) → SELL zone
- Attraversamento zero → Crossover (entry/exit)

**Panel "Prezzo"**:
- Freccia verde (^) → Crossover rialzista = BUY
- Freccia rossa (v) → Crossover ribassista = SELL
- Più crossover recenti → Più opportunità

### Grafico Screening

**Barre verdi lunghe** → Forte segnale BUY
**Barre rosse lunghe** → Forte segnale SELL
**Barre corte** → Segnale debole (evitare)

## ⚠️ Avvertenze

1. **Non fare overtrading**: Non tradare tutte le opportunità, scegli le migliori
2. **Usa stop-loss**: Sempre, anche con confidence alta
3. **Verifica con altri sistemi**: Usa anche AI ML e indicatori tecnici
4. **Backtesting**: Testa la strategia prima di usare soldi reali
5. **Gestione rischio**: Max 2% del capitale per trade

## 📞 Supporto

Per problemi o domande:
- Controlla i log di errore
- Verifica connessione a Binance
- Riduci numero di coppie se timeout

---

**Buon Screening! 📊🚀**
