# authors:
# David Hernandez Lopez, david.hernandez@uclm.es
import os
import sys

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(current_path, '..'))

from VolumeTimeSeries.defs import defs_paths, defs_project
from VolumeTimeSeries.defs import defs_geometric_design_projects as defs_gdp
common_libs_absolute_path = os.path.join(current_path, defs_paths.COMMON_LIBS_RELATIVE_PATH)
sys.path.append(common_libs_absolute_path)

DIALOG_TITLE = "Volumes Computations"
# CONST_NO_COMBO_SELECT = " ... "
# CONST_NO_COMBO_SELECT = " ... "
RESUME_CONTENT = "Click to view"

VOLUME_TYPE_DTMS_DIFFERENCE = "DTMSs DIFFERENCE"
VOLUME_TYPE_DSMS_DIFFERENCE = "DSMs DIFFERENCE"
VOLUME_TYPE_GD_DTM_DIFFERENCE = "GD-DTM"
VOLUME_TYPE_GD_DSM_DIFFERENCE = "GD-DSM"
VOLUME_DATE_FROM = "DATE FROM"
VOLUME_DATE_TO = "DATE TO"


