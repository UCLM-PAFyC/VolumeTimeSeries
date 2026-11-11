# **VolumeTimeSeries - QGIS**

## A plugin to compute volume change in time series

This plugin works in Windows and QGIS version from 3.40.10-1:
https://download.osgeo.org/qgis/win64/QGIS-OSGeo4W-3.40.10-1.msi

## **David Hernández López**

Professor of Geomatics

University of Castilla-La Mancha - UCLM, 
david.hernandez@uclm.es

University of Salamanca - USAL, 
dhernand@usal.es

ORCID, [https://orcid.org/0000-0001-9874-5243](https://orcid.org/0000-0001-9874-5243)

**Research groups:**

UCLM - PAFyC, [http://pafyc.uclm.es](http://pafyc.uclm.es)

USAL - TIDOP, [http://tidop.usal.es](http://tidop.usal.es)

Any use of this version is allowed without 
responsibility for the author

Please report any bugs and enhancement ideas by email: david.hernandez@uclm.es

Contact the author to request any custom development or migration to other operating systems 

Current functionalities:
- Create Project
- Import data geometry of interest (LandXml)
- Build triangulation and mesh of data geometry
- Import DEMs and orthoimages time series
- Compute data geometry volume for a DEM 
- ...

To do ...
- Create a user manual

Install libraries:
OSGeo4W console:
- pyLibQtTools
cd E:\dev\python\lib\pyLibQtTools
pip install -e E:\dev\python\lib\pyLibQtTools
- pyLibCRSs
cd E:\dev\python\lib\pyLibCRSs
pip install -e E:\dev\python\lib\pyLibCRSs
- pyLibGDAL
cd E:\dev\python\lib\pyLibGDAL
pip install -e E:\dev\python\lib\pyLibGDAL
- pyLibProcesses
cd E:\dev\python\lib\pyLibProcesses
pip install -e E:\dev\python\lib\pyLibProcesses
- pyLibProject
cd E:\dev\python\lib\pyLibProject
pip install -e E:\dev\python\lib\pyLibProject
- pyLibQGIS
cd E:\dev\python\lib\pyLibQGIS
pip install -e E:\dev\python\lib\pyLibQGIS
- pyLibParameters
cd E:\dev\python\lib\pyLibParameters
pip install -e E:\dev\python\lib\pyLibParameters


