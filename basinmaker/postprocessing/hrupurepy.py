import numpy as np
import sys
import os
import csv
import tempfile 
import copy 
import pandas as pd
import geopandas
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from basinmaker.func.purepy import *
from basinmaker.func.pdtable import *
from osgeo import gdal, ogr
from basinmaker.func.fgdal import *

def GenerateHRUS_purepy(
    Path_Subbasin_Ply,
    Landuse_info,
    Soil_info,
    Veg_info,
    Inmportance_order,
    min_hru_area_pct_sub,
    Sub_Lake_ID="HyLakeId",
    Sub_ID="SubId",
    Path_Connect_Lake_ply="#",
    Path_Non_Connect_Lake_ply="#",
    Lake_Id="Hylak_id",
    Path_Landuse_Ply="#",
    Landuse_ID="Landuse_ID",
    Path_Soil_Ply="#",
    Soil_ID="Soil_ID",
    Path_Veg_Ply="#",
    Veg_ID="Veg_ID",
    Path_Other_Ply_1="#",
    Other_Ply_ID_1="O_ID_1",
    Path_Other_Ply_2="#",
    Other_Ply_ID_2="O_ID_2",
    DEM="#",
    Project_crs = '3573',
    OutputFolder="#",
    pixel_size = 30,
    area_ratio_thresholds = [0,0,0],
):
    """Generate HRU polygons and their attributes needed by hydrological model

    Function that be used to overlay: subbasin polygon, lake polygon (optional)
    , Land use polygon (optional), soil type polygon(optional),
    vegetation polygon (optional), and two other user defined polygons
    (optional).
    Non-lake HRU polygons in a subbasin is defined by an unique
    combination of all user provided datasets.
    A lake HRU polygon is defined the same as the provided lake polygon.
    All value of landuse and Veg polygon covered by lake will
    be changed to 1, indicating it is a covered by lake.
    All value of the soil polygon covered by the lake will be change to
    the soil id of the polygon covered by the lake with largest area.

    Parameters
    ----------
    Path_Subbasin_Ply                 : string
        It is the path of the subbasin polygon, which is generated by
        toolbox. if not generated by toolbox, the attribute table should
        including following attribute.
        ##############Subbasin related attributes###########################
        SubID           - integer, The subbasin Id
        DowSubId        - integer, The downstream subbasin ID of this
                                   subbasin
        IsLake          - integer, If the subbasin is a lake / reservior
                                   subbasin. 1 yes, <0, no
        IsObs           - integer, If the subbasin contains a observation
                                   gauge. 1 yes, < 0 no.
        RivLength       - float,   The length of the river in current
                                   subbasin in m
        RivSlope        - float,   The slope of the river path in
                                   current subbasin, in m/m
        FloodP_n        - float,   Flood plain manning's coefficient, in -
        Ch_n            - float,   main channel manning's coefficient, in -
        BkfWidth        - float,   the bankfull width of the main channel
                                   in m
        BkfDepth        - float,   the bankfull depth of the main channel
                                   in m
        HyLakeId        - integer, the lake id
        LakeVol         - float,   the Volume of the lake in km3
        LakeDepth       - float,   the average depth of the lake m
        LakeArea        - float,   the area of the lake in m2
    Landuse_info                      : string
        Path to a csv file that contains landuse information, including
        following attributes:
        Landuse_ID (can be any string)  - integer, the landuse ID in the
                                                   landuse polygon
        LAND_USE_C                      - string,  the landuse class name
                                                   for each landuse Type
    Soil_info                        : string
        Path to a csv file that contains soil information, including
        following attributes:
        Soil_ID (can be any string)     - integer, the Soil ID in the
                                                   soil polygon
        SOIL_PROF                       - string,  the Soil profile name
                                                   for each soil type
    Veg_info                         : string
        Path to a csv file that contains vegetation information, including
        following attributes:
        Veg_ID (can be any string)      - integer, the vegetation ID in the
                                                   vegetation polygon
        VEG_C                           - string,  the vegetation class name
                                                   for each vegetation Type
    Sub_Lake_ID                      : string (optional)
        The column name of the lake id in the subbasin polygon
    Sub_ID                           : string (optional)
        The column name of the subbasin id in the subbasin polygon
    Path_Connect_Lake_ply            : string (Optional)
        Path to the connected lake's polygon
    Path_Non_Connect_Lake_ply        : string (Optional)
        Path to the non connected lake's polygon
    Lake_Id                          : string (Optional)
        The the column name in lake polygon indicate the lake ID.
    Path_Landuse_Ply                 : string (Optional)
        Path to the landuse polygon. when Path_Landuse_Ply is not
        provided. The Landuse ID in Landuse_info should be
        1: land, -1: lake
    Landuse_ID                       : string (Optional)
        the the column name in landuse polygon and Landuse_info csv
        indicate the landuse ID. when Path_Landuse_Ply is not
        provided. The Landuse ID should be
        1: land, -1: lake.
    Path_Soil_Ply                    : string (Optional)
        Path to the soil polygon. when soil polygon is not
        provided. The Soil ID in Soil_info should be the same
        as Landuse ID.
    Soil_ID                          : string (Optional)
        the the column name in soil polygon and soil_info csv
        indicate the soil ID. when soil polygon is not
        provided. The Soil ID in Soil_info should be the same
        as Landuse ID.
    Path_Veg_Ply                     : string (Optional)
        Path to the vegetation polygon. when Veg polygon is not
        provided. The Veg ID in Veg_info should be the same
        as Landuse ID.
    Veg_ID                           : string (Optional)
        the the column name in vegetation polygon and veg_info csv
        indicate the vegetation ID. when Veg polygon is not
        provided. The Veg ID in Veg_info should be the same
        as Landuse ID.
    Path_Other_Ply_1                 : string (Optional)
        Path to the other polygon that will be used to define HRU,
        such as elevation band, or aspect.
    Other_Ply_ID_1                   : string (Optional)
        the the column name in Other_Ply_1 polygon
        indicate the landuse ID.
    Path_Other_Ply_2                 : string (Optional)
        Path to the other polygon that will be used to define HRU,
        such as elevation band, or aspect.
    Other_Ply_ID_2                   : string (Optional)
        the the column name in Other_Ply_2 polygon
        indicate the landuse ID.
    DEM                              : string (optional)
        the path to a raster elevation dataset, that will be used to
        calcuate average apspect, elevation and slope within each HRU.
        if no data is provided, basin average value will be used for
        each HRU.
    Project_crs                      : string
        the EPSG code of a projected coodinate system that will be used to
        calcuate HRU area and slope.
    OutputFolder                     : string
        The path to the folder that will save output HRU polygon.

    Notes
    -------
    Following ouput files will be generated in "<OutputFolder>/"
    'finalcat_hru_info.shp'              - HRU polygon and it's attributes


    Returns:
    -------
       None

    Examples
    -------
    >>> from ToolboxClass import LRRT
    >>> import pandas as pd
    >>> DataFolder = "C:/Path_to_foldr_of_example_dataset_provided_in_Github_wiki/"
    >>> RTtool=LRRT()
    >>> RTtool.GenerateHRUS(OutputFolder = DataFolder,
                           Path_Subbasin_Ply = os.path.join(DataFolder,"finalcat_info.shp"),
                           Path_Connect_Lake_ply = os.path.join(DataFolder,'Con_Lake_Ply.shp'),
                           Path_Non_Connect_Lake_ply = os.path.join(DataFolder,'Non_Con_Lake_Ply.shp'),
                           Path_Landuse_Ply = os.path.join(DataFolder,'modislanduse_exp_lg_pre.shp'),
                           Landuse_ID = 'gridcode',
                           Path_Soil_Ply = os.path.join(DataFolder,'ca_all_slc_v3r2_exp_lg.shp'),
                           Soil_ID = 'POLY_ID',
                           Landuse_info=os.path.join(DataFolder,'landuse_info.csv'),
                           Soil_info=os.path.join(DataFolder,'soil_info.csv'),
                           Veg_info=os.path.join(DataFolder,'veg_info.csv'),
                           DEM = os.path.join(DataFolder,'na_dem_15s_1.tif')
                           )

    """

    if not os.path.exists(OutputFolder):
        os.makedirs(OutputFolder)
        
    tempfolder = os.path.join(
        OutputFolder, "HRU_TEMP" + str(np.random.randint(1, 10000 + 1))
    )
    if not os.path.exists(tempfolder):
        os.makedirs(tempfolder)
    
    prj_crs = Project_crs
    Merge_layer_list = []
    Merge_layer_raster_list = []
    Merge_layer_shp_list = []
    Merge_ID_list = []


    Sub_Lake_HRU_Layer, trg_crs, fieldnames_list = GeneratelandandlakeHRUS(
        OutputFolder,
        tempfolder,
        Path_Subbasin_ply=Path_Subbasin_Ply,
        Path_Connect_Lake_ply=Path_Connect_Lake_ply,
        Path_Non_Connect_Lake_ply=Path_Non_Connect_Lake_ply,
        Sub_ID=Sub_ID,
        Sub_Lake_ID=Sub_Lake_ID,
        Lake_Id=Lake_Id,
    ) 
    
    lakehruinfo = geopandas.read_file(Sub_Lake_HRU_Layer)
    hru_lake_info = lakehruinfo.loc[lakehruinfo['HRU_IsLake'] > 0].copy()
    lakehruinfo_landhrus = lakehruinfo.loc[lakehruinfo['HRU_IsLake'] <= 0].copy()
    
    hru_lake_info = clean_geometry_purepy(hru_lake_info)
    lakehruinfo_landhrus = clean_geometry_purepy(lakehruinfo_landhrus)
    

    path_to_landhru_shp= os.path.join(tempfolder,'land_hru.shp')
    path_to_lakehru_shp= os.path.join(tempfolder,'lake_hru.shp')
    path_to_landuse_shp = os.path.join(tempfolder,'landuse.shp')
    path_to_soil_shp = os.path.join(tempfolder,'soil.shp')
    path_to_veg_shp = os.path.join(tempfolder,'veg.shp')
    path_to_other1_shp = os.path.join(tempfolder,'o1.shp')
    path_to_other2_shp = os.path.join(tempfolder,'o2.shp')

    
    lakehruinfo_landhrus.to_file(path_to_landhru_shp)
    if len(hru_lake_info) > 0:
        hru_lake_info.to_file(path_to_lakehru_shp)

    
    fieldnames_list.extend(
        [
            Landuse_ID,
            Soil_ID,
            Veg_ID,
            Other_Ply_ID_1,
            Other_Ply_ID_2,
            "LAND_USE_C",
            "VEG_C",
            "SOIL_PROF",
            "HRU_Slope",
            "HRU_Area",
            "HRU_Aspect",
            "geometry",
        ]
    )
    dissolve_filedname_list = ["HRULake_ID"]
    
    Merge_layer_list.append(lakehruinfo_landhrus)

    Landuse_info_data = pd.read_csv(Landuse_info)
    Soil_info_data = pd.read_csv(Soil_info)
    Veg_info_data = pd.read_csv(Veg_info)
    
                
    #### check which data will be inlucded to determine HRU
    if Path_Landuse_Ply != "#":
        land_landuse_clean = Reproj_Clip_Dissolve_Simplify_Polygon_purepy(
            layer_path = Path_Landuse_Ply, 
            Class_Col = Landuse_ID, 
            tempfolder = tempfolder,
            mask_layer = lakehruinfo,
            Class_NM_Col = "LAND_USE_C",
            info_table = Landuse_info_data,
        )
        
        if Landuse_ID not in land_landuse_clean.columns:
            print("Landuse polygon attribute table do not contain: ",Landuse_ID)
            sys.exit()            
        land_landuse_clean.to_file(path_to_landuse_shp)

        dissolve_filedname_list.append(Landuse_ID)
        Merge_layer_shp_list.append(path_to_landuse_shp)
        Merge_ID_list.append(Landuse_ID)

    if Path_Soil_Ply != "#":
        land_soil_clean = Reproj_Clip_Dissolve_Simplify_Polygon_purepy(
            layer_path = Path_Soil_Ply, 
            Class_Col = Soil_ID, 
            tempfolder = tempfolder,
            mask_layer = lakehruinfo,
            Class_NM_Col = "SOIL_PROF",
            info_table = Soil_info_data,            
        )

        if Soil_ID not in land_soil_clean.columns:
            print("Soil polygon attribute table do not contain: ",Soil_ID)
            sys.exit()            
        land_soil_clean.to_file(path_to_soil_shp)
        dissolve_filedname_list.append(Soil_ID)
        Merge_layer_shp_list.append(path_to_soil_shp)
        Merge_ID_list.append(Soil_ID)
        
    if Path_Veg_Ply != "#":
        land_veg_clean = Reproj_Clip_Dissolve_Simplify_Polygon_purepy(
            layer_path = Path_Veg_Ply, 
            Class_Col = Veg_ID, 
            tempfolder = tempfolder,
            mask_layer = lakehruinfo
        )

        if Veg_ID not in land_veg_clean.columns:
            print("Veg polygon attribute table do not contain: ",Veg_ID)
            sys.exit()            
        land_veg_clean.to_file(path_to_veg_shp)
        dissolve_filedname_list.append(Veg_ID)
        Merge_layer_shp_list.append(path_to_veg_shp)
        Merge_ID_list.append(Veg_ID)
        
                
    if Path_Other_Ply_1 != "#":
        land_o1_clean = Reproj_Clip_Dissolve_Simplify_Polygon_purepy(
            layer_path = Path_Other_Ply_1, 
            Class_Col = Other_Ply_ID_1, 
            tempfolder = tempfolder,
            mask_layer = lakehruinfo
        )        

        if Other_Ply_ID_1 not in land_o1_clean.columns:
            print("Other_Ply_1 polygon attribute table do not contain: ",Other_Ply_ID_1)
            sys.exit()            
        land_o1_clean.to_file(path_to_other1_shp)
        dissolve_filedname_list.append(Other_Ply_ID_1)
        Merge_layer_shp_list.append(path_to_other1_shp)
        Merge_ID_list.append(Other_Ply_ID_1)

    if Path_Other_Ply_2 != "#":
        land_o2_clean = Reproj_Clip_Dissolve_Simplify_Polygon_purepy(
            layer_path = Path_Other_Ply_2, 
            Class_Col = Other_Ply_ID_2, 
            tempfolder = tempfolder,
            mask_layer = lakehruinfo
        )        

        if Other_Ply_ID_2 not in land_o2_clean.columns:
            print("Other_Ply_1 polygon attribute table do not contain: ",Other_Ply_ID_2)
            sys.exit()            
        land_o2_clean.to_file(path_to_other2_shp)
        dissolve_filedname_list.append(Other_Ply_ID_2)
        Merge_layer_shp_list.append(path_to_other2_shp)
        Merge_ID_list.append(Other_Ply_ID_2)
                
    fieldnames = np.array(fieldnames_list)

       
    path_to_hru_temp_shp = RasterHRUUnionInt32(OutputFolder,tempfolder,Merge_layer_shp_list,
                            Merge_ID_list,Sub_Lake_HRU_Layer,Sub_ID,
                            Landuse_ID,Soil_ID,Veg_ID,Other_Ply_ID_1,
                            Other_Ply_ID_2,pixel_size,lakehruinfo)
                            
    HRU_temp1 = geopandas.read_file(path_to_hru_temp_shp)
    
    HRU_temp1 = decode_hru_attri_ids(HRU_temp1,lakehruinfo,Landuse_ID,Soil_ID,
                                     Veg_ID,Other_Ply_ID_1,Other_Ply_ID_2)
                                     
    HRU_temp1.to_file(os.path.join(tempfolder,'HRU_DEDOCE.shp'))
    #####     
    hru_lake_info = HRU_temp1.loc[HRU_temp1['HRU_IsLake'] > 0].copy()
    hru_land_info = HRU_temp1.loc[HRU_temp1['HRU_IsLake'] <= 0].copy()
    
    # landuse polygon is not provided,landused id the same as IS_lake
    if Path_Landuse_Ply == "#":
        hru_land_info[Landuse_ID] = -hru_land_info['HRU_IsLake']
    hru_lake_info[Landuse_ID] = -1
    # if soil is not provied, it the value,will be the same as land use
    if Path_Soil_Ply == "#":
        hru_land_info[Soil_ID] = -hru_land_info['HRU_IsLake']
    hru_lake_info[Soil_ID] = -1
    # if no vegetation polygon is provide vegetation, will be the same as landuse
    if Path_Veg_Ply == "#":
        hru_land_info[Veg_ID] = hru_land_info[Landuse_ID]
    hru_lake_info[Veg_ID] = -1
    if Path_Other_Ply_1 == "#":
        hru_land_info[Other_Ply_ID_1] = -hru_land_info['HRU_IsLake']
    hru_lake_info[Other_Ply_ID_1] = -1
    if Path_Other_Ply_2 == "#":
        hru_land_info[Other_Ply_ID_2] = -hru_land_info['HRU_IsLake']
    hru_lake_info[Other_Ply_ID_2] = -1

    hru_lake_info = clean_attribute_name_purepy(hru_lake_info,fieldnames)
    hru_land_info = clean_attribute_name_purepy(hru_land_info,fieldnames)

    
    hruinfo = hru_lake_info.append(hru_land_info)
    
    hruinfo.to_file(os.path.join(tempfolder,'HRU_with_attributes.shp'))

       
    HRU_draf_final = Define_HRU_Attributes_purepy(
        prj_crs = prj_crs,
        trg_crs = trg_crs,
        hruinfo = hruinfo,
        dissolve_filedname_list = dissolve_filedname_list,
        Sub_ID = Sub_ID,
        Landuse_ID = Landuse_ID,
        Soil_ID = Soil_ID,
        Veg_ID = Veg_ID,
        Other_Ply_ID_1 = Other_Ply_ID_1,
        Other_Ply_ID_2 = Other_Ply_ID_2,
        Landuse_info_data = Landuse_info_data,
        Soil_info_data = Soil_info_data,
        Veg_info_data = Veg_info_data,
        DEM = DEM,
        Path_Subbasin_Ply = Path_Subbasin_Ply,
        min_hru_area_pct_sub = min_hru_area_pct_sub,
        Inmportance_order = Inmportance_order,
        OutputFolder = OutputFolder,
        tempfolder = tempfolder,
        area_ratio_thresholds = area_ratio_thresholds,
    )    
    
    COLUMN_NAMES_CONSTANT_HRU_extend = COLUMN_NAMES_CONSTANT_HRU.extend(
        [
            Landuse_ID,
            Soil_ID,
            Veg_ID,
            Other_Ply_ID_1,
            Other_Ply_ID_2,
            'geometry',
            'HRU_A_G'
        ]
    )
    HRU_draf_final = clean_attribute_name_purepy(HRU_draf_final,COLUMN_NAMES_CONSTANT_HRU)
    for col in [Landuse_ID,Soil_ID,Veg_ID,Other_Ply_ID_1,Other_Ply_ID_2,'SubId']:
        HRU_draf_final = HRU_draf_final.loc[HRU_draf_final[col] != 0]
            
    HRU_draf_final.to_file(os.path.join(OutputFolder,'finalcat_hru_info.shp'))
    HRU_draf_final_wgs_84 = HRU_draf_final.to_crs('EPSG:4326')
    HRU_draf_final_wgs_84 = HRU_draf_final_wgs_84[['HRU_ID','geometry']]
    TOLERANCEs = [0.0001,0.0005,0.001,0.005,0.01,0.05]
    output_jason_path = os.path.join(OutputFolder,'finalcat_hru_info.geojson')
    for TOLERANCE in TOLERANCEs:                               
        HRU_draf_final_wgs_84['geometry'] = HRU_draf_final_wgs_84.simplify(TOLERANCE)
        HRU_draf_final_wgs_84.to_file(output_jason_path,driver="GeoJSON") 

        json_file_size = os.stat(output_jason_path).st_size/1024/1024 #to MB
        if json_file_size <= 100:
            break
    
