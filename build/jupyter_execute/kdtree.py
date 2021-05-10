#!/usr/bin/env python
# coding: utf-8

# 
# # Datasets
# 
# The Datasets are divided up by their model domain

# ## Model Domains
# 
# The FWF model resolves the FWI System/ FBP System in the D02 (12 km) and D03 (4 km) at 55 hour forecast horizon.
# 
# ![title](_static/images/fwf-model-domains.png)

# ### Description
# 
# For each domain there are two `.nc` (netcdf) files generated, four total datasets each day.
# 
# **Domain: d02 (12 km)**
# -  `fwf-hourly-d02-YYYYMMDDHH.nc`
#     - File Size: ~ 780M
#     - File Dimensions: (time: 55, south_north: 417, west_east: 627)
# -  `fwf-daily-d02-YYYYMMDDHH.nc`
#     - File Size: ~ 16M
#     - File Dimensions: (time: 2, south_north: 417, west_east: 627)
# 
# 
# **Domain: d03 (4 km)**
# -  `fwf-hourly-d03-YYYYMMDDHH.nc`
#     - File Size:  ~ 1.7G
#     - File Dimensions: (time: 55, south_north: 840, west_east: 642)
# -  `fwf-daily-d03-YYYYMMDDHH.nc`
#     - File Size: ~ 30M
#     - File Dimensions: (time: 2, south_north: 840, west_east: 642)
# 
# 
# ### Dataset Variables
# 
# Regardless of Domain, each dataset hourly/daily contain the following variables.

# | Hourly Dataset <br> `fwf-hourly-<domain>-YYYYMMDDHH.nc`  | Daily Dataset <br> `fwf-daily-<domain>--YYYYMMDDHH.nc`  | 
# | --------------------------- | ------------------------- |
# |**Time**: Hourly UTC  |**Time**: Noon Local for that Day |
# |**XLAT**: Degrees Latitude  |**XLAT**: Degrees Latitude|
# |**XLON**: Degrees Longitude  |**XLON**: Degrees Longitude|
# |**F**: Fine Fuel Moisture Code  |**P**: Duff Moisture Code  |
# |**m_o**: Fine Fuel Moisture Content  |**D**: Drought Moisture Code  |
# |**R**: Initial Spread Index   |**U**: Build Up Index   |
# |**S**: Fire Weather Index|**T**: 2 meter Temperature C |
# |**DSR**: Daily Severity Rating  | **TD**: 2 meter Dew Point Temperature C |
# |**FMC**: Foliar Moisture Content %  | **H**: 2 meter Relative Humdity %  |
# |**SFC**: Surface Fuel Consumption kg m^{-2}  | **W**: 10 meter Wind Speed km/h |
# |**TFC**: Total Fuel Consumption kg m^{-2} | **WD**: 10 meter Wind Direction deg  |
# |**ROS**: Rate of Spread m min^{-1}  | **r_o**: Total Accumulated Precipitation mm  |
# |**CFB**: Crown Fraction Burned % | **r_o_tomorrow**: Carry Over Precipitation mm  |
# |**HFI**: Head Fire Intensity  kW m^{-1} |**SNOWC**: Flag Inidicating Snow <br> Cover (1 for Snow Cover) Snow Depth m   |
# |**T**: 2 meter Temperature C  |   |
# |**TD**: 2 meter Dew Point Temperature C  | |
# |**H**: 2 meter Relative Humdity % |  |
# |**W**: 10 meter Wind Speed km/h  |  |
# |**WD**: 10 meter Wind Direction deg  |   |
# |**U10**:  U Component of Wind at 10 meter m/s  | |
# |**V10**: V Component of Wind at 10 meter m/s  |   |
# |**r_o**: Total Accumulated Precipitation mm  |   |
# |**r_o_hourly**: Hourly Accumulated Precipitation mm  |  |
# |**SNW**: Total Accumulated Snow cm  |   |
# |**SNOWH**: Physical Snow Depth m  |   |
# |**SNOWC**: Flag Indicating Snow <br> Cover (1 for Snow Cover) Snow Depth m  |   |

# ## Working with
# 
# Suggest using [xarray](http://xarray.pydata.org/en/stable/) to open and work with data.
# 
# An example of how to open and view 

# In[1]:


import context
import numpy as np
import xarray as xr
from context import data_dir, fwf_dir

forecast_date = '2021051006'  ## "YYYYMMDDHH"
domain        = 'd02'         ## or 'd03'
name 	        = 'hourly'      ## or 'daily'

## file directory
filein = str(fwf_dir) + f"/fwf-{name}-{domain}-{forecast_date}.nc"

