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
RESUME_CONTENT = "Click to view"

AXIS_POINTS_DISTANCE = 10.0

FORMAT_LANDXML = 'LandXml'
FORMAT_LANDXML_EXTENSION = 'xml'
extension_by_format = {}
extension_by_format[FORMAT_LANDXML] = FORMAT_LANDXML_EXTENSION

FIELD_ID = "Id"
FIELD_ENABLED = "Enabled"
FIELD_DESCRIPTION = "Description"
FIELD_CRS = "CRS"
FIELD_CONTENT = "Content"
FIELD_AXIS3D = "Axis 3D"
FIELD_PROFILE = "Profile"
FIELD_TRIANGULATION_PLY = "Triangulation PLY"
FIELD_SOURCE_FILE = "Source file"
FIELD_TRIANGULATION_POINTS = "Triangulation Points"
FIELD_TRIANGULATION_TRIANGLES = "Triangulation Triangles"
fields = [FIELD_ID, FIELD_ENABLED, FIELD_DESCRIPTION,
          FIELD_CRS, FIELD_CONTENT, FIELD_AXIS3D, FIELD_PROFILE,
          FIELD_TRIANGULATION_PLY, FIELD_SOURCE_FILE,
          FIELD_TRIANGULATION_TRIANGLES, FIELD_TRIANGULATION_POINTS]
HEADER_ID_TAG = FIELD_ID
HEADER_ENABLED_TAG = FIELD_ENABLED
HEADER_DESCRIPTION_TAG = FIELD_DESCRIPTION
HEADER_CRS_TAG = FIELD_CRS
HEADER_CONTENT_TAG = FIELD_CONTENT
HEADER_AXIS3D_TAG = FIELD_AXIS3D
HEADER_PROFILE_TAG = FIELD_PROFILE
HEADER_TRIANGULATION_PLY_TAG = FIELD_TRIANGULATION_PLY
HEADER_SOURCE_FILE_TAG = FIELD_SOURCE_FILE
headers = [HEADER_ID_TAG,
           HEADER_ENABLED_TAG,
           HEADER_DESCRIPTION_TAG,
           HEADER_CRS_TAG,
           HEADER_CONTENT_TAG,
           HEADER_AXIS3D_TAG,
           HEADER_PROFILE_TAG,
           HEADER_TRIANGULATION_PLY_TAG,
           HEADER_SOURCE_FILE_TAG]
HEADER_ID_TOOLTIP = "Geometric design project identifier"
HEADER_ENABLE_TOOLTIP = "Enabled"
HEADER_DESCRIPTION_TOOLTIP = "Description"
HEADER_CRS_TOOLTIP = "CRS"
HEADER_CONTENT_TOOLTIP = "Content as JSON"
HEADER_AXIS3D_TOOLTIP = "Axis 3D as WKT"
HEADER_PROFILE_TOOLTIP = "Profile as WKT: cumulative distance and height"
HEADER_TRIANGULATION_PLY = "Triangulation as PLY"
HEADER_SOURCE_FILE_TOOLTIP = "Source file"
header_tooltips = [HEADER_ID_TOOLTIP,
                   HEADER_ENABLE_TOOLTIP,
                   HEADER_DESCRIPTION_TOOLTIP,
                   HEADER_CRS_TOOLTIP,
                   HEADER_CONTENT_TOOLTIP,
                   HEADER_AXIS3D_TOOLTIP,
                   HEADER_PROFILE_TOOLTIP,
                   HEADER_TRIANGULATION_PLY,
                   HEADER_SOURCE_FILE_TOOLTIP]