def GeneratelandandlakeHRUS(
    OutputFolder,
    tempfolder,
    Path_Subbasin_ply,
    Path_Connect_Lake_ply="#",
    Path_Non_Connect_Lake_ply="#",
    Sub_ID="SubId",
    Sub_Lake_ID="HyLakeId",
    Lake_Id="Hylak_id",
):

    """Overlay subbasin polygon and lake polygons

    Function that will overlay subbasin polygon and lake polygon

    Parameters
    ----------
    processing                        : qgis object
    context                           : qgis object
    OutputFolder                     : string
        The path to the folder that will save output HRU polygon.

    Path_Subbasin_Ply                 : string
        It is the path of the subbasin polygon, which is generated by
        toolbox. if not generated by toolbox, the attribute table should
        including following attribute.
        ##############Subbasin related attributes###########################
        SubID           - integer, The subbasin Id
        DowSubId        - integer, The downstream subbasin ID of this
                                   subbasin
        IsLake          - integer, If the subbasin is a lake / reservior
                                   subbasin. 1 yes, <0, no
        IsObs           - integer, If the subbasin contains a observation
                                   gauge. 1 yes, < 0 no.
        RivLength       - float,   The length of the river in current
                                   subbasin in m
        RivSlope        - float,   The slope of the river path in
                                   current subbasin, in m/m
        FloodP_n        - float,   Flood plain manning's coefficient, in -
        Ch_n            - float,   main channel manning's coefficient, in -
        BkfWidth        - float,   the bankfull width of the main channel
                                   in m
        BkfDepth        - float,   the bankfull depth of the main channel
                                   in m
        HyLakeId        - integer, the lake id
        LakeVol         - float,   the Volume of the lake in km3
        LakeDepth       - float,   the average depth of the lake m
        LakeArea        - float,   the area of the lake in m2
    Path_Connect_Lake_ply            : string (Optional)
        Path to the connected lake's polygon
    Path_Non_Connect_Lake_ply        : string (Optional)
        Path to the non connected lake's polygon
    Sub_ID                           : string (optional)
        The column name of the subbasin id in the subbasin polygon
    Sub_Lake_ID                      : string (optional)
        The column name of the lake id in the subbasin polygon
    Lake_Id                          : string (Optional)
        The the column name in lake polygon indicate the lake ID.


    Notes
    -------
        None

    Returns:
    -------
        Sub_Lake_HRU['OUTPUT']                   : qgis object
            it is a polygon after overlay between subbasin polygon and
            lake polygon
        Sub_Lake_HRU['OUTPUT'].crs().authid()    : string
            it is a string indicate the geospatial reference used by SubBasin
            polygon
        ['HRULake_ID','HRU_IsLake',Sub_ID]       : list
            it is a string list
    """

    # Fix geometry errors in subbasin polygon
