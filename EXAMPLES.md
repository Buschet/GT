# 📚 Esempi di Utilizzo - AI Trading System

Questa guida contiene esempi pratici di utilizzo del sistema di trading AI.

## 🎯 Scenario 1: Analisi Quick Start

**Obiettivo**: Analisi rapida di BTC ed ETH per trovare opportunità immediate.

```bash
python quick_analysis.py
```

**Output Atteso**:
```
ANALISI RAPIDA: BTCUSDT - 1h
✓ Scaricati 720 candelieri
✓ Calcolati 45 indicatori
✓ Modello addestrato - Accuracy: 68.5%

RACCOMANDAZIONE FINALE
✅ SEGNALE DI ACQUISTO per BTCUSDT
   Confidence: 75.2% (FORTE)
   Prezzo ingresso suggerito: $43,250.00
   Consenso AI + Tecnica: STRONG
```

---

## 🔍 Scenario 2: Analisi Dettagliata Singolo Asset

**Obiettivo**: Analizzare Bitcoin su multipli timeframe per conferma segnale.

```bash
python main.py --symbols BTCUSDT --timeframes 15m 1h 4h 1d --days 60
```

**Quando Usarlo**:
- Vuoi conferma cross-timeframe
- Stai pianificando un trade importante
- Vuoi vedere allineamento tra timeframe brevi e lunghi

**Interpretazione**:
- Se **tutti i timeframe** mostrano BUY → Segnale molto forte
- Se **solo timeframe corti** mostrano BUY → Scalping opportunity
- Se **solo timeframe lunghi** mostrano BUY → Position trading

---

## 📊 Scenario 3: Scansione Mercato Altcoin

**Obiettivo**: Trovare le migliori opportunità tra le top altcoin.

```bash
python main.py --mode multi --symbols ETHUSDT BNBUSDT ADAUSDT SOLUSDT DOTUSDT LINKUSDT MATICUSDT AVAXUSDT --timeframes 1h --days 30
```

**Output**:
```
RIASSUNTO SEGNALI - TOP OPPORTUNITÀ
Symbol       TF     Action  Confidence  Forza      Consenso   Prezzo
-------------------------------------------------------------------------
SOLUSDT      1h     🟢 BUY    82.3%      FORTE      STRONG     $98.45
ADAUSDT      1h     🟢 BUY    71.5%      MODERATO   STRONG     $0.52
LINKUSDT     1h     🟡 HOLD   45.2%      DEBOLE     MODERATE   $14.23
ETHUSDT      1h     🔴 SELL   68.9%      MODERATO   STRONG     $2,245.00
```

**Come Usarlo**:
1. Identifica i simboli con confidence > 70%
2. Verifica che abbiano consenso STRONG
3. Considera solo segnali FORTE o MODERATO
4. Fai ulteriore analisi sui top 3

---

## 🏆 Scenario 4: Top Simboli per Volume

**Obiettivo**: Analizzare automaticamente i 20 asset più scambiati.

```bash
python main.py --mode multi --top 20 --timeframes 4h --days 45
```

**Vantaggi**:
- Scopre opportunità che non avresti considerato
- Si concentra su asset liquidi (più sicuri)
- Ideale per swing trading (timeframe 4h)

**Strategia**:
```bash
# Mattina: Scansione giornaliera
python main.py --mode multi --top 30 --timeframes 1d --days 90

# Pomeriggio: Opportunità intraday
python main.py --mode multi --top 20 --timeframes 1h --days 30
```

---

## ⚡ Scenario 5: Scalping / Day Trading

**Obiettivo**: Identificare setup rapidi per trading giornaliero.

```bash
python main.py --symbols BTCUSDT ETHUSDT --timeframes 5m 15m --days 7
```

**Timeframe Ideali per Scalping**:
- `5m`: Scalping ultra-veloce (5-30 min hold)
- `15m`: Scalping/Day trading (30min-2h hold)

