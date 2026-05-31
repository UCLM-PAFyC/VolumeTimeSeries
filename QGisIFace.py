# authors:
# David Hernandez Lopez, david.hernandez@uclm.es

import sys, os
from pathlib import Path

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(current_path, '..'))
# sys.path.insert(0, '..')

from VolumeTimeSeries.lib.Project import Project
from VolumeTimeSeries.defs import defs_project
from VolumeTimeSeries.defs import defs_main
from VolumeTimeSeries.defs import defs_qgis_paths
from VolumeTimeSeries.defs import defs_geometric_design_projects as defs_gdps
# from lib import gui_defines as gd
# from lib import qgis_gui_defines as qgd
# from pyCRSs import CRSsDefines as cd
# import json
# import Tools

from qgis.core import (QgsApplication, QgsDataSourceUri, QgsProject,
                       QgsCoordinateReferenceSystem, QgsCoordinateTransform)
from qgis.core import (QgsProject, QgsVectorLayer, QgsSymbol, QgsRendererCategory,
                       QgsCategorizedSymbolRenderer,QgsMeshLayer)
from qgis.core import QgsField, QgsFeature, QgsPoint, QgsGeometry
from qgis import utils
from qgis.core import Qgis
from qgis.core import QgsSettings

class QGisIFace:
    def __init__(self,
                 iface,
                 plugin_path):
        self.iface = iface
        self.plugin_path = plugin_path
        self.project = None
        self.project_crs = None
        qgis_bin_path = Path(QgsApplication.prefixPath())
        self.qgis_prefix_path = os.path.realpath(str(qgis_bin_path.parent.parent))
        self.osge4w_bat_path = os.path.normpath(self.qgis_prefix_path + defs_qgis_paths.OSGEO4W_BAT_SUFFIX_WINDOWS)
        self.osge4w_bin_path = os.path.normpath(self.qgis_prefix_path + defs_qgis_paths.OSGEO4W_BIN_SUFFIX_WINDOWS)
        self.qgis_bin_path = os.path.normpath(self.qgis_prefix_path + defs_qgis_paths.QGIS_BIN_SUFFIX_WINDOWS)
        self.qgis_plugins_path = os.path.normpath(self.qgis_prefix_path + defs_qgis_paths.QGIS_PLUGINS_SUFFIX_WINDOWS)
        self.qgis_python_path = os.path.normpath(self.qgis_prefix_path + defs_qgis_paths.QIGS_PYTHON_PATH_SUFFIX_WINDOWS)
        self.layerTreeProjectName = ''
        self.layerTreeProject = None
        self.layerTreeGDPById = {}

    def close_project(self):
        if not self.project:
            return
        if self.layerTreeProjectName:
            self.project = None
            return
        root = QgsProject.instance().layerTreeRoot()
        if self.layerTreeProjectName:
            self.removeGroup(root, self.layerTreeProjectName)
            self.layerTreeProjectName = ''
            self.project = None
            self.layerTreeGDPById.clear()

    def get_map_canvas_wkb_geometry_in_project_crs(self):
        str_error = ''
        if not self.project_crs:
            str_project_crs_epsg_code = self.project.project_definition[
                defs_project.PROJECT_DEFINITIONS_TAG_PROJECTED_CRS]
            epsg_code = -1
            try:
                epsg_code = int(str_project_crs_epsg_code.replace(defs_main.EPSG_STRING_PREFIX, ''))
            except ValueError:
                str_error = ('Invalid integer value from: {}'.format(str_project_crs_epsg_code))
            self.project_crs = QgsCoordinateReferenceSystem(epsg_code)
        geometry = QgsGeometry.fromRect(self.iface.mapCanvas().extent())
        qgis_project_crs = QgsProject.instance().crs()
        tr = QgsCoordinateTransform(qgis_project_crs, self.project_crs, QgsProject.instance())
        geometry.transform(tr)
        wkb = geometry.asWkb()
        return str_error, wkb

    def get_qgis_prefix_path(self):
        return self.qgis_prefix_path

    def load_project(self):
        root = QgsProject.instance().layerTreeRoot()
        project_tag = self.project.project_definition[defs_project.PROJECT_DEFINITIONS_TAG_TAG]
        project_crs = self.project.project_definition[defs_project.PROJECT_DEFINITIONS_TAG_PROJECTED_CRS]
        if not project_tag or not project_crs:
            return
        self.layerTreeProjectName = defs_project.QGIS_PROJECT_LAYERS_GROUP_PREFIX + project_tag
        # self.layerTreeProject = root.addGroup(self.layerTreeProjectName)
        self.layerTreeProject = root.insertGroup(0, self.layerTreeProjectName)
        qgisProjectCrsAsEpsg = QgsProject.instance().crs().authid()
        if qgisProjectCrsAsEpsg != project_crs:
            QgsProject.instance().setCrs(QgsCoordinateReferenceSystem(project_crs))

        # Create a QSettings instance
        # qgsSettings = QgsSettings()

        # 1. Action: Define the default CRS behavior for new layers
        # Valid options are:
        # 'useProject'    -> Uses the current project's CRS
        # 'useDefault'     -> Uses a specific predefined default CRS
        # 'prompt'        -> Asks the user to choose a CRS upon creation
        # 'useUnknown'    -> Leaves the layer's CRS as unknown
        # projections_default_behavior_current = qgsSettings.value("/Projections/defaultBehavior")
        self.iface.mainWindow().blockSignals(True)
        for gdp_id in self.project.geometric_design_projects:
            gdp = self.project.geometric_design_projects[gdp_id]
            layerTreeGDPName = defs_gdps.QGIS_GDPS_LAYERS_GROUP_PREFIX + gdp_id
            self.layerTreeGDPById[gdp_id] = self.layerTreeProject.addGroup(layerTreeGDPName)
            if not gdp_id in self.project.gdp_ply_file_path_by_id:
                continue
            gdp_ply_file_path = self.project.gdp_ply_file_path_by_id[gdp_id]
            str_crs = gdp[defs_gdps.FIELD_CRS]
            if '+' in str_crs:
                str_crs = str_crs.split('+')
                str_crs = str_crs[0]
            # qgsSettings.setValue("/Projections/defaultBehavior", "useUnknown")
            # qgsSettings.sync()
            # gdp_mesh_uri = gdp_ply_file_path + '?crs=25830' + gdp[defs_gdps.FIELD_CRS]
            layer_name = defs_gdps.QGIS_GDPS_MESH_LAYER_NAME
            provider_name = 'mdal'
            mesh_layer = QgsMeshLayer(gdp_ply_file_path, layer_name, provider_name)
            mesh_layer.setCrs(QgsCoordinateReferenceSystem(str_crs)) #gdp[defs_gdps.FIELD_CRS]))
            # mesh_layer.loadNamedStyle(self.qml_network_points)
            QgsProject.instance().addMapLayer(mesh_layer, False)
            self.layerTreeGDPById[gdp_id].addLayer(mesh_layer)
            # mesh_layer.updateExtents()
            self.iface.mapCanvas().setExtent(mesh_layer.extent())
        # qgsSettings.setValue("/Projections/defaultBehavior", projections_default_behavior_current)
        self.iface.mainWindow().blockSignals(False)

            # self.layerTreeLSAs = self.layerTreeProject.addGroup(layerTreeLSAsName)
        # self.layerNetworkPoints.updateExtents()
        # self.iface.mapCanvas().setExtent(self.layerNetworkPoints.extent())

    def open_project(self,
                     project):
        self.close_project()
        self.project = project
        self.load_project()

    def reload_all_layers(self):
        str_error = ''
        QgsProject.instance().reloadAllLayers()
        return str_error

    def set_map_canvas_from_wkb_geometry_in_project_crs(self,
                                                        wkb_geometry):
        str_error = ''
        if not self.project_crs:
            str_project_crs_epsg_code = self.project.project_definition[
                defs_project.PROJECT_DEFINITIONS_TAG_PROJECTED_CRS]
            epsg_code = -1
            try:
                epsg_code = int(str_project_crs_epsg_code.replace(defs_main.EPSG_STRING_PREFIX, ''))
            except ValueError:
                str_error = ('Invalid integer value from: {}'.format(str_project_crs_epsg_code))
            self.project_crs = QgsCoordinateReferenceSystem(epsg_code)
        geometry = QgsGeometry()
        geometry.fromWkb(wkb_geometry)
        qgis_project_crs = QgsProject.instance().crs()
        tr = QgsCoordinateTransform(self.project_crs, qgis_project_crs, QgsProject.instance())
        geometry.transform(tr)
        self.iface.mapCanvas().setExtent(geometry.boundingBox())
        self.iface.mapCanvas().refresh()
        return str_error

    def set_project(self,
                    project):
        self.project = project
