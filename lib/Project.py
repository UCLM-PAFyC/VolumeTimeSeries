# authors:
# David Hernandez Lopez, david.hernandez@uclm.es
from codecs import strict_errors

from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog, QFileDialog, QPushButton, QComboBox
from PyQt5.QtCore import QDir, QFileInfo, QFile, QDate, QDateTime

import os
import sys
import math
import random
import re
import json
import xmltodict
import numpy as np
from datetime import datetime

from osgeo import gdal, osr, ogr
gdal.UseExceptions()

current_path = os.path.dirname(__file__)
sys.path.append(os.path.join(current_path, '..'))
sys.path.append(os.path.join(current_path, '../..'))
# sys.path.insert(0, '..')
# sys.path.insert(0, '../..')

from VolumeTimeSeries.defs import defs_paths, defs_project, defs_main
from VolumeTimeSeries.defs import defs_geometric_design_projects as defs_gdp

from VolumeTimeSeries.gui.ProjectDefinitionDialog import ProjectDefinitionDialog
from VolumeTimeSeries.gui.GeometricDesignProjectsDialog import GeometricDesignProjectsDialog

common_libs_absolute_path = os.path.join(current_path, defs_paths.COMMON_LIBS_RELATIVE_PATH)
sys.path.append(common_libs_absolute_path)

from pyLibCRSs import CRSsDefines as defs_crs
from pyLibCRSs.CRSsTools import CRSsTools
from pyLibQtTools import Tools
# from pyLibGDAL import defs_gdal
# from pyLibGDAL.GDALTools import GDALTools
# from pyLibGDAL.RasterDEM import RasterDEM
from pyLibLandXml.LandXml import LandXml


