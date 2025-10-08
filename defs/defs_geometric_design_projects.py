# authors:
# David Hernandez Lopez, david.hernandez@uclm.es
import os
import sys

current_path = os.path.dirname(__file__)
sys.path.append(os.path.join(current_path, '..'))

from VolumeTimeSeries.defs import defs_paths, defs_project
common_libs_absolute_path = os.path.join(current_path, defs_paths.COMMON_LIBS_RELATIVE_PATH)
sys.path.append(common_libs_absolute_path)

DIALOG_TITLE = "Geometric Design Projects"
CONST_NO_COMBO_SELECT = " ... "

FORMAT_LANDXML = 'LandXml'
FORMAT_LANDXML_EXTENSION = 'xml'
extension_by_format = {}
extension_by_format[FORMAT_LANDXML] = FORMAT_LANDXML_EXTENSION

HEADER_ID_TAG = "Id"
HEADER_ENABLED_TAG = "Enabled"
HEADER_CONTENT_TAG = "Content"
HEADER_TRIANGULATION_PLY_TAG = "Triangulation PLY"
HEADER_SOURCE_FILE_TAG = "Source file"
HEADER_DESCRIPTION_TAG = "Description"
headers = [HEADER_ID_TAG,
           HEADER_ENABLED_TAG,
           HEADER_CONTENT_TAG,
           HEADER_TRIANGULATION_PLY_TAG,
           HEADER_SOURCE_FILE_TAG]
HEADER_ID_TOOLTIP = "Geometric design project identifier"
HEADER_ENABLE_TOOLTIP = "Enabled"
HEADER_CONTENT_TOOLTIP = "Content as JSON"
HEADER_TRIANGULATION_PLY = "Triangulation PLY"
HEADER_SOURCE_FILE_TOOLTIP = "Source file"
header_tooltips = [HEADER_ID_TOOLTIP,
                   HEADER_ENABLE_TOOLTIP,
                   HEADER_CONTENT_TOOLTIP,
                   HEADER_TRIANGULATION_PLY,
                   HEADER_SOURCE_FILE_TOOLTIP]