#    arcpy.RepairGeometry_management(Path_Subbasin_ply)
    
    # Create a file name list that will be strored in output attribute table
    fieldnames_list = [
        "HRULake_ID",
        "HRU_IsLake",
        Lake_Id,
        Sub_ID,
        Sub_Lake_ID,
        "geometry"
    ]  ### attribubte name in the need to be saved
    fieldnames = np.array(fieldnames_list)

    # if no lake polygon is provided, use subId as HRULake_ID.
    if Path_Connect_Lake_ply == "#" and Path_Non_Connect_Lake_ply == "#":
        
        cat_info = geopandas.read_file(Path_Subbasin_ply)
        cat_info['Hylak_id'] = -1
        cat_info['HRULake_ID'] = cat_info.index +1
        cat_info['HRU_IsLake'] = -1
        
        # remove column not in fieldnames
        cat_info = clean_attribute_name_purepy(cat_info,fieldnames)
        cat_info.to_file(os.path.join(OutputFolder,'finalcat_hru_lake_info.shp'))
        crs_id = cat_info.crs
        return os.path.join(OutputFolder,'finalcat_hru_lake_info.shp'), crs_id, ["HRULake_ID", "HRU_IsLake", Sub_ID]
    else:
        cat_info = geopandas.read_file(Path_Subbasin_ply)

    # fix lake polygon  geometry
    if Path_Connect_Lake_ply != "#":
