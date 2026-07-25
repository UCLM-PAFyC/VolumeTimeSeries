# authors:
# David Hernandez Lopez, david.hernandez@uclm.es

import sys, os
from qgis.PyQt.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QApplication

from vts_gui.VolumeTimeSeriesDialog import VolumeTimeSeriesDialog
from vts_defs import defs_main

def main():
    app = QApplication(sys.argv)
    current_path = os.path.dirname(os.path.realpath(__file__))
    path_file_qsettings = current_path + "/" + defs_main.SETTINGS_FILE
    settings = QSettings(path_file_qsettings, QSettings.IniFormat)
    dialog = VolumeTimeSeriesDialog(settings, current_path)
    icon_path = current_path + "/" + defs_main.IMAGES_PATH + "/" + defs_main.VOLUMETIMESERIES_ICON_FILE
    dialog.setWindowIcon(QIcon(icon_path))
    dialog.show()
    app.exec()


if __name__ == '__main__':
    main()
