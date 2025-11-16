# 🧠 Rete Neurale Multi-Timeframe - Documentazione Tecnica

## Panoramica

Questo sistema implementa una **rete neurale feedforward** pre-addestrata progettata per identificare trend rialzisti e ribassisti nel mercato crypto, con particolare focus sull'identificazione di **punti di ingresso e uscita**.

La rete è basata sul sistema "Delfini/Squali/Balene" di TradingView e utilizza **3 istanze della stessa rete** analizzando **3 timeframe diversi** per conferma cross-timeframe.

## Architettura della Rete

### Struttura

```
Input Layer:    15 neuroni (Linear activation)
                    ↓
Hidden Layer 1: 30 neuroni (Tanh activation)
                    ↓
Hidden Layer 2: 9 neuroni (Tanh activation)
                    ↓
Output Layer:   1 neurone (Tanh activation)
```

### Parametri

- **Totale pesi**: 15×30 + 30×9 + 9×1 = 729 pesi
- **Funzioni attivazione**:
  - Input: Linear (identity)
  - Hidden/Output: Tanh
- **Range output**: [-1, +1]
  - Valori positivi → Trend rialzista
  - Valori negativi → Trend ribassista

## Input della Rete

L'input è la **variazione percentuale del prezzo** calcolata come:

```python
price_change = (ohlc4_today - ohlc4_yesterday) / ohlc4_yesterday
```

Dove `ohlc4 = (open + high + low + close) / 4`

### Caratteristica Unica

Tutti e 15 i neuroni del layer di input ricevono **lo stesso valore** (la variazione percentuale). Questo permette alla rete di applicare **15 diverse trasformazioni** allo stesso input attraverso i pesi del primo layer.

## Sistema Multi-Timeframe

### I Tre Livelli

1. **🐬 Delfini** (Timeframe Corto - default: 15m)
   - Cattura movimenti rapidi e trend intraday
   - Sensibile a variazioni di breve termine
   - Ottimo per scalping e day trading

2. **🦈 Squali** (Timeframe Medio - default: 1h)
   - Identifica trend di medio periodo
   - Bilancia rumore e segnale
   - Ideale per swing trading

3. **🐋 Balene** (Timeframe Lungo - default: 4h)
   - Rileva trend di lungo periodo
   - Meno sensibile al rumore
   - Adatto per position trading

### Combinazione degli Output

Gli output delle 3 reti vengono combinati:

```python
combined_output = nn_dolphins + nn_sharks + nn_whales
```

**Range**: [-3, +3]

**Interpretazione**:
- `> +0.3`: Trend RIALZISTA forte (tutti timeframe allineati)
- `-0.3 to +0.3`: Trend NEUTRALE o laterale
- `< -0.3`: Trend RIBASSISTA forte (tutti timeframe allineati)

## Identificazione Punti Entry/Exit

### 1. Crossover Detection

Il sistema identifica automaticamente i **crossover** (attraversamenti dello zero):

#### Crossover Rialzista (Bullish Cross) 🟢
```
Output passa da negativo a positivo
→ Segnale di INGRESSO LONG
```

#### Crossover Ribassista (Bearish Cross) 🔴
```
Output passa da positivo a negativo
→ Segnale di USCITA LONG / INGRESSO SHORT
```

### 2. Timing dei Segnali

I segnali sono considerati **validi** se il crossover è avvenuto negli **ultimi 10 bar**.

Esempio:
```
bars_since_cross = 3
→ "Crossover rialzista 3 bar fa" = SEGNALE FRESCO
```

### 3. Calcolo Normalizzato

Il sistema calcola un segnale normalizzato per identificare estremi:

```python
get1 = open * -(combined_output)
highest = max(get1[-30:])
lowest = min(get1[-30:])
max_abs = max(highest, -lowest)
normalized = get1 / max_abs
```

Questo valore normalizzato aiuta a identificare:
- Condizioni di ipercomprato
- Condizioni di ipervenduto
- Livelli estremi dove potrebbero verificarsi inversioni

## Uso Pratico

### Analisi Singola Rete

```python
from neural_network_trader import NeuralNetworkTrader

nn = NeuralNetworkTrader()

# Test con variazione +2%
output = nn.forward(0.02)
print(f"Output: {output:.4f}")  # Valore tra -1 e +1
```

### Analisi Multi-Timeframe

```python
from neural_network_trader import MultiTimeframeNNTrader

trader = MultiTimeframeNNTrader()

# Analizza BTC su 3 timeframe
results = trader.analyze_multi_timeframe(
    'BTCUSDT',
    tf_dolphins='15m',  # Breve
    tf_sharks='1h',     # Medio
    tf_whales='4h',     # Lungo
    days_back=30
)

# Genera segnali
signals = trader.generate_signals(results)

# Stampa report
trader.print_analysis_report('BTCUSDT', signals)
```

### Analisi Avanzata (Multi-Sistema)

Combina Rete Neurale + AI ML + Indicatori Tecnici:

```bash
python advanced_nn_analysis.py --symbol BTCUSDT --tf-short 15m --tf-medium 1h --tf-long 4h
```

## Output e Interpretazione

### Output Tipico

