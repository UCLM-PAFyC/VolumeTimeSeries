# authors:
# David Hernandez Lopez, david.hernandez@uclm.es

import sys, os
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

current_path = os.path.dirname(__file__)
sys.path.append(os.path.join(current_path, '..'))
# sys.path.insert(0, '..')

from VolumeTimeSeries.gui.VolumeTimeSeriesDialog import VolumeTimeSeriesDialog
from VolumeTimeSeries.defs import defs_main
# import Tools


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
