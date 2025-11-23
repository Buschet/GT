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
import csv
import os
from datetime import datetime

# ==============================================================================
# ⚙️ CONFIGURAZIONE PRINCIPALE
# ==============================================================================

# 🔴 VARIABILE PRINCIPALE - MODALITÀ OPERATIVA
Copy = True  # False = Analizza | True = Ricrea

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
# CONTROLLO NOMI DUPLICATI (solo modalità ANALYZE)
# ==============================================================================

if not Copy:
	print("\n[CONTROLLO NOMI DUPLICATI]")
	print("Verifico che non ci siano geometrie con lo stesso nome...")

	# Raccogli tutti i nomi
	geometry_names = []
	for k, geom in doc.geometries.items():
		geometry_names.append(geom.name)

	# Trova nomi che appaiono più di una volta
	duplicates = []
	for name in geometry_names:
		if geometry_names.count(name) > 1 and name not in duplicates:
			duplicates.append(name)

	if duplicates:
		print("\n🚫 ERRORE: Rilevati nomi duplicati!")
		print("="*80)
		print("Le seguenti geometrie hanno lo stesso nome:")
		print()
		for name in duplicates:
			count = geometry_names.count(name)
			print(f"  • '{name}' (ripetuto {count} volte)")
		print()
		print("="*80)
		print("\n🚫 AZIONE RICHIESTA:")
		print("Devi rinominare le geometrie duplicate prima di procedere.")
		print("Ogni geometria deve avere un nome unico.")
		print()
		raise SystemExit
	else:
		print("✓ Tutti i nomi sono univoci")

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

# ==============================================================================
# FUNZIONI HELPER
# ==============================================================================

def get_shape_type_name(shape_type):
	"""Converte il tipo di shape in nome leggibile"""
	type_map = {
		TopAbs_ShapeEnum.TopAbs_VERTEX: "VERTEX",
		TopAbs_ShapeEnum.TopAbs_EDGE: "EDGE",
		TopAbs_ShapeEnum.TopAbs_WIRE: "WIRE",
		TopAbs_ShapeEnum.TopAbs_FACE: "FACE",
		TopAbs_ShapeEnum.TopAbs_SHELL: "SHELL",
		TopAbs_ShapeEnum.TopAbs_SOLID: "SOLID",
		TopAbs_ShapeEnum.TopAbs_COMPSOLID: "COMPSOLID",
		TopAbs_ShapeEnum.TopAbs_COMPOUND: "COMPOUND",
	}
	return type_map.get(shape_type, "UNKNOWN")

def extract_vertex_coordinates(shape, vertex_id):
	"""Estrae le coordinate X, Y, Z di un vertice"""
	try:
		pos = shape.vertexPosition(vertex_id)
		return {'x': pos.x, 'y': pos.y, 'z': pos.z}
	except:
		return {'x': None, 'y': None, 'z': None}

def extract_attribute_value(attr):
	"""Estrae il valore di un attributo XObject"""
	try:
		if hasattr(attr, 'real'):
			return float(attr.real)
		elif hasattr(attr, 'integer'):
			return int(attr.integer)
		elif hasattr(attr, 'boolean'):
			return bool(attr.boolean)
		elif hasattr(attr, 'string'):
			return str(attr.string)
		elif hasattr(attr, 'quantityScalar'):
			return float(attr.quantityScalar.value)
		elif hasattr(attr, 'quantityVector3'):
			v = attr.quantityVector3
			return [float(v.valueAt(0)), float(v.valueAt(1)), float(v.valueAt(2))]
		elif hasattr(attr, 'index'):
			return int(attr.index)
		elif hasattr(attr, 'indexVector'):
			return list(attr.indexVector)
		else:
			return str(attr)
	except:
		return None

def extract_property_data(prop, prop_type):
	"""Estrae TUTTI i dati di una proprietà (physical o element)"""
	prop_data = {
		'property_id': prop.id,
		'property_name': prop.name,
		'property_type': None,
		'parameters': {}
	}

	try:
		if prop.XObject:
			prop_data['property_type'] = prop.XObject.completeName

			xobj = prop.XObject
			# Usa .items() per iterare sugli attributi
			for attr_name, attr in xobj.attributes.items():
				try:
					prop_data['parameters'][attr_name] = extract_attribute_value(attr)
				except:
					pass
		else:
			prop_data['property_type'] = 'Unknown'
	except Exception as e:
		prop_data['property_type'] = f'Error: {str(e)}'

	return prop_data

def extract_interaction_data(interaction_id, interaction):
	"""Estrae i dati di un'interazione tra geometrie"""
	interaction_data = {
		'id': interaction_id,
		'name': interaction.name,
		'type': None,
		'physical_property': None,
		'element_property': None,
		'masters': [],
		'slaves': [],
		'errors': []
	}

	try:
		# Tipo di interazione - salva come stringa per compatibilità JSON
		if hasattr(interaction, 'type'):
			try:
				# Converte l'enum in stringa
				interaction_data['type'] = str(interaction.type)
			except:
				interaction_data['type'] = 'NodeToNode'  # Default

		# Physical Property associata
		if hasattr(interaction, 'physicalProperty') and interaction.physicalProperty:
			interaction_data['physical_property'] = {
				'property_id': interaction.physicalProperty.id,
				'property_name': interaction.physicalProperty.name
			}

		# Element Property associata
		if hasattr(interaction, 'elementProperty') and interaction.elementProperty:
			interaction_data['element_property'] = {
				'property_id': interaction.elementProperty.id,
				'property_name': interaction.elementProperty.name
			}

		# Estrai MASTERS
		if hasattr(interaction.items, 'masters'):
			for master in interaction.items.masters:
				try:
					master_geom = master.geometry
					master_data = {
						'geometry_id': master_geom.id,
						'geometry_name': master_geom.name,
						'subshape_id': master.subshapeId,
						'subshape_type': get_mpc_subshape_type_name(master.subshapeType),
						'vertex_coordinates': []
					}

					# Estrai coordinate dei vertici per matching
					try:
						shape = master_geom.shape
						if master.subshapeType == MpcSubshapeType.Vertex:
							# È un vertice singolo
							master_data['vertex_coordinates'] = [extract_vertex_coordinates(shape, master.subshapeId)]
						else:
							# Estrai vertici della subshape
							vertices = shape.getSubshapeChildren(
								master.subshapeId,
								master.subshapeType,
								MpcSubshapeType.Vertex
							)
							master_data['vertex_coordinates'] = [
								extract_vertex_coordinates(shape, v_id) for v_id in vertices
							]
					except Exception as e:
						interaction_data['errors'].append(f"Errore estrazione coordinate master: {str(e)}")

					interaction_data['masters'].append(master_data)
				except Exception as e:
					interaction_data['errors'].append(f"Errore analisi master: {str(e)}")

		# Estrai SLAVES
		if hasattr(interaction.items, 'slaves'):
			for slave in interaction.items.slaves:
				try:
					slave_geom = slave.geometry
					slave_data = {
						'geometry_id': slave_geom.id,
						'geometry_name': slave_geom.name,
						'subshape_id': slave.subshapeId,
						'subshape_type': get_mpc_subshape_type_name(slave.subshapeType),
						'vertex_coordinates': []
					}

					# Estrai coordinate dei vertici per matching
					try:
						shape = slave_geom.shape
						if slave.subshapeType == MpcSubshapeType.Vertex:
							# È un vertice singolo
							slave_data['vertex_coordinates'] = [extract_vertex_coordinates(shape, slave.subshapeId)]
						else:
							# Estrai vertici della subshape
							vertices = shape.getSubshapeChildren(
								slave.subshapeId,
								slave.subshapeType,
								MpcSubshapeType.Vertex
							)
							slave_data['vertex_coordinates'] = [
								extract_vertex_coordinates(shape, v_id) for v_id in vertices
							]
					except Exception as e:
						interaction_data['errors'].append(f"Errore estrazione coordinate slave: {str(e)}")

					interaction_data['slaves'].append(slave_data)
				except Exception as e:
					interaction_data['errors'].append(f"Errore analisi slave: {str(e)}")

	except Exception as e:
		interaction_data['errors'].append(f"Errore generale: {str(e)}")

	return interaction_data