class Project:
    def __init__(self,
                 qgis_iface,
                 settings,
                 app_path):
        self.qgis_iface = qgis_iface
        self.settings = settings
        self.file_path = None
        self.app_path = app_path
        self.project_definition = {}
        self.project_definition[defs_project.PROJECT_DEFINITIONS_TAG_NAME] = None
        self.project_definition[defs_project.PROJECT_DEFINITIONS_TAG_TAG] = None
        self.project_definition[defs_project.PROJECT_DEFINITIONS_TAG_AUTHOR] = None
        # self.project_definition[defs_project.PROJECT_DEFINITIONS_TAG_GEO3D_CRS] = None
        # self.project_definition[defs_project.PROJECT_DEFINITIONS_TAG_GEO2D_CRS] = None
        # self.project_definition[defs_project.PROJECT_DEFINITIONS_TAG_ECEF_CRS] = None
        self.project_definition[defs_project.PROJECT_DEFINITIONS_TAG_PROJECTED_CRS] = defs_project.CRS_PROJECTED_DEFAULT
        self.project_definition[defs_project.PROJECT_DEFINITIONS_TAG_VERTICAL_CRS] = defs_project.CRS_VERTICAL_DEFAULT
        self.project_definition[defs_project.PROJECT_DEFINITIONS_TAG_OUTPUT_PATH] = None
        self.project_definition[defs_project.PROJECT_DEFINITIONS_TAG_DESCRIPTION] = None
        self.project_definition[defs_project.PROJECT_DEFINITIONS_TAG_START_DATE] = None
        self.project_definition[defs_project.PROJECT_DEFINITIONS_TAG_FINISH_DATE] = None
        self.crs_id = ''
        self.crs_tools = None
        self.geometric_design_projects = {}
        # self.gpkg_tools = None
        self.initialize()

    def create_geometric_design_project_from_landxml(self,
                                                     id,
                                                     crs_id,
                                                     file_path):
        str_error = ''
        geometric_design_project = {}
        landXml = LandXml()
        str_error = landXml.set_from_file(file_path)
        if str_error:
            return str_error, None
        points_distance = defs_gdp.AXIS_POINTS_DISTANCE
        str_error = landXml.set_axis_points(points_distance)
        if str_error:
            return str_error, None
        str_error, wkt_linestring, wkt_profile_linestring = landXml.get_axis_points_as_wktlinestring()
        if str_error:
            return str_error, None
        grading_axis = False # must be False, option use grading axis for triangulation of LandXml is not implemented yet
        cross_sections = True
        # ply_file_path = None
        ply_file_path = landXml.file_path
        ply_file_path = ply_file_path.lower()
        ply_file_path = ply_file_path.replace(".xml", ".ply")
        ply_file_path = os.path.normpath(ply_file_path)
        str_error = landXml.compute_triangulation(grading_axis,
                                                  cross_sections,
                                                  ply_file_path)
        if str_error:
            return str_error, None
        geometric_design_project = {}
        geometric_design_project[defs_gdp.FIELD_ID] = id
        geometric_design_project[defs_gdp.FIELD_ENABLED] = 1
        geometric_design_project[defs_gdp.FIELD_DESCRIPTION] = ""
        geometric_design_project[defs_gdp.FIELD_CRS] = crs_id
        geometric_design_project[defs_gdp.FIELD_CONTENT] = landXml.as_dict
        geometric_design_project[defs_gdp.FIELD_AXIS3D] = wkt_linestring
        geometric_design_project[defs_gdp.FIELD_PROFILE] = wkt_profile_linestring
        geometric_design_project[defs_gdp.FIELD_TRIANGULATION_PLY] = landXml.triangulation_ply_content
        geometric_design_project[defs_gdp.FIELD_SOURCE_FILE] = file_path
        geometric_design_project[defs_gdp.FIELD_TRIANGULATION_POINTS] = landXml.triangulation_points
        geometric_design_project[defs_gdp.FIELD_TRIANGULATION_TRIANGLES] = landXml.triangulation_triangles
        return str_error, geometric_design_project

    def geometric_design_projects_gui(self, parent_widget):
        str_error = ''
        title = defs_gdp.DIALOG_TITLE
        dialog = GeometricDesignProjectsDialog(self, title, parent_widget)
        dialog_result = dialog.exec()
        # if dialog_result != QDialog.Accepted:
        #     return str_error
        # definition_is_saved = dialog.is_saved
        # if dialog_result != QDialog.Accepted:
        #     return str_error, definition_is_saved
        # return str_error, definition_is_saved
        return str_error

    def initialize(self):
        self.crs_tools = CRSsTools()
        epsg_crs_prefix = defs_crs.EPSG_TAG + ':'
        crs_2d_id = self.project_definition[defs_project.PROJECT_DEFINITIONS_TAG_PROJECTED_CRS]
        crs_2d_epsg_code = int(crs_2d_id.replace(epsg_crs_prefix, ''))
        self.crs_id = epsg_crs_prefix + str(crs_2d_epsg_code)
        crs_vertical_id = self.project_definition[defs_project.PROJECT_DEFINITIONS_TAG_VERTICAL_CRS]
        if crs_vertical_id != defs_crs.VERTICAL_ELLIPSOID_TAG:
            crs_vertical_epsg_code = int(crs_vertical_id.replace(epsg_crs_prefix, ''))
            self.crs_id += ('+' + str(crs_vertical_epsg_code))
        # self.gpkg_tools = GpkgTools(self.crs_tools)
        if self.qgis_iface:
            self.qgis_iface.set_project(self)
        return

    def project_definition_gui(self,
                               is_process_creation):
        str_error = ""
        title = defs_project.PROJECT_DEFINITION_DIALOG_TITLE
        dialog = ProjectDefinitionDialog(self, title, is_process_creation)
        dialog_result = dialog.exec()
        # if dialog_result != QDialog.Accepted:
        #     return str_error
        definition_is_saved = dialog.is_saved
        if dialog_result != QDialog.Accepted:
            return str_error, definition_is_saved
        return str_error, definition_is_saved
        return str_error

    def save_to_json(self):
        str_error = ''
        # if not os.path.exists(self.file_name):
        if not self.file_path:
            str_error = Project.__name__ + "." + self.save_to_json.__name__
            str_error = ("Project has not json file")
            return str_error
        as_dict = {}
        # str_aux_error, definition_as_dict = self.definition_old.get_as_dict()
        # if str_aux_error:
        #     str_error = Project.__name__ + "." + self.save_to_json.__name__
        #     str_error += ('\nSaving project to json file, error:\n{}'.format(str_aux_error))
        #     return str_error
        # as_dict[gd.PROJECT_DEFINITIONS_TAG] = definition_as_dict
        as_dict[defs_project.PROJECT_DEFINITIONS_TAG] = self.project_definition
        as_dict[defs_project.PROJECT_GEOMETRIC_DESIGNS_TAG] = self.geometric_design_projects
        json_object = json.dumps(as_dict, indent=4, ensure_ascii=False)
        # Writing to sample.json
        with open(self.file_path, "w") as outfile:
            outfile.write(json_object)
        if self.qgis_iface:
            self.qgis_iface.open_project(self)
        return str_error

    def set_definition_from_json(self, json_content):
        str_error = ''
        if not defs_project.PROJECT_DEFINITIONS_TAG_NAME in json_content:
            str_error = ("No {} in json content {}".format(defs_project.PROJECT_DEFINITIONS_TAG_NAME,
                                                           defs_project.PROJECT_DEFINITIONS_TAG))
            return str_error
        if not defs_project.PROJECT_DEFINITIONS_TAG_TAG in json_content:
            str_error = ("No {} in json content {}".format(defs_project.PROJECT_DEFINITIONS_TAG_TAG,
                                                           defs_project.PROJECT_DEFINITIONS_TAG))
            return str_error
        if not defs_project.PROJECT_DEFINITIONS_TAG_AUTHOR in json_content:
            str_error = ("No {} in json content {}".format(defs_project.PROJECT_DEFINITIONS_TAG_AUTHOR,
                                                           defs_project.PROJECT_DEFINITIONS_TAG))
            return str_error
        if not defs_project.PROJECT_DEFINITIONS_TAG_PROJECTED_CRS in json_content:
            str_error = ("No {} in json content {}".format(defs_project.PROJECT_DEFINITIONS_TAG_PROJECTED_CRS,
                                                           defs_project.PROJECT_DEFINITIONS_TAG))
            return str_error
        if not defs_project.PROJECT_DEFINITIONS_TAG_VERTICAL_CRS in json_content:
            str_error = ("No {} in json content {}".format(defs_project.PROJECT_DEFINITIONS_TAG_VERTICAL_CRS,
                                                           defs_project.PROJECT_DEFINITIONS_TAG))
            return str_error
        if not defs_project.PROJECT_DEFINITIONS_TAG_OUTPUT_PATH in json_content:
            str_error = ("No {} in json content {}".format(defs_project.PROJECT_DEFINITIONS_TAG_OUTPUT_PATH,
                                                           defs_project.PROJECT_DEFINITIONS_TAG))
            return str_error
        if not defs_project.PROJECT_DEFINITIONS_TAG_START_DATE in json_content:
            str_error = ("No {} in json content {}".format(defs_project.PROJECT_DEFINITIONS_TAG_START_DATE,
                                                           defs_project.PROJECT_DEFINITIONS_TAG))
            return str_error
        if not defs_project.PROJECT_DEFINITIONS_TAG_FINISH_DATE in json_content:
            str_error = ("No {} in json content {}".format(defs_project.PROJECT_DEFINITIONS_TAG_FINISH_DATE,
                                                           defs_project.PROJECT_DEFINITIONS_TAG))
            return str_error
        name = json_content[defs_project.PROJECT_DEFINITIONS_TAG_NAME]
        tag = json_content[defs_project.PROJECT_DEFINITIONS_TAG_TAG]
        author = json_content[defs_project.PROJECT_DEFINITIONS_TAG_AUTHOR]
        crs_projected_id = json_content[defs_project.PROJECT_DEFINITIONS_TAG_PROJECTED_CRS]
        crs_vertical_id = json_content[defs_project.PROJECT_DEFINITIONS_TAG_VERTICAL_CRS]
        output_path = json_content[defs_project.PROJECT_DEFINITIONS_TAG_OUTPUT_PATH]
        description = json_content[defs_project.PROJECT_DEFINITIONS_TAG_DESCRIPTION]
        start_date = json_content[defs_project.PROJECT_DEFINITIONS_TAG_START_DATE]
        if start_date:
            date_start_date = QDate.fromString(start_date, defs_main.QDATE_TO_STRING_FORMAT)
            if not date_start_date.isValid():
                str_error = ("Invalid date: {} for format: {}".format(start_date, defs_main.QDATE_TO_STRING_FORMAT))
                return str_error
        finish_date = json_content[defs_project.PROJECT_DEFINITIONS_TAG_FINISH_DATE]
        if finish_date:
            date_finish_date = QDate.fromString(finish_date, defs_main.QDATE_TO_STRING_FORMAT)
            if not date_finish_date.isValid():
                str_error = ("Invalid date: {} for format: {}".format(finish_date, defs_main.QDATE_TO_STRING_FORMAT))
                return str_error
        self.project_definition[defs_project.PROJECT_DEFINITIONS_TAG_NAME] = name
        self.project_definition[defs_project.PROJECT_DEFINITIONS_TAG_TAG] = tag
        self.project_definition[defs_project.PROJECT_DEFINITIONS_TAG_AUTHOR] = author
        self.project_definition[defs_project.PROJECT_DEFINITIONS_TAG_PROJECTED_CRS] = crs_projected_id
        self.project_definition[defs_project.PROJECT_DEFINITIONS_TAG_VERTICAL_CRS] = crs_vertical_id
        self.project_definition[defs_project.PROJECT_DEFINITIONS_TAG_OUTPUT_PATH] = output_path
        self.project_definition[defs_project.PROJECT_DEFINITIONS_TAG_DESCRIPTION] = description
        self.project_definition[defs_project.PROJECT_DEFINITIONS_TAG_START_DATE] = start_date
        self.project_definition[defs_project.PROJECT_DEFINITIONS_TAG_FINISH_DATE] = finish_date
        epsg_crs_prefix = defs_crs.EPSG_TAG + ':'
        crs_2d_id = self.project_definition[defs_project.PROJECT_DEFINITIONS_TAG_PROJECTED_CRS]
        crs_2d_epsg_code = int(crs_2d_id.replace(epsg_crs_prefix, ''))
        self.crs_id = epsg_crs_prefix + str(crs_2d_epsg_code)
        crs_vertical_id = self.project_definition[defs_project.PROJECT_DEFINITIONS_TAG_VERTICAL_CRS]
        if crs_vertical_id != defs_crs.VERTICAL_ELLIPSOID_TAG:
            crs_vertical_epsg_code = int(crs_vertical_id.replace(epsg_crs_prefix, ''))
            self.crs_id += ('+' + str(crs_vertical_epsg_code))

        return

    def set_geometric_design_projects_from_json(self,
                                                json_content):
        str_error = ""
        geometric_design_projects = {}
        for id in json_content:
            gdp_json_content = json_content[id]
            for field_name in defs_gdp.fields:
                if not field_name in gdp_json_content:
                    str_error = ('For geomatric design project id: {}'.format(id))
                    str_error += ("\nNo {} in json content".format(field_name))
                    return str_error
            geometric_design_projects[id] = gdp_json_content
        self.geometric_design_projects = geometric_design_projects
        return str_error

    def set_from_json(self, file_name):
        str_error = ''
        if not os.path.exists(file_name):
            str_error = Project.__name__ + "." + self.set_from_json.__name__
            str_error += ("Not exists json project file:\n{}".format(file_name))
            return str_error
        with open(file_name, 'r') as file:
            project_from_json = json.load(file)
        if not defs_project.PROJECT_DEFINITIONS_TAG in project_from_json:
            str_error = Project.__name__ + "." + self.set_from_json.__name__
            str_error += ("No {} in json project file:\n{}".format(defs_project.PROJECT_DEFINITIONS_TAG,
                                                                  file_name))
            return str_error
        str_aux_error = self.set_definition_from_json(project_from_json[defs_project.PROJECT_DEFINITIONS_TAG])
        if str_aux_error:
            str_error = Project.__name__ + "." + self.set_from_json.__name__
            str_error += ('\nSetting from json project file:\n{}\nerror:\n{}'.format(file_name, str_aux_error))
            return str_error
        if defs_project.PROJECT_GEOMETRIC_DESIGNS_TAG in project_from_json:
            str_aux_error = self.set_geometric_design_projects_from_json(
                project_from_json[defs_project.PROJECT_GEOMETRIC_DESIGNS_TAG])
            if str_aux_error:
                str_error = Project.__name__ + "." + self.set_from_json.__name__
                str_error += ('\nSetting from json project file:\n{}\nerror:\n{}'.format(file_name, str_aux_error))
                return str_error
        self.file_path = file_name
        return str_error

