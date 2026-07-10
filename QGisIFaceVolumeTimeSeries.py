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
from VolumeTimeSeries.defs import defs_geometric_design_projects as defs_gdps
from VolumeTimeSeries.defs import defs_volumes_computations as defs_vc
from VolumeTimeSeries.defs import defs_qgis
from pyLibQGIS.QGisIFace import QGisIFace

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

class QGisIFaceVolumeTimeSeries(QGisIFace):
    def __init__(self, iface, plugin_path):
        super().__init__(iface, plugin_path)
        self.qml_path = self.plugin_path + defs_qgis.QML_PATH
        self.layerTreeProject = None
        self.qml_path = self.plugin_path + defs_qgis.CONST_QML_PATH
        self.qml_mesh = self.qml_path + defs_qgis.CONTS_LAYER_MESH_QML
        self.qml_footprint = self.qml_path + defs_qgis.CONTS_LAYER_FOOTPRINT_QML

    def close_project(self):
        super().close_project()

    def load_geometric_design_project(self, gdp_id):
        str_error = ''
        root = QgsProject.instance().layerTreeRoot()
        layerTreeProject = root.findGroup(self.layerTreeProjectName)
        if layerTreeProject is None:
            self.open_project(self.project)
        if not gdp_id in self.project.geometric_design_projects:
            str_error = ('Not exists Geometric Design Projed Id: {}'.format(gdp_id))
            return str_error
        if not gdp_id in self.project.gdp_ply_file_path_by_id:
            str_error = ('Empty PLY file for Geometric Design Projed Id: {}'.format(gdp_id))
            return str_error
        gdp_ply_file_path = self.project.gdp_ply_file_path_by_id[gdp_id]
        if not os.path.exists(gdp_ply_file_path):
            str_error = ('For Geometric Design Projed Id: {}, not exists ply file:\n{}'
                         .format(gdp_id, gdp_ply_file_path))
            return str_error
        gdp = self.project.geometric_design_projects[gdp_id]
        layerTreeGDPName = defs_qgis.GDPS_LAYERS_GROUP_PREFIX + gdp_id
        layerTreeGDP = layerTreeProject.findGroup(layerTreeGDPName)
        if layerTreeGDP is not None:
            self.removeGroup(layerTreeProject, layerTreeGDPName)
        layerTreeGDP = layerTreeProject.addGroup(layerTreeGDPName)
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
        layerTreeGDP.addLayer(mesh_layer)
        # mesh_layer.updateExtents()
        self.iface.mapCanvas().setExtent(mesh_layer.extent())
        return str_error

    def load_project(self):
        str_error = super().load_project(defs_qgis.PROJECT_LAYERS_GROUP_PREFIX)
        if str_error:
            return str_error
        for gdp_id in self.project.geometric_design_projects:
            str_error = self.load_geometric_design_project(gdp_id)
            if str_error:
                return str_error
        return str_error

    def load_raster(self, root, name, file_path):
        str_error = ''

        return str_error

    def load_volume(self,
                    id,
                    gdp_id,
                    raster_file_path,
                    footprint_file_path):
        str_error = ''
        if not gdp_id in self.project.geometric_design_projects:
            str_error = ('Not exists Geometric Design Projed Id: {}'.format(gdp_id))
            return str_error
        if not id in self.project.volumes_computations:
            str_error = ('For Geometric Design Projed Id: {}\nnot exist volume id: {}'.format(gdp_id, id))
            return str_error
        root = QgsProject.instance().layerTreeRoot()
        layerTreeProject = root.findGroup(self.layerTreeProjectName)
        if layerTreeProject is None:
            self.open_project(self.project)
        layerTreeGDPName = defs_qgis.GDPS_LAYERS_GROUP_PREFIX + gdp_id
        layerTreeGDP = layerTreeProject.findGroup(layerTreeGDPName)
        if layerTreeGDP is None:
            str_error = self.load_geometric_design_project(gdp_id)
            if str_error:
                return str_error
            layerTreeGDP = layerTreeProject.findGroup(layerTreeGDPName)
        layerTreeVolumeName = defs_qgis.VOLUMES_LAYERS_GROUP_PREFIX + id
        layerTreeVolume = layerTreeGDP.findGroup(layerTreeVolumeName)
        if layerTreeVolume is None:
            layerTreeVolume = layerTreeGDP.addGroup(layerTreeVolumeName)
        str_date_from =  self.project.volumes_computations[id][defs_vc.FIELD_VOLUME_DATE_FROM]
        str_date_from_formatted = str_date_from.replace(':', '')
        str_date_to =  self.project.volumes_computations[id][defs_vc.FIELD_VOLUME_DATE_TO]
        str_date_to_formatted = str_date_from.replace(':', '')
        raster_basename = os.path.basename(raster_file_path).split('.')[0]
        raster_layer_name = str_date_from_formatted + '_' + str_date_to_formatted + '_' + raster_basename
        # # listLayers = QgsProject.instance().mapLayersByName(layer_name)
        # # if listLayers:
        # #     return str_error
        raster_layer = None
        for child in layerTreeVolume.children():
            if child.name() == raster_layer_name:
                raster_layer = child
        if raster_layer is None:
            raster_layer = QgsRasterLayer(raster_file_path, raster_layer_name)
            if not raster_layer.isValid():
                str_error = ('For Geometric Design Projed Id: {}\ninvalid raster layer from file:\n{}'
                             .format(gdp_id, raster_file_path))
                return str_error
            QgsProject.instance().addMapLayer(raster_layer, False)
            layerTreeVolume.addLayer(raster_layer)
        vector_basename = os.path.basename(footprint_file_path).split('.')[0]
        vector_basename = str_date_from_formatted + '_' + str_date_to_formatted + '_' + vector_basename
        vector_basename += defs_qgis.FOOTPRINT_LAYER_NAME_SUFFIX
        vector_layer = None
        for child in layerTreeVolume.children():
            if child.name() == vector_basename:
                vector_layer = child
        if vector_layer is None:
            vector_layer = QgsVectorLayer(footprint_file_path, vector_basename, "ogr")
            if not vector_layer.isValid():
                str_error = ('For Geometric Design Projed Id: {}\ninvalid footpring vector layer from file:\n{}'
                             .format(gdp_id, vector_layer))
                return str_error
            if os.path.exists(self.qml_footprint):
                vector_layer.loadNamedStyle(self.qml_footprint)
            QgsProject.instance().addMapLayer(vector_layer, False)
            layerTreeVolume.addLayer(vector_layer)
        return str_error

    def open_project(self,
                     project):
        super().open_project(project)
        self.load_project()
