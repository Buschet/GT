"""
Modello AI per analisi trading e predizione buy/sell signals
Combina multiple strategie e machine learning
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from typing import Tuple, Dict, Optional
import pickle
import os


class TradingAIModel:
    """
    Modello AI per generare segnali di trading
    Combina analisi tecnica e machine learning
    """

    def __init__(self):
        self.scaler = StandardScaler()
        self.rf_model = None
        self.gb_model = None
        self.feature_importance = None
        self.is_trained = False

    def create_labels(self, df: pd.DataFrame, forward_periods: int = 5, threshold: float = 0.02) -> pd.Series:
        """
        Crea le label per il training basate sul movimento futuro del prezzo

        Args:
            df: DataFrame con i dati
            forward_periods: Numero di periodi da guardare avanti
            threshold: Soglia percentuale per classificare buy/sell

        Returns:
            Series con label: 1 (buy), 0 (hold), -1 (sell)
        """
        # Calcola il rendimento futuro
        future_return = df['close'].shift(-forward_periods) / df['close'] - 1

        # Crea le label
        labels = pd.Series(0, index=df.index)  # Default: hold
        labels[future_return > threshold] = 1  # Buy
        labels[future_return < -threshold] = -1  # Sell

        return labels

    def prepare_features(self, df: pd.DataFrame, feature_cols: list) -> Tuple[np.ndarray, list]:
        """
        Prepara le feature per il training/prediction

        Args:
            df: DataFrame con tutte le colonne
            feature_cols: Lista di colonne da usare come feature

        Returns:
            Tuple (feature_array, feature_names)
        """
        # Rimuovi righe con NaN
        df_clean = df[feature_cols].dropna()

        return df_clean.values, df_clean.columns.tolist()

    def train(self,
              df: pd.DataFrame,
              feature_cols: list,
              forward_periods: int = 5,
              threshold: float = 0.02,
              test_size: float = 0.2) -> Dict:
        """
        Addestra i modelli AI

        Args:
            df: DataFrame con dati e indicatori
            feature_cols: Lista di colonne da usare come feature
            forward_periods: Periodi da guardare avanti per le label
            threshold: Soglia per classificare buy/sell
            test_size: Percentuale di dati per test

        Returns:
            Dict con metriche di performance
        """
        print("Preparazione dati per training...")

        # Crea le label
        labels = self.create_labels(df, forward_periods, threshold)

        # Prepara le feature
        df_with_labels = df.copy()
        df_with_labels['label'] = labels

        # Rimuovi righe con NaN
        df_clean = df_with_labels.dropna()

        X = df_clean[feature_cols].values
        y = df_clean['label'].values

        print(f"Dataset: {len(X)} samples")
        print(f"Distribuzione labels - Buy: {sum(y==1)}, Hold: {sum(y==0)}, Sell: {sum(y==-1)}")

        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )

        # Normalizza le feature
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Addestra Random Forest
        print("\nTraining Random Forest...")
        self.rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=20,
            min_samples_leaf=10,
            random_state=42,
            n_jobs=-1
        )
        self.rf_model.fit(X_train_scaled, y_train)

        # Addestra Gradient Boosting
        print("Training Gradient Boosting...")
        self.gb_model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        self.gb_model.fit(X_train_scaled, y_train)

        # Calcola feature importance
        self.feature_importance = pd.DataFrame({
            'feature': feature_cols,
            'importance_rf': self.rf_model.feature_importances_,
            'importance_gb': self.gb_model.feature_importances_
        }).sort_values('importance_rf', ascending=False)

        # Valuta i modelli
        rf_train_score = self.rf_model.score(X_train_scaled, y_train)
        rf_test_score = self.rf_model.score(X_test_scaled, y_test)
        gb_train_score = self.gb_model.score(X_train_scaled, y_train)
        gb_test_score = self.gb_model.score(X_test_scaled, y_test)

        self.is_trained = True

        metrics = {
            'rf_train_accuracy': rf_train_score,
            'rf_test_accuracy': rf_test_score,
            'gb_train_accuracy': gb_train_score,
            'gb_test_accuracy': gb_test_score,
            'n_samples': len(X),
            'n_features': len(feature_cols)
        }

        print("\n" + "=" * 60)
        print("METRICHE DI PERFORMANCE")
        print("=" * 60)
        print(f"Random Forest - Train: {rf_train_score:.4f}, Test: {rf_test_score:.4f}")
        print(f"Gradient Boosting - Train: {gb_train_score:.4f}, Test: {gb_test_score:.4f}")

        return metrics

    def predict(self, df: pd.DataFrame, feature_cols: list) -> Dict:
        """
        Genera predizioni per nuovi dati

        Args:
            df: DataFrame con dati e indicatori
            feature_cols: Lista di colonne da usare come feature

        Returns:
            Dict con predizione, confidence e dettagli
        """
        if not self.is_trained:
            raise ValueError("Il modello deve essere addestrato prima di fare predizioni!")

        # Usa l'ultimo record
        X = df[feature_cols].iloc[-1:].values

        # Normalizza
        X_scaled = self.scaler.transform(X)

        # Predizioni dai due modelli
        rf_pred = self.rf_model.predict(X_scaled)[0]
        rf_proba = self.rf_model.predict_proba(X_scaled)[0]

        gb_pred = self.gb_model.predict(X_scaled)[0]
        gb_proba = self.gb_model.predict_proba(X_scaled)[0]

        # Ensemble: media delle probabilità
        avg_proba = (rf_proba + gb_proba) / 2
        ensemble_pred = self.rf_model.classes_[np.argmax(avg_proba)]

        # Calcola confidence (probabilità della classe predetta)
        confidence = avg_proba[np.argmax(avg_proba)]

        # Mappa le predizioni a azioni
        action_map = {-1: 'SELL', 0: 'HOLD', 1: 'BUY'}

        result = {
            'action': action_map[ensemble_pred],
            'confidence': float(confidence),
            'rf_prediction': action_map[rf_pred],
            'gb_prediction': action_map[gb_pred],
            'probabilities': {
                'buy': float(avg_proba[2] if len(avg_proba) == 3 else 0),
                'hold': float(avg_proba[1] if len(avg_proba) >= 2 else 0),
                'sell': float(avg_proba[0] if len(avg_proba) >= 1 else 0)
            }
        }

        return result

    def get_top_features(self, n: int = 10) -> pd.DataFrame:
        """
        Ottiene le top N feature più importanti

        Args:
            n: Numero di feature da restituire

        Returns:
            DataFrame con le top feature
        """
        if self.feature_importance is None:
            raise ValueError("Il modello deve essere addestrato prima!")

        return self.feature_importance.head(n)

    def save_model(self, path: str = 'models'):
        """
        Salva il modello addestrato

        Args:
            path: Directory dove salvare il modello
        """
        if not self.is_trained:
            raise ValueError("Il modello deve essere addestrato prima di salvarlo!")

        os.makedirs(path, exist_ok=True)

        model_data = {
            'scaler': self.scaler,
            'rf_model': self.rf_model,
            'gb_model': self.gb_model,
            'feature_importance': self.feature_importance
        }

        with open(f'{path}/trading_model.pkl', 'wb') as f:
            pickle.dump(model_data, f)

        print(f"Modello salvato in {path}/trading_model.pkl")

    def load_model(self, path: str = 'models/trading_model.pkl'):
        """
        Carica un modello precedentemente salvato

        Args:
            path: Path del file del modello
        """
        with open(path, 'rb') as f:
            model_data = pickle.load(f)

        self.scaler = model_data['scaler']
        self.rf_model = model_data['rf_model']
        self.gb_model = model_data['gb_model']
        self.feature_importance = model_data['feature_importance']
        self.is_trained = True

        print(f"Modello caricato da {path}")


# Test del modulo
if __name__ == '__main__':
    from binance_data_loader import BinanceDataLoader
    from technical_indicators import TechnicalIndicators

    print("=" * 60)
    print("TEST: AI Trading Model")
    print("=" * 60)

    # Carica dati
    loader = BinanceDataLoader()
    df = loader.get_historical_klines('BTCUSDT', '1h', days_back=60)

    # Calcola indicatori
    indicators = TechnicalIndicators(df)
    df_with_indicators = indicators.add_all_indicators()
    indicators.add_price_patterns()
    df_clean = indicators.get_features_dataframe()

    # Prepara feature
    feature_cols = indicators.get_feature_names()

    # Inizializza e addestra il modello
    model = TradingAIModel()
    metrics = model.train(
        df_clean,
        feature_cols,
        forward_periods=5,
        threshold=0.015
    )

    # Top features
    print("\n" + "=" * 60)
    print("TOP 10 FEATURE PIÙ IMPORTANTI")
    print("=" * 60)
    print(model.get_top_features(10))

    # Fai una predizione
    print("\n" + "=" * 60)
    print("PREDIZIONE PER L'ULTIMO CANDLE")
    print("=" * 60)
    prediction = model.predict(df_clean, feature_cols)
    print(f"\nAzione raccomandata: {prediction['action']}")
    print(f"Confidence: {prediction['confidence']:.2%}")
    print(f"\nRandom Forest: {prediction['rf_prediction']}")
    print(f"Gradient Boosting: {prediction['gb_prediction']}")
    print(f"\nProbabilità:")
    print(f"  BUY:  {prediction['probabilities']['buy']:.2%}")
    print(f"  HOLD: {prediction['probabilities']['hold']:.2%}")
    print(f"  SELL: {prediction['probabilities']['sell']:.2%}")

    # Salva il modello
    model.save_model()
