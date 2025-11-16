# 🤖 AI Trading Analysis System - Binance

Sistema di analisi trading avanzato che combina **Intelligenza Artificiale** e **Analisi Tecnica** per generare segnali di acquisto/vendita su coppie di trading Binance.

## 🌟 Caratteristiche Principali

- 📊 **Scaricamento Dati Automatico** da Binance per qualsiasi coppia di trading
- ⏱️ **Supporto Multi-Timeframe**: 1m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d, 1w, 1M
- 📈 **30+ Indicatori Tecnici**: RSI, MACD, Bollinger Bands, Medie Mobili, ATR, OBV, Stochastic e altri
- 🤖 **Machine Learning**: Random Forest e Gradient Boosting per predizioni AI
- 🎯 **Segnali di Trading Intelligenti**: Combina AI e analisi tecnica tradizionale
- 📊 **Confidence Score**: Ogni segnale include un punteggio di fiducia
- 🔍 **Analisi Multi-Simbolo**: Analizza contemporaneamente multiple coppie

## 📋 Requisiti

- Python 3.8+
- Connessione Internet (per scaricare dati da Binance)
- (Opzionale) API Key Binance per funzionalità avanzate

## 🚀 Installazione

### 1. Clona il Repository

```bash
git clone <repository-url>
cd GT
```

### 2. Installa le Dipendenze

```bash
pip install -r requirements.txt
```

### 3. (Opzionale) Configura API Binance

Se hai un account Binance, puoi configurare le API keys:

```bash
cp .env.example .env
# Modifica .env e inserisci le tue chiavi API
```

**Nota**: Le API keys NON sono necessarie per scaricare dati pubblici di mercato.

## 📖 Guida Rapida

### Analisi Veloce (Quick Start)

Per una analisi rapida di BTC e ETH:

```bash
python quick_analysis.py
```

Questo script:
- Scarica dati storici
- Calcola indicatori tecnici
- Addestra il modello AI
- Genera segnali di trading
- Confronta BTC vs ETH

### Analisi Personalizzata

#### Analizza un singolo simbolo

```bash
python main.py --symbols BTCUSDT --timeframes 1h 4h 1d --days 30
```

#### Analizza multiple coppie

```bash
python main.py --mode multi --symbols BTCUSDT ETHUSDT BNBUSDT --timeframes 1h --days 30
```

#### Analizza i top 20 simboli per volume

```bash
python main.py --mode multi --top 20 --timeframes 4h --days 30
```

## 🎮 Esempi di Utilizzo

### Esempio 1: Analisi BTC su Timeframe Multipli

```bash
python main.py --symbols BTCUSDT --timeframes 15m 1h 4h 1d --days 60
```

Output:
```
RACCOMANDAZIONE: BUY
Confidence: 78.5% (FORTE)
Consenso: STRONG
Prezzo attuale: $43,250.00
```

### Esempio 2: Scansione Top Altcoin

```bash
python main.py --mode multi --top 30 --timeframes 1h --days 30
```

Mostra una tabella con tutti i segnali ordinati per confidence.

### Esempio 3: Uso Programmatico

```python
from binance_data_loader import BinanceDataLoader
from technical_indicators import TechnicalIndicators
from ai_trading_model import TradingAIModel
from trading_signals import TradingSignals

# Setup
loader = BinanceDataLoader()
df = loader.get_historical_klines('BTCUSDT', '1h', days_back=30)

# Calcola indicatori
indicators = TechnicalIndicators(df)
df_with_indicators = indicators.add_all_indicators()
indicators.add_price_patterns()
df_clean = indicators.get_features_dataframe()

# Addestra modello
model = TradingAIModel()
feature_cols = indicators.get_feature_names()
model.train(df_clean, feature_cols)

# Predizione
ai_prediction = model.predict(df_clean, feature_cols)

# Genera segnale
signal_gen = TradingSignals()
signal = signal_gen.generate_signal(df_clean, ai_prediction, 'BTCUSDT', '1h')

print(f"Azione: {signal['action']}")
print(f"Confidence: {signal['confidence']:.1%}")
```