def analyze_geometry_comprehensive(geom_id, geom):
	"""Analizza in modo completo una singola geometria"""

	geometry_data = {
		'id': geom_id,
		'name': geom.name,
		'shape_type': None,
		'topology': {
			'num_vertices': 0,
			'num_edges': 0,
			'num_faces': 0,
			'num_solids': 0
		},
		'vertices': [],
		'properties': {
			'physical': {
				'vertices': [],
				'edges': [],
				'faces': [],
				'solids': []
			},
			'element': {
				'vertices': [],
				'edges': [],
				'faces': [],
				'solids': []
			}
		},
		'errors': []
	}

	try:
		shape = geom.shape
		geometry_data['shape_type'] = get_shape_type_name(shape.shapeType)

		# ANALISI TOPOLOGIA
		try:
			geometry_data['topology']['num_vertices'] = shape.getNumberOfSubshapes(MpcSubshapeType.Vertex)
			geometry_data['topology']['num_edges'] = shape.getNumberOfSubshapes(MpcSubshapeType.Edge)
			geometry_data['topology']['num_faces'] = shape.getNumberOfSubshapes(MpcSubshapeType.Face)
			geometry_data['topology']['num_solids'] = shape.getNumberOfSubshapes(MpcSubshapeType.Solid)
		except Exception as e:
			geometry_data['errors'].append(f"Errore analisi topologia: {str(e)}")

		# ANALISI VERTICES (coordinate)
		try:
			num_vertices = geometry_data['topology']['num_vertices']
			for v_id in range(num_vertices):
				vertex_info = {
					'id': v_id,
					'coordinates': extract_vertex_coordinates(shape, v_id)
				}
				geometry_data['vertices'].append(vertex_info)
		except Exception as e:
			geometry_data['errors'].append(f"Errore analisi vertices: {str(e)}")

		# ANALISI PHYSICAL PROPERTIES
		try:
			# Physical Properties su VERTICES
			if geometry_data['topology']['num_vertices'] > 0:
				pp_vertices = geom.physicalPropertyAssignment.onVertices
				for v_id in range(len(pp_vertices)):
					pp = pp_vertices[v_id]
					if pp is not None:
						prop_data = extract_property_data(pp, 'physical')
						prop_data['vertex_id'] = v_id
						# Aggiungi coordinate del vertice
						prop_data['coordinates'] = extract_vertex_coordinates(shape, v_id)
						geometry_data['properties']['physical']['vertices'].append(prop_data)

			# Physical Properties su EDGES
			if geometry_data['topology']['num_edges'] > 0:
				pp_edges = geom.physicalPropertyAssignment.onEdges
				for e_id in range(len(pp_edges)):
					pp = pp_edges[e_id]
					if pp is not None:
						prop_data = extract_property_data(pp, 'physical')
						prop_data['edge_id'] = e_id
						# Aggiungi coordinate vertici dell'edge
						try:
							vertices = shape.getSubshapeChildren(e_id, MpcSubshapeType.Edge, MpcSubshapeType.Vertex)
							prop_data['vertex_coordinates'] = [extract_vertex_coordinates(shape, v_id) for v_id in vertices]
						except:
							prop_data['vertex_coordinates'] = []
						geometry_data['properties']['physical']['edges'].append(prop_data)

			# Physical Properties su FACES
			if geometry_data['topology']['num_faces'] > 0:
				pp_faces = geom.physicalPropertyAssignment.onFaces
				for f_id in range(len(pp_faces)):
					pp = pp_faces[f_id]
					if pp is not None:
						prop_data = extract_property_data(pp, 'physical')
						prop_data['face_id'] = f_id
						# Aggiungi coordinate vertici della face
						try:
							vertices = shape.getSubshapeChildren(f_id, MpcSubshapeType.Face, MpcSubshapeType.Vertex)
							prop_data['vertex_coordinates'] = [extract_vertex_coordinates(shape, v_id) for v_id in vertices]
						except:
							prop_data['vertex_coordinates'] = []
						geometry_data['properties']['physical']['faces'].append(prop_data)

			# Physical Properties su SOLIDS
			if geometry_data['topology']['num_solids'] > 0:
				pp_solids = geom.physicalPropertyAssignment.onSolids
				for s_id in range(len(pp_solids)):
					pp = pp_solids[s_id]
					if pp is not None:
						prop_data = extract_property_data(pp, 'physical')
						prop_data['solid_id'] = s_id
						# Aggiungi coordinate vertici del solid
						try:
							vertices = shape.getSubshapeChildren(s_id, MpcSubshapeType.Solid, MpcSubshapeType.Vertex)
							prop_data['vertex_coordinates'] = [extract_vertex_coordinates(shape, v_id) for v_id in vertices]
						except:
							prop_data['vertex_coordinates'] = []
						geometry_data['properties']['physical']['solids'].append(prop_data)

		except Exception as e:
			geometry_data['errors'].append(f"Errore analisi physical properties: {str(e)}")

		# ANALISI ELEMENT PROPERTIES
		try:
			# Element Properties su VERTICES
			if geometry_data['topology']['num_vertices'] > 0:
				ep_vertices = geom.elementPropertyAssignment.onVertices
				for v_id in range(len(ep_vertices)):
					ep = ep_vertices[v_id]
					if ep is not None:
						prop_data = extract_property_data(ep, 'element')
						prop_data['vertex_id'] = v_id
						prop_data['coordinates'] = extract_vertex_coordinates(shape, v_id)
						geometry_data['properties']['element']['vertices'].append(prop_data)

			# Element Properties su EDGES
			if geometry_data['topology']['num_edges'] > 0:
				ep_edges = geom.elementPropertyAssignment.onEdges
				for e_id in range(len(ep_edges)):
					ep = ep_edges[e_id]
					if ep is not None:
						prop_data = extract_property_data(ep, 'element')
						prop_data['edge_id'] = e_id
						try:
							vertices = shape.getSubshapeChildren(e_id, MpcSubshapeType.Edge, MpcSubshapeType.Vertex)
							prop_data['vertex_coordinates'] = [extract_vertex_coordinates(shape, v_id) for v_id in vertices]
						except:
							prop_data['vertex_coordinates'] = []
						geometry_data['properties']['element']['edges'].append(prop_data)

			# Element Properties su FACES
			if geometry_data['topology']['num_faces'] > 0:
				ep_faces = geom.elementPropertyAssignment.onFaces
				for f_id in range(len(ep_faces)):
					ep = ep_faces[f_id]
					if ep is not None:
						prop_data = extract_property_data(ep, 'element')
						prop_data['face_id'] = f_id
						try:
							vertices = shape.getSubshapeChildren(f_id, MpcSubshapeType.Face, MpcSubshapeType.Vertex)
							prop_data['vertex_coordinates'] = [extract_vertex_coordinates(shape, v_id) for v_id in vertices]
						except:
							prop_data['vertex_coordinates'] = []
						geometry_data['properties']['element']['faces'].append(prop_data)

			# Element Properties su SOLIDS
			if geometry_data['topology']['num_solids'] > 0:
				ep_solids = geom.elementPropertyAssignment.onSolids
				for s_id in range(len(ep_solids)):
					ep = ep_solids[s_id]
					if ep is not None:
						prop_data = extract_property_data(ep, 'element')
						prop_data['solid_id'] = s_id
						try:
							vertices = shape.getSubshapeChildren(s_id, MpcSubshapeType.Solid, MpcSubshapeType.Vertex)
							prop_data['vertex_coordinates'] = [extract_vertex_coordinates(shape, v_id) for v_id in vertices]
						except:
							prop_data['vertex_coordinates'] = []
						geometry_data['properties']['element']['solids'].append(prop_data)

		except Exception as e:
			geometry_data['errors'].append(f"Errore analisi element properties: {str(e)}")

	except Exception as e:
		geometry_data['errors'].append(f"Errore generale: {str(e)}")

	return geometry_data

