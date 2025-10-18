# authors:
# David Hernandez Lopez, david.hernandez@uclm.es

import os
import sys
import math
import pathlib
import json

import subprocess

from PyQt5 import QtCore, QtWidgets
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import (QApplication, QMessageBox, QDialog, QInputDialog,
                             QFileDialog, QPushButton, QComboBox, QPlainTextEdit, QLineEdit,
                             QDialogButtonBox, QVBoxLayout, QTableWidget, QTableWidgetItem)
from PyQt5.QtCore import QDir, QFileInfo, QFile, QSize, Qt

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(current_path, '..'))
sys.path.append(os.path.join(current_path, '../..'))
# sys.path.insert(0, '..')
# sys.path.insert(0, '../..')

from VolumeTimeSeries.defs import defs_paths, defs_project, defs_main
from VolumeTimeSeries.defs import defs_geometric_design_projects as defs_gdp

common_libs_absolute_path = os.path.join(current_path, defs_paths.COMMON_LIBS_RELATIVE_PATH)
sys.path.append(common_libs_absolute_path)

from pyLibCRSs.CompoundProjectedCRSDialog import CompoundProjectedCRSDialog
from pyLibQtTools import Tools
from pyLibQtTools.Tools import SimpleTextEditDialog, SimpleJSONDialog
# from pyLibLandXml.LandXml import LandXml

from pyLibQtTools.QProcessDialog import QProcessDialog
from pyLibQtTools import defs_qprocess

