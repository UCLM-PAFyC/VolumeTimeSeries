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
from VolumeTimeSeries.defs import qgis_gui_defines as defs_qgis
from VolumeTimeSeries.defs import defs_volumes_computations as defs_vc
# from lib import gui_defines as gd
# from lib import qgis_gui_defines as qgd
# from pyCRSs import CRSsDefines as cd
# import json
# import Tools

from qgis.core import (QgsApplication, QgsDataSourceUri, QgsProject,
                       QgsCoordinateReferenceSystem, QgsCoordinateTransform)
from qgis.core import (QgsProject, QgsVectorLayer, QgsSymbol, QgsRendererCategory,
                       QgsCategorizedSymbolRenderer, QgsMeshLayer, QgsRasterLayer)
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
        self.layerTreeVolumeById = {}
        self.layer_by_name = {}
        self.qml_path = self.plugin_path + defs_qgis.CONST_QML_PATH
        self.qml_mesh = self.qml_path + defs_qgis.CONTS_LAYER_MESH_QML
        self.qml_footprint = self.qml_path + defs_qgis.CONTS_LAYER_FOOTPRINT_QML

    def close_project(self):
        if not self.project:
            return
        # if self.layerTreeProjectName:
        #     self.project = None
        #     return
        root = QgsProject.instance().layerTreeRoot()
        if self.layerTreeProjectName:
            self.removeGroup(root, self.layerTreeProjectName)
            self.layerTreeProjectName = ''
            self.project = None
            self.layer_by_name.clear()
            self.layerTreeVolumeById.clear()
            self.layerTreeGDPById.clear()
        self.iface.mapCanvas().refresh()

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
                return str_error
            self.project_crs = QgsCoordinateReferenceSystem(epsg_code)
        geometry = QgsGeometry.fromRect(self.iface.mapCanvas().extent())
        qgis_project_crs = QgsProject.instance().crs()
        tr = QgsCoordinateTransform(qgis_project_crs, self.project_crs, QgsProject.instance())
        geometry.transform(tr)
        wkb = geometry.asWkb()
        return str_error, wkb

    def get_qgis_prefix_path(self):
        return self.qgis_prefix_path

    def load_geometric_design_project(self, gdp_id):
        str_error = ''
        if not gdp_id in self.project.geometric_design_projects:
            str_error = ('Not exists Geometric Design Projed Id: {}'.format(gdp_id))
            return str_error
        gdp = self.project.geometric_design_projects[gdp_id]
        layerTreeGDPName = defs_qgis.GDPS_LAYERS_GROUP_PREFIX + gdp_id
        if gdp_id in self.layerTreeGDPById:
            self.removeGroup(self.layerTreeProject, layerTreeGDPName)
            return str_error
        self.layerTreeGDPById[gdp_id] = self.layerTreeProject.addGroup(layerTreeGDPName)
        if not gdp_id in self.project.gdp_ply_file_path_by_id:
            return str_error
        gdp_ply_file_path = self.project.gdp_ply_file_path_by_id[gdp_id]
        if not os.path.exists(gdp_ply_file_path):
            str_error = ('For Geometric Design Projed Id: {}, not exists ply file:\n{}'
                         .format(gdp_id, gdp_ply_file_path))
            return str_error
        str_crs = gdp[defs_gdps.FIELD_CRS]
        if '+' in str_crs:
            str_crs = str_crs.split('+')
            str_crs = str_crs[0]
        # gdp_mesh_uri = gdp_ply_file_path + '?crs=25830' + gdp[defs_gdps.FIELD_CRS]
        layer_name = gdp_id + '_' + defs_qgis.GDPS_MESH_LAYER_NAME
        provider_name = 'mdal'
        self.iface.mainWindow().blockSignals(True)
        mesh_layer = QgsMeshLayer(gdp_ply_file_path, layer_name, provider_name)
        mesh_layer.setCrs(QgsCoordinateReferenceSystem(str_crs))  # gdp[defs_gdps.FIELD_CRS]))
        self.iface.mainWindow().blockSignals(False)
        if os.path.exists(self.qml_mesh):
            mesh_layer.loadNamedStyle(self.qml_mesh)
        QgsProject.instance().addMapLayer(mesh_layer, False)
        self.layerTreeGDPById[gdp_id].addLayer(mesh_layer)
        # mesh_layer.updateExtents()
        self.iface.mapCanvas().setExtent(mesh_layer.extent())
        self.layer_by_name[layer_name] = mesh_layer
        return str_error

    def load_project(self):
        str_error = ''
        root = QgsProject.instance().layerTreeRoot()
        project_tag = self.project.project_definition[defs_project.PROJECT_DEFINITIONS_TAG_TAG]
        project_crs = self.project.project_definition[defs_project.PROJECT_DEFINITIONS_TAG_PROJECTED_CRS]
        if not project_tag or not project_crs:
            return str_error
        self.layerTreeProjectName = defs_qgis.PROJECT_LAYERS_GROUP_PREFIX + project_tag
        # self.layerTreeProject = root.addGroup(self.layerTreeProjectName)
        self.layerTreeProject = root.insertGroup(0, self.layerTreeProjectName)
        qgisProjectCrsAsEpsg = QgsProject.instance().crs().authid()
        if qgisProjectCrsAsEpsg != project_crs:
            QgsProject.instance().setCrs(QgsCoordinateReferenceSystem(project_crs))
        for gdp_id in self.project.geometric_design_projects:
            str_error = self.load_geometric_design_project(gdp_id)
            if str_error:
                return str_error
        return str_error

    def load_raster(self, root, name, file_path):
        str_error = ''

        return str_error

    def load_volume(self,
                    id, gdp_id, raster_file_path, footprint_file_path):
        str_error = ''
        if not gdp_id in self.project.geometric_design_projects:
            str_error = ('Not exists Geometric Design Projed Id: {}'.format(gdp_id))
            return str_error
        if not id in self.project.volumes_computations:
            str_error = ('For Geometric Design Projed Id: {}\nnot exist volume id: {}'.format(gdp_id, id))
            return str_error
        if not gdp_id in self.layerTreeGDPById:
            str_error = self.load_geometric_design_project(gdp_id)
            if str_error:
                return str_error
        if not id in self.layerTreeVolumeById:
            layerTreeVolumeName = defs_qgis.VOLUMES_LAYERS_GROUP_PREFIX + id
            # self.layerTreeProject = root.addGroup(self.layerTreeProjectName)
            self.layerTreeVolumeById[id] = self.layerTreeGDPById[gdp_id].addGroup(layerTreeVolumeName)
        str_date_from =  self.project.volumes_computations[id][defs_vc.FIELD_VOLUME_DATE_FROM]
        str_date_from_formatted = str_date_from.replace(':', '')
        str_date_to =  self.project.volumes_computations[id][defs_vc.FIELD_VOLUME_DATE_TO]
        str_date_to_formatted = str_date_from.replace(':', '')
        raster_basename = os.path.basename(raster_file_path).split('.')[0]
        raster_layer_name = str_date_from_formatted + '_' + str_date_to_formatted + '_' + raster_basename
        # listLayers = QgsProject.instance().mapLayersByName(layer_name)
        # if listLayers:
        #     return str_error
        if not raster_layer_name in self.layer_by_name:
            raster_layer = QgsRasterLayer(raster_file_path, raster_layer_name)
            if not raster_layer.isValid():
                str_error = ('For Geometric Design Projed Id: {}\ninvalid raster layer from file:\n{}'
                             .format(gdp_id, raster_file_path))
                return str_error
            QgsProject.instance().addMapLayer(raster_layer, False)
            self.layerTreeVolumeById[id].addLayer(raster_layer)
            self.layer_by_name[raster_layer_name] = raster_layer
        vector_basename = os.path.basename(footprint_file_path).split('.')[0]
        vector_basename = str_date_from_formatted + '_' + str_date_to_formatted + '_' + vector_basename
        vector_basename += '_' + defs_qgis.FOOTPRINT_LAYER_NAME_SUFFIX
        # listLayers = QgsProject.instance().mapLayersByName(layer_name)
        # if listLayers:
        #     return str_error
        if not vector_basename in self.layer_by_name:
            vector_layer = QgsVectorLayer(footprint_file_path, vector_basename, "ogr")
            if not vector_layer.isValid():
                str_error = ('For Geometric Design Projed Id: {}\ninvalid footpring vector layer from file:\n{}'
                             .format(gdp_id, vector_layer))
                return str_error
            if os.path.exists(self.qml_footprint):
                vector_layer.loadNamedStyle(self.qml_footprint)
            QgsProject.instance().addMapLayer(vector_layer, False)
            self.layerTreeVolumeById[id].addLayer(vector_layer)
            self.layer_by_name[vector_basename] = vector_layer
        return str_error

    def open_project(self,
                     project):
        str_error = ''
        self.close_project()
        self.project = project
        self.load_project()
        return str_error

    def reload_all_layers(self):
        str_error = ''
        QgsProject.instance().reloadAllLayers()
        return str_error

    def removeGroup(self, root, name):
        # root = QgsProject.instance().layerTreeRoot()
        group = root.findGroup(name)
        if not group is None:
            for child in group.children():
                dump = child.dump()
                id = dump.split("=")[-1].strip()
                QgsProject.instance().removeMapLayer(id)
            root.removeChildNode(group)

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
