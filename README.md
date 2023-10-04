# VPDSeasonalCorr
Code to explore correlations between tree-ring oxygen-isotope ratios and climate variables of various seasons

Description
This package was written to calculate correlations between european oxigen isotope ratios 
from treerings and CRU climate variables corresponding to the sites.
The data used is in the subdirectory data.
The following python modules are present:
- data.py Support for handling CRU timeseries and O18 time series.
- data_defs.py Declaration of which data will be processed: sites, climate variables, time range. Edit this file to restric date, sites or climat variables.
- seasons.py Support for generating all possible seasons.
- heatmap.py Calculate heatmaps for for the data declared in data_defs
- sitecorr.py Calculate all site correlations for all climate variables for the standard seasons

Usage
You need a machine where R is installed and have a standard python distribution with the module rpy2.
As a preparation, you need to make sure that rpy2 can find R.
On Windows you can do this by setting the environment variable R_USER to point to your R installation.

Run 
        python sitecorr.py
to calculate correlations for all sites and seasons between climat variables and oxygen isotope ratio. A separate file with statistics for the main season is also calculated.

Run
        python heatmap.py
to get heatmap data.

All generated files have the timestamp of the run in the name, so that no files will be overwritten upon consecutive runs.



