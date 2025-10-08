@echo off
SETLOCAL
set OSGEO4W_ROOT=C:/Program Files/QGIS 3.40.10
call "%OSGEO4W_ROOT%\bin\o4w_env.bat"
start pythonw .\VolumeTimeSeriesApp.py
REM start /B python .\TopographicSurveyNetworkApp.py
ENDLOCAL