class GeometricDesignProjectsDialog(QDialog):
    """Employee dialog."""

    def __init__(self,
                 project,
                 title,
                 parent=None):
        super().__init__(parent)
        loadUi(os.path.join(os.path.dirname(__file__), 'GeometricDesignProjectsDialog.ui'), self)
        # loadUi("lib/InstrumentsDialog.ui", self)
        self.project = project
        self.last_past = None
        self.title = title
        self.setWindowTitle(title)
        self.formats = None
        self.geometric_design_projects = None
        self.initialize()

    # def create_geometric_design_project_from_landxml(self,
    #                                                  id,
    #                                                  crs_id,
    #                                                  file_path):
    #     str_error = ''
    #     geometric_design_project = {}
    #     landXml = LandXml()
    #     str_error = landXml.set_from_file(file_path)
    #     if str_error:
    #         return str_error, None
    #     points_distance = defs_gdp.AXIS_POINTS_DISTANCE
    #     str_error = landXml.set_axis_points(points_distance)
    #     if str_error:
    #         return str_error, None
    #     str_error, wkt_linestring, wkt_profile_linestring = landXml.get_axis_points_as_wktlinestring()
    #     if str_error:
    #         return str_error, None
    #     grading_axis = False # must be False, option use grading axis for triangulation of LandXml is not implemented yet
    #     cross_sections = True
    #     # ply_file_path = None
    #     ply_file_path = landXml.file_path
    #     ply_file_path = ply_file_path.lower()
    #     ply_file_path = ply_file_path.replace(".xml", ".ply")
    #     ply_file_path = os.path.normpath(ply_file_path)
    #     str_error = landXml.compute_triangulation(grading_axis,
    #                                               cross_sections,
    #                                               ply_file_path)
    #     if str_error:
    #         return str_error, None
    #     geometric_design_project = {}
    #     geometric_design_project[defs_gdp.FIELD_ID] = id
    #     geometric_design_project[defs_gdp.FIELD_ENABLED] = 1
    #     geometric_design_project[defs_gdp.FIELD_DESCRIPTION] = ""
    #     geometric_design_project[defs_gdp.FIELD_CRS] = crs_id
    #     geometric_design_project[defs_gdp.FIELD_CONTENT] = landXml.as_dict
    #     geometric_design_project[defs_gdp.FIELD_AXIS3D] = wkt_linestring
    #     geometric_design_project[defs_gdp.FIELD_PROFILE] = wkt_profile_linestring
    #     geometric_design_project[defs_gdp.FIELD_TRIANGULATION_PLY] = landXml.triangulation_ply_content
    #     geometric_design_project[defs_gdp.FIELD_SOURCE_FILE] = file_path
    #     geometric_design_project[defs_gdp.FIELD_TRIANGULATION_POINTS] = landXml.triangulation_points
    #     geometric_design_project[defs_gdp.FIELD_TRIANGULATION_TRIANGLES] = landXml.triangulation_triangles
    #     return str_error, geometric_design_project

    def disable(self):
        if len(self.geometric_design_projects) == 0:
            return
        for i in range(self.tableWidget.rowCount()):
            id_item = self.tableWidget.item(i, 0)
            if id_item.isSelected():
                id = id_item.text()
                if self.geometric_design_projects[id][defs_gdp.FIELD_ENABLED] == 1:
                    enabled_item = self.tableWidget.item(i, 1)
                    enabled_item.setText("False")
                    self.geometric_design_projects[id][defs_gdp.FIELD_ENABLED] = 0
        return

    def enable(self):
        if len(self.geometric_design_projects) == 0:
            return
        for i in range(self.tableWidget.rowCount()):
            id_item = self.tableWidget.item(i, 0)
            if id_item.isSelected():
                id = id_item.text()
                if self.geometric_design_projects[id][defs_gdp.FIELD_ENABLED] == 0:
                    enabled_item = self.tableWidget.item(i, 1)
                    enabled_item.setText("True")
                    self.geometric_design_projects[id][defs_gdp.FIELD_ENABLED] = 1
        return

    def import_file(self):
        file_path = self.fileLineEdit.text()
        if not file_path:
            str_msg = ("Select file before")
            Tools.error_msg(str_msg)
            return
        if not os.path.exists(file_path):
            str_msg = ("Not exists file:\n{}".format(file_path))
            Tools.error_msg(str_msg)
            return
        format = self.formatComboBox.currentText()
        if format == defs_gdp.CONST_NO_COMBO_SELECT:
            str_msg = ("Select format before")
            Tools.error_msg(str_msg)
            return
        id = self.idLineEdit.text()
        if not id:
            str_msg = ("Select id before")
            Tools.error_msg(str_msg)
            return
        if id in self.geometric_design_projects:
            str_msg = ("Exists another geometric design project with id: {}\nSelect a new id".format(id))
            Tools.error_msg(str_msg)
            return
        crs_id = self.crsLineEdit.text()
        if not crs_id:
            str_msg = ("Select CRS before")
            Tools.error_msg(str_msg)
            return
        if format != defs_gdp.FORMAT_LANDXML:
            str_msg = ("Format: {} is not implemented\nContact the author").format(format)
            Tools.error_msg(str_msg)
            return
        str_error = ''
        geometric_design_project = None
        if format == defs_gdp.FORMAT_LANDXML:
            str_error, geometric_design_project = self.project.create_geometric_design_project_from_landxml(id,
                                                                                                            crs_id,
                                                                                                            file_path)
        if str_error or geometric_design_project is None:
            str_error = ('Creating Geometric Design Project from file:\n{}\nError:\n{}'
                         .format(file_path, str_error))
            Tools.error_msg(str_error)
            return
        self.geometric_design_projects[id] = geometric_design_project
        self.update_gui()
        return

    def initialize(self):
        self.last_path = self.project.settings.value("last_path")
        current_dir = QDir.current()
        if not self.last_path:
            self.last_path = QDir.currentPath()
            self.project.settings.setValue("last_path", self.last_path)
            self.project.settings.sync()
        # deep copy using the dict() constructor
        self.geometric_design_projects = dict(self.project.geometric_design_projects)
        if len(defs_gdp.extension_by_format) > 1:
            self.formatComboBox.addItem(defs_gdp.CONST_NO_COMBO_SELECT)
        for format in defs_gdp.extension_by_format:
            self.formatComboBox.addItem(format)
        if len(defs_gdp.extension_by_format) == 1:
            self.formatComboBox.setEnabled(False)
        crs_id = self.project.crs_id
        self.crsLineEdit.setText(crs_id)
        self.selectFilePushButton.clicked.connect(self.select_file)
        self.idPushButton.clicked.connect(self.select_id)
        self.crsPushButton.clicked.connect(self.select_crs)
        self.importPushButton.clicked.connect(self.import_file)
        self.savePushButton.clicked.connect(self.save)
        self.tableWidget.itemDoubleClicked.connect(self.on_click)
        self.tableWidget.itemClicked.connect(self.on_click)
        self.removePushButton.clicked.connect(self.remove)
        self.enablePushButton.clicked.connect(self.enable)
        self.disablePushButton.clicked.connect(self.disable)
        headers = defs_gdp.headers
        headers_tooltips = defs_gdp.header_tooltips
        self.tableWidget.setColumnCount(len(headers))
        self.tableWidget.setStyleSheet("QHeaderView::section { color:black; background : lightGray; }")
        for i in range(len(headers)):
            header_item = QTableWidgetItem(headers[i])
            header_tooltip = headers_tooltips[i]
            header_item.setToolTip(header_tooltip)
            self.tableWidget.setHorizontalHeaderItem(i, header_item)
        self.tableWidget.setSizeAdjustPolicy(
            QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.update_gui()
        return

    @QtCore.pyqtSlot(QtWidgets.QTableWidgetItem)
    def on_click(self, item):
        row = item.row()
        column = item.column()
        id = self.tableWidget.item(row, 0).text()
        current_text = item.text()
        label = self.tableWidget.horizontalHeaderItem(column).text()
        tool_tip_text = self.tableWidget.horizontalHeaderItem(column).toolTip()
        title = label + ":"
        if label == defs_gdp.HEADER_DESCRIPTION_TAG:
            text = self.geometric_design_projects[id][defs_gdp.FIELD_DESCRIPTION]
            readOnly = False
            dialog =  SimpleTextEditDialog(title, text, readOnly)
            ret = dialog.exec()
            text = dialog.get_text()
            if text != self.geometric_design_projects[id][defs_gdp.FIELD_DESCRIPTION]:
                self.geometric_design_projects[id][defs_gdp.FIELD_DESCRIPTION] = text
            return
        elif label == defs_gdp.HEADER_CONTENT_TAG:
            # return
            text = self.geometric_design_projects[id][defs_gdp.FIELD_CONTENT]
            json_content = json.dumps(text)
            readOnly = True
            dialog = SimpleJSONDialog(title, json_content, readOnly)
            ret = dialog.exec()
        elif label == defs_gdp.HEADER_AXIS3D_TAG:
            text = self.geometric_design_projects[id][defs_gdp.FIELD_AXIS3D]
            readOnly = True
            dialog =  SimpleTextEditDialog(title, text, readOnly)
            ret = dialog.exec()
        elif label == defs_gdp.HEADER_PROFILE_TAG:
            text = self.geometric_design_projects[id][defs_gdp.FIELD_PROFILE]
            readOnly = True
            dialog =  SimpleTextEditDialog(title, text, readOnly)
            ret = dialog.exec()
        elif label == defs_gdp.HEADER_TRIANGULATION_PLY_TAG:
            text = self.geometric_design_projects[id][defs_gdp.FIELD_TRIANGULATION_PLY]
            readOnly = True
            dialog =  SimpleTextEditDialog(title, text, readOnly)
            ret = dialog.exec()
        return

    def remove(self):
        if len(self.geometric_design_projects) == 0:
            return
        ids_to_remove = []
        for i in range(self.tableWidget.rowCount()):
            id_item = self.tableWidget.item(i, 0)
            if id_item.isSelected():
                ids_to_remove.append(id_item.text())
        if len(ids_to_remove) < 1:
            str_error = "Select rows to remove"
            Tools.error_msg(str_error)
            return
        for i in range(len(ids_to_remove)):
            for j in range(self.tableWidget.rowCount()):
                id_item = self.tableWidget.item(j, 0)
                if id_item.text() == ids_to_remove[i]:
                    self.tableWidget.removeRow(id_item.row())
                    break
        for id in ids_to_remove:
            self.geometric_design_projects.pop(id)
        return

    def save(self):
        self.project.geometric_design_projects = dict(self.geometric_design_projects)
        str_aux_error = self.project.save_to_json()
        if str_aux_error:
            str_error = ('Error saving project definition:\n{}'.
                         format(str_aux_error))
            Tools.error_msg(str_error)
        else:
            str_msg = "Process completed"
            Tools.info_msg(str_msg)
        return

    def select_crs(self):
        crs_id = self.crsLineEdit.text()
        dialog = CompoundProjectedCRSDialog(self.project.crs_tools, crs_id)
        dialog_result = dialog.exec()
        if dialog.is_accepted:
            crs_id = dialog.crs_id
            self.crsLineEdit.setText(crs_id)
        return

    def select_file(self):
        selected_format = self.formatComboBox.currentText()
        if selected_format == defs_gdp.CONST_NO_COMBO_SELECT:
            str_msg = "Select format before"
            Tools.info_msg(str_msg)
            return
        title = "Select Geometric Design File"
        previous_file_name = self.fileLineEdit.text()
        previous_file_name = os.path.normpath(previous_file_name)
        dlg = QFileDialog()
        dlg.setDirectory(self.last_path)
        dlg.setFileMode(QFileDialog.AnyFile)
        str_content = ('Geometric Design File (*.{})'.format(defs_gdp.extension_by_format[selected_format]))
        dlg.setNameFilter(str_content)
        if dlg.exec_():
            file_names = dlg.selectedFiles()
            file_name = file_names[0]
        else:
            return
        # fileName, aux = QFileDialog.getSaveFileName(self, title, self.path, "Project File (*.json)")
        if file_name:
            file_name = os.path.normpath(file_name)
            if file_name != previous_file_name:
                self.fileLineEdit.setText(file_name)
                self.last_path = QFileInfo(file_name).absolutePath()
                self.project.settings.setValue("last_path", self.last_path)
                self.project.settings.sync()
        return

    def select_id(self):
        current_text = self.idLineEdit.text()
        text, okPressed = QInputDialog.getText(self, "Id", "Enter value (case sensitive):",
                                               QLineEdit.Normal, current_text)
        if okPressed and text != '' and text != current_text:
            # check exists previous id
            if text in self.project.geometric_design_projects:
                str_msg = ("Exists another geometric design project with id: {}\nSelect another id".format(text))
                Tools.info_msg(str_msg)
                return
            self.idLineEdit.setText(text)
        return

    def update_gui(self):
        self.tableWidget.setRowCount(0)
        for id in self.geometric_design_projects:
            rowPosition = self.tableWidget.rowCount()
            self.tableWidget.insertRow(rowPosition)
            # id
            id_item = QTableWidgetItem(id)
            id_item.setTextAlignment(Qt.AlignCenter)
            column_pos = 0
            self.tableWidget.setItem(rowPosition, column_pos, id_item)
            # enabled
            str_enabled = 'True'
            if self.geometric_design_projects[id][defs_gdp.FIELD_ENABLED] == 0:
                str_enabled = 'False'
            enabled_item = QTableWidgetItem(str_enabled)
            enabled_item.setTextAlignment(Qt.AlignCenter)
            column_pos = column_pos + 1
            self.tableWidget.setItem(rowPosition, column_pos, enabled_item)
            # description
            # description = self.geometric_design_projects[id][defs_gdp.FIELD_DESCRIPTION]
            description = defs_gdp.RESUME_CONTENT
            description_item = QTableWidgetItem(description)
            description_item.setTextAlignment(Qt.AlignCenter)
            column_pos = column_pos + 1
            self.tableWidget.setItem(rowPosition, column_pos, description_item)
            # crs
            crs_id = self.geometric_design_projects[id][defs_gdp.FIELD_CRS]
            crs_id_item = QTableWidgetItem(crs_id)
            crs_id_item.setTextAlignment(Qt.AlignCenter)
            column_pos = column_pos + 1
            self.tableWidget.setItem(rowPosition, column_pos, crs_id_item)
            # content
            # content = self.geometric_design_projects[id][defs_gdp.FIELD_CONTENT]
            content = defs_gdp.RESUME_CONTENT
            content_item = QTableWidgetItem(content)
            content_item.setTextAlignment(Qt.AlignCenter)
            column_pos = column_pos + 1
            self.tableWidget.setItem(rowPosition, column_pos, content_item)
            # wkt_linestring
            # wkt_linestring = self.geometric_design_projects[id][defs_gdp.FIELD_AXIS3D]
            wkt_linestring = defs_gdp.RESUME_CONTENT
            wkt_linestring_item = QTableWidgetItem(wkt_linestring)
            wkt_linestring_item.setTextAlignment(Qt.AlignCenter)
            column_pos = column_pos + 1
            self.tableWidget.setItem(rowPosition, column_pos, wkt_linestring_item)
            # wkt_profile_linestring
            # wkt_profile_linestring = self.geometric_design_projects[id][defs_gdp.FIELD_PROFILE]
            wkt_profile_linestring = defs_gdp.RESUME_CONTENT
            wkt_profile_linestring_item = QTableWidgetItem(wkt_profile_linestring)
            wkt_profile_linestring_item.setTextAlignment(Qt.AlignCenter)
            column_pos = column_pos + 1
            self.tableWidget.setItem(rowPosition, column_pos, wkt_profile_linestring_item)
            # triangulation_ply_content
            # triangulation_ply_content = self.geometric_design_projects[id][defs_gdp.FIELD_TRIANGULATION_PLY]
            triangulation_ply_content = defs_gdp.RESUME_CONTENT
            triangulation_ply_content_item = QTableWidgetItem(triangulation_ply_content)
            triangulation_ply_content_item.setTextAlignment(Qt.AlignCenter)
            column_pos = column_pos + 1
            self.tableWidget.setItem(rowPosition, column_pos, triangulation_ply_content_item)
            # source_file
            source_file = self.geometric_design_projects[id][defs_gdp.FIELD_SOURCE_FILE]
            source_file_item = QTableWidgetItem(source_file)
            source_file_item.setTextAlignment(Qt.AlignCenter)
            column_pos = column_pos + 1
            self.tableWidget.setItem(rowPosition, column_pos, source_file_item)
        self.tableWidget.resizeColumnsToContents()
        return