## 📊 Struttura del Progetto

```
GT/
├── binance_data_loader.py      # Scaricamento dati da Binance
├── technical_indicators.py     # Calcolo indicatori tecnici
├── ai_trading_model.py         # Modelli di Machine Learning
├── trading_signals.py          # Sistema di generazione segnali
├── main.py                     # Script principale
├── quick_analysis.py           # Script analisi rapida
├── requirements.txt            # Dipendenze Python
├── .env.example               # Template configurazione
└── README.md                  # Questa documentazione
```

## 🔧 Moduli Principali

### 1. BinanceDataLoader

Gestisce lo scaricamento dati da Binance.

**Funzionalità**:
- Scarica dati storici OHLCV
- Supporta tutti i timeframe Binance
- Gestisce automaticamente rate limiting
- Ottiene prezzi correnti
- Identifica simboli top per volume

### 2. TechnicalIndicators

Calcola indicatori tecnici sui dati.

**Indicatori Implementati**:
- **Trend**: SMA, EMA (7, 14, 21, 50, 100, 200 periodi), MACD
- **Momentum**: RSI, Stochastic Oscillator
- **Volatilità**: Bollinger Bands, ATR
- **Volume**: OBV, Volume Ratio, VWAP
- **Pattern**: Candle patterns, momentum

### 3. TradingAIModel

Modelli di machine learning per predizioni.

**Caratteristiche**:
- **Random Forest Classifier**: 100 alberi, ottimizzato per trading
- **Gradient Boosting Classifier**: Per catturare pattern complessi
- **Ensemble Method**: Combina le predizioni dei due modelli
- **Feature Importance**: Identifica gli indicatori più rilevanti
- **Normalizzazione**: StandardScaler per feature scaling

**Label Generation**:
- BUY: Prezzo sale > 2% nei prossimi 5 periodi
- SELL: Prezzo scende > 2% nei prossimi 5 periodi
- HOLD: Movimento < 2%

### 4. TradingSignals

Combina AI e analisi tecnica per segnali finali.

**Componenti**:
- Analisi RSI (overbought/oversold)
- Analisi MACD (crossover)
- Analisi Bollinger Bands (posizione prezzo)
- Analisi Medie Mobili (trend)
- Analisi Volume (conferma)
- Sistema di consenso AI + Tecnica

**Output**:
- Azione: BUY / SELL / HOLD
- Confidence Score: 0-100%
- Forza Segnale: FORTE / MODERATO / DEBOLE
- Consenso: STRONG / MODERATE / CONFLICT
- Dettagli completi di ogni analisi

## 📈 Come Funziona il Sistema

### 1. Raccolta Dati
Il sistema scarica dati OHLCV storici da Binance per il simbolo e timeframe specificato.

### 2. Calcolo Indicatori
Vengono calcolati 30+ indicatori tecnici che fungono da "features" per il modello AI.

### 3. Training AI
Il modello viene addestrato su dati storici, imparando a riconoscere pattern che precedono movimenti di prezzo significativi.

### 4. Predizione AI
Il modello genera una predizione (BUY/SELL/HOLD) con probabilità associate.

### 5. Analisi Tecnica
In parallelo, vengono applicati algoritmi di analisi tecnica tradizionale (RSI, MACD, BB, MA).

### 6. Consensus
I segnali AI e tecnici vengono combinati:
- **STRONG**: AI e tecnica concordano
- **MODERATE**: Solo uno dei due segnala
- **CONFLICT**: AI e tecnica in disaccordo → HOLD

### 7. Confidence Score
Il punteggio finale viene calcolato considerando:
- Probabilità AI
- Numero di segnali tecnici concordi
- Forza degli indicatori
- Volume di conferma

## ⚙️ Parametri Configurabili

### Timeframe Disponibili
- `1m`, `3m`, `5m`, `15m`, `30m` - Per scalping/day trading
- `1h`, `2h`, `4h`, `6h`, `12h` - Per swing trading
- `1d`, `3d`, `1w`, `1M` - Per position trading