# ==============================================================================
# MODALITÀ ANALISI
# ==============================================================================

def run_analyze_mode():
	"""Esegue la modalità ANALISI"""
	print("\n[MODALITÀ ANALISI ATTIVA]")
	print("Analizzando minuziosamente le geometrie...")
	print("-"*80)

	# CONTROLLO OMONIMIE
	print("\n[CONTROLLO OMONIMIE]")
	print("Verifico che non ci siano nomi simili che possono causare problemi...")
	
	geometry_names = [geom.name for geom_id, geom in doc.geometries.items()]
	potential_conflicts = []

	# Cerca potenziali conflitti
	for i, name1 in enumerate(geometry_names):
		for j, name2 in enumerate(geometry_names):
			if i >= j:  # Evita confronti duplicati
				continue

			# Controlla se un nome è contenuto nell'altro
			if name1 in name2 or name2 in name1:
				# Se i nomi sono esattamente uguali o uno contiene l'altro
				if name1 != name2:
					conflict = (name1, name2) if len(name1) < len(name2) else (name2, name1)
					if conflict not in potential_conflicts:
						potential_conflicts.append(conflict)

	if potential_conflicts:
		print("\n⚠️  ATTENZIONE: Rilevate potenziali omonimie!")
		print("="*80)
		print("Le seguenti coppie di nomi potrebbero causare problemi durante l'import:")
		print()
		for name1, name2 in potential_conflicts:
			print(f"  • '{name1}' ↔ '{name2}'")
			print(f"    ('{name1}' è contenuto in '{name2}')")
			print()

		print("="*80)
		print("\n⚠️  RACCOMANDAZIONE:")
		print("Rinomina le geometrie per evitare confusione durante il matching.")
		print("Esempio: 'Lines' → 'Lines_Main', 'Lines(1)' → 'Lines_A', etc.")
		print()
		print("Vuoi continuare comunque? Il sistema userà il matching intelligente,")
		print("ma potrebbero verificarsi errori nell'assegnazione delle proprietà.")
		print()

		risposta = input("Continuare? (s/N): ").strip().lower()

		if risposta not in ['s', 'si', 'y', 'yes']:
			print("\n✗ Analisi annullata. Rinomina le geometrie e riesegui lo script.")
			return

		print("\n⚠️  Proseguo con l'analisi (a tuo rischio)...")
	else:
		print("✓ Nessuna omonimia rilevata")

	all_geometries_data = {
		'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
		'total_geometries': len(doc.geometries),
		'total_interactions': len(doc.interactions),
		'geometries': [],
		'interactions': []
	}

	# Analizza ogni geometria
	for idx, (geom_id, geom) in enumerate(doc.geometries.items(), 1):
		print(f"  [{idx}/{len(doc.geometries)}] Analizzando: [{geom_id}] {geom.name}")

		geom_data = analyze_geometry_comprehensive(geom_id, geom)
		all_geometries_data['geometries'].append(geom_data)

		App.processEvents()

	# Analizza le interazioni
	print("\n[ANALISI INTERAZIONI]")
	print(f"Totale interazioni: {len(doc.interactions)}")
	print("-"*80)

	for idx, (int_id, interaction) in enumerate(doc.interactions.items(), 1):
		print(f"  [{idx}/{len(doc.interactions)}] Analizzando interazione: [{int_id}] {interaction.name}")

		int_data = extract_interaction_data(int_id, interaction)
		all_geometries_data['interactions'].append(int_data)

		App.processEvents()

	# EXPORT JSON con proprietà
	print("\n[EXPORT JSON]")
	json_filename = os.path.join(output_folder, "STKO_Analysis.json")
	with open(json_filename, 'w', encoding='utf-8') as f:
		json.dump(all_geometries_data, f, indent=2, ensure_ascii=False)
	print(f"✓ Esportato JSON: {json_filename}")

	# EXPORT GEOMETRIE
	print("\n[EXPORT GEOMETRIE]")
	print(f"Cartella: {geometries_folder}/")
	print("-"*80)

	export_count = 0
	export_errors = 0

	for idx, (geom_id, geom) in enumerate(doc.geometries.items(), 1):
		try:
			safe_name = "".join(c for c in geom.name if c.isalnum() or c in (' ', '-', '_')).strip()
			if not safe_name:
				safe_name = f"geometry_{geom_id}"

			nome_geometry = f"geom_{geom_id}_{safe_name}"
			new_dir = os.path.join(geometries_folder, nome_geometry)

			# Seleziona geometria
			doc.scene.select(geom)

			# Imposta path nelle QSettings per pre-popolare il dialog
			sett = QSettings()
			sett.beginGroup('FileDialogManager')
			sett.beginGroup('LD_ImpGeom')
			sett.setValue('LastDirectory', new_dir)
			sett.endGroup()
			sett.endGroup()

			# Esegui comando export (apre dialog STKO)
			App.runCommand("ExportGeometry")

			# Deseleziona tutto
			doc.scene.unselectAll()

			# Salva percorso nel JSON
			all_geometries_data['geometries'][idx-1]['exported_file'] = new_dir

			export_count += 1
			print(f"  [{idx}/{len(doc.geometries)}] ✓ {geom.name}")

		except Exception as e:
			export_errors += 1
			print(f"  [{idx}/{len(doc.geometries)}] ✗ Errore: {str(e)}")
			all_geometries_data['geometries'][idx-1]['exported_file'] = None
			doc.scene.unselectAll()

		App.processEvents()

	# Ri-esporta JSON con percorsi geometrie aggiornati
	with open(json_filename, 'w', encoding='utf-8') as f:
		json.dump(all_geometries_data, f, indent=2, ensure_ascii=False)

	print(f"\n✓ Geometrie esportate: {export_count}/{len(doc.geometries)}")
	if export_errors > 0:
		print(f"✗ Errori export: {export_errors}")

	print("\n" + "="*80)
	print("ANALISI COMPLETATA!")
	print(f"Geometrie analizzate: {all_geometries_data['total_geometries']}")
	print(f"Interazioni analizzate: {all_geometries_data['total_interactions']}")
	print(f"File salvati in: {output_folder}/")
	print("="*80)

