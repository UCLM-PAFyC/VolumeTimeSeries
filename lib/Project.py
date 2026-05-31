# authors:
# David Hernandez Lopez, david.hernandez@uclm.es
from codecs import strict_errors

from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog, QFileDialog, QPushButton, QComboBox, QProgressDialog
from PyQt5.QtCore import QDir, QFileInfo, QFile, QDate, QDateTime, Qt

import os
import sys
import subprocess
import math
import random
import re
import json
import xmltodict
import numpy as np
from datetime import datetime

from osgeo import gdal, osr, ogr
from remotior_sensus.util.files_directories import output_path

gdal.UseExceptions()

class GdalErrorHandler(object):
    def __init__(self):
        self.err_level = gdal.CE_None
        self.err_no = 0
        self.err_msg = ''

    def handler(self, err_level, err_no, err_msg):
        self.err_level = err_level
        self.err_no = err_no
        self.err_msg = err_msg

err = GdalErrorHandler()
gdal.PushErrorHandler(err.handler)
gdal.UseExceptions()  # Exceptions will get raised on anything >= gdal.CE_Failure
assert err.err_level == gdal.CE_None, 'the error level starts at 0'

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(current_path, '..'))
sys.path.append(os.path.join(current_path, '../..'))
# sys.path.insert(0, '..')
# sys.path.insert(0, '../..')

from VolumeTimeSeries.defs import defs_paths, defs_project, defs_main
from VolumeTimeSeries.defs import defs_geometric_design_projects as defs_gdp
from VolumeTimeSeries.defs import defs_volumes_computations as defs_vc
from VolumeTimeSeries.defs import defs_qgis_paths

from VolumeTimeSeries.gui.ProjectDefinitionDialog import ProjectDefinitionDialog
from VolumeTimeSeries.gui.GeometricDesignProjectsDialog import GeometricDesignProjectsDialog
from VolumeTimeSeries.gui.VolumesComputationsDialog import VolumesComputationsDialog

common_libs_absolute_path = os.path.join(current_path, defs_paths.COMMON_LIBS_RELATIVE_PATH)
sys.path.append(common_libs_absolute_path)

from pyLibCRSs import CRSsDefines as defs_crs
from pyLibCRSs.CRSsTools import CRSsTools
from pyLibQtTools import Tools
from pyLibGDAL import defs_gdal
from pyLibGDAL.GDALTools import GDALTools
# from pyLibGDAL.RasterDEM import RasterDEM
from pyLibLandXml.LandXml import LandXml
from pyLibPhotogrammetry.defs import defs_projects_dialog as defs_ph_prjs_dlg
from pyLibPhotogrammetry.gui.PhotogrammetryProjectsDialog import PhotogrammetryProjectsDialog