## open dataset
ds = xr.open_dataset(filein)

## chunk data to dask.arrays 
ds = ds.chunk(chunks="auto")
ds = ds.unify_chunks()
# NOTE this is not needed. Arrays will be either numpy float32 or objects

## Example: look at variable F (Fine Fuels Moisture Code)
print(ds.F)


# # How to search the FWF data set by locations

# In[ ]:


import context
import pickle
import numpy as np
import pandas as pd
import xarray as xr
from sklearn.neighbors import KDTree


from pathlib import Path

from context import data_dir, fwf_dir
from datetime import datetime, date, timedelta


# ## Set Up
# Define forecast date, domain and set paths to dataset

# In[ ]:



forecast_date = '2021051006'  ## "YYYYMMDDHH"
domain        = 'd02'         ## or 'd03'
name 	        = 'hourly'      ## or 'daily'

## set path to gridded forecast dataset
filein = str(fwf_dir) + f"/fwf-{name}-{domain}-{forecast_date}.nc"


# Open forecast dataset and print 

# In[ ]:


## open forecast dataset
ds = xr.open_dataset(filein)

## take a look inside
print(ds)


# Load a data set of weather sation locations and look at the first four rows as an example

# In[ ]:


## load a data set of weather sation locations
df = pd.read_csv(str(data_dir) + "/nrcan-wxstations.csv", sep=",", usecols = ['wmo',	'lat',	'lon'])

## look at the first four wxstation in dataframe as example
print(df.head())


# 
# ## Set up to build a kdtree

# In[ ]:


## first, set path to store kdtree
kdtree_dir = Path(str(data_dir) + "/kdtree/")

## make directory if it doesn't exist 
kdtree_dir.mkdir(parents=True, exist_ok=True)

## now take gridded lats and long and convert to np arrays
XLAT, XLONG = ds.XLAT.values, ds.XLONG.values

## get shape of gridded domain
shape = XLAT.shape
print(shape)


# ## Build a kdtree and save

# In[ ]:


try:
  ## try and open kdtree for domain
  fwf_tree, fwf_locs = pickle.load(open(str(kdtree_dir) + f'fwf_{domain}_tree.p', "rb"))
  print('Found FWF Tree')
except:
  ## build a kd-tree for fwf domain if not found
  print("Could not find FWF KDTree building....")
  ## create dataframe with columns of all lat/long in the domian...rows are cord pairs 
  fwf_locs = pd.DataFrame({"XLAT": XLAT.ravel(), "XLONG": XLONG.ravel()})
  ## build kdtree
  fwf_tree = KDTree(fwf_locs)
  ## save tree
  pickle.dump([fwf_tree, fwf_locs], open(str(kdtree_dir) + f'fwf_{domain}_tree.p', "wb"))
  print("FWF KDTree built")


# 
# ## Search the data
# With a built kdtree we can query the tree to find the nearest neighbor model grid to our locations of interest.

# In[ ]:


## define empty list to append index of weather station locations
south_north,  west_east, wmo = [], [], []
## loop each weather station in dataframe
for loc in df.itertuples(index=True, name='Pandas'):
  ## arange wx station lat and long in a formate to query the kdtree
  single_loc = np.array([loc.lat, loc.lon]).reshape(1, -1)

  ## query the kdtree retuning the distacne of nearest neighbor and the index on the raveled grid
  fwf_dist, fwf_ind = fwf_tree.query(single_loc, k=1)

  ## set condition to pass on stations outside model domian 
  if fwf_dist > 0.1:
    pass
  else:
    ## if condition passed reformate 1D index to 2D indexes
    fwf_2D_ind = np.unravel_index(int(fwf_ind), shape)
    ## append the indexes to lists
    wmo.append(loc.wmo)
    south_north.append(fwf_2D_ind[0])
    west_east.append(fwf_2D_ind[1])


# 

# In[ ]:


## now the magic of xarray..convert lists of indexes to a dataarray with dimension wmo (weather staton)..this allows you to index and entire dataset 
south_north = xr.DataArray(np.array(south_north), dims= 'wmo', coords= dict(wmo = wmo))
west_east = xr.DataArray(np.array(west_east), dims= 'wmo', coords= dict(wmo = wmo))


# 

# In[ ]:


## index the entire dataset at the locations of interest leaving diemion time with new dimension wx stations
ds_loc = ds.sel(south_north = south_north, west_east = west_east)


# 

# In[ ]:


## print to see new time series dataset at every weather station location
print(ds_loc)


# 
# ## Data License
# [Creative Commons Attribution 4.0 International License.](https://creativecommons.org/licenses/by/4.0/)