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

    def initialize(self):
        self.last_path = self.project.settings.value("last_path")
        current_dir = QDir.current()
        if not self.last_path:
            self.last_path = QDir.currentPath()
            self.project.settings.setValue("last_path", self.last_path)
            self.project.settings.sync()
        # deep copy using the dict() constructor
        self.volumes_computations = dict(self.project.volumes_computations)