# ==============================================================================
# COORDINATE MATCHING SYSTEM
# ==============================================================================

# Tolleranza per confronto coordinate (gestisce arrotondamenti numerici)
COORD_TOLERANCE = 1e-6

def coordinates_match(coord1, coord2, tolerance=COORD_TOLERANCE):
	"""Confronta due coordinate con tolleranza"""
	if coord1 is None or coord2 is None:
		return False
	if 'x' not in coord1 or 'x' not in coord2:
		return False

	return (abs(coord1['x'] - coord2['x']) < tolerance and
	        abs(coord1['y'] - coord2['y']) < tolerance and
	        abs(coord1['z'] - coord2['z']) < tolerance)

def find_vertex_by_coordinates(shape, target_coords):
	"""Trova l'ID del vertice con le coordinate specificate"""
	num_vertices = shape.getNumberOfSubshapes(MpcSubshapeType.Vertex)

	for v_id in range(num_vertices):
		vertex_coords = extract_vertex_coordinates(shape, v_id)
		if coordinates_match(vertex_coords, target_coords):
			return v_id

	return None

def find_edge_by_vertices(shape, target_vertex_coords):
	"""Trova l'ID dell'edge con i vertici specificati (confronto coordinate)"""
	num_edges = shape.getNumberOfSubshapes(MpcSubshapeType.Edge)

	for e_id in range(num_edges):
		try:
			# Ottieni vertici dell'edge
			vertices = shape.getSubshapeChildren(e_id, MpcSubshapeType.Edge, MpcSubshapeType.Vertex)
			edge_coords = [extract_vertex_coordinates(shape, v_id) for v_id in vertices]

			# Confronta coordinate (l'ordine potrebbe essere invertito)
			if len(edge_coords) == len(target_vertex_coords):
				# Match diretto
				match_direct = all(
					any(coordinates_match(ec, tc) for tc in target_vertex_coords)
					for ec in edge_coords
				)
				if match_direct:
					return e_id
		except:
			pass

	return None

def find_face_by_vertices(shape, target_vertex_coords):
	"""Trova l'ID della face con i vertici specificati (confronto coordinate)"""
	num_faces = shape.getNumberOfSubshapes(MpcSubshapeType.Face)

	for f_id in range(num_faces):
		try:
			# Ottieni vertici della face
			vertices = shape.getSubshapeChildren(f_id, MpcSubshapeType.Face, MpcSubshapeType.Vertex)
			face_coords = [extract_vertex_coordinates(shape, v_id) for v_id in vertices]

			# Confronta coordinate
			if len(face_coords) == len(target_vertex_coords):
				# Tutti i vertici target devono matchare
				match = all(
					any(coordinates_match(fc, tc) for tc in target_vertex_coords)
					for fc in face_coords
				)
				if match:
					return f_id
		except:
			pass

	return None

def find_solid_by_vertices(shape, target_vertex_coords):
	"""Trova l'ID del solid con i vertici specificati (confronto coordinate)"""
	num_solids = shape.getNumberOfSubshapes(MpcSubshapeType.Solid)

	for s_id in range(num_solids):
		try:
			# Ottieni vertici del solid
			vertices = shape.getSubshapeChildren(s_id, MpcSubshapeType.Solid, MpcSubshapeType.Vertex)
			solid_coords = [extract_vertex_coordinates(shape, v_id) for v_id in vertices]

			# Confronta coordinate
			if len(solid_coords) == len(target_vertex_coords):
				# Tutti i vertici target devono matchare
				match = all(
					any(coordinates_match(sc, tc) for tc in target_vertex_coords)
					for sc in solid_coords
				)
				if match:
					return s_id
		except:
			pass

	return None

def find_matching_subgeometry_index(shape, geom_data, subgeom_type):
	"""
	Trova quale subgeometry del JSON (solid/edge/face) corrisponde alla geometria importata
	confrontando le coordinate dei vertici

	Returns: index del subgeometry nel JSON che matcha, o None
	"""
	# Ottieni tutti i vertici della geometria importata
	num_vertices = shape.getNumberOfSubshapes(MpcSubshapeType.Vertex)
	imported_coords = []
	for v_id in range(num_vertices):
		coords = extract_vertex_coordinates(shape, v_id)
		if coords['x'] is not None:
			imported_coords.append(coords)

	if not imported_coords:
		return None

	# Cerca quale subgeometry del JSON ha gli stessi vertici
	if subgeom_type == 'solid':
		props_list = geom_data['properties']['physical']['solids'] + geom_data['properties']['element']['solids']
	elif subgeom_type == 'edge':
		props_list = geom_data['properties']['physical']['edges'] + geom_data['properties']['element']['edges']
	elif subgeom_type == 'face':
		props_list = geom_data['properties']['physical']['faces'] + geom_data['properties']['element']['faces']
	else:
		return None

	# Raggruppa per solid/edge/face id
	subgeom_coords_map = {}
	for prop in props_list:
		if subgeom_type == 'solid':
			idx = prop.get('solid_id')
		elif subgeom_type == 'edge':
			idx = prop.get('edge_id')
		elif subgeom_type == 'face':
			idx = prop.get('face_id')

		if idx is not None and idx not in subgeom_coords_map:
			coords = prop.get('vertex_coordinates', [])
			if coords:
				subgeom_coords_map[idx] = coords

	# Confronta coordinate
	for idx, json_coords in subgeom_coords_map.items():
		# Verifica che il numero di vertici sia uguale
		if len(json_coords) != len(imported_coords):
			continue

		# Verifica che tutti i vertici matchino
		match = all(
			any(coordinates_match(ic, jc) for jc in json_coords)
			for ic in imported_coords
		)

		if match:
			return idx

	return None

def get_shape_type_from_name(shape_type_name):
	"""Converte il nome del tipo di shape in enum"""
	type_map = {
		"VERTEX": TopAbs_ShapeEnum.TopAbs_VERTEX,
		"EDGE": TopAbs_ShapeEnum.TopAbs_EDGE,
		"WIRE": TopAbs_ShapeEnum.TopAbs_WIRE,
		"FACE": TopAbs_ShapeEnum.TopAbs_FACE,
		"SHELL": TopAbs_ShapeEnum.TopAbs_SHELL,
		"SOLID": TopAbs_ShapeEnum.TopAbs_SOLID,
		"COMPSOLID": TopAbs_ShapeEnum.TopAbs_COMPSOLID,
		"COMPOUND": TopAbs_ShapeEnum.TopAbs_COMPOUND,
	}
	return type_map.get(shape_type_name)

def get_mpc_subshape_type_name(mpc_subshape_type):
	"""Converte MpcSubshapeType in nome stringa"""
	type_map = {
		MpcSubshapeType.Vertex: "VERTEX",
		MpcSubshapeType.Edge: "EDGE",
		MpcSubshapeType.Face: "FACE",
		MpcSubshapeType.Solid: "SOLID",
	}
	return type_map.get(mpc_subshape_type, "UNKNOWN")