```
🧠 OUTPUT RETI NEURALI:
   🐬 Delfini (breve):  +0.4521
   🦈 Squali (medio):   +0.3204
   🐋 Balene (lungo):   +0.2103
   📊 Combinato:        +0.9828

🎯 TREND IDENTIFICATO: RIALZISTA
⚡ AZIONE RACCOMANDATA: BUY

🔄 CROSSOVER RILEVATI: 3
   🟢 Rialzista: $43,150.00 - 2025-11-16 10:00:00
   🔴 Ribassista: $42,800.00 - 2025-11-15 18:30:00
   🟢 Rialzista: $42,200.00 - 2025-11-15 04:15:00

🟢 INGRESSO LONG - Crossover rialzista 5 bar fa
```

### Livelli di Confidence

| Combined Output | Trend | Azione | Confidence |
|----------------|-------|--------|-----------|
| > +1.5 | RIALZISTA Forte | BUY | Alta |
| +0.3 a +1.5 | RIALZISTA | BUY | Media |
| -0.3 a +0.3 | NEUTRALE | HOLD | Bassa |
| -1.5 a -0.3 | RIBASSISTA | SELL | Media |
| < -1.5 | RIBASSISTA Forte | SELL | Alta |

## Strategie di Trading

### Strategia 1: Conferma Multi-Timeframe

**Setup**:
- Tutti e 3 i timeframe devono essere allineati
- `combined_output` > +1.0 o < -1.0

**Ingresso**:
- LONG: Quando avviene crossover rialzista su timeframe corto
- SHORT: Quando avviene crossover ribassista su timeframe corto

**Uscita**:
- Crossover opposto su qualsiasi timeframe
- Stop-loss: 3% dal punto di ingresso

### Strategia 2: Scalping con Delfini

**Setup**:
- Usa solo output Delfini (15m o 5m)
- Cerca crossover frequenti

**Ingresso**:
- Immediato al crossover

**Uscita**:
- Al crossover opposto
- Take profit: +1-2%
- Stop loss: -1%

### Strategia 3: Swing Trading con Squali

**Setup**:
- Usa Squali (1h o 4h)
- Conferma con Balene nella stessa direzione

**Ingresso**:
- Crossover su Squali + Balene allineate

**Uscita**:
- Crossover opposto su Squali
- Take profit: +5-10%
- Stop loss: -3%

## Confronto con Altri Sistemi

### vs. AI Machine Learning

| Aspetto | Rete Neurale | AI ML |
|---------|--------------|-------|
| Input | Solo price change | 30+ features |
| Training | Pre-trained | Dynamic training |
| Speed | Molto veloce | Medio |
| Interpretabilità | Media | Bassa |
| Adattabilità | Bassa | Alta |

**Migliore uso**: Combinare entrambi per consenso

### vs. Indicatori Tecnici

| Aspetto | Rete Neurale | Indicatori |
|---------|--------------|------------|
| Complessità | Alta | Variabile |
| Laggenzia | Media | Alta (MA, MACD) |
| Segnali | Continui | Discreti |
| False positives | Medi | Alti |

**Migliore uso**: Usare NN per direzione, indicatori per timing

## Limitazioni

### 1. Pesi Pre-Addestrati
- I pesi sono fissi e non si adattano a nuove condizioni di mercato
- Potrebbero non performare bene in mercati molto diversi da quelli di training

### 2. Input Semplice
- Usa solo la variazione percentuale del prezzo
- Non considera volume, volatilità, o altri fattori

### 3. Nessun Context Memory
- Ogni predizione è indipendente
- Non ha memoria di stati precedenti (non è una RNN/LSTM)

### 4. Overfitting Potenziale
- 729 pesi per un singolo input potrebbero indicare overfitting
- Testare sempre su dati out-of-sample

## Best Practices

### ✅ DO

1. **Usa conferma multi-timeframe**
   - Non tradare su un solo segnale
   - Aspetta allineamento tra timeframe

2. **Combina con altri sistemi**
   - Usa insieme ad AI ML e indicatori tecnici
   - Cerca consenso tra sistemi

3. **Rispetta i crossover**
   - Sono i segnali più affidabili
   - Entra/esci ai crossover, non in mezzo

4. **Usa stop-loss**
   - Sempre, senza eccezioni
   - 2-3% per timeframe corti
   - 3-5% per timeframe lunghi

### ❌ DON'T

1. **Non ignorare il consenso**
   - Se NN dice BUY ma AI dice SELL → HOLD

2. **Non tradare su valori neutrali**
   - `combined_output` tra -0.3 e +0.3 → HOLD

3. **Non aumentare size su conflitto**
   - Se i timeframe sono in disaccordo → riduci o aspetta

4. **Non ignorare il volume**
   - Anche con segnale forte, se volume è basso → cautela

## Metriche di Performance

Durante i test, monitora:

1. **Win Rate**: % di trade vincenti
2. **Average Return**: Rendimento medio per trade
3. **Sharpe Ratio**: Rendimento aggiustato per rischio
4. **Max Drawdown**: Massima perdita consecutiva
5. **Signal Quality**:
   - Lag medio dal crossover all'inversione
   - % di crossover che portano a movimento significativo

## Conclusione

Questa rete neurale è uno strumento **potente ma non infallibile**. I migliori risultati si ottengono:

1. Combinandola con altri sistemi (AI ML, indicatori)
2. Usando conferma multi-timeframe
3. Rispettando rigorosamente la gestione del rischio
4. Adattando le strategie alle condizioni di mercato

**Ricorda**: Nessun sistema garantisce profitti. Usa sempre un approccio disciplinato e gestisci il rischio appropriatamente.

---

**Disclaimer**: Questo sistema è fornito a scopo educativo. Il trading comporta rischi significativi. Non investire più di quanto puoi permetterti di perdere.
