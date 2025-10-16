# authors:
# David Hernandez Lopez, david.hernandez@uclm.es
import os
import sys

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(current_path, '..'))
# sys.path.insert(0, '..')

IMAGES_PATH = "images"
VOLUMETIMESERIES_ICON_FILE = "VolumeTimeSeries.ico"
QDATE_TO_STRING_FORMAT = "yyyy:MM:dd"
TIME_STRING_FORMAT = "%H:%M:%S.%f"
DATE_STRING_FORMAT = "yyyy:MM:dd"
DATE_TIME_STRING_FORMAT = "%Y%m%d %H:%M:%S"
QDATETIME_TO_STRING_FORMAT_FOR_FILE_NAME = "yyyyMMdd_hhmmss"
TEMPLATES_PATH = "templates"
SETTINGS_FILE = "settings.ini"
NO_COMBO_SELECT = " ... "
EPSG_STRING_PREFIX = "EPSG:"
CONST_SELECT_IMAGES_FILES_DIALOG_TITLE = "Select Image Files"
CONST_SELECT_UNDISTORT_IMAGES_FILES_DIALOG_TITLE = "Select Undistort Image Files"
CONST_DOCUMENTS_TYPE_JPG = "jpg"
CONST_DOCUMENTS_TYPE_TIF = "tif"
CONST_DOCUMENTS_TYPE_TIFF = "tiff"