def get_mpc_subshape_type_from_name(type_name):
	"""Converte nome stringa in MpcSubshapeType"""
	type_map = {
		"VERTEX": MpcSubshapeType.Vertex,
		"EDGE": MpcSubshapeType.Edge,
		"FACE": MpcSubshapeType.Face,
		"SOLID": MpcSubshapeType.Solid,
	}
	return type_map.get(type_name)

def get_interaction_type_from_string(type_string):
	"""Converte la stringa del tipo di interazione in enum MpcInteractionType"""
	if not type_string:
		return MpcInteractionType.NodeToNode  # Default

	# Estrai il nome del tipo dalla stringa (es. "MpcInteractionType.NodeToNode" -> "NodeToNode")
	if '.' in type_string:
		type_name = type_string.split('.')[-1]
	else:
		type_name = type_string

	# Prova a ottenere il tipo direttamente dall'enum usando getattr
	try:
		interaction_type = getattr(MpcInteractionType, type_name)
		return interaction_type
	except AttributeError:
		print(f"    [WARNING] Tipo interazione '{type_name}' non trovato, uso NodeToNode come default")
		return MpcInteractionType.NodeToNode

def find_subshape_by_coordinates(shape, target_coords, subshape_type_name):
	"""Trova la subshape con le coordinate specificate"""
	subshape_type = get_mpc_subshape_type_from_name(subshape_type_name)
	if not subshape_type:
		return None

	if subshape_type == MpcSubshapeType.Vertex:
		# Per i vertici, cerca direttamente
		return find_vertex_by_coordinates(shape, target_coords[0] if target_coords else None)
	elif subshape_type == MpcSubshapeType.Edge:
		return find_edge_by_vertices(shape, target_coords)
	elif subshape_type == MpcSubshapeType.Face:
		return find_face_by_vertices(shape, target_coords)
	elif subshape_type == MpcSubshapeType.Solid:
		return find_solid_by_vertices(shape, target_coords)

	return None

