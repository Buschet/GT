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
			prop_data['property_type'] = prop.XObject.getXObjectName()

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

	all_geometries_data = {
		'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
		'total_geometries': len(doc.geometries),
		'geometries': []
	}

	# Analizza ogni geometria
	for idx, (geom_id, geom) in enumerate(doc.geometries.items(), 1):
		print(f"  [{idx}/{len(doc.geometries)}] Analizzando: [{geom_id}] {geom.name}")

		geom_data = analyze_geometry_comprehensive(geom_id, geom)
		all_geometries_data['geometries'].append(geom_data)

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
	print(f"File salvati in: {output_folder}/")
	print("="*80)

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

	import_count = 0
	import_errors = 0

	for idx, geom_data in enumerate(geometries_data, 1):
		geom_name = geom_data['name']
		geom_id = geom_data['id']

		print(f"\n  [{idx}/{len(geometries_data)}] Importando: {geom_name}")

		# Trova file esportato
		safe_name = "".join(c for c in geom_name if c.isalnum() or c in (' ', '-', '_')).strip()
		if not safe_name:
			safe_name = f"geometry_{geom_id}"

		nome_geometry = f"geom_{geom_id}_{safe_name}"
		geometry_path = os.path.join(geometries_folder, nome_geometry)

		# Verifica esistenza (cerca con possibili estensioni)
		found_file = None
		for ext in ['.stp', '.step', '.iges', '.igs', '.brep']:
			test_path = geometry_path + ext
			if os.path.exists(test_path):
				found_file = test_path
				break

		if found_file:
			try:
				# Imposta path per import
				sett = QSettings()
				sett.beginGroup('FileDialogManager')
				sett.beginGroup('LD_ImpGeom')
				sett.setValue('LastDirectory', os.path.dirname(found_file))
				sett.endGroup()
				sett.endGroup()

				# Import geometria tramite dialog
				App.runCommand("ImportGeometry")

				import_count += 1
				print(f"    ✓ Importata da: {found_file}")

			except Exception as e:
				import_errors += 1
				print(f"    ✗ Errore import: {str(e)}")
		else:
			import_errors += 1
			print(f"    ✗ File non trovato: {geometry_path}.*")

		App.processEvents()

	print(f"\n✓ Geometrie importate: {import_count}/{len(geometries_data)}")
	if import_errors > 0:
		print(f"✗ Errori import: {import_errors}")

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
	print("IMPORT COMPLETATO!")
	print(f"Geometrie importate: {import_count}")
	print(f"Physical Properties create: {len(created_physical_props)}")
	print(f"Element Properties create: {len(created_element_props)}")
	print("\n💡 PROSSIMO STEP:")
	print("   Implementare coordinate matching per assegnare proprietà")
	print("="*80)

# ==============================================================================
# ESECUZIONE
# ==============================================================================

if not Copy:
	run_analyze_mode()
else:
	run_copy_mode()