#        arcpy.RepairGeometry_management(Path_Connect_Lake_ply)
        cl_lake = geopandas.read_file(Path_Connect_Lake_ply)
    # fix lake polygon geometry
    if Path_Non_Connect_Lake_ply != "#":
#        arcpy.RepairGeometry_management(Path_Non_Connect_Lake_ply)
        ncl_lake = geopandas.read_file(Path_Non_Connect_Lake_ply)
        
    # Merge connected and non connected lake polygons first
    if Path_Connect_Lake_ply != "#" and Path_Non_Connect_Lake_ply != "#":
        merged_lake_ply = cl_lake.append(ncl_lake)
#        arcpy.Merge_management([Path_Connect_Lake_ply, Path_Non_Connect_Lake_ply], os.path.join(tempfolder,'merged_lake_ply.shp'))   
    elif Path_Connect_Lake_ply != "#" and Path_Non_Connect_Lake_ply == "#":
#        arcpy.CopyFeatures_management(Path_Connect_Lake_ply, os.path.join(tempfolder,'merged_lake_ply.shp'))
        merged_lake_ply = cl_lake
    elif Path_Connect_Lake_ply == "#" and Path_Non_Connect_Lake_ply != "#":
#        arcpy.CopyFeatures_management(Path_Non_Connect_Lake_ply, os.path.join(tempfolder,'merged_lake_ply.shp'))
        merged_lake_ply = ncl_lake
    else:
        print("should never happened......")

    # union merged polygon and subbasin polygon