def assign_properties_to_geometries(geometries_data, created_physical_props, created_element_props):
	"""Assegna le proprietà alle geometrie importate tramite coordinate matching"""
	print("\n[FASE 4] Assegnazione Proprietà tramite Coordinate Matching")
	print("-"*80)

	assigned_count = 0
	failed_count = 0

	# Per ogni geometria nel documento corrente
	for geom_id, geom in doc.geometries.items():
		# Cerca la geometria corrispondente nel JSON (matching per nome flessibile e specifico)
		geom_data = None
		best_match_score = 0

		for gd in geometries_data:
			json_name = gd['name']
			imported_name = geom.name

			# Calcola score di matching (più alto = migliore)
			match_score = 0

			# Match esatto ha priorità massima
			if json_name == imported_name:
				match_score = 100
			# Nome JSON completamente contenuto nel nome importato
			elif json_name in imported_name:
				# Dai più punti se il match è più lungo
				match_score = 50 + len(json_name)
			# Nome importato completamente contenuto nel JSON
			elif imported_name in json_name:
				match_score = 30 + len(imported_name)

			# Se questo match è migliore del precedente, usalo
			if match_score > best_match_score:
				best_match_score = match_score
				geom_data = gd

		if not geom_data or best_match_score == 0:
			print(f"\n  [SKIP] Geometria '{geom.name}' non trovata nel JSON")
			continue

		print(f"\n  Match trovato: '{geom.name}' ↔ '{geom_data['name']}' (score: {best_match_score})")
		print(f"  Assegnando proprietà a: {geom.name}")
		shape = geom.shape

		# Determina il tipo di geometria e trova il subgeometry corrispondente nel JSON
		shape_type = geom_data['shape_type']
		matched_subgeom_index = None

		if shape_type in ['SOLID', 'COMPSOLID']:
			# Per solidi, trova quale solid del JSON corrisponde
			matched_subgeom_index = find_matching_subgeometry_index(shape, geom_data, 'solid')
			if matched_subgeom_index is not None:
				print(f"    → Match trovato: Solid {matched_subgeom_index} del JSON")
			else:
				print(f"    → Nessun solid matching trovato, assegno a tutti")

		elif shape_type == 'EDGE':
			# Per edge, trova quale edge del JSON corrisponde
			matched_subgeom_index = find_matching_subgeometry_index(shape, geom_data, 'edge')
			if matched_subgeom_index is not None:
				print(f"    → Match trovato: Edge {matched_subgeom_index} del JSON")
			else:
				print(f"    → Nessun edge matching trovato, assegno a tutti")

		elif shape_type == 'FACE':
			# Per face, trova quale face del JSON corrisponde
			matched_subgeom_index = find_matching_subgeometry_index(shape, geom_data, 'face')
			if matched_subgeom_index is not None:
				print(f"    → Match trovato: Face {matched_subgeom_index} del JSON")
			else:
				print(f"    → Nessuna face matching trovata, assegno a tutti")

		# ═══════════════════════════════════════════════════════════
		# PHYSICAL PROPERTIES - VERTICES
		# ═══════════════════════════════════════════════════════════
		for prop_data in geom_data['properties']['physical']['vertices']:
			try:
				target_coords = prop_data.get('coordinates')
				if not target_coords:
					continue

				# Trova vertice con queste coordinate
				v_id = find_vertex_by_coordinates(shape, target_coords)

				if v_id is not None:
					prop_name = prop_data['property_name']
					if prop_name in created_physical_props:
						pp = created_physical_props[prop_name]
						geom.physicalPropertyAssignment.onVertices[v_id] = pp
						assigned_count += 1
						print(f"    ✓ Physical Property '{prop_name}' → Vertex {v_id}")
				else:
					failed_count += 1
					print(f"    ✗ Vertex non trovato per {prop_data['property_name']}")
			except Exception as e:
				failed_count += 1
				print(f"    ✗ Errore: {str(e)}")

		# ═══════════════════════════════════════════════════════════
		# PHYSICAL PROPERTIES - EDGES
		# ═══════════════════════════════════════════════════════════
		for prop_data in geom_data['properties']['physical']['edges']:
			try:
				# Se abbiamo un match specifico, assegna SOLO le proprietà di quell'edge
				if matched_subgeom_index is not None and prop_data.get('edge_id') != matched_subgeom_index:
					continue

				target_coords = prop_data.get('vertex_coordinates', [])
				if not target_coords:
					continue

				# Trova edge con questi vertici
				e_id = find_edge_by_vertices(shape, target_coords)

				if e_id is not None:
					prop_name = prop_data['property_name']
					if prop_name in created_physical_props:
						pp = created_physical_props[prop_name]
						geom.physicalPropertyAssignment.onEdges[e_id] = pp
						assigned_count += 1
						print(f"    ✓ Physical Property '{prop_name}' → Edge {e_id}")
				else:
					failed_count += 1
					print(f"    ✗ Edge non trovato per {prop_data['property_name']}")
			except Exception as e:
				failed_count += 1
				print(f"    ✗ Errore: {str(e)}")

		# ═══════════════════════════════════════════════════════════
		# PHYSICAL PROPERTIES - FACES
		# ═══════════════════════════════════════════════════════════
		for prop_data in geom_data['properties']['physical']['faces']:
			try:
				# Se abbiamo un match specifico, assegna SOLO le proprietà di quella face
				if matched_subgeom_index is not None and prop_data.get('face_id') != matched_subgeom_index:
					continue

				target_coords = prop_data.get('vertex_coordinates', [])
				if not target_coords:
					continue

				# Trova face con questi vertici
				f_id = find_face_by_vertices(shape, target_coords)

				if f_id is not None:
					prop_name = prop_data['property_name']
					if prop_name in created_physical_props:
						pp = created_physical_props[prop_name]
						geom.physicalPropertyAssignment.onFaces[f_id] = pp
						assigned_count += 1
						print(f"    ✓ Physical Property '{prop_name}' → Face {f_id}")
				else:
					failed_count += 1
					print(f"    ✗ Face non trovata per {prop_data['property_name']}")
			except Exception as e:
				failed_count += 1
				print(f"    ✗ Errore: {str(e)}")

		# ═══════════════════════════════════════════════════════════
		# PHYSICAL PROPERTIES - SOLIDS
		# ═══════════════════════════════════════════════════════════
		for prop_data in geom_data['properties']['physical']['solids']:
			try:
				# Se abbiamo un match specifico, assegna SOLO le proprietà di quel solid
				if matched_subgeom_index is not None and prop_data.get('solid_id') != matched_subgeom_index:
					continue

				target_coords = prop_data.get('vertex_coordinates', [])
				if not target_coords:
					continue

				# Trova solid con questi vertici
				s_id = find_solid_by_vertices(shape, target_coords)

				if s_id is not None:
					prop_name = prop_data['property_name']
					if prop_name in created_physical_props:
						pp = created_physical_props[prop_name]
						geom.physicalPropertyAssignment.onSolids[s_id] = pp
						assigned_count += 1
						print(f"    ✓ Physical Property '{prop_name}' → Solid {s_id}")
				else:
					failed_count += 1
					print(f"    ✗ Solid non trovato per {prop_data['property_name']}")
			except Exception as e:
				failed_count += 1
				print(f"    ✗ Errore: {str(e)}")

		# ═══════════════════════════════════════════════════════════
		# ELEMENT PROPERTIES - VERTICES
		# ═══════════════════════════════════════════════════════════
		for prop_data in geom_data['properties']['element']['vertices']:
			try:
				target_coords = prop_data.get('coordinates')
				if not target_coords:
					continue

				v_id = find_vertex_by_coordinates(shape, target_coords)

				if v_id is not None:
					prop_name = prop_data['property_name']
					if prop_name in created_element_props:
						ep = created_element_props[prop_name]
						geom.elementPropertyAssignment.onVertices[v_id] = ep
						assigned_count += 1
						print(f"    ✓ Element Property '{prop_name}' → Vertex {v_id}")
				else:
					failed_count += 1
					print(f"    ✗ Vertex non trovato per {prop_data['property_name']}")
			except Exception as e:
				failed_count += 1
				print(f"    ✗ Errore: {str(e)}")

		# ═══════════════════════════════════════════════════════════
		# ELEMENT PROPERTIES - EDGES
		# ═══════════════════════════════════════════════════════════
		for prop_data in geom_data['properties']['element']['edges']:
			try:
				# Se abbiamo un match specifico, assegna SOLO le proprietà di quell'edge
				if matched_subgeom_index is not None and prop_data.get('edge_id') != matched_subgeom_index:
					continue

				target_coords = prop_data.get('vertex_coordinates', [])
				if not target_coords:
					continue

				e_id = find_edge_by_vertices(shape, target_coords)

				if e_id is not None:
					prop_name = prop_data['property_name']
					if prop_name in created_element_props:
						ep = created_element_props[prop_name]
						geom.elementPropertyAssignment.onEdges[e_id] = ep
						assigned_count += 1
						print(f"    ✓ Element Property '{prop_name}' → Edge {e_id}")
				else:
					failed_count += 1
					print(f"    ✗ Edge non trovato per {prop_data['property_name']}")
			except Exception as e:
				failed_count += 1
				print(f"    ✗ Errore: {str(e)}")

		# ═══════════════════════════════════════════════════════════
		# ELEMENT PROPERTIES - FACES
		# ═══════════════════════════════════════════════════════════
		for prop_data in geom_data['properties']['element']['faces']:
			try:
				# Se abbiamo un match specifico, assegna SOLO le proprietà di quella face
				if matched_subgeom_index is not None and prop_data.get('face_id') != matched_subgeom_index:
					continue

				target_coords = prop_data.get('vertex_coordinates', [])
				if not target_coords:
					continue

				f_id = find_face_by_vertices(shape, target_coords)

				if f_id is not None:
					prop_name = prop_data['property_name']
					if prop_name in created_element_props:
						ep = created_element_props[prop_name]
						geom.elementPropertyAssignment.onFaces[f_id] = ep
						assigned_count += 1
						print(f"    ✓ Element Property '{prop_name}' → Face {f_id}")
				else:
					failed_count += 1
					print(f"    ✗ Face non trovata per {prop_data['property_name']}")
			except Exception as e:
				failed_count += 1
				print(f"    ✗ Errore: {str(e)}")

		# ═══════════════════════════════════════════════════════════
		# ELEMENT PROPERTIES - SOLIDS
		# ═══════════════════════════════════════════════════════════
		for prop_data in geom_data['properties']['element']['solids']:
			try:
				# Se abbiamo un match specifico, assegna SOLO le proprietà di quel solid
				if matched_subgeom_index is not None and prop_data.get('solid_id') != matched_subgeom_index:
					continue

				target_coords = prop_data.get('vertex_coordinates', [])
				if not target_coords:
					continue

				s_id = find_solid_by_vertices(shape, target_coords)

				if s_id is not None:
					prop_name = prop_data['property_name']
					if prop_name in created_element_props:
						ep = created_element_props[prop_name]
						geom.elementPropertyAssignment.onSolids[s_id] = ep
						assigned_count += 1
						print(f"    ✓ Element Property '{prop_name}' → Solid {s_id}")
				else:
					failed_count += 1
					print(f"    ✗ Solid non trovato per {prop_data['property_name']}")
			except Exception as e:
				failed_count += 1
				print(f"    ✗ Errore: {str(e)}")

		# Commit changes per questa geometria
		doc.commitChanges()

	print("\n" + "-"*80)
	print(f"✓ Proprietà assegnate: {assigned_count}")
	if failed_count > 0:
		print(f"✗ Assegnazioni fallite: {failed_count}")

	return assigned_count, failed_count

