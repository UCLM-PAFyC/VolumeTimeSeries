# authors:
# David Hernandez Lopez, david.hernandez@uclm.es

import os
from qgis.PyQt.uic import loadUi
from qgis.PyQt.QtWidgets import QDialog, QFileDialog
from qgis.PyQt.QtCore import QDir, QFileInfo

current_path = os.path.dirname(os.path.realpath(__file__))

from core.Project import Project

from pyLibQtTools import Tools

class VolumeTimeSeriesDialog(QDialog):
    """Employee dialog."""

    def __init__(self,
                 settings,
                 main_path,
                 parent=None):
        super().__init__(parent)
        loadUi(os.path.join(os.path.dirname(__file__), 'VolumeTimeSeriesDialog.ui'), self)
        self.settings = settings
        self.main_path = main_path
        self.project = None
        self.widget_project_definitions = None
        self.qgis_iface = None
        self.app_path = current_path
        self.last_path = None
        self.initialize()

    def close_qgis(self):
        if self.qgis_iface is None:
            return
        if self.project is None:
            return
        str_error = self.project.close_qgis()
        if str_error:
            str_error = ('Error closing project:\n{}'.format(str_error))
            Tools.error_msg(str_error)
            return
        self.closeProjectQgisPushButton.setEnabled(False)
        self.openProjectQgisPushButton.setEnabled(True)

    def create_project(self, file_path):
        str_error = ''
        self.project = Project(self.qgis_iface,
                               self.settings,
                               self.app_path)
        self.project.file_path = file_path
        is_process_creation = True
        definition_is_saved = False
        while not definition_is_saved:
            definition_is_saved = self.project_definition(is_process_creation)
            if not definition_is_saved:
                str_error = ('Project definition must be save')
                str_error += '\n{}'.format("CRSs definition cannot will be changed")
                Tools.error_msg(str_error)
        if self.project.qgis_iface is not None:
            qgis_prefix_path = self.project.qgis_iface.get_qgis_prefix_path()
            str_aux_error = self.project.set_qgis_prefix_path(qgis_prefix_path)
            if str_aux_error:
                str_error = ('Error setting QGIS paths:\n{}'.format(str_aux_error))
                Tools.error_msg(str_error)
        else:
            qgis_prefix_path = self.settings.value("qgis_prefix_path")
            if qgis_prefix_path:
                str_aux_error = self.project.set_qgis_prefix_path(qgis_prefix_path)
                if str_aux_error:
                    str_error = ('Error setting QGIS paths:\n{}'.format(str_aux_error))
                    Tools.error_msg(str_error)
        return str_error

    def geometric_design_projects(self):
        if not self.project:
            str_error = ('Not exists project')
            Tools.error_msg(str_error)
            return
        str_error = self.project.geometric_design_projects_gui(self)
        if str_error:
            str_error = ('Geometric design project, error:\n{}'.format(str_error))
            Tools.error_msg(str_error)
            return
        return

    def initialize(self):
        self.last_path = self.settings.value("last_path")
        current_dir = QDir.current()
        if not self.last_path:
            self.last_path = QDir.currentPath()
            self.settings.setValue("last_path", self.last_path)
            self.settings.sync()
        self.projectFilePushButton.clicked.connect(self.select_project_file)
        self.projectDefinitionPushButton.clicked.connect(self.project_definition)
        self.photogrammetryProjectsPushButton.clicked.connect(self.photogrammetry_projects)
        self.geometricDesignProjectsPushButton.clicked.connect(self.geometric_design_projects)
        self.saveProjectPushButton.clicked.connect(self.save_project)
        self.volumesComputationsPushButton.clicked.connect(self.volumes_computations)
        self.tabWidget.setEnabled(False)
        self.saveProjectPushButton.setEnabled(False)
        self.updateQGISPushButton.clicked.connect(self.update_qgis)
        self.openProjectQgisPushButton.setVisible(False)
        self.openProjectQgisPushButton.setEnabled(False)
        self.updateQGISPushButton.setVisible(False)
        self.updateQGISPushButton.setEnabled(False)
        self.openProjectQgisPushButton.clicked.connect(self.open_qgis)
        self.closeProjectQgisPushButton.clicked.connect(self.close_qgis)
        return

    def open_qgis(self):
        if self.qgis_iface is None:
            return
        if self.project is None:
            return
        str_error = self.project.open_qgis()
        if str_error:
            str_error = ('Error opening project:\n{}'.format(str_error))
            Tools.error_msg(str_error)
            return
        self.closeProjectQgisPushButton.setEnabled(True)
        self.openProjectQgisPushButton.setEnabled(False)

    def open_project(self, file_name):
        str_error = ''
        self.project = Project(self.qgis_iface,
                               self.settings,
                               self.app_path)
        if self.project.qgis_iface is not None:
            qgis_prefix_path = self.project.qgis_iface.get_qgis_prefix_path()
            str_aux_error = self.project.set_qgis_prefix_path(qgis_prefix_path)
            if str_aux_error:
                str_error = ('Error setting QGIS paths:\n{}'.format(str_aux_error))
                Tools.error_msg(str_error)
        else:
            qgis_prefix_path = self.settings.value("qgis_prefix_path")
            if qgis_prefix_path:
                str_aux_error = self.project.set_qgis_prefix_path(qgis_prefix_path)
                if str_aux_error:
                    str_error = ('Error setting QGIS paths:\n{}'.format(str_aux_error))
                    Tools.error_msg(str_error)
        str_error = self.project.set_from_json(file_name)
        return str_error

    def photogrammetry_projects(self):
        if not self.project:
            str_error = ('Not exists project')
            Tools.error_msg(str_error)
            return False
        str_error = self.project.photogrammetry_projects_gui(self)
        if str_error:
            str_error = ('Photogrammetry Projects, error:\n{}'.format(str_error))
            Tools.error_msg(str_error)
            return False
        return

    def project_definition(self,
                           is_process_creation = False):
        if not self.project:
            str_error = ('Not exists project')
            Tools.error_msg(str_error)
            return False
        str_error, definition_is_saved = self.project.project_definition_gui(is_process_creation)
        if str_error:
            str_error = ('Project definition, error:\n{}'.format(str_error))
            Tools.error_msg(str_error)
            return False
        return definition_is_saved

    def save_project(self):
        str_error = self.project.save_to_json()
        if str_error:
            # self.project_definition()
            str_error = ('Saving project, error:\n{}'.format(str_error))
            Tools.error_msg(str_error)
            return
        else:
            str_msg = "Process completed"
            Tools.info_msg(str_msg)
        return

    def select_project_file(self):
        title = "Select Project File"
        previous_file = self.projectLineEdit.text()
        dlg = QFileDialog(self)
        dlg.setDirectory(self.last_path)
        dlg.setFileMode(QFileDialog.AnyFile)
        dlg.setNameFilter("Project File (*.json)")
        if dlg.exec_():
            file_names = dlg.selectedFiles()
            file_name = file_names[0]
        else:
            return
        # fileName, aux = QFileDialog.getSaveFileName(self, title, self.path, "Project File (*.json)")
        if file_name:
            self.projectLineEdit.setText(file_name)
            self.last_path = QFileInfo(file_name).absolutePath()
            self.settings.setValue("last_path", self.last_path)
            self.settings.sync()
            self.tabWidget.setEnabled(False)
            self.saveProjectPushButton.setEnabled(False)
            # self.projectDefinitionPushButton.setEnabled(False)
            if os.path.exists(file_name):
                str_error = self.open_project(file_name)
                if str_error:
                    Tools.error_msg(str_error)
                    return
            else:
                if not file_name.endswith(".json"):
                    file_name += ".json"
                self.create_project(file_name)
            if not self.project:
                return
            self.tabWidget.setEnabled(True)
            self.saveProjectPushButton.setEnabled(True)
            if self.qgis_iface:
                self.qgis_iface.open_project(self.project)
                self.updateQGISPushButton.setEnabled(True)
                self.closeProjectQgisPushButton.setEnabled(True)
                self.openProjectQgisPushButton.setEnabled(False)
            # self.projectDefinitionPushButton.setEnabled(True)
        return

    def set_qgis_iface(self, qgis_iface):
        self.qgis_iface = qgis_iface
        if self.qgis_iface is not None:
            self.openProjectQgisPushButton.setVisible(True)
            self.openProjectQgisPushButton.setEnabled(False)
            self.closeProjectQgisPushButton.setVisible(True)
            self.closeProjectQgisPushButton.setEnabled(False)
        else:
            self.openProjectQgisPushButton.setVisible(False)
            self.openProjectQgisPushButton.setEnabled(False)
            self.closeProjectQgisPushButton.setVisible(False)
            self.closeProjectQgisPushButton.setEnabled(False)

    def update_qgis(self):
        if not self.qgis_iface:
            return
        # str_error = self.qgis_iface.update_all()
        # if str_error:
        #     str_error += ('Updating QGIS, error:\n{}'.format(str_error))
        #     Tools.error_msg(str_error)
        return

    def volumes_computations(self):
        if not self.project:
            str_error = ('Not exists project')
            Tools.error_msg(str_error)
            return False
        str_error = self.project.volumes_computations_gui(self)
        if str_error:
            str_error = ('Volumes Computations, error:\n{}'.format(str_error))
            Tools.error_msg(str_error)
            return False
        return