#    cat_info.spatial.to_featureclass(location=os.path.join(tempfolder,'cat_ply.shp'))
#    arcpy.RepairGeometry_management(os.path.join(tempfolder,'cat_ply.shp'))
    
    inFeatures = [[Path_Subbasin_ply, 1], [os.path.join(tempfolder,'merged_lake_ply.shp'), 2]]
    
    cat_lake_union = geopandas.overlay(cat_info, merged_lake_ply, how='union',make_valid = True,keep_geom_type = True)
    
#    cat_lake_union.to_file(os.path.join(tempfolder,'cat_lake_union.shp'))


#    arcpy.Union_analysis(inFeatures, os.path.join(tempfolder,'cat_lake_union.shp'))
#    arcpy.RepairGeometry_management(os.path.join(tempfolder,'cat_lake_union.shp'))
    cat_lake_union = clean_geometry_purepy(cat_lake_union)

    sub_lake_info = cat_lake_union.copy(deep=True)
    sub_lake_info['HRULake_ID'] = -9999
    sub_lake_info['HRU_IsLake'] = -9999
    
    crs_id = sub_lake_info.crs

    sub_lake_info = sub_lake_info.sort_values(by=['SubId',Lake_Id]).copy(deep=True).reset_index()
    
    sub_lake_info['HRU_ID_Temp'] = sub_lake_info.index + 1
    
    sub_lake_info = Determine_Lake_HRU_Id(sub_lake_info)
    # copy determined lake hru id to vector
    sub_lake_info = clean_attribute_name_purepy(sub_lake_info,fieldnames)
    save_modified_attributes_to_outputs(
        mapoldnew_info = sub_lake_info,
        tempfolder = tempfolder,
        OutputFolder = OutputFolder,
        cat_name = 'finalcat_hru_lake_info.shp',
        riv_name = '#',
        Path_final_riv = '#',
        dis_col_name='HRULake_ID'
    ) 
    return os.path.join(OutputFolder,'finalcat_hru_lake_info.shp'), crs_id, ["HRULake_ID", "HRU_IsLake", Sub_ID]


