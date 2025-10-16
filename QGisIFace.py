# authors:
# David Hernandez Lopez, david.hernandez@uclm.es

import sys, os
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(current_path, '..'))
# sys.path.insert(0, '..')

from VolumeTimeSeries.lib.Project import Project
from VolumeTimeSeries.defs import defs_project
from VolumeTimeSeries.defs import defs_main
# from lib import gui_defines as gd
# from lib import qgis_gui_defines as qgd
# from pyCRSs import CRSsDefines as cd
# import json
# import Tools

from qgis.core import (QgsApplication, QgsDataSourceUri, QgsProject,
                       QgsCoordinateReferenceSystem, QgsCoordinateTransform)
from qgis.core import QgsProject, QgsVectorLayer, QgsSymbol, QgsRendererCategory, QgsCategorizedSymbolRenderer
from qgis.core import QgsField, QgsFeature, QgsPoint, QgsGeometry
from qgis import utils
from qgis.core import Qgis

class QGisIFace:
    def __init__(self,
                 iface,
                 plugin_path):
        self.iface = iface
        self.plugin_path = plugin_path
        self.project = None
        self.project_crs = None

    def close_project(self):
        if not self.project:
            return
        # if not self.layerTreeProjectName:
        #     self.project = None
        #     return
        # root = QgsProject.instance().layerTreeRoot()
        # if self.layerTreeProjectName:
        #     self.removeGroup(root, self.layerTreeProjectName)
        #     self.layerTreeProjectName = None
        #     self.layerTreeMeasurements = None
        #     self.layerTreeLSAs = None
        #     self.project = None
        #     self.layerNetworkPoints= None
        #     self.layerNetworkMeasurementsByTypeBySession.clear()
        #     self.layerLSAsMeasurements.clear()
        #     self.layerLSAsPositions.clear()
        #     self.layerTreeLsaById.clear()

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

    def load_project(self):
        root = QgsProject.instance().layerTreeRoot()
        # project_tag = self.project.project_definition[gd.PROJECT_DEFINITIONS_TAG_TAG]
        # project_crs = self.project.project_definition[gd.PROJECT_DEFINITIONS_TAG_PROJECTED_CRS]
        # if not project_tag or not project_crs:
        #     return
        # group_name = qgd.CONST_LAYER_TREE_PROJECT_NAME
        # self.layerTreeProjectName = group_name + '_' + project_tag
        # # self.layerTreeProject = root.addGroup(self.layerTreeProjectName)
        # self.layerTreeProject = root.insertGroup(0, self.layerTreeProjectName)
        # qgisProjectCrsAsEpsg = QgsProject.instance().crs().authid()
        # if qgisProjectCrsAsEpsg != project_crs:
        #     QgsProject.instance().setCrs(QgsCoordinateReferenceSystem(project_crs))
        # if len(self.project.points) == 0:
        #     return
        # self.layerNetworkPoints = None
        # self.layerNetworkPoints = QgsVectorLayer("Point?crs=" + project_crs,
        #                                          qgd.CONST_LAYER_NETWORK_POINTS_NAME, "memory")
        # layerNetworkPointsProvider = self.layerNetworkPoints.dataProvider()
        # for field_name in qgd.layer_network_points_attributes:
        #     layerNetworkPointsProvider.addAttributes([QgsField(field_name,
        #                                      qgd.layer_network_points_attributes[field_name])])
        # nop = 0
        # self.layerNetworkPoints.startEditing()
        # points_geometry = {}
        # for point_id in self.project.points:
        #     position = self.project.points[point_id].get_position_for_qgis()
        #     if not position:
        #         continue
        #     feature = QgsFeature()
        #     feature.setFields(layerNetworkPointsProvider.fields())
        #     fc = position.coordinates[cd.X_PROJECTION_LABEL]
        #     sc = position.coordinates[cd.Y_PROJECTION_LABEL]
        #     position_type = position.type
        #     geom = QgsPoint(fc, sc)
        #     feature.setGeometry(QgsGeometry.fromPoint(geom))
        #     feature.setAttribute("id", point_id)
        #     feature.setAttribute("type", position_type)
        #     self.layerNetworkPoints.addFeature(feature)
        #     nop = nop + 1
        #     enabled = True
        #     points_geometry[point_id] = geom
        #     # enabled = position.enabled_by_position_type[position_type]
        # self.layerNetworkPoints.commitChanges()
        # self.layerNetworkPoints.loadNamedStyle(self.qml_network_points)
        # QgsProject.instance().addMapLayer(self.layerNetworkPoints, False)
        # self.layerTreeProject.addLayer(self.layerNetworkPoints)
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
