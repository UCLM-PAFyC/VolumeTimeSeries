# authors:
# David Hernandez Lopez, david.hernandez@uclm.es

import os
import sys
import math
import pathlib

from PyQt5 import QtCore, QtWidgets
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import (QApplication, QMessageBox, QDialog, QInputDialog,
                             QFileDialog, QPushButton, QComboBox, QPlainTextEdit, QLineEdit,
                             QDialogButtonBox, QVBoxLayout, QTableWidget, QTableWidgetItem)
from PyQt5.QtCore import QDir, QFileInfo, QFile, QSize, Qt

current_path = os.path.dirname(__file__)
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
        self.title = title
        self.setWindowTitle(title)
        self.formats = None
        self.initialize()

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

    def import_file(self):
        return

    def initialize(self):
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

        headers = defs_gdp.headers
        headers_tooltips = defs_gdp.header_tooltips
        self.tableWidget.setColumnCount(len(headers))
        self.tableWidget.setStyleSheet("QHeaderView::section { color:black; background : lightGray; }")
        for i in range(len(headers)):
            header_item = QTableWidgetItem(headers[i])
            header_tooltip = headers_tooltips[i]
            header_item.setToolTip(header_tooltip)
            self.tableWidget.setHorizontalHeaderItem(i, header_item)

        self.update_gui()
        return

    def save(self):
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

    def update_gui(self):
        return