############


def Define_HRU_Attributes_purepy(
    prj_crs,
    trg_crs,
    hruinfo,
    dissolve_filedname_list,
    Sub_ID,
    Landuse_ID,
    Soil_ID,
    Veg_ID,
    Other_Ply_ID_1,
    Other_Ply_ID_2,
    Landuse_info_data,
    Soil_info_data,
    Veg_info_data,
    DEM,
    Path_Subbasin_Ply,
    Inmportance_order,
    min_hru_area_pct_sub,
    OutputFolder,
    tempfolder,
    area_ratio_thresholds,
):

    """Generate attributes of each HRU

    Function will generate attributes that are needed by Raven and
    other hydrological models for each HRU

    Parameters
    ----------
    processing                        : qgis object
    context                           : qgis object
    Project_crs                       : string
        the EPSG code of a projected coodinate system that will be used to
        calcuate HRU area and slope.
    hru_layer                         : qgis object
        a polygon layer generated by overlay all input polygons
    dissolve_filedname_list           : list
        a list contain column name of ID in each polygon layer
        in Merge_layer_list
    Sub_ID                            : string
        The column name of the subbasin id in the subbasin polygon
    Landuse_ID                        : string
        the the column name in landuse polygon and Landuse_info csv
        indicate the landuse ID. when Path_Landuse_Ply is not
        provided. The Landuse ID should be
        1: land, -1: lake.
    Soil_ID                           : string
        the the column name in soil polygon and soil_info csv
        indicate the soil ID. when soil polygon is not
        provided. The Soil ID in Soil_info should be the same
        as Landuse ID.
    Veg_ID                            : string
        the the column name in vegetation polygon and veg_info csv
        indicate the vegetation ID. when Veg polygon is not
        provided. The Veg ID in Veg_info should be the same
        as Landuse ID.

    Landuse_info                      : Dataframe
        a dataframe that contains landuse information, including
        following attributes:
        Landuse_ID (can be any string)  - integer, the landuse ID in the
                                                   landuse polygon
        LAND_USE_C                      - string,  the landuse class name
                                                   for each landuse Type
    Soil_info                         : Dataframe
        a dataframe that contains soil information, including
        following attributes:
        Soil_ID (can be any string)     - integer, the Soil ID in the
                                                   soil polygon
        SOIL_PROF                       - string,  the Soil profile name
                                                   for each soil type
    Veg_info                          : Dataframe
        a dataframe file that contains vegetation information, including
        following attributes:
        Veg_ID (can be any string)      - integer, the vegetation ID in the
                                                   vegetation polygon
        VEG_C                           - string,  the vegetation class name
                                                   for each vegetation Type
    DEM                               : string (optional)
        the path to a raster elevation dataset, that will be used to
        calcuate average apspect, elevation and slope within each HRU.
        if no data is provided, basin average value will be used for
        each HRU.
    Path_Subbasin_Ply                 : string
        It is the path of the subbasin polygon, which is generated by
        toolbox. if not generated by toolbox, the attribute table should
        including following attribute.
        ##############Subbasin related attributes###########################
        SubID           - integer, The subbasin Id
        DowSubId        - integer, The downstream subbasin ID of this
                                   subbasin
        IsLake          - integer, If the subbasin is a lake / reservior
                                   subbasin. 1 yes, <0, no
        IsObs           - integer, If the subbasin contains a observation
                                   gauge. 1 yes, < 0 no.
        RivLength       - float,   The length of the river in current
                                   subbasin in m
        RivSlope        - float,   The slope of the river path in
                                   current subbasin, in m/m
        FloodP_n        - float,   Flood plain manning's coefficient, in -
        Ch_n            - float,   main channel manning's coefficient, in -
        BkfWidth        - float,   the bankfull width of the main channel
                                   in m
        BkfDepth        - float,   the bankfull depth of the main channel
                                   in m
        HyLakeId        - integer, the lake id
        LakeVol         - float,   the Volume of the lake in km3
        LakeDepth       - float,   the average depth of the lake m
        LakeArea        - float,   the area of the lake in m2
    OutputFolder                      : String
        The path to a folder to save result during the processing

    Returns:
    -------
    HRU_draf_final                  : qgis object
        it is a polygon object that generated by overlay all input
        layers and inlcude all needed attribue for hydrological model
        like RAVEN
    """
    num = str(np.random.randint(1, 10000 + 1))
    hruinfo["LAND_USE_C"] = '-9999'
    hruinfo["VEG_C"] = '-9999'
    hruinfo["SOIL_PROF"] = '-9999'
    hruinfo["HRU_CenX"] = -9999.9999
    hruinfo["HRU_CenY"] = -9999.9999
    hruinfo["HRU_ID_New"] = -9999
    hruinfo["HRU_Area"] = -9999.99 

    hruinfo_area = add_area_in_m2(hruinfo,prj_crs,'HRU_Area')
    
    hruinfo_area = simplify_hrus_method2(area_ratio_thresholds,hruinfo_area, Landuse_ID,
                          Soil_ID,Veg_ID,Other_Ply_ID_1,Other_Ply_ID_2)

    hruinfo_area = hruinfo_area.sort_values(by=[Sub_ID,Soil_ID,Landuse_ID]).copy(deep=True).reset_index()

 
    hruinfo_area['HRU_ID'] = hruinfo_area.index + 1
    hruinfo_area["HRU_ID_New"] = hruinfo_area.index + 1  
        
    hruinfo_area_update_attribute = Determine_HRU_Attributes(
        hruinfo_area,
        Sub_ID,
        Landuse_ID,
        Soil_ID,
        Veg_ID,
        Other_Ply_ID_1,
        Other_Ply_ID_2,
        Landuse_info_data,
        Soil_info_data,
        Veg_info_data,
    )
   
    hruinfo_area_update_attribute = clean_geometry_purepy(hruinfo_area_update_attribute,set_precision = -1)
   
    hruinfo_new = save_modified_attributes_to_outputs(
        mapoldnew_info = hruinfo_area_update_attribute,
        tempfolder = tempfolder,
        OutputFolder = tempfolder,
        cat_name = 'finalcat_hru_info.shp',
        riv_name = '#',
        Path_final_riv = '#',
        dis_col_name='HRU_ID_New'
    )
    hruinfo_new = add_area_in_m2(hruinfo_new,prj_crs,'HRU_Area')
    
    hruinfo_simple = simplidfy_hrus(
        min_hru_pct_sub_area = min_hru_area_pct_sub,
        hruinfo = hruinfo_new,
        importance_order = Inmportance_order,
    )
    
    hruinfo_simple = clean_geometry_purepy(hruinfo_simple,set_precision = -1)
    
    hruinfo_simple = save_modified_attributes_to_outputs(
        mapoldnew_info = hruinfo_simple,
        tempfolder = tempfolder,
        OutputFolder = tempfolder,
        cat_name = 'hru_simple.shp',
        riv_name = '#',
        Path_final_riv = '#',
        dis_col_name='HRU_ID_New'
    )

    hruinfo_simple = add_centroid_in_wgs84(hruinfo_simple,"HRU_CenX","HRU_CenY")

    cat_info = geopandas.read_file(Path_Subbasin_Ply)
    cat_info = cat_info.drop(columns = 'geometry').copy(deep=True) 
    
    hruinfo_simple = pd.merge(hruinfo_simple, cat_info, on='SubId', how='left')             

    hruinfo_simple = add_area_in_m2(hruinfo_simple,prj_crs,'HRU_Area')

    if DEM != "#":
        
        hru_proj= hruinfo_simple.to_crs(prj_crs)
        hru_proj.to_file(os.path.join(tempfolder,"hru_proj.shp"))
        proj_clip_raster(DEM,os.path.join(tempfolder,"demproj.tif"),prj_crs)