def recreate_interactions(interactions_data, created_physical_props, created_element_props):
	"""Ricrea le interazioni salvate nel JSON"""
	print("\n[FASE 5] Ricreazione Interazioni")
	print("-"*80)

	if not interactions_data:
		print("✓ Nessuna interazione da ricreare")
		return 0, 0

	created_count = 0
	failed_count = 0

	for int_data in interactions_data:
		print(f"\n  Ricreando interazione: {int_data['name']}")

		try:
			# Trova o crea l'interazione
			interaction = None
			interaction_id = None

			# Cerca se esiste già un'interazione con lo stesso nome
			for k, existing_int in doc.interactions.items():
				if existing_int.name == int_data['name']:
					interaction = existing_int
					interaction_id = k
					print(f"    ✓ Usando interazione esistente: {int_data['name']}")
					break

			# Se non esiste, creane una nuova
			if not interaction:
				# Crea nuova interazione con costruttore corretto
				interaction_id = doc.interactions.getlastkey(0) + 1
				interaction = MpcInteraction(interaction_id, int_data['name'])

				# Imposta tipo di interazione dal JSON
				type_string = int_data.get('type')
				print(f"    Tipo dal JSON: {type_string}")
				interaction.type = get_interaction_type_from_string(type_string)
				print(f"    Tipo impostato: {interaction.type}")

				# Imposta proprietà fisiche/elemento se presenti
				if int_data['physical_property']:
					prop_name = int_data['physical_property']['property_name']
					if prop_name in created_physical_props:
						interaction.physicalProperty = created_physical_props[prop_name]
						print(f"    ✓ Physical Property: {prop_name}")

				if int_data['element_property']:
					prop_name = int_data['element_property']['property_name']
					if prop_name in created_element_props:
						interaction.elementProperty = created_element_props[prop_name]
						print(f"    ✓ Element Property: {prop_name}")

				# Aggiungi l'interazione al documento
				doc.addInteraction(interaction)
				print(f"    ✓ Interazione creata: {int_data['name']} [ID: {interaction_id}]")

			# Ricrea MASTERS
			masters_added = 0
			for master_data in int_data['masters']:
				try:
					# Trova TUTTE le geometrie con nome simile (potrebbero essere divise)
					candidate_geoms = []
					for geom_id, geom in doc.geometries.items():
						if geom.name == master_data['geometry_name'] or master_data['geometry_name'] in geom.name:
							candidate_geoms.append(geom)

					if not candidate_geoms:
						print(f"    ✗ Geometria master non trovata: {master_data['geometry_name']}")
						failed_count += 1
						continue

					# Prova a trovare la subshape in ciascuna geometria candidata
					target_geom = None
					subshape_id = None

					for geom in candidate_geoms:
						# Cerca la subshape tramite coordinate matching
						found_id = find_subshape_by_coordinates(
							geom.shape,
							master_data['vertex_coordinates'],
							master_data['subshape_type']
						)

						if found_id is not None:
							target_geom = geom
							subshape_id = found_id
							break

					if target_geom is None or subshape_id is None:
						print(f"    ✗ Subshape master non trovata: {master_data['subshape_type']} in {master_data['geometry_name']}")
						failed_count += 1
						continue

					# Crea l'item master con costruttore corretto
					subshape_type = get_mpc_subshape_type_from_name(master_data['subshape_type'])
					master_item = MpcInteractionItem(target_geom, subshape_type, subshape_id)

					# Aggiungi ai masters
					interaction.items.masters.append(master_item)
					masters_added += 1
					print(f"    ✓ Master aggiunto: {master_data['subshape_type']} da {target_geom.name}")

				except Exception as e:
					print(f"    ✗ Errore creazione master: {str(e)}")
					failed_count += 1

			print(f"    ✓ Masters aggiunti: {masters_added}/{len(int_data['masters'])}")

			# Ricrea SLAVES
			slaves_added = 0
			for slave_data in int_data['slaves']:
				try:
					# Trova TUTTE le geometrie con nome simile (potrebbero essere divise)
					candidate_geoms = []
					for geom_id, geom in doc.geometries.items():
						if geom.name == slave_data['geometry_name'] or slave_data['geometry_name'] in geom.name:
							candidate_geoms.append(geom)

					if not candidate_geoms:
						print(f"    ✗ Geometria slave non trovata: {slave_data['geometry_name']}")
						failed_count += 1
						continue

					# Prova a trovare la subshape in ciascuna geometria candidata
					target_geom = None
					subshape_id = None

					for geom in candidate_geoms:
						# Cerca la subshape tramite coordinate matching
						found_id = find_subshape_by_coordinates(
							geom.shape,
							slave_data['vertex_coordinates'],
							slave_data['subshape_type']
						)

						if found_id is not None:
							target_geom = geom
							subshape_id = found_id
							break

					if target_geom is None or subshape_id is None:
						print(f"    ✗ Subshape slave non trovata: {slave_data['subshape_type']} in {slave_data['geometry_name']}")
						failed_count += 1
						continue

					# Crea l'item slave con costruttore corretto
					subshape_type = get_mpc_subshape_type_from_name(slave_data['subshape_type'])
					slave_item = MpcInteractionItem(target_geom, subshape_type, subshape_id)

					# Aggiungi agli slaves
					interaction.items.slaves.append(slave_item)
					slaves_added += 1
					print(f"    ✓ Slave aggiunto: {slave_data['subshape_type']} da {target_geom.name}")

				except Exception as e:
					print(f"    ✗ Errore creazione slave: {str(e)}")
					failed_count += 1

			print(f"    ✓ Slaves aggiunti: {slaves_added}/{len(int_data['slaves'])}")

			# Commit delle modifiche
			doc.commitChanges()
			created_count += 1

		except Exception as e:
			print(f"    ✗ Errore ricreazione interazione: {str(e)}")
			failed_count += 1

	print("\n" + "-"*80)
	print(f"✓ Interazioni ricreate: {created_count}/{len(interactions_data)}")
	if failed_count > 0:
		print(f"✗ Errori durante la ricreazione: {failed_count}")

	return created_count, failed_count

# ==============================================================================
# MODALITÀ COPY
# ==============================================================================

def load_json_data(json_path):
	"""Carica i dati dal file JSON"""
	try:
		with open(json_path, 'r', encoding='utf-8') as f:
			data = json.load(f)
		return data
	except Exception as e:
		print(f"✗ Errore caricamento JSON: {str(e)}")
		return None

def set_attribute_value(attr, value):
	"""Imposta il valore di un attributo XObject"""
	try:
		if hasattr(attr, 'real') and isinstance(value, (int, float)):
			attr.real = float(value)
		elif hasattr(attr, 'integer') and isinstance(value, int):
			attr.integer = value
		elif hasattr(attr, 'boolean') and isinstance(value, bool):
			attr.boolean = value
		elif hasattr(attr, 'string') and isinstance(value, str):
			attr.string = value
		elif hasattr(attr, 'quantityScalar') and isinstance(value, (int, float)):
			attr.quantityScalar.value = float(value)
		elif hasattr(attr, 'quantityVector3') and isinstance(value, list):
			v = attr.quantityVector3
			if len(value) >= 3:
				v.setValueAt(0, value[0])
				v.setValueAt(1, value[1])
				v.setValueAt(2, value[2])
		elif hasattr(attr, 'index') and isinstance(value, int):
			attr.index = value
	except Exception as e:
		print(f"    [WARNING] Errore impostazione attributo: {str(e)}")