def get_exists_footprint_from_geojson(file_path):
    exists_footprint = False
    if not os.path.isfile(file_path):
        return exists_footprint
    with open(file_path) as json_file:
        data = json.load(json_file)
        if defs_vc.JSON_FP_FIELD_FEATURES in data:
            features = data[defs_vc.JSON_FP_FIELD_FEATURES]
            if isinstance(features, list):
                for feature in features:
                    if isinstance(feature, dict):
                        if defs_vc.JSON_FP_FIELD_FEATURES_GEOMETRY in feature:
                            geometry = feature[defs_vc.JSON_FP_FIELD_FEATURES_GEOMETRY]
                            if not geometry is None:
                                exists_footprint = True
                                break
    return exists_footprint

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
        self.photogrammetry_projects = {}
        self.volumes_computations = {}
        # self.gpkg_tools = None
        self.qgis_prefix_path = None
        self.osge4w_bat_path = None
        self.osge4w_bin_path = None
        self.qgis_bin_path = None
        self.qgis_plugins_path = None
        self.qgis_python_path = None
        self.initialize()

    def create_geometric_design_project_from_landxml(self,
                                                     id,
                                                     crs_id,
                                                     file_path,
                                                     roi_width,
                                                     gsd_computation):
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
        try:
            axis_geom = ogr.CreateGeometryFromWkt(wkt_linestring)
        except Exception as e:
            str_error = 'GDAL Error: ' + e.args[0]
            return str_error, None
        try:
            roi_geom = axis_geom.Buffer(roi_width)
        except Exception as e:
            str_error = 'GDAL Error: ' + e.args[0]
            return str_error, None
        try:
            wkt_roi = roi_geom.ExportToWkt()
        except Exception as e:
            str_error = 'GDAL Error: ' + e.args[0]
            return str_error, None
        try:
            roi_min_x, roi_max_x, roi_min_y, roi_max_y = roi_geom.GetEnvelope()
        except Exception as e:
            str_error = 'GDAL Error: ' + e.args[0]
            return str_error, None
        min_x = np.floor(roi_min_x / gsd_computation) * gsd_computation
        max_x = np.ceil(roi_max_x / gsd_computation) * gsd_computation
        min_y = np.floor(roi_min_y / gsd_computation) * gsd_computation
        max_y = np.ceil(roi_max_y / gsd_computation) * gsd_computation
        wkt_bb = "POLYGON(("
        wkt_bb += "{:.2f}".format(min_x)
        wkt_bb += " "
        wkt_bb += "{:.2f}".format(min_y)
        wkt_bb += ","
        wkt_bb += "{:.2f}".format(min_x)
        wkt_bb += " "
        wkt_bb += "{:.2f}".format(max_y)
        wkt_bb += ","
        wkt_bb += "{:.2f}".format(max_x)
        wkt_bb += " "
        wkt_bb += "{:.2f}".format(max_y)
        wkt_bb += ","
        wkt_bb += "{:.2f}".format(max_x)
        wkt_bb += " "
        wkt_bb += "{:.2f}".format(min_y)
        wkt_bb += ","
        wkt_bb += "{:.2f}".format(min_x)
        wkt_bb += " "
        wkt_bb += "{:.2f}".format(min_y)
        wkt_bb += "))"
        try:
            bb_geom = ogr.CreateGeometryFromWkt(wkt_linestring)
        except Exception as e:
            str_error = 'GDAL Error: ' + e.args[0]
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
        geometric_design_project[defs_gdp.FIELD_ROI_WIDTH] = roi_width
        geometric_design_project[defs_gdp.FIELD_ROI] = wkt_roi
        geometric_design_project[defs_gdp.FIELD_GSD_VOLUMES_COMPUTATION] = gsd_computation
        geometric_design_project[defs_gdp.FIELD_SOURCE_FILE] = file_path
        geometric_design_project[defs_gdp.FIELD_TRIANGULATION_POINTS] = landXml.triangulation_points
        geometric_design_project[defs_gdp.FIELD_TRIANGULATION_TRIANGLES] = landXml.triangulation_triangles
        geometric_design_project[defs_gdp.FIELD_MINIMUM_X] = min_x
        geometric_design_project[defs_gdp.FIELD_MAXIMUM_X] = max_x
        geometric_design_project[defs_gdp.FIELD_MINIMUM_Y] = min_y
        geometric_design_project[defs_gdp.FIELD_MAXIMUM_Y] = max_y
        geometric_design_project[defs_gdp.FIELD_BB_WKT] = wkt_bb
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

    def get_qgis_prefix_path(self):
        return self.qgis_prefix_path

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

    def photogrammetry_projects_gui(self, parent_widget):
        str_error = ''
        title = defs_ph_prjs_dlg.PHOTOGRAMMETRY_PROJECTS_DIALOG_TITLE
        dialog = PhotogrammetryProjectsDialog(self, title, parent_widget)
        dialog_result = dialog.exec()
        # if dialog_result != QDialog.Accepted:
        #     return str_error
        # is_saved = dialog.is_saved
        # if dialog_result != QDialog.Accepted:
        #     return str_error, is_saved
        # return str_error, is_saved
        return str_error

    def processVolumesComputations(self,
                                   computeForDtm,
                                   computeForDsm,
                                   computeForGeometricDesigns,
                                   computeFromPreviousDates):
        str_error = ''
        error_msgs = []
        output_path = self.project_definition[defs_project.PROJECT_DEFINITIONS_TAG_OUTPUT_PATH]
        if not output_path:
            str_error = Project.__name__ + "." + self.save_to_json.__name__
            str_error += ("\nProject output path is not defined")
            return str_error
        if self.qgis_prefix_path is None:
            str_error = Project.__name__ + "." + self.save_to_json.__name__
            str_error += ("\nQGIS prefix path is None")
            return str_error
        if not os.path.isdir(output_path):
            str_error = Project.__name__ + "." + self.save_to_json.__name__
            str_error += ("\nProject output path is not a path:\n{}".format(output_path))
            return str_error
        if not os.path.exists(output_path):
            str_error = Project.__name__ + "." + self.save_to_json.__name__
            str_error += ("\nProject output path not exists:\n{}".format(output_path))
            return str_error
        if not computeForGeometricDesigns:
            str_error = Project.__name__ + "." + self.save_to_json.__name__
            str_error += ("\nNot compute for Geometric Design Projects option is not implemented")
            return str_error
        # compute design projects as raster
        gdp_raster_filepath_by_id = {}
        gdp_raster_fp_filepath_by_id = {}
        gdp_raster_fp_geometry_by_id = {}
        steps = len(self.geometric_design_projects)
        progress = QProgressDialog("Computing raster for geometric design projects...", "Cancel", 0, 0)
        # progress = QProgressDialog("Computing raster for geometric design projects...", "Cancel", 0, steps)
        progress.setWindowModality(Qt.WindowModal)  # Bloquea la ventana principal
        progress.setWindowTitle("Wait for finished")
        progress.show()
        geojson_fp_fields = defs_vc.geojson_fp_fields
        geojson_fp_filter_fields = None
        QApplication.processEvents()
        # i = 0
        for gdp_id in self.geometric_design_projects:
            # i = i + 1
            # progress.setValue(i)
            # if progress.wasCanceled():
            #     break
            progress.setLabelText('Processing Geometric Design Project: {}'.format(gdp_id))
            QApplication.processEvents()
            # progress.show()
            gdp = self.geometric_design_projects[gdp_id]
            gdp_enabled = gdp[defs_gdp.FIELD_ENABLED]
            if gdp_enabled == 0:
                continue
            gdp_file_basename = "gdp_" + gdp_id
            gdp_crs = gdp[defs_gdp.FIELD_CRS]
            gdp_gsd = np.round(gdp[defs_gdp.FIELD_GSD_VOLUMES_COMPUTATION]*100.)/100. # cm accuracy
            gdp_min_x = np.floor(gdp[defs_gdp.FIELD_MINIMUM_X])
            gdp_max_x = np.ceil(gdp[defs_gdp.FIELD_MAXIMUM_X])
            gdp_min_y = np.floor(gdp[defs_gdp.FIELD_MINIMUM_Y])
            gdp_max_y = np.ceil(gdp[defs_gdp.FIELD_MAXIMUM_Y])
            gdp_raster_aux_filename = gdp_file_basename + "_aux.tif"
            gdp_raster_aux_filepath = os.path.join(output_path, gdp_raster_aux_filename)
            gdp_raster_aux_filepath = os.path.normpath(gdp_raster_aux_filepath)
            gdp_raster_filename = gdp_file_basename + ".tif"
            gdp_raster_filepath = os.path.join(output_path, gdp_raster_filename)
            gdp_raster_filepath = os.path.normpath(gdp_raster_filepath)
            gdp_raster_fp_aux_filename = gdp_file_basename + "_aux.geojson"
            gdp_raster_fp_aux_filepath = os.path.join(output_path, gdp_raster_fp_aux_filename)
            gdp_raster_fp_aux_filepath = os.path.normpath(gdp_raster_fp_aux_filepath)
            gdp_raster_fp_filename = gdp_file_basename + ".geojson"
            gdp_raster_fp_filepath = os.path.join(output_path, gdp_raster_fp_filename)
            gdp_raster_fp_filepath = os.path.normpath(gdp_raster_fp_filepath)
            if not os.path.exists(gdp_raster_filepath):
                files_to_remove = []
                # gdp_raster_qgis_filename = gdp_file_basename + "_qgis.tif"
                # gdp_raster_qgis_filepath = os.path.join(output_path, gdp_raster_qgis_filename)
                # gdp_raster_qgis_filepath = os.path.normpath(gdp_raster_qgis_filepath)
                # if os.path.exists(gdp_raster_qgis_filepath):
                #     os.remove(gdp_raster_qgis_filepath)
                # if os.path.exists(gdp_raster_qgis_filepath):
                #     str_error = Project.__name__ + "." + self.save_to_json.__name__
                #     str_error += ("\nError removing existing raster QGIS for geometric design project: {}".format(gdp_id))
                #     progress.close()
                #     return str_error
                # files_to_remove.append(gdp_raster_qgis_filepath)
                # ply
                gdp_ply_filename = gdp_file_basename + ".ply"
                gdp_ply_filepath = os.path.join(output_path, gdp_ply_filename)
                gdp_ply_filepath = os.path.normpath(gdp_ply_filepath)
                if os.path.exists(gdp_ply_filepath):
                    os.remove(gdp_ply_filepath)
                if os.path.exists(gdp_ply_filepath):
                    str_error = Project.__name__ + "." + self.save_to_json.__name__
                    str_error += ("\nError removing existing PLY for geometric design project: {}".format(gdp_id))
                    progress.close()
                    return str_error
                gdp_ply_content = gdp[defs_gdp.FIELD_TRIANGULATION_PLY]
                with open(gdp_ply_filepath, "w") as f_ply:
                    f_ply.write(gdp_ply_content)
                if not os.path.exists(gdp_ply_filepath):
                    str_error = Project.__name__ + "." + self.save_to_json.__name__
                    str_error += ("\nError making PLY for geometric design project: {}".format(gdp_id))
                    progress.close()
                    return str_error
                files_to_remove.append(gdp_ply_filepath)
                # py
                gdp_py_filename = gdp_file_basename + ".py"
                gdp_py_filepath = os.path.join(output_path, gdp_py_filename)
                gdp_py_filepath = os.path.normpath(gdp_py_filepath)
                if os.path.exists(gdp_py_filepath):
                    os.remove(gdp_py_filepath)
                if os.path.exists(gdp_py_filepath):
                    str_error = Project.__name__ + "." + self.save_to_json.__name__
                    str_error += ("\nError removing existing PY for geometric design project: {}".format(gdp_id))
                    progress.close()
                    return str_error
                files_to_remove.append(gdp_py_filepath)
                f_py = open(gdp_py_filepath, "w")
                f_py.write("import sys\n")
                f_py.write("from qgis.core import QgsApplication, QgsProcessingFeedback\n")
                f_py.write("from qgis.analysis import QgsNativeAlgorithms\n")
                # f_py.write("QgsApplication.setPrefixPath(r'C:/Program Files/QGIS 3.40.10', True)\n")
                f_py.write("QgsApplication.setPrefixPath(r'{}', True)\n".format(self.qgis_prefix_path))
                f_py.write("qgs = QgsApplication([], False)\n")
                f_py.write("qgs.initQgis()\n")
                f_py.write("sys.path.append(r'{}')\n".format(self.qgis_plugins_path))
                # f_py.write("sys.path.append(r'C:/Program Files/QGIS 3.40.10/apps/qgis-ltr/python/plugins')\n")
                f_py.write("from qgis import processing\n")
                f_py.write("from processing.core.Processing import Processing\n")
                f_py.write("Processing.initialize()\n")
                f_py.write("processing.run(\"native:meshrasterize\",{ \"DATASET_GROUPS\" : [0], ")
                f_py.write("\"DATASET_TIME\" : {\'type\': \'static\'}, \"EXTENT\" : ")
                f_py.write("\'{:.1f},{:.1f},".format(gdp_min_x, gdp_max_x))
                f_py.write("{:.1f},{:.1f}\', ".format(gdp_min_y, gdp_max_y))
                f_py.write("\"INPUT\" : \'PLY:\"")
                # gdp_ply_filepath_str = gdp_ply_filepath.replace("\\", "\\\\")
                f_py.write(gdp_ply_filepath.replace("\\", "\\\\"))
                f_py.write("\"\', ")
                f_py.write("\"OUTPUT\" : \"")
                # gdp_raster_aux_filepath = gdp_raster_aux_filepath.replace("\\", "\\\\")
                # gdp_raster_filepath = gdp_raster_filepath.replace("\\", "\\\\")
                f_py.write(gdp_raster_aux_filepath.replace("\\", "\\\\"))
                # f_py.write(gdp_raster_qgis_filepath_str)
                f_py.write("\", ")
                str_gsd = ("{:.3f}".format(gdp_gsd))
                f_py.write("\"PIXEL_SIZE\" : ")
                f_py.write(str_gsd)
                f_py.write(", \"CREATE_OPTIONS\" : \'COMPRESS=LZW\'")
                f_py.write(" })\n")
                f_py.close()
                # bat
                gdp_bat_filename = gdp_file_basename + ".bat"
                gdp_bat_filepath = os.path.join(output_path, gdp_bat_filename)
                gdp_bat_filepath = os.path.normpath(gdp_bat_filepath)
                if os.path.exists(gdp_bat_filepath):
                    os.remove(gdp_bat_filepath)
                if os.path.exists(gdp_bat_filepath):
                    str_error = Project.__name__ + "." + self.save_to_json.__name__
                    str_error += ("\nError removing existing BAT for geometric design project: {}".format(gdp_id))
                    progress.close()
                    return str_error
                files_to_remove.append(gdp_bat_filepath)
                f_bat = open(gdp_bat_filepath, "w")
                f_bat.write("@echo off\n")
                f_bat.write("set OSGEO4W_ROOT={}\n".format(self.qgis_prefix_path))
                # f_bat.write("set OSGEO4W_ROOT=C:/Program Files/QGIS 3.40.10\n")
                # windows
                f_bat.write("call \"{}\"\n".format(self.osge4w_bat_path))
                # f_bat.write("call \"%OSGEO4W_ROOT%\\bin\\o4w_env.bat\"\n")
                f_bat.write("set PROCESS_PATH={}\n".format(output_path))
                # f_bat.write("set PROCESS_PATH=D:/master_co2/tafalla/qVolumeTimeSeriesProjects/output\n")
                f_bat.write("set PYTHON_TOOL=\"{}\"\n".format(gdp_py_filepath))
                # f_bat.write("{}\"\n".format(gdp_py_filename))
                f_bat.write("set PYTHONPATH={};%PYTHONPATH%\n".format(self.qgis_python_path))
                # f_bat.write("set PYTHONPATH=%OSGEO4W_ROOT%\\apps\\qgis-ltr\\python;%PYTHONPATH%\n")
                f_bat.write("set PATH={};{};%PATH%\n".format(self.osge4w_bin_path, self.qgis_bin_path))
                # f_bat.write("set PATH=%OSGEO4W_ROOT%\\bin;%OSGEO4W_ROOT%\\apps\qgis-ltr\\bin;%PATH%\n")
                f_bat.write("echo \"start\"\n")
                f_bat.write("python %PYTHON_TOOL%\n")
                crs_str = gdp_crs
                f_bat.write("gdal_edit -a_nodata -9999 -a_srs \"{}\" \"".format(crs_str))
                f_bat.write(gdp_raster_aux_filepath)
                f_bat.write("\"\n")
                f_bat.write("gdal_translate -ot Float32 -co \"COMPRESS=LZW\" \"")
                f_bat.write(gdp_raster_aux_filepath)
                f_bat.write("\" \"")
                f_bat.write(gdp_raster_filepath)
                f_bat.write("\"\n")
                f_bat.write("del \"")
                f_bat.write(gdp_raster_aux_filepath)
                # f_bat.write(gdp_raster_aux_filepath.replace("\\\\","\\"))
                f_bat.write("\" /Q\n")
                # gdal raster contour --overwrite --levels MIN,MAX --polygonize gdp_1_20250507_DSM_vol.tif gdp_1_20250507_DSM_vol.geojson
                f_bat.write("gdal raster contour --levels MIN,MAX --polygonize")
                f_bat.write(" \"{}\" \"{}\"".format(gdp_raster_filepath, gdp_raster_fp_aux_filepath))
                f_bat.write("\n")
                # f_bat.write("gdal vector dissolve")
                # f_bat.write(" \"{}\" \"{}\"".format(gdp_raster_fp_aux_filepath, gdp_raster_fp_filepath))
                # f_bat.write("\n")
                f_bat.write("ogr2ogr")
                f_bat.write(" \"{}\" \"{}\"".format(gdp_raster_fp_filepath, gdp_raster_fp_aux_filepath)) # first output
                f_bat.write(" -simplify {:.3f} -dialect sqlite -sql \"SELECT ST_Union(geometry) FROM contour\"\n".format(gdp_gsd))
                f_bat.write("del \"")
                f_bat.write(gdp_raster_fp_aux_filepath)
                # f_bat.write(gdp_raster_fp_aux_filepath.replace("\\\\","\\"))
                f_bat.write("\" /Q\n")
                # f_bat.write("gdal raster footprint --split-multipolygons")
                # f_bat.write(" --simplify-tolerance {:.3f}".format(gdp_gsd))
                # f_bat.write(" \"{}\" \"{}\"".format(gdp_raster_filepath, gdp_raster_fp_filepath))
                # f_bat.write("\n")

                # str_gdal_translate = ("gdal_translate -a_srs \"{}\" ".format(crs_str))
                # str_gdal_translate += ("-ot uint32 -a_nodata 4294967295 -co compress=lzw ")
                # str_gdal_translate += ("-scale 0 10000 0 1000000 -a_scale 0.01 ")
                # str_gdal_translate += ("\"")
                # str_gdal_translate += gdp_raster_qgis_filepath
                # str_gdal_translate += ("\" \"")
                # str_gdal_translate += gdp_raster_filepath
                # str_gdal_translate += ("\"")
                # f_bat.write("{}\n".format(str_gdal_translate))
                # f_bat.write("del /q \"{}\"\n".format(gdp_raster_qgis_filepath))
                f_bat.write("echo \"end\"\n")
                f_bat.close()
                command = gdp_bat_filepath
                result = subprocess.run([command], capture_output=True, text=True)
                # os.system(command)
                # if not os.path.exists(gdp_raster_qgis_filepath):
                if not os.path.exists(gdp_raster_filepath):
                    str_error = Project.__name__ + "." + self.save_to_json.__name__
                    str_error += ("\nSomething fails executing:\n{}".format(command))
                    progress.close()
                    return str_error
                for file_to_remove in files_to_remove:
                    if os.path.exists(file_to_remove):
                        os.remove(file_to_remove)
                    if os.path.exists(file_to_remove):
                        str_error = Project.__name__ + "." + self.save_to_json.__name__
                        str_error += (
                            "\nError removing file: {}".format(file_to_remove))
                        progress.close()
                        return str_error
                QApplication.processEvents()
            progress.close()
            gdp_raster_filepath_by_id[gdp_id] = gdp_raster_filepath
            gdp_raster_fp_filepath_by_id[gdp_id] = gdp_raster_fp_filepath
            str_error, features = GDALTools.get_features(gdp_raster_fp_filepath,
                                                         defs_vc.GEOJSON_FP_LAYER_NAME,
                                                         geojson_fp_fields,
                                                         geojson_fp_filter_fields)
            if len(features) != 1:
                str_error = Project.__name__ + "." + self.save_to_json.__name__
                str_error += (
                    "\nThere are no one feature in footprint file:\n{}".format(gdp_raster_fp_filepath))
                progress.close()
                return str_error
            if not defs_vc.GEOJSON_FP_FIELD_FEATURES_GEOMETRY in features[0]:
                str_error = Project.__name__ + "." + self.save_to_json.__name__
                str_error += (
                    "\nThere are no geometry in feature in footprint file:\n{}".format(gdp_raster_fp_filepath))
                progress.close()
                return str_error
            try:
                ogr_geometry = ogr.CreateGeometryFromWkb(features[0][defs_vc.GEOJSON_FP_FIELD_FEATURES_GEOMETRY])
            except Exception as e:
                str_error = Project.__name__ + "." + self.save_to_json.__name__
                str_error += (
                    "\nCreatring geometry in feature in footprint file:\n{}".format(gdp_raster_fp_filepath))
                str_error += '\nGDAL Error: ' + e.args[0]
                progress.close()
                return str_error
            gdp_raster_fp_geometry_by_id[gdp_id] = ogr_geometry
        # compute optimized raster DSM files
        dsm_commands = []
        dsm_commands_output_filepaths = []
        dsm_filepath_by_gdp_id_by_id = {}
        dsm_fp_filepath_by_gdp_id_by_id = {}
        dsm_fp_geometry_by_gdp_id_by_id = {}
        dsms_id_by_gdp_id_by_date = {}
        if computeForDsm:
            for gdp_id in self.geometric_design_projects:
                gdp = self.geometric_design_projects[gdp_id]
                gdp_enabled = gdp[defs_gdp.FIELD_ENABLED]
                if gdp_enabled == 0:
                    continue
                gdp_file_basename = "gdp_" + gdp_id
                gdp_crs = gdp[defs_gdp.FIELD_CRS]
                gdp_gsd = np.round(gdp[defs_gdp.FIELD_GSD_VOLUMES_COMPUTATION] * 100.) / 100.  # cm accuracy
                gdp_min_x = np.floor(gdp[defs_gdp.FIELD_MINIMUM_X])
                gdp_max_x = np.ceil(gdp[defs_gdp.FIELD_MAXIMUM_X])
                gdp_min_y = np.floor(gdp[defs_gdp.FIELD_MINIMUM_Y])
                gdp_max_y = np.ceil(gdp[defs_gdp.FIELD_MAXIMUM_Y])
                for phgmp_id in self.photogrammetry_projects:
                    phgmp = self.photogrammetry_projects[phgmp_id]
                    phgmp_enabled = phgmp[defs_ph_prjs_dlg.FIELD_ENABLED]
                    if phgmp_enabled == 0:
                        continue
                    phgmp_dsm_filepath = phgmp[defs_ph_prjs_dlg.FIELD_DSM]
                    if not phgmp_dsm_filepath:
                        continue
                    if not os.path.exists(phgmp_dsm_filepath):
                        continue
                    dsm_gdp_phgmp_filename = (gdp_file_basename + '_' + phgmp_id + '_'
                                              + defs_ph_prjs_dlg.FIELD_DSM + ".tif")
                    dsm_gdp_phgmp_file_path = os.path.join(output_path, dsm_gdp_phgmp_filename)
                    dsm_gdp_phgmp_file_path = os.path.normpath(dsm_gdp_phgmp_file_path)
                    dsm_fp_gdp_phgmp_aux_filename = (gdp_file_basename + '_' + phgmp_id + '_'
                                              + defs_ph_prjs_dlg.FIELD_DSM + "_aux.geojson")
                    dsm_fp_gdp_phgmp_aux_file_path = os.path.join(output_path, dsm_fp_gdp_phgmp_aux_filename)
                    dsm_fp_gdp_phgmp_aux_file_path = os.path.normpath(dsm_fp_gdp_phgmp_aux_file_path)
                    dsm_fp_gdp_phgmp_filename = (gdp_file_basename + '_' + phgmp_id + '_'
                                              + defs_ph_prjs_dlg.FIELD_DSM + ".geojson")
                    dsm_fp_gdp_phgmp_file_path = os.path.join(output_path, dsm_fp_gdp_phgmp_filename)
                    dsm_fp_gdp_phgmp_file_path = os.path.normpath(dsm_fp_gdp_phgmp_file_path)
                    phgmp_dsm_date = phgmp[defs_ph_prjs_dlg.FIELD_DATE]
                    if not gdp_id in dsms_id_by_gdp_id_by_date:
                        dsms_id_by_gdp_id_by_date[gdp_id] = {}
                    if not phgmp_dsm_date in dsms_id_by_gdp_id_by_date[gdp_id]:
                        dsms_id_by_gdp_id_by_date[gdp_id][phgmp_dsm_date] = []
                    dsms_id_by_gdp_id_by_date[gdp_id][phgmp_dsm_date].append(phgmp_id)
                    if not gdp_id in dsm_filepath_by_gdp_id_by_id:
                        dsm_filepath_by_gdp_id_by_id[gdp_id] = {}
                    dsm_filepath_by_gdp_id_by_id[gdp_id][phgmp_id] = dsm_gdp_phgmp_file_path
                    if not gdp_id in dsm_fp_filepath_by_gdp_id_by_id:
                        dsm_fp_filepath_by_gdp_id_by_id[gdp_id] = {}
                    dsm_fp_filepath_by_gdp_id_by_id[gdp_id][phgmp_id] = dsm_fp_gdp_phgmp_file_path
                    if not os.path.exists(dsm_gdp_phgmp_file_path) or not os.path.exists(dsm_fp_gdp_phgmp_file_path):
                        if not os.path.exists(dsm_gdp_phgmp_file_path):
                        # if os.path.exists(dsm_gdp_phgmp_file_path):
                        #     os.remove(dsm_gdp_phgmp_file_path)
                            if os.path.exists(dsm_fp_gdp_phgmp_file_path):
                                os.remove(dsm_fp_gdp_phgmp_file_path)
                            phgmp_dsm_crs = phgmp[defs_ph_prjs_dlg.FIELD_DSM_CRS]
                            dsm_command = ("gdalwarp -ot Float32 -te {:.1f} {:.1f}".format(gdp_min_x, gdp_min_y))
                            dsm_command += (" {:.1f} {:.1f}".format(gdp_max_x, gdp_max_y))
                            dsm_command += (" -tr {:.3f} {:.3f}".format(gdp_gsd, gdp_gsd))
                            dsm_command += (" -s_srs {}".format(gdp_crs))
                            dsm_command += (" -t_srs {}".format(phgmp_dsm_crs))
                            dsm_command += (" -dstnodata -9999 -co \"COMPRESS=LZW\"")
                            dsm_command += (" \"{}\" \"{}\"".format(phgmp_dsm_filepath, dsm_gdp_phgmp_file_path))
                            dsm_commands.append(dsm_command)
                            dsm_commands_output_filepaths.append(dsm_gdp_phgmp_file_path)
                        if not os.path.exists(dsm_fp_gdp_phgmp_file_path):
                            dsm_fp_1_command = ("gdal raster contour --levels MIN,MAX --polygonize ");
                            dsm_fp_1_command += (" \"{}\" \"{}\"".format(dsm_gdp_phgmp_file_path,
                                                                         dsm_fp_gdp_phgmp_aux_file_path))
                            dsm_commands.append(dsm_fp_1_command)
                            dsm_commands_output_filepaths.append(dsm_fp_gdp_phgmp_aux_file_path)
                            dsm_fp_2_command = ("ogr2ogr  \"{}\" \"{}\"".format(dsm_fp_gdp_phgmp_file_path,
                                                                         dsm_fp_gdp_phgmp_aux_file_path))
                            dsm_fp_2_command += (" -simplify {:.3f} -dialect sqlite -sql \"SELECT ST_Union(geometry) FROM contour\"".format(gdp_gsd))
                            dsm_commands.append(dsm_fp_2_command)
                            dsm_commands_output_filepaths.append(dsm_fp_gdp_phgmp_file_path)
                            dsm_fp_3_command = ("del \"{}\" /Q".format(dsm_fp_gdp_phgmp_aux_file_path))
                            dsm_commands.append(dsm_fp_3_command)
                            dsm_commands_output_filepaths.append(dsm_fp_gdp_phgmp_file_path) # for equal indexes
                            # dsm_fp_command = ("gdal raster footprint --split-multipolygons")
                            # dsm_fp_command += (" --simplify-tolerance {:.3f}".format(gdp_gsd))
                            # dsm_fp_command += (" \"{}\" \"{}\"".format(dsm_gdp_phgmp_file_path, dsm_fp_gdp_phgmp_file_path))
                            # dsm_commands.append(dsm_fp_command)
                            # dsm_commands_output_filepaths.append(dsm_fp_gdp_phgmp_file_path)
            if len(dsm_commands) > 0:
                steps = len(dsm_commands)
                progress = QProgressDialog("Computing optimized DSM files...", "Cancel", 0, steps)
                # progress = QProgressDialog("Computing raster for geometric design projects...", "Cancel", 0, steps)
                progress.setWindowModality(Qt.WindowModal)  # Bloquea la ventana principal
                progress.setWindowTitle("Wait for finished")
                progress.show()
                i = 0
                for dsm_command in dsm_commands:
                    output_filepath = dsm_commands_output_filepaths[i]
                    i = i + 1
                    progress.setValue(i)
                    if progress.wasCanceled():
                        break
                    QApplication.processEvents()
                    gdp_bat_filename = "Optimize_DSM.bat"
                    gdp_bat_filepath = os.path.join(output_path, gdp_bat_filename)
                    gdp_bat_filepath = os.path.normpath(gdp_bat_filepath)
                    if os.path.exists(gdp_bat_filepath):
                        os.remove(gdp_bat_filepath)
                    if os.path.exists(gdp_bat_filepath):
                        str_error = Project.__name__ + "." + self.save_to_json.__name__
                        str_error += ("\nError removing existing BAT file:\n{}".format(gdp_bat_filepath))
                        progress.close()
                        return str_error
                    # files_to_remove.append(gdp_bat_filepath)
                    f_bat = open(gdp_bat_filepath, "w")
                    f_bat.write("@echo off\n")
                    f_bat.write("set OSGEO4W_ROOT={}\n".format(self.qgis_prefix_path))
                    # f_bat.write("set OSGEO4W_ROOT=C:/Program Files/QGIS 3.40.10\n")
                    # windows
                    f_bat.write("call \"{}\"\n".format(self.osge4w_bat_path))
                    # f_bat.write("call \"%OSGEO4W_ROOT%\\bin\\o4w_env.bat\"\n")
                    f_bat.write("set PROCESS_PATH={}\n".format(output_path))
                    # f_bat.write("set PROCESS_PATH=D:/master_co2/tafalla/qVolumeTimeSeriesProjects/output\n")
                    f_bat.write("set PATH={};{};%PATH%\n".format(self.osge4w_bin_path, self.qgis_bin_path))
                    # f_bat.write("set PATH=%OSGEO4W_ROOT%\\bin;%OSGEO4W_ROOT%\\apps\qgis-ltr\\bin;%PATH%\n")
                    f_bat.write("echo \"start\"\n")
                    f_bat.write(dsm_command)
                    f_bat.write("\n")
                    f_bat.write("echo \"end\"\n")
                    f_bat.close()
                    command = gdp_bat_filepath
                    result = subprocess.run([command], capture_output=True, text=True)
                    # os.system(command)
                    # if not os.path.exists(gdp_raster_qgis_filepath):
                    if not os.path.exists(output_filepath):
                        msg_error = Project.__name__ + "." + self.save_to_json.__name__
                        msg_error += ("\nSomething fails computing optimized DSM:\n{}".format(output_filepath))
                        error_msgs.append(msg_error)
                    if os.path.exists(gdp_bat_filepath):
                        os.remove(gdp_bat_filepath)
                progress.close()
                QApplication.processEvents()
        dsm_fp_geometry_by_gdp_id_by_id = {}
        for gdp_id in dsm_fp_filepath_by_gdp_id_by_id:
            for dsm_id in dsm_fp_filepath_by_gdp_id_by_id[gdp_id]:
                dsm_fp_file_path = dsm_fp_filepath_by_gdp_id_by_id[gdp_id][dsm_id]
                str_error, features = GDALTools.get_features(dsm_fp_file_path,
                                                             defs_vc.GEOJSON_FP_LAYER_NAME,
                                                             geojson_fp_fields,
                                                             geojson_fp_filter_fields)
                if len(features) != 1:
                    str_error = Project.__name__ + "." + self.save_to_json.__name__
                    str_error += (
                        "\nThere are no one feature in footprint file:\n{}".format(dsm_fp_file_path))
                    progress.close()
                    return str_error
                if not defs_vc.GEOJSON_FP_FIELD_FEATURES_GEOMETRY in features[0]:
                    str_error = Project.__name__ + "." + self.save_to_json.__name__
                    str_error += (
                        "\nThere are no geometry in feature in footprint file:\n{}".format(dsm_fp_file_path))
                    progress.close()
                    return str_error
                try:
                    ogr_geometry = ogr.CreateGeometryFromWkb(features[0][defs_vc.GEOJSON_FP_FIELD_FEATURES_GEOMETRY])
                except Exception as e:
                    str_error = Project.__name__ + "." + self.save_to_json.__name__
                    str_error += (
                        "\nCreatring geometry in feature in footprint file:\n{}".format(dsm_fp_file_path))
                    str_error += '\nGDAL Error: ' + e.args[0]
                    progress.close()
                    return str_error
                if not gdp_id in dsm_fp_geometry_by_gdp_id_by_id:
                    dsm_fp_geometry_by_gdp_id_by_id[gdp_id] = {}
                dsm_fp_geometry_by_gdp_id_by_id[gdp_id][dsm_id] = ogr_geometry
        # compute optimized raster DTM files
        dtm_commands = []
        dtm_commands_output_filepaths = []
        dtm_filepath_by_gdp_id_by_id = {}
        dtm_fp_filepath_by_gdp_id_by_id = {}
        dtms_id_by_gdp_id_by_date = {}
        if computeForDtm:
            for gdp_id in self.geometric_design_projects:
                gdp = self.geometric_design_projects[gdp_id]
                gdp_enabled = gdp[defs_gdp.FIELD_ENABLED]
                if gdp_enabled == 0:
                    continue
                gdp_file_basename = "gdp_" + gdp_id
                gdp_crs = gdp[defs_gdp.FIELD_CRS]
                gdp_gsd = np.round(gdp[defs_gdp.FIELD_GSD_VOLUMES_COMPUTATION] * 100.) / 100.  # cm accuracy
                gdp_min_x = np.floor(gdp[defs_gdp.FIELD_MINIMUM_X])
                gdp_max_x = np.ceil(gdp[defs_gdp.FIELD_MAXIMUM_X])
                gdp_min_y = np.floor(gdp[defs_gdp.FIELD_MINIMUM_Y])
                gdp_max_y = np.ceil(gdp[defs_gdp.FIELD_MAXIMUM_Y])
                for phgmp_id in self.photogrammetry_projects:
                    phgmp = self.photogrammetry_projects[phgmp_id]
                    phgmp_enabled = phgmp[defs_ph_prjs_dlg.FIELD_ENABLED]
                    if phgmp_enabled == 0:
                        continue
                    phgmp_dtm_filepath = phgmp[defs_ph_prjs_dlg.FIELD_DTM]
                    if not phgmp_dtm_filepath:
                        continue
                    if not os.path.exists(phgmp_dtm_filepath):
                        continue
                    dtm_gdp_phgmp_filename = (gdp_file_basename + '_' + phgmp_id + '_'
                                              + defs_ph_prjs_dlg.FIELD_DTM + ".tif")
                    dtm_gdp_phgmp_file_path = os.path.join(output_path, dtm_gdp_phgmp_filename)
                    dtm_gdp_phgmp_file_path = os.path.normpath(dtm_gdp_phgmp_file_path)
                    dtm_fp_gdp_phgmp_aux_filename = (gdp_file_basename + '_' + phgmp_id + '_'
                                              + defs_ph_prjs_dlg.FIELD_DTM + "_aux.geojson")
                    dtm_fp_gdp_phgmp_aux_file_path = os.path.join(output_path, dtm_fp_gdp_phgmp_aux_filename)
                    dtm_fp_gdp_phgmp_aux_file_path = os.path.normpath(dtm_fp_gdp_phgmp_aux_file_path)
                    dtm_fp_gdp_phgmp_filename = (gdp_file_basename + '_' + phgmp_id + '_'
                                              + defs_ph_prjs_dlg.FIELD_DTM + ".geojson")
                    dtm_fp_gdp_phgmp_file_path = os.path.join(output_path, dtm_fp_gdp_phgmp_filename)
                    dtm_fp_gdp_phgmp_file_path = os.path.normpath(dtm_fp_gdp_phgmp_file_path)
                    phgmp_dtm_date = phgmp[defs_ph_prjs_dlg.FIELD_DATE]
                    if not gdp_id in dtms_id_by_gdp_id_by_date:
                        dtms_id_by_gdp_id_by_date[gdp_id] = {}
                    if not phgmp_dtm_date in dtms_id_by_gdp_id_by_date[gdp_id]:
                        dtms_id_by_gdp_id_by_date[gdp_id][phgmp_dtm_date] = []
                    dtms_id_by_gdp_id_by_date[gdp_id][phgmp_dtm_date].append(phgmp_id)
                    if not gdp_id in dtm_filepath_by_gdp_id_by_id:
                        dtm_filepath_by_gdp_id_by_id[gdp_id] = {}
                    dtm_filepath_by_gdp_id_by_id[gdp_id][phgmp_id] = dtm_gdp_phgmp_file_path
                    if not gdp_id in dtm_fp_filepath_by_gdp_id_by_id:
                        dtm_fp_filepath_by_gdp_id_by_id[gdp_id] = {}
                    dtm_fp_filepath_by_gdp_id_by_id[gdp_id][phgmp_id] = dtm_fp_gdp_phgmp_file_path
                    if not os.path.exists(dtm_gdp_phgmp_file_path) or not os.path.exists(dtm_fp_gdp_phgmp_file_path):
                        # if os.path.exists(dtm_gdp_phgmp_file_path):
                        #     os.remove(dtm_gdp_phgmp_file_path)
                        # if os.path.exists(dtm_fp_gdp_phgmp_file_path):
                        #     os.remove(dtm_fp_gdp_phgmp_file_path)
                        if not os.path.exists(dtm_gdp_phgmp_file_path):
                            if os.path.exists(dtm_fp_gdp_phgmp_file_path):
                                os.remove(dtm_fp_gdp_phgmp_file_path)
                            phgmp_dtm_crs = phgmp[defs_ph_prjs_dlg.FIELD_DTM_CRS]
                            dtm_command = ("gdalwarp -ot Float32 -te {:.1f} {:.1f}".format(gdp_min_x, gdp_min_y))
                            dtm_command += (" {:.1f} {:.1f}".format(gdp_max_x, gdp_max_y))
                            dtm_command += (" -tr {:.3f} {:.3f}".format(gdp_gsd, gdp_gsd))
                            dtm_command += (" -s_srs {}".format(gdp_crs))
                            dtm_command += (" -t_srs {}".format(phgmp_dtm_crs))
                            dtm_command += (" -dstnodata -9999 -co \"COMPRESS=LZW\"")
                            dtm_command += (" \"{}\" \"{}\"".format(phgmp_dtm_filepath, dtm_gdp_phgmp_file_path))
                            dtm_commands.append(dtm_command)
                            dtm_commands_output_filepaths.append(dtm_gdp_phgmp_file_path)
                        if not os.path.exists(dtm_fp_gdp_phgmp_file_path):
                            dtm_fp_1_command = ("gdal raster contour --levels MIN,MAX --polygonize ");
                            dtm_fp_1_command += (" \"{}\" \"{}\"".format(dtm_gdp_phgmp_file_path,
                                                                         dtm_fp_gdp_phgmp_aux_file_path))
                            dtm_commands.append(dtm_fp_1_command)
                            dtm_commands_output_filepaths.append(dtm_fp_gdp_phgmp_aux_file_path)
                            dtm_fp_2_command = ("ogr2ogr  \"{}\" \"{}\"".format(dtm_fp_gdp_phgmp_file_path,
                                                                         dtm_fp_gdp_phgmp_aux_file_path))
                            dtm_fp_2_command += (" -simplify {:.3f} -dialect sqlite -sql \"SELECT ST_Union(geometry) FROM contour\"".format(gdp_gsd))
                            dtm_commands.append(dtm_fp_2_command)
                            dtm_commands_output_filepaths.append(dtm_fp_gdp_phgmp_file_path)
                            dtm_fp_3_command = ("del \"{}\" /Q".format(dtm_fp_gdp_phgmp_aux_file_path))
                            dtm_commands.append(dtm_fp_3_command)
                            dtm_commands_output_filepaths.append(dtm_fp_gdp_phgmp_file_path) # for equal indexes
                            # dtm_fp_command = ("gdal raster footprint --split-multipolygons")
                            # dtm_fp_command += (" --simplify-tolerance {:.3f}".format(gdp_gsd))
                            # dtm_fp_command += (" \"{}\" \"{}\"".format(dtm_gdp_phgmp_file_path, dtm_fp_gdp_phgmp_file_path))
                            # dtm_commands.append(dtm_fp_command)
                            # dtm_commands_output_filepaths.append(dtm_fp_gdp_phgmp_file_path)
            if len(dtm_commands) > 0:
                steps = len(dtm_commands)
                progress = QProgressDialog("Computing optimized DTM files...", "Cancel", 0, steps)
                # progress = QProgressDialog("Computing raster for geometric design projects...", "Cancel", 0, steps)
                progress.setWindowModality(Qt.WindowModal)  # Bloquea la ventana principal
                progress.setWindowTitle("Wait for finished")
                progress.show()
                i = 0
                for dtm_command in dtm_commands:
                    output_filepath = dtm_commands_output_filepaths[i]
                    i = i + 1
                    progress.setValue(i)
                    if progress.wasCanceled():
                        break
                    QApplication.processEvents()
                    gdp_bat_filename = "Optimize_DTM.bat"
                    gdp_bat_filepath = os.path.join(output_path, gdp_bat_filename)
                    gdp_bat_filepath = os.path.normpath(gdp_bat_filepath)
                    if os.path.exists(gdp_bat_filepath):
                        os.remove(gdp_bat_filepath)
                    if os.path.exists(gdp_bat_filepath):
                        str_error = Project.__name__ + "." + self.save_to_json.__name__
                        str_error += ("\nError removing existing BAT file:\n{}".format(gdp_bat_filepath))
                        progress.close()
                        return str_error
                    # files_to_remove.append(gdp_bat_filepath)
                    f_bat = open(gdp_bat_filepath, "w")
                    f_bat.write("@echo off\n")
                    f_bat.write("set OSGEO4W_ROOT={}\n".format(self.qgis_prefix_path))
                    # f_bat.write("set OSGEO4W_ROOT=C:/Program Files/QGIS 3.40.10\n")
                    # windows
                    f_bat.write("call \"{}\"\n".format(self.osge4w_bat_path))
                    # f_bat.write("call \"%OSGEO4W_ROOT%\\bin\\o4w_env.bat\"\n")
                    f_bat.write("set PROCESS_PATH={}\n".format(output_path))
                    # f_bat.write("set PROCESS_PATH=D:/master_co2/tafalla/qVolumeTimeSeriesProjects/output\n")
                    f_bat.write("set PATH={};{};%PATH%\n".format(self.osge4w_bin_path, self.qgis_bin_path))
                    # f_bat.write("set PATH=%OSGEO4W_ROOT%\\bin;%OSGEO4W_ROOT%\\apps\qgis-ltr\\bin;%PATH%\n")
                    f_bat.write("echo \"start\"\n")
                    f_bat.write(dtm_command)
                    f_bat.write("\n")
                    f_bat.write("echo \"end\"\n")
                    f_bat.close()
                    command = gdp_bat_filepath
                    result = subprocess.run([command], capture_output=True, text=True)
                    # os.system(command)
                    # if not os.path.exists(gdp_raster_qgis_filepath):
                    if not os.path.exists(output_filepath):
                        msg_error = Project.__name__ + "." + self.save_to_json.__name__
                        msg_error += ("\nSomething fails computing optimized DTM:\n{}".format(output_filepath))
                        error_msgs.append(msg_error)
                    if os.path.exists(gdp_bat_filepath):
                        os.remove(gdp_bat_filepath)
                progress.close()
                QApplication.processEvents()
        dtm_fp_geometry_by_gdp_id_by_id = {}
        for gdp_id in dtm_fp_filepath_by_gdp_id_by_id:
            for dtm_id in dtm_fp_filepath_by_gdp_id_by_id[gdp_id]:
                dtm_fp_file_path = dtm_fp_filepath_by_gdp_id_by_id[gdp_id][dtm_id]
                str_error, features = GDALTools.get_features(dtm_fp_file_path,
                                                             defs_vc.GEOJSON_FP_LAYER_NAME,
                                                             geojson_fp_fields,
                                                             geojson_fp_filter_fields)
                if len(features) != 1:
                    str_error = Project.__name__ + "." + self.save_to_json.__name__
                    str_error += (
                        "\nThere are no one feature in footprint file:\n{}".format(dtm_fp_file_path))
                    progress.close()
                    return str_error
                if not defs_vc.GEOJSON_FP_FIELD_FEATURES_GEOMETRY in features[0]:
                    str_error = Project.__name__ + "." + self.save_to_json.__name__
                    str_error += (
                        "\nThere are no geometry in feature in footprint file:\n{}".format(dtm_fp_file_path))
                    progress.close()
                    return str_error
                try:
                    ogr_geometry = ogr.CreateGeometryFromWkb(features[0][defs_vc.GEOJSON_FP_FIELD_FEATURES_GEOMETRY])
                except Exception as e:
                    str_error = Project.__name__ + "." + self.save_to_json.__name__
                    str_error += (
                        "\nCreatring geometry in feature in footprint file:\n{}".format(dtm_fp_file_path))
                    str_error += '\nGDAL Error: ' + e.args[0]
                    progress.close()
                    return str_error
                if not gdp_id in dtm_fp_geometry_by_gdp_id_by_id:
                    dtm_fp_geometry_by_gdp_id_by_id[gdp_id] = {}
                dtm_fp_geometry_by_gdp_id_by_id[gdp_id][dtm_id] = ogr_geometry

        volumes_computations = {}
        volumes_computations_commands = []
        # compute dsm volumes
        if computeForDsm:
            for gdp_id in gdp_raster_filepath_by_id:
                gdp = self.geometric_design_projects[gdp_id]
                gdp_enabled = gdp[defs_gdp.FIELD_ENABLED]
                if gdp_enabled == 0:
                    continue
                gdp_crs = gdp[defs_gdp.FIELD_CRS]
                gdp_gsd = np.round(gdp[defs_gdp.FIELD_GSD_VOLUMES_COMPUTATION] * 100.) / 100.  # cm accuracy
                gdp_min_x = np.floor(gdp[defs_gdp.FIELD_MINIMUM_X])
                gdp_max_x = np.ceil(gdp[defs_gdp.FIELD_MAXIMUM_X])
                gdp_min_y = np.floor(gdp[defs_gdp.FIELD_MINIMUM_Y])
                gdp_max_y = np.ceil(gdp[defs_gdp.FIELD_MAXIMUM_Y])
                gdp_raster_file_path = gdp_raster_filepath_by_id[gdp_id]
                if not os.path.exists(gdp_raster_file_path): # never
                    continue
                gdp_raster_fp_file_path = gdp_raster_fp_filepath_by_id[gdp_id]
                if not os.path.exists(gdp_raster_fp_file_path): # never
                    continue
                if not gdp_id in gdp_raster_fp_geometry_by_id: # never
                    continue
                gdp_raster_fp_geometry = gdp_raster_fp_geometry_by_id[gdp_id]
                if not gdp_id in dsm_filepath_by_gdp_id_by_id or not gdp_id in dsm_fp_filepath_by_gdp_id_by_id:
                    continue
                for phgmp_id in dsm_fp_filepath_by_gdp_id_by_id[gdp_id]:
                    dsm_id = phgmp_id
                    dsm_file_path = dsm_filepath_by_gdp_id_by_id[gdp_id][dsm_id]
                    if not os.path.exists(dsm_file_path):
                        continue
                    dsm_fp_file_path = dsm_fp_filepath_by_gdp_id_by_id[gdp_id][dsm_id]
                    if not os.path.exists(dsm_fp_file_path):
                        continue
                    if not gdp_id in dsm_fp_geometry_by_gdp_id_by_id:  # never
                        continue
                    if not dsm_id in dsm_fp_geometry_by_gdp_id_by_id[gdp_id]:
                        continue
                    dsm_fp_geometry = dsm_fp_geometry_by_gdp_id_by_id[gdp_id][dsm_id]
                    # check exists overlaps
                    if (not gdp_raster_fp_geometry.Intersects(dsm_fp_geometry)
                            and not gdp_raster_fp_geometry.Within(dsm_fp_geometry)
                            and not gdp_raster_fp_geometry.Within(dsm_fp_geometry)):
                        continue
                    str_date = self.photogrammetry_projects[dsm_id][defs_ph_prjs_dlg.FIELD_DATE]
                    str_date_formated = str_date.replace(':','')
                    dsm_vol_filename = ("gdp_" + gdp_id + '_' #+ str_date_formated + '_'
                                        + dsm_id + '_'
                                        + defs_ph_prjs_dlg.FIELD_DSM + '_'
                                        + defs_vc.VOLUME_RASTER_FILE_SUFIX
                                        + ".tif")
                    dsm_vol_file_path = os.path.join(output_path, dsm_vol_filename)
                    dsm_vol_file_path = os.path.normpath(dsm_vol_file_path)
                    dsm_vol_fp_aux_filename = ("gdp_" + gdp_id + '_' #+ str_date_formated + '_'
                                               + dsm_id + '_'
                                               + defs_ph_prjs_dlg.FIELD_DSM + '_'
                                               + defs_vc.VOLUME_RASTER_FILE_SUFIX
                                               + "_aux.geojson")
                    dsm_vol_fp_aux_file_path = os.path.join(output_path, dsm_vol_fp_aux_filename)
                    dsm_vol_fp_aux_file_path = os.path.normpath(dsm_vol_fp_aux_file_path)
                    dsm_vol_fp_filename = ("gdp_" + gdp_id + '_' #+ str_date_formated + '_'
                                           + dsm_id + '_'
                                           + defs_ph_prjs_dlg.FIELD_DSM + '_'
                                           + defs_vc.VOLUME_RASTER_FILE_SUFIX
                                           + ".geojson")
                    dsm_vol_fp_file_path = os.path.join(output_path, dsm_vol_fp_filename)
                    dsm_vol_fp_file_path = os.path.normpath(dsm_vol_fp_file_path)
                    if not os.path.exists(dsm_vol_file_path):
                        if os.path.exists(dsm_vol_fp_file_path):
                            os.remove(dsm_vol_fp_file_path)
                        command_calc = ("gdal_calc -A \"{}\"".format(gdp_raster_file_path))
                        command_calc += (" -B \"{}\"".format(dsm_file_path))
                        command_calc += (" --outfile=\"{}\"".format(dsm_vol_file_path))
                        command_calc += (" --calc=\"A-B\" --NoDataValue -9999 --type=Float32 --co \"COMPRESS=LZW\"")
                        volumes_computations_commands.append(command_calc)
                    if not os.path.exists(dsm_vol_fp_file_path):
                        commmand_fp_1_command = ("gdal raster contour --levels MIN,MAX --polygonize ");
                        commmand_fp_1_command += (" \"{}\" \"{}\"".format(dsm_vol_file_path,
                                                                          dsm_vol_fp_aux_file_path))
                        volumes_computations_commands.append(commmand_fp_1_command)
                        commmand_fp_2_command = ("ogr2ogr  \"{}\" \"{}\"".format(dsm_vol_fp_file_path,
                                                                                 dsm_vol_fp_aux_file_path))
                        commmand_fp_2_command += (
                            " -simplify {:.3f} -dialect sqlite -sql \"SELECT ST_Union(geometry) FROM contour\"".format(
                                gdp_gsd))
                        volumes_computations_commands.append(commmand_fp_2_command)
                        command_fp_3_command = ("del \"{}\" /Q".format(dsm_vol_fp_aux_file_path))
                        volumes_computations_commands.append(command_fp_3_command)
                    vc_id = "gdp_" + gdp_id
                    vc_id += "_" + str_date_formated
                    vc_id += "_" + defs_ph_prjs_dlg.FIELD_DSM
                    volume_computation = {}
                    volume_computation[defs_vc.FIELD_ID] = vc_id
                    volume_computation[defs_vc.FIELD_ENABLED] = 1
                    volume_computation[defs_vc.FIELD_VOLUME_DATE_FROM] = str_date
                    volume_computation[defs_vc.FIELD_VOLUME_DATE_TO] = str_date
                    volume_computation[defs_vc.FIELD_VOLUME_TYPE] = defs_vc.VOLUME_TYPE_GD_DSM_DIFFERENCE
                    volume_computation[defs_vc.FIELD_CRS] = gdp_crs
                    volume_computation[defs_vc.FIELD_RASTER_FILE_RESULT] = dsm_vol_file_path
                    volume_computation[defs_vc.FIELD_RASTER_FILE_RESULT_GEOJSON] = dsm_vol_fp_file_path
                    volume_computation[defs_vc.FIELD_RASTER_FILE_FROM] = dsm_file_path
                    volume_computation[defs_vc.FIELD_RASTER_FILE_FROM_GEOJSON] = dsm_fp_file_path
                    volume_computation[defs_vc.FIELD_RASTER_FILE_TO] = gdp_raster_file_path
                    volume_computation[defs_vc.FIELD_RASTER_FILE_TO_GEOJSON] = gdp_raster_fp_file_path
                    volume_computation[defs_vc.FIELD_DESCRIPTION] = ''
                    # volume_computation[defs_vc.FIELD_CONTENT] = ''
                    volumes_computations[vc_id] = volume_computation
                # uav to uav
                phgmp_ids_as_list = list(dsm_filepath_by_gdp_id_by_id[gdp_id].keys())
                for i in range(len(phgmp_ids_as_list) - 1):
                    dsm_first_id = phgmp_ids_as_list[i]
                    dsm_first_file_path = dsm_filepath_by_gdp_id_by_id[gdp_id][dsm_first_id]
                    if not os.path.exists(dsm_first_file_path):
                        continue
                    dsm_first_fp_file_path = dsm_fp_filepath_by_gdp_id_by_id[gdp_id][dsm_first_id]
                    if not os.path.exists(dsm_first_fp_file_path):
                        continue
                    if not dsm_first_id in dsm_fp_geometry_by_gdp_id_by_id[gdp_id]:
                        continue
                    dsm_first_fp_geometry = dsm_fp_geometry_by_gdp_id_by_id[gdp_id][dsm_first_id]
                    str_first_date = self.photogrammetry_projects[dsm_first_id][defs_ph_prjs_dlg.FIELD_DATE]
                    str_first_date_formated = str_first_date.replace(':', '')
                    for j in range(i + 1, len(phgmp_ids_as_list)):
                        dsm_second_id = phgmp_ids_as_list[j]
                        dsm_second_file_path = dsm_filepath_by_gdp_id_by_id[gdp_id][dsm_second_id]
                        if not os.path.exists(dsm_second_file_path):
                            continue
                        dsm_second_fp_file_path = dsm_fp_filepath_by_gdp_id_by_id[gdp_id][dsm_second_id]
                        if not os.path.exists(dsm_second_fp_file_path):
                            continue
                        if not dsm_second_id in dsm_fp_geometry_by_gdp_id_by_id[gdp_id]:
                            continue
                        dsm_second_fp_geometry = dsm_fp_geometry_by_gdp_id_by_id[gdp_id][dsm_second_id]
                        # check exists overlaps
                        if (not dsm_first_fp_geometry.Intersects(dsm_second_fp_geometry)
                                and not dsm_first_fp_geometry.Within(dsm_second_fp_geometry)
                                and not dsm_first_fp_geometry.Within(dsm_second_fp_geometry)):
                            continue
                        str_second_date = self.photogrammetry_projects[dsm_second_id][defs_ph_prjs_dlg.FIELD_DATE]
                        str_second_date_formated = str_second_date.replace(':', '')
                        str_date_from = str_first_date
                        str_date_to = str_second_date
                        str_date_from_formated = str_first_date_formated
                        str_date_to_formated = str_second_date_formated
                        dsm_from_id = dsm_first_id
                        dsm_to_id = dsm_second_id
                        dsm_from_file_path = dsm_first_file_path
                        dsm_to_file_path = dsm_second_file_path
                        dsm_fp_from_file_path = dsm_first_fp_file_path
                        dsm_fp_to_file_path = dsm_second_fp_file_path
                        if str_first_date_formated > str_second_date_formated:
                            str_date_from = str_second_date
                            str_date_to = str_first_date
                            str_date_from_formated = str_second_date_formated
                            str_date_to_formated = str_first_date_formated
                            dsm_from_id = dsm_second_id
                            dsm_to_id = dsm_first_id
                            dsm_from_file_path = dsm_second_file_path
                            dsm_to_file_path = dsm_first_file_path
                            dsm_fp_from_file_path = dsm_second_fp_file_path
                            dsm_fp_to_file_path = dsm_first_fp_file_path
                        dsm_vol_filename = ("gdp_" + gdp_id + '_' #+ str_date_formated + '_'
                                            + dsm_from_id + '_'
                                            + dsm_to_id + '_'
                                            + defs_ph_prjs_dlg.FIELD_DSM + '_'
                                            + defs_vc.VOLUME_RASTER_FILE_SUFIX
                                            + ".tif")
                        dsm_vol_file_path = os.path.join(output_path, dsm_vol_filename)
                        dsm_vol_file_path = os.path.normpath(dsm_vol_file_path)
                        dsm_vol_fp_aux_filename = ("gdp_" + gdp_id + '_' #+ str_date_formated + '_'
                                                   + dsm_from_id + '_'
                                                   + dsm_to_id + '_'
                                                   + defs_ph_prjs_dlg.FIELD_DSM + '_'
                                                   + defs_vc.VOLUME_RASTER_FILE_SUFIX
                                                   + "_aux.geojson")
                        dsm_vol_fp_aux_file_path = os.path.join(output_path, dsm_vol_fp_aux_filename)
                        dsm_vol_fp_aux_file_path = os.path.normpath(dsm_vol_fp_aux_file_path)
                        dsm_vol_fp_filename = ("gdp_" + gdp_id + '_' #+ str_date_formated + '_'
                                               + dsm_from_id + '_'
                                               + dsm_to_id + '_'
                                               + defs_ph_prjs_dlg.FIELD_DSM + '_'
                                               + defs_vc.VOLUME_RASTER_FILE_SUFIX
                                               + ".geojson")
                        dsm_vol_fp_file_path = os.path.join(output_path, dsm_vol_fp_filename)
                        dsm_vol_fp_file_path = os.path.normpath(dsm_vol_fp_file_path)
                        if not os.path.exists(dsm_vol_file_path):
                            if os.path.exists(dsm_vol_fp_file_path):
                                os.remove(dsm_vol_fp_file_path)
                            command_calc = ("gdal_calc -A \"{}\"".format(dsm_to_file_path))
                            command_calc += (" -B \"{}\"".format(dsm_from_file_path))
                            command_calc += (" --outfile=\"{}\"".format(dsm_vol_file_path))
                            command_calc += (" --calc=\"A-B\" --NoDataValue -9999 --type=Float32 --co \"COMPRESS=LZW\"")
                            volumes_computations_commands.append(command_calc)
                        if not os.path.exists(dsm_vol_fp_file_path):
                            commmand_fp_1_command = ("gdal raster contour --levels MIN,MAX --polygonize ");
                            commmand_fp_1_command += (" \"{}\" \"{}\"".format(dsm_vol_file_path,
                                                                              dsm_vol_fp_aux_file_path))
                            volumes_computations_commands.append(commmand_fp_1_command)
                            commmand_fp_2_command = ("ogr2ogr  \"{}\" \"{}\"".format(dsm_vol_fp_file_path,
                                                                                     dsm_vol_fp_aux_file_path))
                            commmand_fp_2_command += (
                                " -simplify {:.3f} -dialect sqlite -sql \"SELECT ST_Union(geometry) FROM contour\"".format(
                                    gdp_gsd))
                            volumes_computations_commands.append(commmand_fp_2_command)
                            command_fp_3_command = ("del \"{}\" /Q".format(dsm_vol_fp_aux_file_path))
                            volumes_computations_commands.append(command_fp_3_command)
                        vc_id = "gdp_" + gdp_id
                        vc_id += "_" + str_date_from_formated
                        vc_id += "_" + str_date_to_formated
                        vc_id += "_" + defs_ph_prjs_dlg.FIELD_DSM
                        volume_computation = {}
                        volume_computation[defs_vc.FIELD_ID] = vc_id
                        volume_computation[defs_vc.FIELD_ENABLED] = 1
                        volume_computation[defs_vc.FIELD_VOLUME_DATE_FROM] = str_date_from
                        volume_computation[defs_vc.FIELD_VOLUME_DATE_TO] = str_date_to
                        volume_computation[defs_vc.FIELD_VOLUME_TYPE] = defs_vc.VOLUME_TYPE_DSMS_DIFFERENCE
                        volume_computation[defs_vc.FIELD_CRS] = gdp_crs
                        volume_computation[defs_vc.FIELD_RASTER_FILE_RESULT] = dsm_vol_file_path
                        volume_computation[defs_vc.FIELD_RASTER_FILE_RESULT_GEOJSON] = dsm_vol_fp_file_path
                        volume_computation[defs_vc.FIELD_RASTER_FILE_FROM] = dsm_from_file_path
                        volume_computation[defs_vc.FIELD_RASTER_FILE_FROM_GEOJSON] = dsm_fp_from_file_path
                        volume_computation[defs_vc.FIELD_RASTER_FILE_TO] = dsm_to_file_path
                        volume_computation[defs_vc.FIELD_RASTER_FILE_TO_GEOJSON] = dsm_fp_to_file_path
                        volume_computation[defs_vc.FIELD_DESCRIPTION] = ''
                        # volume_computation[defs_vc.FIELD_CONTENT] = ''
                        volumes_computations[vc_id] = volume_computation
        # compute dtm volumes
        if computeForDtm:
            for gdp_id in gdp_raster_filepath_by_id:
                gdp = self.geometric_design_projects[gdp_id]
                gdp_enabled = gdp[defs_gdp.FIELD_ENABLED]
                if gdp_enabled == 0:
                    continue
                gdp_crs = gdp[defs_gdp.FIELD_CRS]
                gdp_gsd = np.round(gdp[defs_gdp.FIELD_GSD_VOLUMES_COMPUTATION] * 100.) / 100.  # cm accuracy
                gdp_min_x = np.floor(gdp[defs_gdp.FIELD_MINIMUM_X])
                gdp_max_x = np.ceil(gdp[defs_gdp.FIELD_MAXIMUM_X])
                gdp_min_y = np.floor(gdp[defs_gdp.FIELD_MINIMUM_Y])
                gdp_max_y = np.ceil(gdp[defs_gdp.FIELD_MAXIMUM_Y])
                gdp_raster_file_path = gdp_raster_filepath_by_id[gdp_id]
                if not os.path.exists(gdp_raster_file_path): # never
                    continue
                gdp_raster_fp_file_path = gdp_raster_fp_filepath_by_id[gdp_id]
                if not os.path.exists(gdp_raster_fp_file_path): # never
                    continue
                if not gdp_id in gdp_raster_fp_geometry_by_id: # never
                    continue
                gdp_raster_fp_geometry = gdp_raster_fp_geometry_by_id[gdp_id]
                if not gdp_id in dtm_filepath_by_gdp_id_by_id or not gdp_id in dtm_fp_filepath_by_gdp_id_by_id:
                    continue
                for phgmp_id in dtm_fp_filepath_by_gdp_id_by_id[gdp_id]:
                    dtm_id = phgmp_id
                    dtm_file_path = dtm_filepath_by_gdp_id_by_id[gdp_id][dtm_id]
                    if not os.path.exists(dtm_file_path):
                        continue
                    dtm_fp_file_path = dtm_fp_filepath_by_gdp_id_by_id[gdp_id][dtm_id]
                    if not os.path.exists(dtm_fp_file_path):
                        continue
                    if not gdp_id in dtm_fp_geometry_by_gdp_id_by_id:  # never
                        continue
                    if not dtm_id in dtm_fp_geometry_by_gdp_id_by_id[gdp_id]:
                        continue
                    dtm_fp_geometry = dtm_fp_geometry_by_gdp_id_by_id[gdp_id][dtm_id]
                    # check exists overlaps
                    if (not gdp_raster_fp_geometry.Intersects(dtm_fp_geometry)
                            and not gdp_raster_fp_geometry.Within(dtm_fp_geometry)
                            and not gdp_raster_fp_geometry.Within(dtm_fp_geometry)):
                        continue
                    str_date = self.photogrammetry_projects[dtm_id][defs_ph_prjs_dlg.FIELD_DATE]
                    str_date_formated = str_date.replace(':','')
                    dtm_vol_filename = ("gdp_" + gdp_id + '_' #+ str_date_formated + '_'
                                        + dtm_id + '_'
                                        + defs_ph_prjs_dlg.FIELD_DTM + '_'
                                        + defs_vc.VOLUME_RASTER_FILE_SUFIX
                                        + ".tif")
                    dtm_vol_file_path = os.path.join(output_path, dtm_vol_filename)
                    dtm_vol_file_path = os.path.normpath(dtm_vol_file_path)
                    dtm_vol_fp_aux_filename = ("gdp_" + gdp_id + '_' #+ str_date_formated + '_'
                                               + dtm_id + '_'
                                               + defs_ph_prjs_dlg.FIELD_DTM + '_'
                                               + defs_vc.VOLUME_RASTER_FILE_SUFIX
                                               + "_aux.geojson")
                    dtm_vol_fp_aux_file_path = os.path.join(output_path, dtm_vol_fp_aux_filename)
                    dtm_vol_fp_aux_file_path = os.path.normpath(dtm_vol_fp_aux_file_path)
                    dtm_vol_fp_filename = ("gdp_" + gdp_id + '_' #+ str_date_formated + '_'
                                           + dtm_id + '_'
                                           + defs_ph_prjs_dlg.FIELD_DTM + '_'
                                           + defs_vc.VOLUME_RASTER_FILE_SUFIX
                                           + ".geojson")
                    dtm_vol_fp_file_path = os.path.join(output_path, dtm_vol_fp_filename)
                    dtm_vol_fp_file_path = os.path.normpath(dtm_vol_fp_file_path)
                    if not os.path.exists(dtm_vol_file_path):
                        if os.path.exists(dtm_vol_fp_file_path):
                            os.remove(dtm_vol_fp_file_path)
                        command_calc = ("gdal_calc -A \"{}\"".format(gdp_raster_file_path))
                        command_calc += (" -B \"{}\"".format(dtm_file_path))
                        command_calc += (" --outfile=\"{}\"".format(dtm_vol_file_path))
                        command_calc += (" --calc=\"A-B\" --NoDataValue -9999 --type=Float32 --co \"COMPRESS=LZW\"")
                        volumes_computations_commands.append(command_calc)
                    if not os.path.exists(dtm_vol_fp_file_path):
                        commmand_fp_1_command = ("gdal raster contour --levels MIN,MAX --polygonize ");
                        commmand_fp_1_command += (" \"{}\" \"{}\"".format(dtm_vol_file_path,
                                                                          dtm_vol_fp_aux_file_path))
                        volumes_computations_commands.append(commmand_fp_1_command)
                        commmand_fp_2_command = ("ogr2ogr  \"{}\" \"{}\"".format(dtm_vol_fp_file_path,
                                                                                 dtm_vol_fp_aux_file_path))
                        commmand_fp_2_command += (
                            " -simplify {:.3f} -dialect sqlite -sql \"SELECT ST_Union(geometry) FROM contour\"".format(
                                gdp_gsd))
                        volumes_computations_commands.append(commmand_fp_2_command)
                        command_fp_3_command = ("del \"{}\" /Q".format(dtm_vol_fp_aux_file_path))
                        volumes_computations_commands.append(command_fp_3_command)
                    vc_id = "gdp_" + gdp_id
                    vc_id += "_" + str_date_formated
                    vc_id += "_" + defs_ph_prjs_dlg.FIELD_DTM
                    volume_computation = {}
                    volume_computation[defs_vc.FIELD_ID] = vc_id
                    volume_computation[defs_vc.FIELD_ENABLED] = 1
                    volume_computation[defs_vc.FIELD_VOLUME_DATE_FROM] = str_date
                    volume_computation[defs_vc.FIELD_VOLUME_DATE_TO] = str_date
                    volume_computation[defs_vc.FIELD_VOLUME_TYPE] = defs_vc.VOLUME_TYPE_GD_DTM_DIFFERENCE
                    volume_computation[defs_vc.FIELD_CRS] = gdp_crs
                    volume_computation[defs_vc.FIELD_RASTER_FILE_RESULT] = dtm_vol_file_path
                    volume_computation[defs_vc.FIELD_RASTER_FILE_RESULT_GEOJSON] = dtm_vol_fp_file_path
                    volume_computation[defs_vc.FIELD_RASTER_FILE_FROM] = dtm_file_path
                    volume_computation[defs_vc.FIELD_RASTER_FILE_FROM_GEOJSON] = dtm_fp_file_path
                    volume_computation[defs_vc.FIELD_RASTER_FILE_TO] = gdp_raster_file_path
                    volume_computation[defs_vc.FIELD_RASTER_FILE_TO_GEOJSON] = gdp_raster_fp_file_path
                    volume_computation[defs_vc.FIELD_DESCRIPTION] = ''
                    # volume_computation[defs_vc.FIELD_CONTENT] = ''
                    volumes_computations[vc_id] = volume_computation
                # uav to uav
                phgmp_ids_as_list = list(dtm_filepath_by_gdp_id_by_id[gdp_id].keys())
                for i in range(len(phgmp_ids_as_list) - 1):
                    dtm_first_id = phgmp_ids_as_list[i]
                    dtm_first_file_path = dtm_filepath_by_gdp_id_by_id[gdp_id][dtm_first_id]
                    if not os.path.exists(dtm_first_file_path):
                        continue
                    dtm_first_fp_file_path = dtm_fp_filepath_by_gdp_id_by_id[gdp_id][dtm_first_id]
                    if not os.path.exists(dtm_first_fp_file_path):
                        continue
                    if not dtm_first_id in dtm_fp_geometry_by_gdp_id_by_id[gdp_id]:
                        continue
                    dtm_first_fp_geometry = dtm_fp_geometry_by_gdp_id_by_id[gdp_id][dtm_first_id]
                    str_first_date = self.photogrammetry_projects[dtm_first_id][defs_ph_prjs_dlg.FIELD_DATE]
                    str_first_date_formated = str_first_date.replace(':', '')
                    for j in range(i + 1, len(phgmp_ids_as_list)):
                        dtm_second_id = phgmp_ids_as_list[j]
                        dtm_second_file_path = dtm_filepath_by_gdp_id_by_id[gdp_id][dtm_second_id]
                        if not os.path.exists(dtm_second_file_path):
                            continue
                        dtm_second_fp_file_path = dtm_fp_filepath_by_gdp_id_by_id[gdp_id][dtm_second_id]
                        if not os.path.exists(dtm_second_fp_file_path):
                            continue
                        if not dtm_second_id in dtm_fp_geometry_by_gdp_id_by_id[gdp_id]:
                            continue
                        dtm_second_fp_geometry = dtm_fp_geometry_by_gdp_id_by_id[gdp_id][dtm_second_id]
                        # check exists overlaps
                        if (not dtm_first_fp_geometry.Intersects(dtm_second_fp_geometry)
                                and not dtm_first_fp_geometry.Within(dtm_second_fp_geometry)
                                and not dtm_first_fp_geometry.Within(dtm_second_fp_geometry)):
                            continue
                        str_second_date = self.photogrammetry_projects[dtm_second_id][defs_ph_prjs_dlg.FIELD_DATE]
                        str_second_date_formated = str_second_date.replace(':', '')
                        str_date_from = str_first_date
                        str_date_to = str_second_date
                        str_date_from_formated = str_first_date_formated
                        str_date_to_formated = str_second_date_formated
                        dtm_from_id = dtm_first_id
                        dtm_to_id = dtm_second_id
                        dtm_from_file_path = dtm_first_file_path
                        dtm_to_file_path = dtm_second_file_path
                        dtm_fp_from_file_path = dtm_first_fp_file_path
                        dtm_fp_to_file_path = dtm_second_fp_file_path
                        if str_first_date_formated > str_second_date_formated:
                            str_date_from = str_second_date
                            str_date_to = str_first_date
                            str_date_from_formated = str_second_date_formated
                            str_date_to_formated = str_first_date_formated
                            dtm_from_id = dtm_second_id
                            dtm_to_id = dtm_first_id
                            dtm_from_file_path = dtm_second_file_path
                            dtm_to_file_path = dtm_first_file_path
                            dtm_fp_from_file_path = dtm_second_fp_file_path
                            dtm_fp_to_file_path = dtm_first_fp_file_path
                        dtm_vol_filename = ("gdp_" + gdp_id + '_' #+ str_date_formated + '_'
                                            + dtm_from_id + '_'
                                            + dtm_to_id + '_'
                                            + defs_ph_prjs_dlg.FIELD_DTM + '_'
                                            + defs_vc.VOLUME_RASTER_FILE_SUFIX
                                            + ".tif")
                        dtm_vol_file_path = os.path.join(output_path, dtm_vol_filename)
                        dtm_vol_file_path = os.path.normpath(dtm_vol_file_path)
                        dtm_vol_fp_aux_filename = ("gdp_" + gdp_id + '_' #+ str_date_formated + '_'
                                                   + dtm_from_id + '_'
                                                   + dtm_to_id + '_'
                                                   + defs_ph_prjs_dlg.FIELD_DTM + '_'
                                                   + defs_vc.VOLUME_RASTER_FILE_SUFIX
                                                   + "_aux.geojson")
                        dtm_vol_fp_aux_file_path = os.path.join(output_path, dtm_vol_fp_aux_filename)
                        dtm_vol_fp_aux_file_path = os.path.normpath(dtm_vol_fp_aux_file_path)
                        dtm_vol_fp_filename = ("gdp_" + gdp_id + '_' #+ str_date_formated + '_'
                                               + dtm_from_id + '_'
                                               + dtm_to_id + '_'
                                               + defs_ph_prjs_dlg.FIELD_DTM + '_'
                                               + defs_vc.VOLUME_RASTER_FILE_SUFIX
                                               + ".geojson")
                        dtm_vol_fp_file_path = os.path.join(output_path, dtm_vol_fp_filename)
                        dtm_vol_fp_file_path = os.path.normpath(dtm_vol_fp_file_path)
                        if not os.path.exists(dtm_vol_file_path):
                            if os.path.exists(dtm_vol_fp_file_path):
                                os.remove(dtm_vol_fp_file_path)
                            command_calc = ("gdal_calc -A \"{}\"".format(dtm_to_file_path))
                            command_calc += (" -B \"{}\"".format(dtm_from_file_path))
                            command_calc += (" --outfile=\"{}\"".format(dtm_vol_file_path))
                            command_calc += (" --calc=\"A-B\" --NoDataValue -9999 --type=Float32 --co \"COMPRESS=LZW\"")
                            volumes_computations_commands.append(command_calc)
                        if not os.path.exists(dtm_vol_fp_file_path):
                            commmand_fp_1_command = ("gdal raster contour --levels MIN,MAX --polygonize ");
                            commmand_fp_1_command += (" \"{}\" \"{}\"".format(dtm_vol_file_path,
                                                                              dtm_vol_fp_aux_file_path))
                            volumes_computations_commands.append(commmand_fp_1_command)
                            commmand_fp_2_command = ("ogr2ogr  \"{}\" \"{}\"".format(dtm_vol_fp_file_path,
                                                                                     dtm_vol_fp_aux_file_path))
                            commmand_fp_2_command += (
                                " -simplify {:.3f} -dialect sqlite -sql \"SELECT ST_Union(geometry) FROM contour\"".format(
                                    gdp_gsd))
                            volumes_computations_commands.append(commmand_fp_2_command)
                            command_fp_3_command = ("del \"{}\" /Q".format(dtm_vol_fp_aux_file_path))
                            volumes_computations_commands.append(command_fp_3_command)
                        vc_id = "gdp_" + gdp_id
                        vc_id += "_" + str_date_from_formated
                        vc_id += "_" + str_date_to_formated
                        vc_id += "_" + defs_ph_prjs_dlg.FIELD_DTM
                        volume_computation = {}
                        volume_computation[defs_vc.FIELD_ID] = vc_id
                        volume_computation[defs_vc.FIELD_ENABLED] = 1
                        volume_computation[defs_vc.FIELD_VOLUME_DATE_FROM] = str_date_from
                        volume_computation[defs_vc.FIELD_VOLUME_DATE_TO] = str_date_to
                        volume_computation[defs_vc.FIELD_VOLUME_TYPE] = defs_vc.VOLUME_TYPE_DTMS_DIFFERENCE
                        volume_computation[defs_vc.FIELD_CRS] = gdp_crs
                        volume_computation[defs_vc.FIELD_RASTER_FILE_RESULT] = dtm_vol_file_path
                        volume_computation[defs_vc.FIELD_RASTER_FILE_RESULT_GEOJSON] = dtm_vol_fp_file_path
                        volume_computation[defs_vc.FIELD_RASTER_FILE_FROM] = dtm_from_file_path
                        volume_computation[defs_vc.FIELD_RASTER_FILE_FROM_GEOJSON] = dtm_fp_from_file_path
                        volume_computation[defs_vc.FIELD_RASTER_FILE_TO] = dtm_to_file_path
                        volume_computation[defs_vc.FIELD_RASTER_FILE_TO_GEOJSON] = dtm_fp_to_file_path
                        volume_computation[defs_vc.FIELD_DESCRIPTION] = ''
                        # volume_computation[defs_vc.FIELD_CONTENT] = ''
                        volumes_computations[vc_id] = volume_computation
        if len(volumes_computations_commands) > 0:
            steps = len(volumes_computations_commands)
            progress = QProgressDialog("Computing volume files...", "Cancel", 0, steps)
            # progress = QProgressDialog("Computing raster for geometric design projects...", "Cancel", 0, steps)
            progress.setWindowModality(Qt.WindowModal)  # Bloquea la ventana principal
            progress.setWindowTitle("Wait for finished")
            progress.show()
            i = 0
            for command in volumes_computations_commands:
                i = i + 1
                progress.setValue(i)
                if progress.wasCanceled():
                    break
                QApplication.processEvents()
                cv_bat_filename = "Compute_Volume.bat"
                cv_bat_filepath = os.path.join(output_path, cv_bat_filename)
                cv_bat_filepath = os.path.normpath(cv_bat_filepath)
                if os.path.exists(cv_bat_filepath):
                    os.remove(cv_bat_filepath)
                if os.path.exists(cv_bat_filepath):
                    str_error = Project.__name__ + "." + self.save_to_json.__name__
                    str_error += ("\nError removing existing BAT file:\n{}".format(cv_bat_filepath))
                    progress.close()
                    return str_error
                # files_to_remove.append(gdp_bat_filepath)
                f_bat = open(cv_bat_filepath, "w")
                f_bat.write("@echo off\n")
                f_bat.write("set OSGEO4W_ROOT={}\n".format(self.qgis_prefix_path))
                # f_bat.write("set OSGEO4W_ROOT=C:/Program Files/QGIS 3.40.10\n")
                # windows
                f_bat.write("call \"{}\"\n".format(self.osge4w_bat_path))
                # f_bat.write("call \"%OSGEO4W_ROOT%\\bin\\o4w_env.bat\"\n")
                f_bat.write("set PROCESS_PATH={}\n".format(output_path))
                # f_bat.write("set PROCESS_PATH=D:/master_co2/tafalla/qVolumeTimeSeriesProjects/output\n")
                f_bat.write("set PATH={};{};%PATH%\n".format(self.osge4w_bin_path, self.qgis_bin_path))
                # f_bat.write("set PATH=%OSGEO4W_ROOT%\\bin;%OSGEO4W_ROOT%\\apps\qgis-ltr\\bin;%PATH%\n")
                f_bat.write("echo \"start\"\n")
                f_bat.write(command)
                f_bat.write("\n")
                f_bat.write("echo \"end\"\n")
                f_bat.close()
                cv_command = cv_bat_filepath
                result = subprocess.run([cv_command], capture_output=True, text=True)
                if os.path.exists(cv_bat_filepath):
                    os.remove(cv_bat_filepath)
            progress.close()
            QApplication.processEvents()
        self.volumes_computations.clear()
        self.volumes_computations = volumes_computations
        # for vc_id in volumes_computations:
        #     volume_computation = volumes_computations[vc_id]
        #     dsm_vol_fp_file_path = volume_computation[defs_vc.FIELD_RASTER_FILE_RESULT_GEOJSON]
        #     if not os.path.exists(dsm_vol_fp_file_path):
        #         continue
        #     exists_footprints = get_exists_footprint_from_geojson(dsm_vol_fp_file_path)
        #     if not exists_footprints:
        #         continue
        #     self.volumes_computations[vc_id] = volume_computation
        return str_error

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
        as_dict[defs_project.PROJECT_PHOTOGRAMMETRY_PROJECTS_TAG] = self.photogrammetry_projects
        as_dict[defs_project.PROJECT_VOLUMES_COMPUTATIONS_TAG] = self.volumes_computations
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
        if defs_project.PROJECT_PHOTOGRAMMETRY_PROJECTS_TAG in project_from_json:
            str_aux_error = self.set_photogrammetry_projects_from_json(
                project_from_json[defs_project.PROJECT_PHOTOGRAMMETRY_PROJECTS_TAG])
            if str_aux_error:
                str_error = Project.__name__ + "." + self.set_from_json.__name__
                str_error += ('\nSetting from json project file:\n{}\nerror:\n{}'.format(file_name, str_aux_error))
                return str_error
        if defs_project.PROJECT_VOLUMES_COMPUTATIONS_TAG in project_from_json:
            str_aux_error = self.set_volumes_computations_from_json(
                project_from_json[defs_project.PROJECT_VOLUMES_COMPUTATIONS_TAG])
            if str_aux_error:
                str_error = Project.__name__ + "." + self.set_from_json.__name__
                str_error += ('\nSetting from json project file:\n{}\nerror:\n{}'.format(file_name, str_aux_error))
                return str_error
        self.file_path = file_name
        return str_error

    def set_photogrammetry_projects_from_json(self,
                                              json_content):
        str_error = ""
        photogrammetry_projects = {}
        for id in json_content:
            phprj_json_content = json_content[id]
            for field_name in defs_ph_prjs_dlg.fields:
                if not field_name in phprj_json_content:
                    str_error = ('For photogrammetry project id: {}'.format(id))
                    str_error += ("\nNo {} in json content".format(field_name))
                    return str_error
            photogrammetry_projects[id] = phprj_json_content
        self.photogrammetry_projects = photogrammetry_projects
        return str_error

    def set_qgis_prefix_path(self, qgis_prefix_path):
        str_error = ""
        self.qgis_prefix_path = os.path.normpath(qgis_prefix_path)
        if not self.qgis_prefix_path:
            self.qgis_prefix_path = None
            str_error = ('QGis prefix path is empty')
            return str_error
        if not os.path.exists(self.qgis_prefix_path):
            self.settings.setValue("qgis_prefix_path", "")
            self.settings.sync()
            str_error = ('Not exists QGis prefix path:\n{}'.format(self.qgis_prefix_path))
            self.qgis_prefix_path = None
            return str_error
        else:
            self.osge4w_bat_path = os.path.normpath(self.qgis_prefix_path + defs_qgis_paths.OSGEO4W_BAT_SUFFIX_WINDOWS)
            if not os.path.exists(self.osge4w_bat_path):
                self.settings.setValue("qgis_prefix_path", "")
                self.settings.sync()
                str_error = ('Not exists OSGeo4W bat file:\n{}'.format(self.osge4w_bat_path))
                self.qgis_prefix_path = None
                self.osge4w_bat_path = None
                return str_error
            self.osge4w_bin_path = os.path.normpath(self.qgis_prefix_path + defs_qgis_paths.OSGEO4W_BIN_SUFFIX_WINDOWS)
            if not os.path.exists(self.osge4w_bin_path):
                self.settings.setValue("qgis_prefix_path", "")
                self.settings.sync()
                str_error = ('Not exists OSGeo4W bin path:\n{}'.format(self.osge4w_bin_path))
                self.qgis_prefix_path = None
                self.osge4w_bat_path = None
                self.osge4w_bin_path = None
                return str_error
            self.qgis_bin_path = os.path.normpath(self.qgis_prefix_path + defs_qgis_paths.QGIS_BIN_SUFFIX_WINDOWS)
            if not os.path.exists(self.qgis_bin_path):
                self.settings.setValue("qgis_prefix_path", "")
                self.settings.sync()
                str_error = ('Not exists QGIS bin path:\n{}'.format(self.qgis_bin_path))
                self.qgis_prefix_path = None
                self.osge4w_bat_path = None
                self.osge4w_bin_path = None
                self.qgis_bin_path = None
                return str_error
            self.qgis_plugins_path = os.path.normpath(
                self.qgis_prefix_path + defs_qgis_paths.QGIS_PLUGINS_SUFFIX_WINDOWS)
            if not os.path.exists(self.qgis_plugins_path):
                self.settings.setValue("qgis_prefix_path", "")
                self.settings.sync()
                str_error = ('Not exists QGIS plugins path:\n{}'.format(self.qgis_plugins_path))
                self.qgis_prefix_path = None
                self.osge4w_bat_path = None
                self.osge4w_bin_path = None
                self.qgis_bin_path = None
                self.qgis_plugins_path = None
                return str_error
            self.qgis_python_path = os.path.normpath(
                self.qgis_prefix_path + defs_qgis_paths.QIGS_PYTHON_PATH_SUFFIX_WINDOWS)
            if not os.path.exists(self.qgis_python_path):
                self.settings.setValue("qgis_prefix_path", "")
                self.settings.sync()
                str_error = ('Not exists QGIS python path:\n{}'.format(self.qgis_python_path))
                self.qgis_prefix_path = None
                self.osge4w_bat_path = None
                self.osge4w_bin_path = None
                self.qgis_bin_path = None
                self.qgis_plugins_path = None
                self.qgis_python_path = None
                return str_error
            self.settings.setValue("qgis_prefix_path", self.qgis_prefix_path)
            self.settings.sync()
        return str_error

    def set_volumes_computations_from_json(self,
                                           json_content):
        str_error = ""
        volumes_computations = {}
        for id in json_content:
            vc_json_content = json_content[id]
            for field_name in defs_vc.fields:
                if not field_name in vc_json_content:
                    str_error = ('For volume computation id: {}'.format(id))
                    str_error += ("\nNo {} in json content".format(field_name))
                    return str_error
            volumes_computations[id] = vc_json_content
        self.volumes_computations = volumes_computations
        return str_error

    def volumes_computations_gui(self, parent_widget):
        str_error = ''
        if len(self.geometric_design_projects) == 0:
            str_error = ('There are no geometric designs projects')
            return str_error
        title = defs_vc.DIALOG_TITLE
        dialog = VolumesComputationsDialog(self, title, parent_widget)
        dialog_result = dialog.exec()
        # if dialog_result != QDialog.Accepted:
        #     return str_error
        # definition_is_saved = dialog.is_saved
        # if dialog_result != QDialog.Accepted:
        #     return str_error, definition_is_saved
        # return str_error, definition_is_saved
        return str_error