**⚠️ Attenzione**:
- Timeframe brevi = più rumore
- Usa sempre stop-loss stretti
- Conferma con volume alto
- Solo con esperienza

---

## 📈 Scenario 6: Swing Trading

**Obiettivo**: Identificare trend di medio termine.

```bash
python main.py --symbols BTCUSDT ETHUSDT BNBUSDT --timeframes 4h 1d --days 90
```

**Strategia**:
1. Analizza timeframe `1d` per trend generale
2. Usa `4h` per timing di ingresso
3. Se entrambi mostrano BUY → Alta probabilità di successo

**Holding Period**: 3-14 giorni

---

## 🎓 Scenario 7: Uso Programmatico Avanzato

**Obiettivo**: Integrare in un bot personalizzato.

```python
#!/usr/bin/env python3
"""
Bot personalizzato che analizza e notifica segnali forti
"""

from binance_data_loader import BinanceDataLoader
from technical_indicators import TechnicalIndicators
from ai_trading_model import TradingAIModel
from trading_signals import TradingSignals

def scan_and_notify(symbols, timeframe='1h', min_confidence=0.7):
    """Scansiona simboli e notifica segnali forti"""

    loader = BinanceDataLoader()
    strong_signals = []

    for symbol in symbols:
        # Carica dati
        df = loader.get_historical_klines(symbol, timeframe, days_back=30)

        # Calcola indicatori
        indicators = TechnicalIndicators(df)
        df_clean = indicators.add_all_indicators()
        indicators.add_price_patterns()
        df_clean = indicators.get_features_dataframe()

        # AI
        model = TradingAIModel()
        features = indicators.get_feature_names()
        model.train(df_clean, features, forward_periods=5, threshold=0.015)
        prediction = model.predict(df_clean, features)

        # Segnale
        sig_gen = TradingSignals()
        signal = sig_gen.generate_signal(df_clean, prediction, symbol, timeframe)

        # Filtra per confidence
        if signal['confidence'] >= min_confidence and signal['action'] != 'HOLD':
            strong_signals.append(signal)

    # Ordina per confidence
    strong_signals.sort(key=lambda x: x['confidence'], reverse=True)

    # Notifica (qui potresti inviare email, telegram, etc.)
    for sig in strong_signals:
        print(f"🚨 ALERT: {sig['symbol']} - {sig['action']} ({sig['confidence']:.1%})")

    return strong_signals

# Esegui ogni ora
if __name__ == '__main__':
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT']
    signals = scan_and_notify(symbols, timeframe='1h', min_confidence=0.70)
```

**Salva come**: `my_scanner.py`

---

## 🔄 Scenario 8: Monitoraggio Continuo

**Obiettivo**: Scansione periodica del mercato.

**Script Bash** (`scan_loop.sh`):
```bash
#!/bin/bash

echo "Inizio monitoraggio trading..."

while true; do
    clear
    echo "==========================="
    echo "Scansione: $(date)"
    echo "==========================="

    python main.py --mode multi --top 15 --timeframes 1h --days 30

    echo ""
    echo "Prossima scansione tra 1 ora..."
    sleep 3600  # 1 ora
done
```

**Uso**:
```bash
chmod +x scan_loop.sh
./scan_loop.sh
```

---

## 📊 Scenario 9: Analisi Pre-Market

**Obiettivo**: Preparazione giornaliera prima di tradare.

**Morning Routine** (`morning_scan.sh`):
```bash
#!/bin/bash

echo "📊 SCANSIONE MATTUTINA - $(date +%Y-%m-%d)"
echo ""

# 1. Overview mercato principale
echo "1️⃣ MAJOR COINS - Timeframe Giornaliero"
python main.py --symbols BTCUSDT ETHUSDT BNBUSDT --timeframes 1d --days 90
echo ""

# 2. Opportunità intraday
echo "2️⃣ OPPORTUNITÀ INTRADAY - Top 20"
python main.py --mode multi --top 20 --timeframes 4h --days 30
echo ""

# 3. Quick check
echo "3️⃣ QUICK CHECK BTC/ETH"
python quick_analysis.py
echo ""

echo "✅ Scansione completata!"
```