def create_or_get_physical_property(prop_data):
	"""Crea o recupera una physical property esistente"""
	prop_name = prop_data['property_name']
	prop_type = prop_data['property_type']

	# Cerca se esiste già una proprietà con lo stesso nome
	for _, existing_pp in doc.physicalProperties.items():
		if existing_pp.name == prop_name:
			print(f"    ✓ Usando physical property esistente: {prop_name}")
			return existing_pp

	# Crea nuova physical property
	try:
		print(f"    Creando physical property: {prop_name} (tipo: {prop_type})")

		pp_meta = doc.metaDataPhysicalProperty(prop_type)
		pp_xobj = MpcXObject.createInstanceOf(pp_meta)

		# Applica parametri
		if 'parameters' in prop_data and prop_data['parameters']:
			for param_name, param_value in prop_data['parameters'].items():
				try:
					if param_name in pp_xobj.attributes:
						attr = pp_xobj.attributes[param_name]
						set_attribute_value(attr, param_value)
						print(f"      - {param_name} = {param_value}")
				except Exception as e:
					print(f"      [WARNING] Errore parametro {param_name}: {str(e)}")

		new_pp = MpcProperty()
		new_pp.id = doc.physicalProperties.getlastkey(0) + 1
		new_pp.name = prop_name
		new_pp.XObject = pp_xobj

		doc.addPhysicalProperty(new_pp)
		doc.commitChanges()

		print(f"    ✓ Physical property creata: {prop_name} [ID: {new_pp.id}]")
		return new_pp

	except Exception as e:
		print(f"    ✗ Errore creazione physical property: {str(e)}")
		return None

def create_or_get_element_property(prop_data):
	"""Crea o recupera una element property esistente"""
	prop_name = prop_data['property_name']
	prop_type = prop_data['property_type']

	# Cerca se esiste già
	for _, existing_ep in doc.elementProperties.items():
		if existing_ep.name == prop_name:
			print(f"    ✓ Usando element property esistente: {prop_name}")
			return existing_ep

	# Crea nuova element property
	try:
		print(f"    Creando element property: {prop_name} (tipo: {prop_type})")

		ep_meta = doc.metaDataElementProperty(prop_type)
		ep_xobj = MpcXObject.createInstanceOf(ep_meta)

		# Applica parametri
		if 'parameters' in prop_data and prop_data['parameters']:
			for param_name, param_value in prop_data['parameters'].items():
				try:
					if param_name in ep_xobj.attributes:
						attr = ep_xobj.attributes[param_name]
						set_attribute_value(attr, param_value)
						print(f"      - {param_name} = {param_value}")
				except Exception as e:
					print(f"      [WARNING] Errore parametro {param_name}: {str(e)}")

		new_ep = MpcElementProperty()
		new_ep.id = doc.elementProperties.getlastkey(0) + 1
		new_ep.name = prop_name
		new_ep.XObject = ep_xobj

		doc.addElementProperty(new_ep)
		doc.commitChanges()

		print(f"    ✓ Element property creata: {prop_name} [ID: {new_ep.id}]")
		return new_ep

	except Exception as e:
		print(f"    ✗ Errore creazione element property: {str(e)}")
		return None

def run_copy_mode():
	"""Esegue la modalità COPY"""
	print("\n[MODALITÀ COPY ATTIVA]")
	print("Importando geometrie e ricreando proprietà...")
	print("-"*80)

	# Carica JSON
	print("\n[FASE 1] Caricamento JSON")
	json_path = os.path.join(input_folder, "STKO_Analysis.json")
	json_data = load_json_data(json_path)

	if not json_data:
		print("✗ Impossibile procedere senza dati JSON")
		return

	geometries_data = json_data['geometries']
	print(f"✓ Caricate {len(geometries_data)} geometrie dal JSON")

	# IMPORT GEOMETRIE
	print("\n[FASE 2] Import Geometrie")
	print("-"*80)

	# Chiedi estensione file da importare
	print("\nEstensioni disponibili: .stp, .step, .iges, .igs, .brep")
	print("Quale estensione vuoi importare? (premi invio per .stp)")
	# Per ora usiamo .stp come default
	list_p=['.stp','.iges']
	
	# Conta file con quell'estensione nella cartella Geometries
	file_list = []
	for i in list_p:
		estensione = i

		for file in os.listdir(geometries_folder):
			if file.endswith(estensione):
				file_list.append(file)

	numero_file = len(file_list)

	if numero_file == 0:
		print(f"✗ Nessun file {estensione} trovato in {geometries_folder}")
		print("Verifica che i file siano stati esportati correttamente")
		return

	print(f"✓ Trovati {numero_file} file {estensione} da importare")
	print("-"*80)

	# Importa tutti i file
	for i, filename in enumerate(file_list, 1):
		App.clearTerminal()
		print(f"[{i}/{numero_file}] Importando: {filename}")

		file_path = os.path.join(geometries_folder, filename)

		# Imposta path nelle QSettings
		sett = QSettings()
		sett.beginGroup('FileDialogManager')
		sett.beginGroup('LD_ImpGeom')
		sett.setValue('LastDirectory', file_path)
		sett.endGroup()
		sett.endGroup()

		# Esegui comando import (apre dialog STKO)
		App.runCommand('ImportGeometry')

		App.processEvents()

	print("\n" + "="*80)
	print(f"✓ Import completato: {numero_file} geometrie importate")
	print("="*80)

	# RICREA PROPRIETÀ (senza ancora assegnarle)
	print("\n[FASE 3] Ricreazione Proprietà")
	print("-"*80)

	created_physical_props = {}
	created_element_props = {}

	for idx, geom_data in enumerate(geometries_data, 1):
		print(f"\n  [{idx}/{len(geometries_data)}] Analizzando proprietà di: {geom_data['name']}")

		# Physical Properties
		all_physical = (
			geom_data['properties']['physical']['vertices'] +
			geom_data['properties']['physical']['edges'] +
			geom_data['properties']['physical']['faces'] +
			geom_data['properties']['physical']['solids']
		)

		for prop_data in all_physical:
			prop_name = prop_data['property_name']
			if prop_name not in created_physical_props:
				pp = create_or_get_physical_property(prop_data)
				if pp:
					created_physical_props[prop_name] = pp

		# Element Properties
		all_element = (
			geom_data['properties']['element']['vertices'] +
			geom_data['properties']['element']['edges'] +
			geom_data['properties']['element']['faces'] +
			geom_data['properties']['element']['solids']
		)

		for prop_data in all_element:
			prop_name = prop_data['property_name']
			if prop_name not in created_element_props:
				ep = create_or_get_element_property(prop_data)
				if ep:
					created_element_props[prop_name] = ep

	print("\n" + "="*80)
	print(f"✓ Import completato: {numero_file} geometrie")
	print(f"✓ Physical Properties create: {len(created_physical_props)}")
	print(f"✓ Element Properties create: {len(created_element_props)}")
	print("="*80)

	# ASSEGNA PROPRIETÀ TRAMITE COORDINATE MATCHING
	assigned, failed = assign_properties_to_geometries(geometries_data, created_physical_props, created_element_props)

	# RICREA INTERAZIONI
	interactions_data = json_data.get('interactions', [])
	interactions_created, interactions_failed = recreate_interactions(interactions_data, created_physical_props, created_element_props)

	print("\n" + "="*80)
	print("🎉 COPY COMPLETATO!")
	print(f"Geometrie importate: {numero_file}")
	print(f"Proprietà assegnate: {assigned}")
	if failed > 0:
		print(f"⚠️  Assegnazioni fallite: {failed}")
	print(f"Interazioni ricreate: {interactions_created}/{len(interactions_data)}")
	if interactions_failed > 0:
		print(f"⚠️  Errori interazioni: {interactions_failed}")
	print("="*80)

	doc.dirty = True

# ==============================================================================
# ESECUZIONE
# ==============================================================================

if not Copy:
	run_analyze_mode()
else:
	run_copy_mode()