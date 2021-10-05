# UPbplot

A copy of Atsushi Noda's [UPbplot](https://github.com/anoda/UPbplot.py). 

# spine

A slightly modified version of Roger Powell's ["Robust isochron calculation"](https://gchron.copernicus.org/articles/2/325/2020/) routine.

# QCustomPlot

Most of the plotting in Chronosaurus is done using QCustomPlot (QCP). It is preferred because it is significantly faster than matplotlib (thus making the user interface more responsive) while also outputing high quality plots suitable for publication. Note that matplotlib can be used in plugins but is not recommended for plots that may involve a lot of data.

Precompiled QCP python modules and accompanying dynamic libraries can be found in the Darwin/Linux/Windows subfolders. These were built with Qt 5.15 and python 3.8. Each was built essentially following [this guide](https://github.com/SBGit-2019/Pyside-QCP). Note that this wrapper does not cover the full QCustomPlot API at this time. Additionally, there are some quirks in the python wrapper such that you must manually increase the reference count of certain plot elements. For example:
```python
from QCustomPlot import *
plot = QCustomPlot()
textItem = QCPItemText(plot)
plot.incref(textItem) # Without this = crash
```