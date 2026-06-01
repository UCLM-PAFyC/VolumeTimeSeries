# authors:
# David Hernandez Lopez, david.hernandez@uclm.es
import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(current_path, '..'))
sys.path.append(os.path.join(current_path, '../..'))
# sys.path.insert(0, '..')
# sys.path.insert(0, '../..')

from qgis.PyQt.QtCore import QVariant


PROJECT_LAYERS_GROUP_PREFIX = "Volumes Computations: "
GDPS_LAYERS_GROUP_PREFIX = "Geometric Design Projects: "
GDPS_MESH_LAYER_NAME = "Mesh Layer"
VOLUMES_LAYERS_GROUP_PREFIX = "Volume: "
FOOTPRINT_LAYER_NAME_SUFFIX = "_footprint"
CONST_QML_PATH = '/templates/qml'
CONTS_LAYER_MESH_QML = '/gdp_mesh.qml'
CONTS_LAYER_FOOTPRINT_QML = '/footprint.qml'