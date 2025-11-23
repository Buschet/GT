"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         STKO GEOMETRY READER & COPIER - UNIFIED SCRIPT (STEP Edition)       ║
║                                                                              ║
║  Copy = False: Analizza geometrie + Export STEP (.stp) + JSON/CSV           ║
║  Copy = True:  Import STEP + Ricrea physical/element properties             ║
║                                                                              ║
║  🆕 NOVITÀ: Usa file STEP per geometria precisa al 100%                     ║
║            Mantiene analisi dettagliata proprietà su subshapes              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from PyMpc import *
from PySide2.QtCore import QSettings
import json
import csv
import os
from datetime import datetime
import math

# ==============================================================================
# ⚙️ CONFIGURAZIONE PRINCIPALE
# ==============================================================================

# 🔴 VARIABILE PRINCIPALE - MODALITÀ OPERATIVA
Copy = True  # False = Analizza | True = Ricrea

# Configurazione per modalità ANALISI (Copy = False)
ANALYZE_CONFIG = {
	'export_json': True,
	'export_csv': True,
	'export_report': True,
	'export_coordinates': True,
	'export_geometries': True,           # Esporta geometrie via dialog nativo STKO
	'output_filename': 'STKO_Analysis',  # Nome file base (senza estensione)
	'add_timestamp': False,              # True = aggiunge _YYYYMMDD_HHMMSS al nome
	'verbose': True
}
# IMPORTANTE: Se add_timestamp = False, i file saranno sovrascritti ad ogni esecuzione
# IMPORTANTE: output_filename deve corrispondere a input_json_file in COPY_CONFIG
# IMPORTANTE: Le geometrie vengono esportate nella cartella STKO_Export/

# Configurazione per modalità COPIA (Copy = True)
COPY_CONFIG = {
	# File JSON da cui leggere i dati per ricreare le geometrie
	'input_json_file': 'STKO_Analysis.json',  # ← Deve corrispondere a output_filename + '.json'
	'import_folder': 'STKO_Export',           # Cartella contenente i file esportati da importare

	# Opzioni di creazione
	'create_new_document': False,  # True = nuovo doc | False = aggiungi al corrente
	'prefix_names': 'Copy_',       # Prefisso per nomi geometrie copiate
	'copy_properties': True,        # Copia anche le proprietà
	'verbose': True,

	# Filtri opzionali per copiare solo alcune geometrie
	'filter_by_name': '',          # Es: "Wall" per copiare solo muri
	'filter_ids': [],              # Es: [1,2,3] per copiare solo questi ID
}

# ==============================================================================
# INIZIALIZZAZIONE
# ==============================================================================

App.clearTerminal()
doc = App.caeDocument()

# Timestamp (usato solo se add_timestamp = True)
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

