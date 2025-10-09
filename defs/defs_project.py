# authors:
# David Hernandez Lopez, david.hernandez@uclm.es
import os
import sys

current_path = os.path.dirname(__file__)
sys.path.append(os.path.join(current_path, '..'))

from VolumeTimeSeries.defs import defs_paths
common_libs_absolute_path = os.path.join(current_path, defs_paths.COMMON_LIBS_RELATIVE_PATH)
sys.path.append(common_libs_absolute_path)
from pyLibCRSs import CRSsDefines as defs_crs
from pyLibGDAL import defs_gdal

CRS_PROJECTED_DEFAULT = "EPSG:25830"
CRS_VERTICAL_DEFAULT = "EPSG:5782"


PROJECT_DEFINITION_DIALOG_TITLE = "Project Definition"
PROJECT_DEFINITIONS_MANAGEMENT_FIELD_NAME = "Project Definition"
PROJECT_DEFINITIONS_TAG = "ProjectDefinition"
PROJECT_DEFINITIONS_TAG_NAME = "Name"
PROJECT_DEFINITIONS_TAG_TAG = "Tag"
PROJECT_DEFINITIONS_TAG_AUTHOR = "Author"
# PROJECT_DEFINITIONS_TAG_GEO3D_CRS = defs_crs.CRS_GEODETIC_3D_LABEL
# PROJECT_DEFINITIONS_TAG_GEO2D_CRS = defs_crs.CRS_GEODETIC_2D_LABEL
# PROJECT_DEFINITIONS_TAG_ECEF_CRS = defs_crs.CRS_ECEF_LABEL
PROJECT_DEFINITIONS_TAG_PROJECTED_CRS = defs_crs.CRS_PROJECTED_LABEL
PROJECT_DEFINITIONS_TAG_VERTICAL_CRS = defs_crs.CRS_VERTICAL_LABEL
PROJECT_DEFINITIONS_TAG_OUTPUT_PATH = "OutputPath"
PROJECT_DEFINITIONS_TAG_DESCRIPTION = "Description"
PROJECT_DEFINITIONS_TAG_START_DATE = "StartDate"
PROJECT_DEFINITIONS_TAG_FINISH_DATE = "FinishDate"

PROJECT_GEOMETRIC_DESIGNS_TAG = "GeometricDesigns"
