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
from VolumeTimeSeries.defs import defs_volumes_computations as defs_vc

common_libs_absolute_path = os.path.join(current_path, defs_paths.COMMON_LIBS_RELATIVE_PATH)
sys.path.append(common_libs_absolute_path)

from pyLibQtTools import Tools
from pyLibQtTools.Tools import SimpleTextEditDialog, SimpleJSONDialog
# from pyLibLandXml.LandXml import LandXml

from pyLibQtTools.QProcessDialog import QProcessDialog
from pyLibQtTools import defs_qprocess

class VolumesComputationsDialog(QDialog):
    """Employee dialog."""

    def __init__(self,
                 project,
                 title,
                 parent=None):
        super().__init__(parent)
        loadUi(os.path.join(os.path.dirname(__file__), 'VolumesComputationsDialog.ui'), self)
        # loadUi("lib/InstrumentsDialog.ui", self)
        self.project = project
        self.last_past = None
        self.title = title
        self.setWindowTitle(title)
        self.formats = None
        self.volumes_computations = None
        self.initialize()

    def disable(self):
        if len(self.volumes_computations) == 0:
            return
        for i in range(self.tableWidget.rowCount()):
            id_item = self.tableWidget.item(i, 0)
            if id_item.isSelected():
                id = id_item.text()
                if self.volumes_computations[id][defs_vc.FIELD_ENABLED] == 1:
                    enabled_item = self.tableWidget.item(i, 1)
                    enabled_item.setText("False")
                    self.volumes_computations[id][defs_vc.FIELD_ENABLED] = 0
        return

    def enable(self):
        if len(self.volumes_computations) == 0:
            return
        for i in range(self.tableWidget.rowCount()):
            id_item = self.tableWidget.item(i, 0)
            if id_item.isSelected():
                id = id_item.text()
                if self.volumes_computations[id][defs_vc.FIELD_ENABLED] == 0:
                    enabled_item = self.tableWidget.item(i, 1)
                    enabled_item.setText("True")
                    self.volumes_computations[id][defs_vc.FIELD_ENABLED] = 1
        return


    def initialize(self):
        self.last_path = self.project.settings.value("last_path")
        current_dir = QDir.current()
        if not self.last_path:
            self.last_path = QDir.currentPath()
            self.project.settings.setValue("last_path", self.last_path)
            self.project.settings.sync()
        # deep copy using the dict() constructor
        self.volumes_computations = dict(self.project.volumes_computations)
        self.computeForDtmCheckBox.setChecked(True)
        self.computeForDsmCheckBox.setChecked(True)
        self.computeForGeometricDesignsCheckBox.setChecked(True)
        self.computeForGeometricDesignsCheckBox.setEnabled(False)
        self.computeFromPreviousDatesCheckBox.setChecked(True)
        self.savePushButton.clicked.connect(self.save)
        self.qgisPathPushButton.clicked.connect(self.select_qgis_path)
        self.tableWidget.itemDoubleClicked.connect(self.on_click)
        self.tableWidget.itemClicked.connect(self.on_click)
        self.removePushButton.clicked.connect(self.remove)
        self.enablePushButton.clicked.connect(self.enable)
        self.disablePushButton.clicked.connect(self.disable)
        self.processPushButton.clicked.connect(self.process)
        headers = defs_vc.headers
        headers_tooltips = defs_vc.header_tooltips
        self.tableWidget.setColumnCount(len(headers))
        self.tableWidget.setStyleSheet("QHeaderView::section { color:black; background : lightGray; }")
        for i in range(len(headers)):
            header_item = QTableWidgetItem(headers[i])
            header_tooltip = headers_tooltips[i]
            header_item.setToolTip(header_tooltip)
            self.tableWidget.setHorizontalHeaderItem(i, header_item)
        self.tableWidget.setSizeAdjustPolicy(
            QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.tableWidget.setSortingEnabled(True)
        qgis_prefix_path = self.project.get_qgis_prefix_path()
        if qgis_prefix_path:
            self.qgisPathLineEdit.setText(qgis_prefix_path)
        if self.project.qgis_iface is None:
            self.loadInQgisLabel.setEnabled(False)
            self.loadInQgisResultPushButton.setEnabled(False)
            self.loadInQgisFromPushButton.setEnabled(False)
            self.loadInQgisToPushButton.setEnabled(False)
            self.loadInQgisAllPushButton.setEnabled(False)
        else:
            self.loadInQgisLabel.setEnabled(True)
            self.loadInQgisResultPushButton.setEnabled(True)
            self.loadInQgisFromPushButton.setEnabled(True)
            self.loadInQgisToPushButton.setEnabled(True)
            self.loadInQgisAllPushButton.setEnabled(True)
        self.loadInQgisResultPushButton.clicked.connect(self.loadInQgisResult)
        self.loadInQgisFromPushButton.clicked.connect(self.loadInQgisFrom)
        self.loadInQgisToPushButton.clicked.connect(self.loadInQgisTo)
        self.loadInQgisAllPushButton.clicked.connect(self.loadInQgisAll)
        self.update_gui()

    def loadInQgisAll(self):
        self.loadInQgisResult()
        self.loadInQgisTo()
        self.loadInQgisFrom()
        return

    def loadInQgisFrom(self):
        if self.project.qgis_iface is None:
            return
        if len(self.volumes_computations) == 0:
            return
        for i in range(self.tableWidget.rowCount()):
            id_item = self.tableWidget.item(i, 0)
            if id_item.isSelected():
                id = id_item.text()
                if self.volumes_computations[id][defs_vc.FIELD_ENABLED] == 0:
                    continue
                gdp_id = self.volumes_computations[id][defs_vc.FIELD_GDP_ID]
                result_file_path = self.volumes_computations[id][defs_vc.FIELD_RASTER_FILE_FROM]
                result_fp_file_path = self.volumes_computations[id][defs_vc.FIELD_RASTER_FILE_FROM_GEOJSON]
                str_error = self.project.qgis_iface.load_volume(id, gdp_id, result_file_path, result_fp_file_path)
                if str_error:
                    Tools.error_msg(str_error)
        return

    def loadInQgisResult(self):
        if self.project.qgis_iface is None:
            return
        if len(self.volumes_computations) == 0:
            return
        for i in range(self.tableWidget.rowCount()):
            id_item = self.tableWidget.item(i, 0)
            if id_item.isSelected():
                id = id_item.text()
                if self.volumes_computations[id][defs_vc.FIELD_ENABLED] == 0:
                    continue
                gdp_id = self.volumes_computations[id][defs_vc.FIELD_GDP_ID]
                result_file_path = self.volumes_computations[id][defs_vc.FIELD_RASTER_FILE_RESULT]
                result_fp_file_path = self.volumes_computations[id][defs_vc.FIELD_RASTER_FILE_RESULT_GEOJSON]
                str_error = self.project.qgis_iface.load_volume(id, gdp_id, result_file_path, result_fp_file_path)
                if str_error:
                    Tools.error_msg(str_error)
        return

    def loadInQgisTo(self):
        if self.project.qgis_iface is None:
            return
        if len(self.volumes_computations) == 0:
            return
        for i in range(self.tableWidget.rowCount()):
            id_item = self.tableWidget.item(i, 0)
            if id_item.isSelected():
                id = id_item.text()
                if self.volumes_computations[id][defs_vc.FIELD_ENABLED] == 0:
                    continue
                gdp_id = self.volumes_computations[id][defs_vc.FIELD_GDP_ID]
                result_file_path = self.volumes_computations[id][defs_vc.FIELD_RASTER_FILE_TO]
                result_fp_file_path = self.volumes_computations[id][defs_vc.FIELD_RASTER_FILE_TO_GEOJSON]
                str_error = self.project.qgis_iface.load_volume(id, gdp_id, result_file_path, result_fp_file_path)
                if str_error:
                    Tools.error_msg(str_error)
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
        if label == defs_vc.HEADER_DESCRIPTION_TAG:
            text = self.volumes_computations[id][defs_vc.FIELD_DESCRIPTION]
            readOnly = False
            dialog =  SimpleTextEditDialog(title, text, readOnly)
            ret = dialog.exec()
            text = dialog.get_text()
            if text != self.volumes_computations[id][defs_vc.FIELD_DESCRIPTION]:
                self.volumes_computations[id][defs_vc.FIELD_DESCRIPTION] = text
            return
        return

    def process(self):
        if len(self.project.geometric_design_projects) == 0:
            str_error = ('There are no geometric designs projects')
            Tools.error_msg(str_error)
        qgis_prefix_path = self.qgisPathLineEdit.text()
        if not qgis_prefix_path:
            str_error = ('Select QGIS prefix path before')
            Tools.error_msg(str_error)
        computeForDtm = self.computeForDtmCheckBox.isChecked()
        computeForDsm = self.computeForDsmCheckBox.isChecked()
        computeForGeometricDesigns = self.computeForGeometricDesignsCheckBox.isChecked()
        computeFromPreviousDates = self.computeFromPreviousDatesCheckBox.isChecked()
        str_aux_error = self.project.processVolumesComputations(computeForDtm,
                                                                computeForDsm,
                                                                computeForGeometricDesigns,
                                                                computeFromPreviousDates)
        if str_aux_error:
            str_error = ('Error processing volumes computations:\n{}'.
                         format(str_aux_error))
            Tools.error_msg(str_error)
        else:
            str_msg = "Process completed"
            Tools.info_msg(str_msg)
        self.volumes_computations = dict(self.project.volumes_computations)
        self.update_gui()
        return

    def remove(self):
        if len(self.volumes_computations) == 0:
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
            self.volumes_computations.pop(id)
        return

    def save(self):
        self.project.volumes_computations = dict(self.volumes_computations)
        str_aux_error = self.project.save_to_json()
        if str_aux_error:
            str_error = ('Error saving project:\n{}'.
                         format(str_aux_error))
            Tools.error_msg(str_error)
        else:
            str_msg = "Process completed"
            Tools.info_msg(str_msg)
        return

    def select_qgis_path(self):
        dialog = QtWidgets.QFileDialog()
        last_path = self.qgisPathLineEdit.text()
        if not last_path:
            last_path = self.project.settings.value("last_path")
            if not last_path:
                last_path = QDir.currentPath()
                self.settings.setValue("last_path", last_path)
                self.settings.sync()
        dialog.setDirectory(last_path)
        qgis_prefix_path = dialog.getExistingDirectory(self, "Select QGIS path")
        if qgis_prefix_path:
            str_aux_error = self.project.set_qgis_prefix_path(qgis_prefix_path) # inside set in settings
            if str_aux_error:
                str_error = ('Error setting QGIS path:\n{}'.format(str_aux_error))
                Tools.error_msg(str_error)
            else:
                self.qgisPathLineEdit.setText(qgis_prefix_path)
        return

    def update_gui(self):
        self.tableWidget.setRowCount(0)
        for id in self.volumes_computations:
            rowPosition = self.tableWidget.rowCount()
            self.tableWidget.insertRow(rowPosition)
            # id
            id_item = QTableWidgetItem(id)
            id_item.setTextAlignment(Qt.AlignCenter)
            column_pos = 0
            self.tableWidget.setItem(rowPosition, column_pos, id_item)
            # gdp_id
            gdp_id = self.volumes_computations[id][defs_vc.FIELD_GDP_ID]
            gdp_id_item = QTableWidgetItem(gdp_id)
            gdp_id_item.setTextAlignment(Qt.AlignCenter)
            column_pos = column_pos + 1
            self.tableWidget.setItem(rowPosition, column_pos, gdp_id_item)
            # enabled
            str_enabled = 'True'
            if self.volumes_computations[id][defs_vc.FIELD_ENABLED] == 0:
                str_enabled = 'False'
            enabled_item = QTableWidgetItem(str_enabled)
            enabled_item.setTextAlignment(Qt.AlignCenter)
            column_pos = column_pos + 1
            self.tableWidget.setItem(rowPosition, column_pos, enabled_item)
            # date from
            crs_id = self.volumes_computations[id][defs_vc.FIELD_VOLUME_DATE_FROM]
            crs_id_item = QTableWidgetItem(crs_id)
            crs_id_item.setTextAlignment(Qt.AlignCenter)
            column_pos = column_pos + 1
            self.tableWidget.setItem(rowPosition, column_pos, crs_id_item)
            # date to
            date_to = self.volumes_computations[id][defs_vc.FIELD_VOLUME_DATE_TO]
            date_to_item = QTableWidgetItem(date_to)
            date_to_item.setTextAlignment(Qt.AlignCenter)
            column_pos = column_pos + 1
            self.tableWidget.setItem(rowPosition, column_pos, date_to_item)
            # type
            type = self.volumes_computations[id][defs_vc.FIELD_VOLUME_TYPE]
            type_item = QTableWidgetItem(type)
            type_item.setTextAlignment(Qt.AlignCenter)
            column_pos = column_pos + 1
            self.tableWidget.setItem(rowPosition, column_pos, type_item)
            # crs
            crs_id = self.volumes_computations[id][defs_vc.FIELD_CRS]
            crs_id_item = QTableWidgetItem(crs_id)
            crs_id_item.setTextAlignment(Qt.AlignCenter)
            column_pos = column_pos + 1
            self.tableWidget.setItem(rowPosition, column_pos, crs_id_item)
            # raster file results
            raster_results = self.volumes_computations[id][defs_vc.FIELD_RASTER_FILE_RESULT]
            raster_results_item = QTableWidgetItem(raster_results)
            raster_results_item.setTextAlignment(Qt.AlignCenter)
            column_pos = column_pos + 1
            self.tableWidget.setItem(rowPosition, column_pos, raster_results_item)
            # raster file from
            raster_file_from = self.volumes_computations[id][defs_vc.FIELD_RASTER_FILE_FROM]
            raster_file_from_item = QTableWidgetItem(raster_file_from)
            raster_file_from_item.setTextAlignment(Qt.AlignCenter)
            column_pos = column_pos + 1
            self.tableWidget.setItem(rowPosition, column_pos, raster_file_from_item)
            # raster file to
            raster_file_to = self.volumes_computations[id][defs_vc.FIELD_RASTER_FILE_TO]
            raster_file_to_item = QTableWidgetItem(raster_file_to)
            raster_file_to_item.setTextAlignment(Qt.AlignCenter)
            column_pos = column_pos + 1
            self.tableWidget.setItem(rowPosition, column_pos, raster_file_to_item)
            # description
            # description = self.geometric_design_projects[id][defs_gdp.FIELD_DESCRIPTION]
            description = defs_vc.RESUME_CONTENT
            description_item = QTableWidgetItem(description)
            description_item.setTextAlignment(Qt.AlignCenter)
            column_pos = column_pos + 1
            self.tableWidget.setItem(rowPosition, column_pos, description_item)
        self.tableWidget.resizeColumnsToContents()
        return