---

## 🎯 Best Practices

### ✅ DO

1. **Conferma Multi-Timeframe**
   ```bash
   # Cerca allineamento tra timeframe
   python main.py --symbols BTCUSDT --timeframes 1h 4h 1d --days 60
   ```

2. **Filtra per Confidence**
   - Solo segnali > 70% per trade reali
   - 60-70% per watchlist
   - < 60% ignora

3. **Verifica Volume**
   - Segnali forti devono avere volume alto
   - Check `volume_ratio > 1.5`

4. **Usa Stop-Loss**
   - Sempre! Non fare trading senza
   - Suggerimento: 2-3% sotto entry per BTC/ETH
   - 3-5% per altcoin più volatili

### ❌ DON'T

1. **Non tradare segnali CONFLICT**
   ```
   Consenso: CONFLICT  ← ⚠️ EVITA!
   ```

2. **Non tradare con bassa confidence**
   ```
   Confidence: 45% ← ⚠️ TROPPO BASSO
   ```

3. **Non fare overtrading**
   - Non tradare ogni segnale
   - Aspetta setup perfetti
   - Qualità > Quantità

4. **Non ignorare il trend generale**
   - Controlla sempre timeframe 1d
   - Non andare contro trend forte

---

## 📱 Integrazioni Possibili

### Telegram Bot
```python
# Invia notifiche Telegram
import requests

def send_telegram(message):
    token = "YOUR_BOT_TOKEN"
    chat_id = "YOUR_CHAT_ID"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, data={'chat_id': chat_id, 'text': message})

# Dopo ogni segnale forte
if signal['confidence'] > 0.75:
    send_telegram(f"🚨 {signal['symbol']}: {signal['action']} - {signal['confidence']:.1%}")
```

### Discord Webhook
```python
import requests

def send_discord(webhook_url, message):
    data = {"content": message}
    requests.post(webhook_url, json=data)
```

---

## 🆘 Troubleshooting Esempi

### Problema: "Dati insufficienti"
```bash
# Soluzione: Aumenta --days
python main.py --symbols BTCUSDT --timeframes 1d --days 120  # invece di 30
```

### Problema: Troppo lento
```bash
# Soluzione: Riduci numero simboli o usa timeframe più lunghi
python main.py --top 10 --timeframes 4h  # invece di --top 50 --timeframes 5m
```

### Problema: Troppi segnali HOLD
```bash
# Possibili cause:
# 1. Mercato laterale (normale)
# 2. Threshold troppo conservativo
# 3. Timeframe non adatto

# Soluzione: Prova timeframe diverso
python main.py --symbols BTCUSDT --timeframes 15m  # invece di 1d
```

---

## 📈 Strategie Complete

### Strategia 1: "Conservative Long-Term"
```bash
# Ogni domenica sera
python main.py --symbols BTCUSDT ETHUSDT --timeframes 1w --days 365

# Solo BUY con confidence > 80% e consenso STRONG
# Holding: settimane/mesi
```

### Strategia 2: "Aggressive Day Trading"
```bash
# Ogni mattina
python main.py --mode multi --top 30 --timeframes 15m --days 14

# BUY/SELL con confidence > 65%
# Multiple operazioni giornaliere
# Stop-loss stretto (1-2%)
```

### Strategia 3: "Balanced Swing"
```bash
# Ogni 2-3 giorni
python main.py --mode multi --top 20 --timeframes 4h 1d --days 60

# Solo quando 4h e 1d sono allineati
# Confidence > 70%
# Holding: 3-10 giorni
```

---

**Ricorda**: Questi sono solo esempi. Adatta alle tue esigenze e **sempre** con gestione del rischio appropriata! 🎯
