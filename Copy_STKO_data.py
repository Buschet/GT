"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    STKO GEOMETRY COPY TOOL                                   ║
║                                                                              ║
║  Copy = False: Analizza geometrie + Export + Salva proprietà in JSON        ║
║  Copy = True:  Import geometrie + Ricrea proprietà tramite coordinate       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from PyMpc import *
from PySide2.QtCore import QSettings
from PySide2.QtWidgets import QFileDialog
import json
import os
from datetime import datetime

# ==============================================================================
# ⚙️ CONFIGURAZIONE PRINCIPALE
# ==============================================================================

# 🔴 VARIABILE PRINCIPALE - MODALITÀ OPERATIVA
Copy = False  # False = Analizza | True = Ricrea

# ==============================================================================
# INIZIALIZZAZIONE
# ==============================================================================

App.clearTerminal()
doc = App.caeDocument()

print("="*80)
print("STKO GEOMETRY COPY TOOL")
print("="*80)
print(f"Modalità: {'COPY (Ricrea Geometrie)' if Copy else 'ANALYZE (Analizza)'}")
print(f"Data/Ora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

# ==============================================================================
# SELEZIONE CARTELLA UTENTE
# ==============================================================================

if not Copy:
	# Modalità ANALISI: chiedi dove salvare
	print("\n[SELEZIONE CARTELLA OUTPUT]")
	print("Seleziona la cartella dove salvare i file esportati...")

	# Apri dialog per selezione cartella
	output_folder = QFileDialog.getExistingDirectory(None, "Seleziona Cartella Output")

	if not output_folder:
		print("✗ Nessuna cartella selezionata. Uscita.")
		raise SystemExit

	output_folder = str(output_folder)
	print(f"✓ Cartella selezionata: {output_folder}")

	# Crea sottocartella per geometrie
	geometries_folder = os.path.join(output_folder, "Geometries")
	if not os.path.exists(geometries_folder):
		os.makedirs(geometries_folder)

	print(f"✓ Cartella geometrie: {geometries_folder}")

else:
	# Modalità COPY: chiedi da dove leggere
	print("\n[SELEZIONE CARTELLA INPUT]")
	print("Seleziona la cartella contenente i file da importare...")

	input_folder = QFileDialog.getExistingDirectory(None, "Seleziona Cartella Input")

	if not input_folder:
		print("✗ Nessuna cartella selezionata. Uscita.")
		raise SystemExit

	input_folder = str(input_folder)
	print(f"✓ Cartella selezionata: {input_folder}")

	# Verifica esistenza file JSON
	json_file = os.path.join(input_folder, "STKO_Analysis.json")
	if not os.path.exists(json_file):
		print(f"✗ File JSON non trovato: {json_file}")
		raise SystemExit

	print(f"✓ File JSON trovato: {json_file}")

	# Cartella geometrie
	geometries_folder = os.path.join(input_folder, "Geometries")
	if not os.path.exists(geometries_folder):
		print(f"✗ Cartella Geometries non trovata: {geometries_folder}")
		raise SystemExit

	print(f"✓ Cartella geometrie trovata: {geometries_folder}")

print("="*80)
print("\n[PRONTO PER INIZIARE]")
print("Premere OK per continuare...")