print("="*80)
print("STKO GEOMETRY READER & COPIER - UNIFIED")
print("="*80)
print(f"Modalità: {'COPY (Ricrea Geometrie)' if Copy else 'ANALYZE (Analizza)'}")
print(f"Data/Ora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
if not Copy and ANALYZE_CONFIG.get('add_timestamp', False):
	print(f"[INFO] Timestamp nei file: ATTIVO")
else:
	print(f"[INFO] Nome file fisso: {ANALYZE_CONFIG.get('output_filename', 'N/A') if not Copy else COPY_CONFIG.get('input_json_file', 'N/A')}")
print("="*80)

# ==============================================================================
# FUNZIONI DI UTILITÀ COMUNI
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

def get_bounding_box(shape):
	"""Calcola il bounding box della shape dai vertici"""
	try:
		num_vertices = shape.getNumberOfSubshapes(MpcSubshapeType.Vertex)
		
		if num_vertices == 0:
			print(f"  [WARNING] Nessun vertice per calcolare bounding box")
			return None
		
		# Inizializza min/max con il primo vertice
		first_pos = shape.vertexPosition(0)
		min_x = max_x = first_pos.x
		min_y = max_y = first_pos.y
		min_z = max_z = first_pos.z
		
		# Trova min/max tra tutti i vertici
		for v_id in range(num_vertices):
			pos = shape.vertexPosition(v_id)
			min_x = min(min_x, pos.x)
			max_x = max(max_x, pos.x)
			min_y = min(min_y, pos.y)
			max_y = max(max_y, pos.y)
			min_z = min(min_z, pos.z)
			max_z = max(max_z, pos.z)
		
		# Calcola dimensioni
		result = {
			'min_x': float(min_x),
			'max_x': float(max_x),
			'min_y': float(min_y),
			'max_y': float(max_y),
			'min_z': float(min_z),
			'max_z': float(max_z),
			'size_x': float(max_x - min_x),
			'size_y': float(max_y - min_y),
			'size_z': float(max_z - min_z)
		}
		
		return result
		
	except Exception as e:
		print(f"  [WARNING] Errore calcolo bounding box manuale: {str(e)}")
		return None

# ==============================================================================
# MODALITÀ ANALISI (Copy = False)
# ==============================================================================

def extract_physical_properties(geom):
	"""Estrae tutte le physical properties assegnate"""
	properties = {'on_edges': [], 'on_faces': [], 'on_solids': []}
	
	try:
		shape = geom.shape
		
		# Physical Properties su Edges
		num_edges = shape.getNumberOfSubshapes(MpcSubshapeType.Edge)
		if num_edges > 0:
			pp_edges = geom.physicalPropertyAssignment.onEdges
			for i in range(len(pp_edges)):
				pp = pp_edges[i]
				if pp is not None:
					# Estrai anche i parametri della proprietà
					prop_params = {}
					try:
						xobj = pp.XObject
						for attr_name in xobj.attributes:
							attr = xobj.getAttribute(attr_name)
							prop_params[attr_name] = extract_attribute_value(attr)
					except:
						pass
					
					properties['on_edges'].append({
						'edge_id': i,
						'property_id': pp.id,
						'property_name': pp.name,
						'property_type': pp.XObject.getXObjectName() if pp.XObject else 'Unknown',
						'parameters': prop_params
					})
		
		# Physical Properties su Faces
		num_faces = shape.getNumberOfSubshapes(MpcSubshapeType.Face)
		if num_faces > 0:
			pp_faces = geom.physicalPropertyAssignment.onFaces
			for i in range(len(pp_faces)):
				pp = pp_faces[i]
				if pp is not None:
					prop_params = {}
					try:
						xobj = pp.XObject
						for attr_name in xobj.attributes:
							attr = xobj.getAttribute(attr_name)
							prop_params[attr_name] = extract_attribute_value(attr)
					except:
						pass
					
					properties['on_faces'].append({
						'face_id': i,
						'property_id': pp.id,
						'property_name': pp.name,
						'property_type': pp.XObject.getXObjectName() if pp.XObject else 'Unknown',
						'parameters': prop_params
					})
		
		# Physical Properties su Solids
		num_solids = shape.getNumberOfSubshapes(MpcSubshapeType.Solid)
		if num_solids > 0:
			pp_solids = geom.physicalPropertyAssignment.onSolids
			for i in range(len(pp_solids)):
				pp = pp_solids[i]
				if pp is not None:
					prop_params = {}
					try:
						xobj = pp.XObject
						for attr_name in xobj.attributes:
							attr = xobj.getAttribute(attr_name)
							prop_params[attr_name] = extract_attribute_value(attr)
					except:
						pass
					
					properties['on_solids'].append({
						'solid_id': i,
						'property_id': pp.id,
						'property_name': pp.name,
						'property_type': pp.XObject.getXObjectName() if pp.XObject else 'Unknown',
						'parameters': prop_params
					})
	except Exception as e:
		print(f"  [WARNING] Errore estrazione physical properties: {str(e)}")
	
	return properties

def extract_element_properties(geom):
	"""Estrae tutte le element properties assegnate"""
	properties = {'on_edges': [], 'on_faces': [], 'on_solids': []}
	
	try:
		shape = geom.shape
		
		# Element Properties su Edges
		num_edges = shape.getNumberOfSubshapes(MpcSubshapeType.Edge)
		if num_edges > 0:
			ep_edges = geom.elementPropertyAssignment.onEdges
			for i in range(len(ep_edges)):
				ep = ep_edges[i]
				if ep is not None:
					prop_params = {}
					try:
						xobj = ep.XObject
						for attr_name in xobj.attributes:
							attr = xobj.getAttribute(attr_name)
							prop_params[attr_name] = extract_attribute_value(attr)
					except:
						pass
					
					properties['on_edges'].append({
						'edge_id': i,
						'property_id': ep.id,
						'property_name': ep.name,
						'property_type': ep.XObject.getXObjectName() if ep.XObject else 'Unknown',
						'parameters': prop_params
					})
		
		# Element Properties su Faces
		num_faces = shape.getNumberOfSubshapes(MpcSubshapeType.Face)
		if num_faces > 0:
			ep_faces = geom.elementPropertyAssignment.onFaces
			for i in range(len(ep_faces)):
				ep = ep_faces[i]
				if ep is not None:
					prop_params = {}
					try:
						xobj = ep.XObject
						for attr_name in xobj.attributes:
							attr = xobj.getAttribute(attr_name)
							prop_params[attr_name] = extract_attribute_value(attr)
					except:
						pass
					
					properties['on_faces'].append({
						'face_id': i,
						'property_id': ep.id,
						'property_name': ep.name,
						'property_type': ep.XObject.getXObjectName() if ep.XObject else 'Unknown',
						'parameters': prop_params
					})
		
		# Element Properties su Solids
		num_solids = shape.getNumberOfSubshapes(MpcSubshapeType.Solid)
		if num_solids > 0:
			ep_solids = geom.elementPropertyAssignment.onSolids
			for i in range(len(ep_solids)):
				ep = ep_solids[i]
				if ep is not None:
					prop_params = {}
					try:
						xobj = ep.XObject
						for attr_name in xobj.attributes:
							attr = xobj.getAttribute(attr_name)
							prop_params[attr_name] = extract_attribute_value(attr)
					except:
						pass
					
					properties['on_solids'].append({
						'solid_id': i,
						'property_id': ep.id,
						'property_name': ep.name,
						'property_type': ep.XObject.getXObjectName() if ep.XObject else 'Unknown',
						'parameters': prop_params
					})
	except Exception as e:
		print(f"  [WARNING] Errore estrazione element properties: {str(e)}")
	
	return properties

def extract_property_data(prop, prop_type):
	"""
	Estrae TUTTI i dati di una proprietà (physical o element)
	per poterla ricreare identicamente
	"""
	prop_data = {
		'property_id': prop.id,
		'property_name': prop.name,
		'property_type': None,
		'parameters': {}
	}
	
	try:
		# Ottieni il tipo/classe della proprietà
		if prop.XObject:
			prop_data['property_type'] = prop.XObject.getXObjectName()
			
			# Estrai TUTTI i parametri della proprietà
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

def analyze_geometry_comprehensive(geom_id, geom):
	"""
	Analizza in modo completo una singola geometria
	Analisi DETTAGLIATA vertex-by-vertex, edge-by-edge, face-by-face, solid-by-solid
	"""
	
	geometry_data = {
		'id': geom_id,
		'name': geom.name,
		'shape_type': None,
		'bounding_box': None,
		'topology': {
			'num_vertices': 0,
			'num_edges': 0,
			'num_faces': 0,
			'num_solids': 0
		},
		'vertices': [],
		'edges': [],
		'faces': [],
		'solids': [],
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
		
		# Bounding Box (calcolato manualmente dai vertici)
		geometry_data['bounding_box'] = get_bounding_box(shape)
		
		# ═══════════════════════════════════════════════════════════
		# ANALISI TOPOLOGIA
		# ═══════════════════════════════════════════════════════════
		try:
			geometry_data['topology']['num_vertices'] = shape.getNumberOfSubshapes(MpcSubshapeType.Vertex)
			geometry_data['topology']['num_edges'] = shape.getNumberOfSubshapes(MpcSubshapeType.Edge)
			geometry_data['topology']['num_faces'] = shape.getNumberOfSubshapes(MpcSubshapeType.Face)
			geometry_data['topology']['num_solids'] = shape.getNumberOfSubshapes(MpcSubshapeType.Solid)
		except Exception as e:
			geometry_data['errors'].append(f"Errore analisi topologia: {str(e)}")
		
		# ═══════════════════════════════════════════════════════════
		# ANALISI VERTICES (uno per uno)
		# ═══════════════════════════════════════════════════════════
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
		
		# ═══════════════════════════════════════════════════════════
		# ANALISI EDGES (uno per uno)
		# ═══════════════════════════════════════════════════════════
		try:
			num_edges = geometry_data['topology']['num_edges']
			for e_id in range(num_edges):
				edge_info = {
					'id': e_id,
					'vertices': []
				}
				
				# Ottieni i vertici che compongono l'edge
				try:
					vertices = shape.getSubshapeChildren(e_id, MpcSubshapeType.Edge, MpcSubshapeType.Vertex)
					for v_id in vertices:
						edge_info['vertices'].append({
							'vertex_id': v_id,
							'coordinates': extract_vertex_coordinates(shape, v_id)
						})
				except:
					pass
				
				geometry_data['edges'].append(edge_info)
		except Exception as e:
			geometry_data['errors'].append(f"Errore analisi edges: {str(e)}")
		
		# ═══════════════════════════════════════════════════════════
		# ANALISI FACES (una per una)
		# ═══════════════════════════════════════════════════════════
		try:
			num_faces = geometry_data['topology']['num_faces']
			for f_id in range(num_faces):
				face_info = {
					'id': f_id,
					'edges': [],
					'vertices': []
				}
				
				# Ottieni gli edges che compongono la faccia
				try:
					edges = shape.getSubshapeChildren(f_id, MpcSubshapeType.Face, MpcSubshapeType.Edge)
					face_info['edges'] = list(edges)
				except:
					pass
				
				# Ottieni i vertici della faccia
				try:
					vertices = shape.getSubshapeChildren(f_id, MpcSubshapeType.Face, MpcSubshapeType.Vertex)
					for v_id in vertices:
						face_info['vertices'].append({
							'vertex_id': v_id,
							'coordinates': extract_vertex_coordinates(shape, v_id)
						})
				except:
					pass
				
				geometry_data['faces'].append(face_info)
		except Exception as e:
			geometry_data['errors'].append(f"Errore analisi faces: {str(e)}")
		
		# ═══════════════════════════════════════════════════════════
		# ANALISI SOLIDS (uno per uno)
		# ═══════════════════════════════════════════════════════════
		try:
			num_solids = geometry_data['topology']['num_solids']
			for s_id in range(num_solids):
				solid_info = {
					'id': s_id,
					'faces': [],
					'edges': [],
					'vertices': []
				}
				
				# Ottieni le facce del solido
				try:
					faces = shape.getSubshapeChildren(s_id, MpcSubshapeType.Solid, MpcSubshapeType.Face)
					solid_info['faces'] = list(faces)
				except:
					pass
				
				# Ottieni gli edges del solido
				try:
					edges = shape.getSubshapeChildren(s_id, MpcSubshapeType.Solid, MpcSubshapeType.Edge)
					solid_info['edges'] = list(edges)
				except:
					pass
				
				# Ottieni i vertici del solido
				try:
					vertices = shape.getSubshapeChildren(s_id, MpcSubshapeType.Solid, MpcSubshapeType.Vertex)
					for v_id in vertices:
						solid_info['vertices'].append({
							'vertex_id': v_id,
							'coordinates': extract_vertex_coordinates(shape, v_id)
						})
				except:
					pass
				
				geometry_data['solids'].append(solid_info)
		except Exception as e:
			geometry_data['errors'].append(f"Errore analisi solids: {str(e)}")
		
		# ═══════════════════════════════════════════════════════════
		# ANALISI PHYSICAL PROPERTIES (per ogni tipo di subshape)
		# ═══════════════════════════════════════════════════════════
		try:
			# Physical Properties su VERTICES
			if geometry_data['topology']['num_vertices'] > 0:
				pp_vertices = geom.physicalPropertyAssignment.onVertices
				for v_id in range(len(pp_vertices)):
					pp = pp_vertices[v_id]
					if pp is not None:
						prop_data = extract_property_data(pp, 'physical')
						prop_data['vertex_id'] = v_id
						geometry_data['properties']['physical']['vertices'].append(prop_data)
			
			# Physical Properties su EDGES
			if geometry_data['topology']['num_edges'] > 0:
				pp_edges = geom.physicalPropertyAssignment.onEdges
				for e_id in range(len(pp_edges)):
					pp = pp_edges[e_id]
					if pp is not None:
						prop_data = extract_property_data(pp, 'physical')
						prop_data['edge_id'] = e_id
						geometry_data['properties']['physical']['edges'].append(prop_data)
			
			# Physical Properties su FACES
			if geometry_data['topology']['num_faces'] > 0:
				pp_faces = geom.physicalPropertyAssignment.onFaces
				for f_id in range(len(pp_faces)):
					pp = pp_faces[f_id]
					if pp is not None:
						prop_data = extract_property_data(pp, 'physical')
						prop_data['face_id'] = f_id
						geometry_data['properties']['physical']['faces'].append(prop_data)
			
			# Physical Properties su SOLIDS
			if geometry_data['topology']['num_solids'] > 0:
				pp_solids = geom.physicalPropertyAssignment.onSolids
				for s_id in range(len(pp_solids)):
					pp = pp_solids[s_id]
					if pp is not None:
						prop_data = extract_property_data(pp, 'physical')
						prop_data['solid_id'] = s_id
						geometry_data['properties']['physical']['solids'].append(prop_data)
		
		except Exception as e:
			geometry_data['errors'].append(f"Errore analisi physical properties: {str(e)}")
		
		# ═══════════════════════════════════════════════════════════
		# ANALISI ELEMENT PROPERTIES (per ogni tipo di subshape)
		# ═══════════════════════════════════════════════════════════
		try:
			# Element Properties su VERTICES
			if geometry_data['topology']['num_vertices'] > 0:
				ep_vertices = geom.elementPropertyAssignment.onVertices
				for v_id in range(len(ep_vertices)):
					ep = ep_vertices[v_id]
					if ep is not None:
						prop_data = extract_property_data(ep, 'element')
						prop_data['vertex_id'] = v_id
						geometry_data['properties']['element']['vertices'].append(prop_data)
			
			# Element Properties su EDGES
			if geometry_data['topology']['num_edges'] > 0:
				ep_edges = geom.elementPropertyAssignment.onEdges
				for e_id in range(len(ep_edges)):
					ep = ep_edges[e_id]
					if ep is not None:
						prop_data = extract_property_data(ep, 'element')
						prop_data['edge_id'] = e_id
						geometry_data['properties']['element']['edges'].append(prop_data)
			
			# Element Properties su FACES
			if geometry_data['topology']['num_faces'] > 0:
				ep_faces = geom.elementPropertyAssignment.onFaces
				for f_id in range(len(ep_faces)):
					ep = ep_faces[f_id]
					if ep is not None:
						prop_data = extract_property_data(ep, 'element')
						prop_data['face_id'] = f_id
						geometry_data['properties']['element']['faces'].append(prop_data)
			
			# Element Properties su SOLIDS
			if geometry_data['topology']['num_solids'] > 0:
				ep_solids = geom.elementPropertyAssignment.onSolids
				for s_id in range(len(ep_solids)):
					ep = ep_solids[s_id]
					if ep is not None:
						prop_data = extract_property_data(ep, 'element')
						prop_data['solid_id'] = s_id
						geometry_data['properties']['element']['solids'].append(prop_data)
		
		except Exception as e:
			geometry_data['errors'].append(f"Errore analisi element properties: {str(e)}")
		
	except Exception as e:
		geometry_data['errors'].append(f"Errore generale: {str(e)}")
	
	return geometry_data

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
		if ANALYZE_CONFIG['verbose']:
			print(f"  [{idx}/{len(doc.geometries)}] Analizzando: [{geom_id}] {geom.name}")
		
		geom_data = analyze_geometry_comprehensive(geom_id, geom)
		all_geometries_data['geometries'].append(geom_data)
		
		App.processEvents()
	
	# Export
	print("\n[EXPORT RISULTATI]")
	print("-"*80)
	
	# Genera nome base per i file
	base_filename = ANALYZE_CONFIG['output_filename']
	if ANALYZE_CONFIG['add_timestamp']:
		base_filename = f"{base_filename}_{timestamp}"
	
	if ANALYZE_CONFIG['export_json']:
		filename = f"{base_filename}.json"
		with open(filename, 'w', encoding='utf-8') as f:
			json.dump(all_geometries_data, f, indent=2, ensure_ascii=False)
		print(f"✓ Esportato JSON: {filename}")
		print(f"  [INFO] Usa questo nome in COPY_CONFIG['input_json_file'] per ricreazione")
	
	if ANALYZE_CONFIG['export_csv']:
		filename = f"{base_filename}_Summary.csv"
		with open(filename, 'w', newline='', encoding='utf-8') as f:
			writer = csv.writer(f)
			writer.writerow(['ID', 'Name', 'Type', 'Vertices', 'Edges', 'Faces', 'Solids'])
			for geom_data in all_geometries_data['geometries']:
				topo = geom_data['topology']
				writer.writerow([
					geom_data['id'], geom_data['name'], geom_data['shape_type'],
					topo['num_vertices'], topo['num_edges'], 
					topo['num_faces'], topo['num_solids']
				])
		print(f"✓ Esportato CSV: {filename}")
	
	if ANALYZE_CONFIG['export_coordinates']:
		filename = f"{base_filename}_Coordinates.csv"
		with open(filename, 'w', newline='', encoding='utf-8') as f:
			writer = csv.writer(f)
			writer.writerow(['Geom_ID', 'Geom_Name', 'Vertex_ID', 'X', 'Y', 'Z'])
			for geom_data in all_geometries_data['geometries']:
				for vertex in geom_data['vertices']:
					coords = vertex['coordinates']
					writer.writerow([
						geom_data['id'], geom_data['name'], vertex['id'],
						coords['x'], coords['y'], coords['z']
					])
		print(f"✓ Esportato Coordinate: {filename}")

	# 🆕 EXPORT GEOMETRIE
	if ANALYZE_CONFIG['export_geometries']:
		# Crea cartella STKO_Export
		export_folder = 'STKO_Export'
		abs_export_folder = os.path.abspath(export_folder)

		if not os.path.exists(abs_export_folder):
			os.makedirs(abs_export_folder)

		print(f"\n[EXPORT GEOMETRIE - Metodo Nativo Dialog]")
		print(f"Cartella: {abs_export_folder}/")
		print("-"*80)

		export_count = 0
		export_errors = 0

		for idx, (geom_id, geom) in enumerate(doc.geometries.items(), 1):
			try:
				safe_name = "".join(c for c in geom.name if c.isalnum() or c in (' ', '-', '_')).strip()
				if not safe_name:
					safe_name = f"geometry_{geom_id}"

				nome_geometry = f"geom_{geom_id}_{safe_name}"
				new_dir = f"{abs_export_folder}/{nome_geometry}"

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

				# Salva percorso nel JSON (assumiamo estensione di default)
				exported_file = f"{new_dir}"  # Il path esatto dipende dall'estensione scelta dall'utente
				all_geometries_data['geometries'][idx-1]['exported_file'] = exported_file

				export_count += 1
				if ANALYZE_CONFIG['verbose']:
					print(f"  [{idx}/{len(doc.geometries)}] ✓ {geom.name}")

			except Exception as e:
				export_errors += 1
				print(f"  [{idx}/{len(doc.geometries)}] ✗ Errore: {str(e)}")
				all_geometries_data['geometries'][idx-1]['exported_file'] = None
				doc.scene.unselectAll()

			App.processEvents()

		print(f"\n✓ Geometrie esportate: {export_count}/{len(doc.geometries)}")
		if export_errors > 0:
			print(f"✗ Errori export: {export_errors}")

		# Ri-esporta JSON con percorsi aggiornati
		if ANALYZE_CONFIG['export_json']:
			filename = f"{base_filename}.json"
			with open(filename, 'w', encoding='utf-8') as f:
				json.dump(all_geometries_data, f, indent=2, ensure_ascii=False)
			print(f"✓ JSON aggiornato con percorsi export: {filename}")

	print("\n" + "="*80)
	print("ANALISI COMPLETATA!")
	print(f"Geometrie analizzate: {all_geometries_data['total_geometries']}")
	if ANALYZE_CONFIG['export_geometries']:
		print(f"Geometrie esportate in: STKO_Export/")
	print(f"\n💡 PROSSIMO STEP:")
	print(f"   Per ricreazione: Imposta Copy = True")
	print(f"   Il file JSON '{base_filename}.json' è pronto")
	print("="*80)

# ==============================================================================
# MODALITÀ COPIA (Copy = True)
# ==============================================================================

def load_geometries_from_json(filename):
	"""Carica i dati delle geometrie da file JSON"""
	try:
		with open(filename, 'r', encoding='utf-8') as f:
			data = json.load(f)
		return data['geometries']
	except Exception as e:
		print(f"✗ Errore caricamento JSON: {str(e)}")
		return None

def create_or_get_physical_property(prop_data):
	"""Crea o recupera una physical property esistente"""
	prop_name = prop_data['property_name']
	prop_type = prop_data['property_type']
	
	# Cerca se esiste già
	for _, existing_pp in doc.physicalProperties.items():
		if existing_pp.name == prop_name:
			if COPY_CONFIG['verbose']:
				print(f"    Usando physical property esistente: {prop_name}")
			return existing_pp
	
	# Crea nuova
	try:
		if COPY_CONFIG['verbose']:
			print(f"    Creando physical property: {prop_name}")
		
		pp_meta = doc.metaDataPhysicalProperty(prop_type)
		pp_xobj = MpcXObject.createInstanceOf(pp_meta)
		
		# Applica parametri
		if 'parameters' in prop_data:
			for param_name, param_value in prop_data['parameters'].items():
				try:
					attr = pp_xobj.getAttribute(param_name)
					set_attribute_value(attr, param_value)
				except:
					pass
		
		new_pp = MpcProperty()
		new_pp.id = doc.physicalProperties.getlastkey(0) + 1
		new_pp.name = prop_name
		new_pp.XObject = pp_xobj
		
		doc.addPhysicalProperty(new_pp)
		doc.commitChanges()
		
		return new_pp
	
	except Exception as e:
		print(f"    [WARNING] Errore creazione physical property: {str(e)}")
		return None

def create_or_get_element_property(prop_data):
	"""Crea o recupera una element property esistente"""
	prop_name = prop_data['property_name']
	prop_type = prop_data['property_type']
	
	# Cerca se esiste già
	for _, existing_ep in doc.elementProperties.items():
		if existing_ep.name == prop_name:
			if COPY_CONFIG['verbose']:
				print(f"    Usando element property esistente: {prop_name}")
			return existing_ep
	
	# Crea nuova
	try:
		if COPY_CONFIG['verbose']:
			print(f"    Creando element property: {prop_name}")
		
		ep_meta = doc.metaDataElementProperty(prop_type)
		ep_xobj = MpcXObject.createInstanceOf(ep_meta)
		
		# Applica parametri
		if 'parameters' in prop_data:
			for param_name, param_value in prop_data['parameters'].items():
				try:
					attr = ep_xobj.getAttribute(param_name)
					set_attribute_value(attr, param_value)
				except:
					pass
		
		new_ep = MpcElementProperty()
		new_ep.id = doc.elementProperties.getlastkey(0) + 1
		new_ep.name = prop_name
		new_ep.XObject = ep_xobj
		
		doc.addElementProperty(new_ep)
		doc.commitChanges()
		
		return new_ep
	
	except Exception as e:
		print(f"    [WARNING] Errore creazione element property: {str(e)}")
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
	except:
		pass

def recreate_geometry_from_data(geom_data):
	"""Ricrea una geometria dai dati JSON usando STEP import (preferito) o metodo manuale (fallback)"""

	shape_type = geom_data['shape_type']
	new_name = COPY_CONFIG['prefix_names'] + geom_data['name']
	new_shape = None

	# ═══════════════════════════════════════════════════════════
	# 🆕 METODO 1: IMPORT DA FILE STEP (PREFERITO)
	# ═══════════════════════════════════════════════════════════
	if COPY_CONFIG['use_step_import'] and 'step_file' in geom_data and geom_data['step_file']:
		step_file = geom_data['step_file']

		try:
			if os.path.exists(step_file):
				if COPY_CONFIG['verbose']:
					print(f"    Importando da STEP: {step_file}")

				# Importa geometria da file STEP
				new_shape = MpcShape()
				new_shape.importFromSTEP(step_file)

				if COPY_CONFIG['verbose']:
					print(f"    ✓ Geometria importata correttamente da STEP")

			else:
				print(f"    [WARNING] File STEP non trovato: {step_file}")
				print(f"              Usando metodo manuale...")

		except Exception as e:
			print(f"    [WARNING] Errore import STEP: {str(e)}")
			print(f"              Usando metodo manuale...")
			new_shape = None

	# ═══════════════════════════════════════════════════════════
	# METODO 2: RICREAZIONE MANUALE (FALLBACK)
	# ═══════════════════════════════════════════════════════════
	if new_shape is None:
		if COPY_CONFIG['verbose']:
			print(f"    Usando ricreazione manuale per tipo: {shape_type}")

		try:
			# Ricrea geometria in base al tipo
			if shape_type == "VERTEX":
				# Crea vertex singolo - coordinate dirette
				if len(geom_data['vertices']) > 0:
					coords = geom_data['vertices'][0]['coordinates']
					new_shape = FxOccBuilder.makeVertex(coords['x'], coords['y'], coords['z'])

			elif shape_type == "EDGE":
				# Crea edge da due vertici - coordinate dirette
				if len(geom_data['vertices']) >= 2:
					v1 = geom_data['vertices'][0]['coordinates']
					v2 = geom_data['vertices'][1]['coordinates']
					# Crea vertici con coordinate dirette
					vert1 = FxOccBuilder.makeVertex(v1['x'], v1['y'], v1['z'])
					vert2 = FxOccBuilder.makeVertex(v2['x'], v2['y'], v2['z'])
					# Crea edge dai vertici
					new_shape = FxOccBuilder.makeEdge(vert1, vert2)

			elif shape_type == "WIRE":
				# Crea wire da edges - coordinate dirette
				edges = []
				for edge_data in geom_data['edges']:
					if len(edge_data['vertices']) >= 2:
						v1 = edge_data['vertices'][0]['coordinates']
						v2 = edge_data['vertices'][1]['coordinates']
						# Crea vertici con coordinate dirette
						vert1 = FxOccBuilder.makeVertex(v1['x'], v1['y'], v1['z'])
						vert2 = FxOccBuilder.makeVertex(v2['x'], v2['y'], v2['z'])
						# Crea edge
						edge = FxOccBuilder.makeEdge(vert1, vert2)
						edges.append(edge)
				if len(edges) > 0:
					new_shape = FxOccBuilder.makeWire(edges)

			elif shape_type in ["FACE", "SHELL", "SOLID", "COMPOUND"]:
				# Per geometrie complesse, usa approccio semplificato con bounding box
				# Ricrea come box solido usando vertici del bounding box
				bbox = geom_data['bounding_box']

				# Debug: mostra valori bbox
				if COPY_CONFIG['verbose']:
					print(f"    [DEBUG] BBox: {bbox}")

				# Check validità bbox più robusto
				if bbox is None:
					print(f"    [WARNING] Bounding box è None per {shape_type}")
					new_shape = None

				# Verifica che tutti i valori necessari esistano e siano validi
				elif not all(key in ['min_x', 'min_y', 'min_z', 'max_x', 'max_y', 'max_z', 'size_x', 'size_y', 'size_z'] for key in bbox if key in bbox):
					print(f"    [WARNING] Bounding box incompleto per {shape_type}")
					new_shape = None

				# Verifica che i valori non siano None
				elif any(bbox.get(key) is None for key in ['min_x', 'min_y', 'min_z', 'max_x', 'max_y', 'max_z']):
					print(f"    [WARNING] Bounding box contiene valori None per {shape_type}")
					new_shape = None

				# Verifica dimensioni positive
				elif bbox.get('size_x', 0) <= 0 or bbox.get('size_y', 0) <= 0 or bbox.get('size_z', 0) <= 0:
					print(f"    [WARNING] Bounding box con dimensioni non positive per {shape_type}")
					print(f"              size_x={bbox.get('size_x')}, size_y={bbox.get('size_y')}, size_z={bbox.get('size_z')}")
					new_shape = None

				else:
					try:
						# Coordinate bounding box
						x0, y0, z0 = bbox['min_x'], bbox['min_y'], bbox['min_z']
						x1, y1, z1 = bbox['max_x'], bbox['max_y'], bbox['max_z']

						# Crea 8 vertici del box - coordinate dirette
						v1 = FxOccBuilder.makeVertex(x0, y0, z0)  # Bottom face
						v2 = FxOccBuilder.makeVertex(x1, y0, z0)
						v3 = FxOccBuilder.makeVertex(x1, y1, z0)
						v4 = FxOccBuilder.makeVertex(x0, y1, z0)
						v5 = FxOccBuilder.makeVertex(x0, y0, z1)  # Top face
						v6 = FxOccBuilder.makeVertex(x1, y0, z1)
						v7 = FxOccBuilder.makeVertex(x1, y1, z1)
						v8 = FxOccBuilder.makeVertex(x0, y1, z1)

						# Bottom face
						e1 = FxOccBuilder.makeEdge(v1, v2)
						e2 = FxOccBuilder.makeEdge(v2, v3)
						e3 = FxOccBuilder.makeEdge(v3, v4)
						e4 = FxOccBuilder.makeEdge(v4, v1)
						w1 = FxOccBuilder.makeWire([e1, e2, e3, e4])
						f1 = FxOccBuilder.makeFace(w1)

						# Top face
						e5 = FxOccBuilder.makeEdge(v5, v6)
						e6 = FxOccBuilder.makeEdge(v6, v7)
						e7 = FxOccBuilder.makeEdge(v7, v8)
						e8 = FxOccBuilder.makeEdge(v8, v5)
						w2 = FxOccBuilder.makeWire([e5, e6, e7, e8])
						f2 = FxOccBuilder.makeFace(w2)

						# Vertical edges
						e9 = FxOccBuilder.makeEdge(v1, v5)
						e10 = FxOccBuilder.makeEdge(v2, v6)
						e11 = FxOccBuilder.makeEdge(v4, v8)
						e12 = FxOccBuilder.makeEdge(v3, v7)

						# Front face
						w3 = FxOccBuilder.makeWire([e1, e10, e5, e9])
						f3 = FxOccBuilder.makeFace(w3)

						# Back face
						w4 = FxOccBuilder.makeWire([e3, e12, e7, e11])
						f4 = FxOccBuilder.makeFace(w4)

						# Left face
						w5 = FxOccBuilder.makeWire([e4, e9, e8, e11])
						f5 = FxOccBuilder.makeFace(w5)

						# Right face
						w6 = FxOccBuilder.makeWire([e2, e10, e6, e12])
						f6 = FxOccBuilder.makeFace(w6)

						# Shell e Solid
						shell = FxOccBuilder.makeShell([f1, f2, f3, f4, f5, f6])
						new_shape = FxOccBuilder.makeSolid(shell)

						print(f"    [INFO] Geometria {shape_type} ricreata come box solido")

					except Exception as e:
						print(f"    [ERROR] Errore creazione box solido: {str(e)}")
						import traceback
						traceback.print_exc()
						new_shape = None

			else:
				print(f"    [WARNING] Tipo {shape_type} non supportato per ricreazione")
				new_shape = None

		except Exception as e:
			print(f"    [WARNING] Errore ricreazione manuale: {str(e)}")
			new_shape = None

	# ═══════════════════════════════════════════════════════════
	# CREAZIONE GEOMETRIA STKO
	# ═══════════════════════════════════════════════════════════
	if new_shape is not None:
		try:
			new_geom_id = doc.geometries.getlastkey(0) + 1
			new_geom = MpcGeometry(new_geom_id, new_name, new_shape)
			doc.addGeometry(new_geom)
			doc.commitChanges()
			return new_geom
		except Exception as e:
			print(f"    [ERROR] Errore creazione geometria STKO: {str(e)}")
			return None
	else:
		print(f"    [ERROR] Impossibile creare geometria")
		return None

def assign_properties_to_geometry(geom, geom_data):
	"""Assegna le proprietà alla geometria ricreata usando la nuova struttura dati"""
	
	if not COPY_CONFIG['copy_properties']:
		return
	
	try:
		shape = geom.shape
		props = geom_data['properties']
		
		# ═══════════════════════════════════════════════════════════
		# ASSEGNA PHYSICAL PROPERTIES
		# ═══════════════════════════════════════════════════════════
		
		# Physical Properties su VERTICES
		for prop_info in props['physical']['vertices']:
			v_id = prop_info.get('vertex_id')
			if v_id is not None:
				pp = create_or_get_physical_property(prop_info)
				if pp and v_id < shape.getNumberOfSubshapes(MpcSubshapeType.Vertex):
					geom.physicalPropertyAssignment.onVertices[v_id] = pp
		
		# Physical Properties su EDGES
		for prop_info in props['physical']['edges']:
			e_id = prop_info.get('edge_id')
			if e_id is not None:
				pp = create_or_get_physical_property(prop_info)
				if pp and e_id < shape.getNumberOfSubshapes(MpcSubshapeType.Edge):
					geom.physicalPropertyAssignment.onEdges[e_id] = pp
		
		# Physical Properties su FACES
		for prop_info in props['physical']['faces']:
			f_id = prop_info.get('face_id')
			if f_id is not None:
				pp = create_or_get_physical_property(prop_info)
				if pp and f_id < shape.getNumberOfSubshapes(MpcSubshapeType.Face):
					geom.physicalPropertyAssignment.onFaces[f_id] = pp
		
		# Physical Properties su SOLIDS
		for prop_info in props['physical']['solids']:
			s_id = prop_info.get('solid_id')
			if s_id is not None:
				pp = create_or_get_physical_property(prop_info)
				if pp and s_id < shape.getNumberOfSubshapes(MpcSubshapeType.Solid):
					geom.physicalPropertyAssignment.onSolids[s_id] = pp
		
		# ═══════════════════════════════════════════════════════════
		# ASSEGNA ELEMENT PROPERTIES
		# ═══════════════════════════════════════════════════════════
		
		# Element Properties su VERTICES
		for prop_info in props['element']['vertices']:
			v_id = prop_info.get('vertex_id')
			if v_id is not None:
				ep = create_or_get_element_property(prop_info)
				if ep and v_id < shape.getNumberOfSubshapes(MpcSubshapeType.Vertex):
					geom.elementPropertyAssignment.onVertices[v_id] = ep
		
		# Element Properties su EDGES
		for prop_info in props['element']['edges']:
			e_id = prop_info.get('edge_id')
			if e_id is not None:
				ep = create_or_get_element_property(prop_info)
				if ep and e_id < shape.getNumberOfSubshapes(MpcSubshapeType.Edge):
					geom.elementPropertyAssignment.onEdges[e_id] = ep
		
		# Element Properties su FACES
		for prop_info in props['element']['faces']:
			f_id = prop_info.get('face_id')
			if f_id is not None:
				ep = create_or_get_element_property(prop_info)
				if ep and f_id < shape.getNumberOfSubshapes(MpcSubshapeType.Face):
					geom.elementPropertyAssignment.onFaces[f_id] = ep
		
		# Element Properties su SOLIDS
		for prop_info in props['element']['solids']:
			s_id = prop_info.get('solid_id')
			if s_id is not None:
				ep = create_or_get_element_property(prop_info)
				if ep and s_id < shape.getNumberOfSubshapes(MpcSubshapeType.Solid):
					geom.elementPropertyAssignment.onSolids[s_id] = ep
		
		doc.commitChanges()
	
	except Exception as e:
		print(f"    [WARNING] Errore assegnazione proprietà: {str(e)}")

def should_copy_geometry(geom_data):
	"""Determina se una geometria deve essere copiata in base ai filtri"""
	
	# Filtro per nome
	if COPY_CONFIG['filter_by_name']:
		if COPY_CONFIG['filter_by_name'].lower() not in geom_data['name'].lower():
			return False
	
	# Filtro per ID
	if len(COPY_CONFIG['filter_ids']) > 0:
		if geom_data['id'] not in COPY_CONFIG['filter_ids']:
			return False
	
	return True

def run_copy_mode():
	"""Esegue la modalità COPIA"""
	print("\n[MODALITÀ COPIA ATTIVA]")
	print("Ricreando geometrie e proprietà...")
	print("-"*80)
	
	# Carica dati JSON
	print(f"\n[FASE 1] Caricamento dati da: {COPY_CONFIG['input_json_file']}")
	
	if not os.path.exists(COPY_CONFIG['input_json_file']):
		print(f"✗ File non trovato: {COPY_CONFIG['input_json_file']}")
		print(f"   Suggerimento: Esegui prima con Copy=False per generare il JSON")
		return
	
	geometries_data = load_geometries_from_json(COPY_CONFIG['input_json_file'])
	if not geometries_data:
		return
	
	print(f"✓ Caricate {len(geometries_data)} geometrie dal JSON")
	
	# Nuovo documento se richiesto
	if COPY_CONFIG['create_new_document']:
		print("\n[INFO] Creazione nuovo documento richiesta")
		print("       Usa: File > New per creare manualmente un nuovo documento")
		print("       Poi ri-esegui questo script")
		return
	
	# Ricrea geometrie
	print(f"\n[FASE 2] Ricreazione geometrie")
	print("-"*80)
	
	created_count = 0
	skipped_count = 0
	error_count = 0
	
	for idx, geom_data in enumerate(geometries_data, 1):
		
		# Controlla filtri
		if not should_copy_geometry(geom_data):
			skipped_count += 1
			if COPY_CONFIG['verbose']:
				print(f"  [{idx}/{len(geometries_data)}] Skipping: {geom_data['name']}")
			continue
		
		print(f"  [{idx}/{len(geometries_data)}] Ricreando: {geom_data['name']}")
		
		# Ricrea geometria
		new_geom = recreate_geometry_from_data(geom_data)
		
		if new_geom:
			# Assegna proprietà
			if COPY_CONFIG['copy_properties']:
				print(f"    Assegnando proprietà...")
				assign_properties_to_geometry(new_geom, geom_data)
			
			created_count += 1
			print(f"    ✓ Creata: [{new_geom.id}] {new_geom.name}")
		else:
			error_count += 1
			print(f"    ✗ Errore nella creazione")
		
		App.processEvents()
		App.runCommand("Regenerate")
	
	print("\n" + "="*80)
	print("RICREAZIONE COMPLETATA!")
	print(f"Geometrie create: {created_count}")
	print(f"Geometrie saltate: {skipped_count}")
	print(f"Errori: {error_count}")
	print("="*80)

# ==============================================================================
# ESECUZIONE PRINCIPALE
# ==============================================================================

if __name__ == "__main__":
	try:
		if Copy:
			run_copy_mode()
		else:
			run_analyze_mode()
		
		doc.dirty = True
		
	except Exception as e:
		print(f"\n✗ ERRORE CRITICO: {str(e)}")
		import traceback
		traceback.print_exc()