### Simboli
Qualsiasi coppia disponibile su Binance:
- Major: `BTCUSDT`, `ETHUSDT`, `BNBUSDT`
- Altcoin: `ADAUSDT`, `DOTUSDT`, `SOLUSDT`
- Stablecoin pairs: `BUSDUSDT`, `USDCUSDT`

### Periodo Storico
- Minimo: 30 giorni (per indicatori long-term)
- Raccomandato: 60 giorni
- Massimo: Illimitato (attenzione ai limiti API)

## 🎯 Interpretazione dei Segnali

### Segnale BUY
```
RACCOMANDAZIONE: BUY
Confidence: 75.0% (FORTE)
Consenso: STRONG
```

**Interpretazione**:
- ✅ Alta probabilità di movimento al rialzo
- ✅ AI e analisi tecnica concordano
- ✅ Momento favorevole per entrare in posizione

### Segnale SELL
```
RACCOMANDAZIONE: SELL
Confidence: 68.0% (MODERATO)
Consenso: MODERATE
```

**Interpretazione**:
- ⚠️ Probabile movimento al ribasso
- ⚠️ Considerare di chiudere posizioni long
- ⚠️ Cautela nell'aprire nuove posizioni

### Segnale HOLD
```
RACCOMANDAZIONE: HOLD
Confidence: 45.0% (DEBOLE)
Consenso: CONFLICT
```

**Interpretazione**:
- 🔄 Mercato incerto o laterale
- 🔄 Attendere segnali più chiari
- 🔄 Non fare trading in questo momento

## ⚡ Performance

### Velocità
- Analisi singola: ~30-60 secondi
- Multi-simbolo (20 coppie): ~15-20 minuti

### Requisiti Hardware
- RAM: Minimo 4GB, raccomandato 8GB
- CPU: Multi-core raccomandato per training veloce
- Disco: ~500MB per installazione + modelli

## ⚠️ Disclaimer

**ATTENZIONE**: Questo sistema è fornito **solo a scopo educativo e informativo**.

- ❌ NON è un consiglio finanziario
- ❌ NON garantisce profitti
- ❌ Il trading comporta rischi significativi
- ✅ Usa sempre stop-loss appropriati
- ✅ Non investire più di quanto puoi permetterti di perdere
- ✅ Considera questo tool come uno strumento di analisi, non una certezza

**Il trading di criptovalute è altamente rischioso. Fai sempre le tue ricerche (DYOR) e consulta un consulente finanziario professionista.**

## 🐛 Troubleshooting

### Errore: "API key not found"
Non serve un'API key per dati pubblici. Se l'errore persiste, verifica la connessione internet.

### Errore: "Insufficient data"
Aumenta il parametro `--days` a 60 o più, specialmente per timeframe lunghi (4h, 1d).

### Errore: "Rate limit exceeded"
Binance ha limiti di richieste. Riduci il numero di simboli analizzati o aggiungi pause tra le richieste.

### Performance lente
- Riduci il numero di simboli analizzati
- Usa timeframe più lunghi (richiedono meno dati)
- Considera l'utilizzo di un computer più potente

## 🔄 Aggiornamenti Futuri

Possibili miglioramenti:
- [ ] Deep Learning (LSTM/Transformer) per serie temporali
- [ ] Backtesting automatico
- [ ] Trading automatico (con approvazione utente)
- [ ] Dashboard web interattiva
- [ ] Notifiche in tempo reale
- [ ] Supporto per altri exchange
- [ ] Analisi sentiment da social media

## 📝 Licenza

Questo progetto è fornito "as-is" per scopi educativi.

## 🤝 Contributi

Contributi, issues e feature requests sono benvenuti!

## 📧 Supporto

Per domande o problemi, apri una issue su GitHub.

---

**Buon Trading! 📈🚀**

*Remember: The best trade is the one you don't take when conditions aren't right.*