#        proj_clip_raster(os.path.join(tempfolder,"demproj.tif"),os.path.join(tempfolder,"demclip.tif"),prj_crs,os.path.join(tempfolder,"hru_proj.shp"))
        gdal_slope_raster(os.path.join(tempfolder,"demproj.tif"),os.path.join(tempfolder,"demslope.tif"))
        gdal_aspect_raster(os.path.join(tempfolder,"demproj.tif"),os.path.join(tempfolder,"demaspect.tif"))
        
        table_elv = ZonalStats(hru_proj, os.path.join(tempfolder,"demproj.tif"), 'mean','HRU_ID_New')
        table_asp = ZonalStats(hru_proj, os.path.join(tempfolder,"demaspect.tif"), 'mean','HRU_ID_New')
        table_slp = ZonalStats(hru_proj, os.path.join(tempfolder,"demslope.tif"), 'mean','HRU_ID_New')

        table_slp['HRU_S_mean'] = table_slp['mean']
        table_slp = table_slp[['HRU_ID_New','HRU_S_mean']]
        table_asp['HRU_A_mean'] = table_asp['mean']
        table_asp = table_asp[['HRU_ID_New','HRU_A_mean']]
        table_elv['HRU_E_mean'] = table_elv['mean']
        table_elv = table_elv[['HRU_ID_New','HRU_E_mean']]
        hru_proj = pd.merge(hru_proj, table_slp, on='HRU_ID_New')          
        hru_proj = pd.merge(hru_proj, table_asp, on='HRU_ID_New')          
        hru_proj = pd.merge(hru_proj, table_elv, on='HRU_ID_New') 
        hruinfo_add_slp_asp = hru_proj.to_crs(trg_crs)
        hruinfo_add_slp_asp = hruinfo_add_slp_asp.sort_values(by=[Sub_ID,Soil_ID,Landuse_ID]).copy(deep=True).reset_index()
        hruinfo_add_slp_asp['HRU_ID'] = hruinfo_add_slp_asp.index + 1        
    else:

        hruinfo_add_slp_asp = hruinfo_simple.sort_values(by=[Sub_ID,Soil_ID,Landuse_ID]).copy(deep=True).reset_index()
        hruinfo_add_slp_asp['HRU_ID'] = hruinfo_add_slp_asp.index + 1
        hruinfo_add_slp_asp['HRU_S_mean'] = hruinfo_add_slp_asp['BasSlope']
        hruinfo_add_slp_asp['HRU_A_mean'] = hruinfo_add_slp_asp['BasAspect']
        hruinfo_add_slp_asp['HRU_E_mean'] = hruinfo_add_slp_asp['MeanElev']
    
    hruinfo_add_slp_asp = adjust_HRUs_area_based_on_ply_sub_area(hruinfo_add_slp_asp)
            
    return hruinfo_add_slp_asp

def adjust_HRUs_area_based_on_ply_sub_area(hruinfo):
    hruinfo['HRU_A_G'] =hruinfo ['HRU_Area']
    subinfo = hruinfo[['SubId','HRU_Area']].copy(deep=True)
    subinfo = subinfo.rename(columns={"HRU_Area": "Bas_A_G"})
    
    subinfo = subinfo.groupby(['SubId'],as_index = False).sum()
    hruinfo = pd.merge(hruinfo, subinfo, on='SubId')
    hruinfo['Ratio_A'] = hruinfo['BasArea']/hruinfo['Bas_A_G'] 
    hruinfo['HRU_Area'] = hruinfo['HRU_A_G'] * hruinfo['Ratio_A']
    
    return hruinfo
    
 
        