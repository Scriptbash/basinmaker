import os

import pytest

from basinmaker import BasinMakerQGIS

#
# BasinMaker_Folder = "C:/Users/dustm/Documents/GitHub/RoutingTool"

###Floder where store the inputs for tests function
datafolder = os.path.join("../../tests/testdata", "Required_data_to_start_from_dem")
path_output_folder = os.path.join("../../tests/testdata", "test3")
path_working_folder = os.path.join("../../tests/testdata", "test4")

basinmaker = BasinMakerQGIS(
    path_output_folder=path_output_folder, path_working_folder=path_working_folder
)

# basinmaker.define_project_extent_method(
#     mode="using_outlet_pt",
#     path_dem_in=os.path.join(datafolder, "DEM_big_merit.tif"),
#     outlet_pt=[-91.977, 48.25],
#     buffer_distance=0.03,
# )
# 
# basinmaker.watershed_delineation_without_lake_method(
#     acc_thresold=200,
#     mode="usingdem",
#     max_memroy=1024 * 4,
#     gis_platform="qgis",
# )


basinmaker.watershed_delineation_with_lakes_method(
    path_lakefile_in=os.path.join(datafolder, "HyLake.shp"),
    lake_attributes=["Hylak_id", "Lake_type", "Lake_area", "Vol_total", "Depth_avg"],
    path_obsfile_in=os.path.join(datafolder, "obs.shp"),
    obs_attributes=["Obs_ID", "STATION_NU", "DA_obs", "SRC_obs"],
    max_memroy=1024 * 4,
    gis_platform="qgis",
)
