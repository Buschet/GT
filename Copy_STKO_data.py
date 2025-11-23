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
			for attr_name in xobj.attributes:
				try:
					attr = xobj.getAttribute(attr_name)
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
# ESECUZIONE
# ==============================================================================

if not Copy:
	run_analyze_mode()
else:
	print("\n[TODO] Modalità COPY non ancora implementata")
	print("Coming soon...")
