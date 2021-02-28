from utilities.utilities import *
from func.pdtable import *


def add_attributes_to_catchments(
    input_geo_names,
    path_bkfwidthdepth="#",
    bkfwd_attributes=[],
    path_landuse="#",
    path_landuse_info="#",
    k_in=-1,
    c_in=-1,
    out_cat_name="catchment_without_merging_lakes",
    out_riv_name="river_without_merging_lakes",
    grassdb="#",
    grass_location="#",
    qgis_prefix_path="#",
    gis_platform="qgis",
    projection="EPSG:3573",
    obs_attributes=[],
    lake_attributes=[],
    outlet_obs_id=1,
    path_sub_reg_outlets_v="#",
    output_folder="#",
):

    """Calculate hydrological paramters

    Calculate hydrological paramters for each subbasin generated by
    "AutomatedWatershedsandLakesFilterToolset". The result generaed
    by this tool can be used as inputs for Define_Final_Catchment
    and other post processing tools

    Parameters
    ----------
    input_geo_names                : dict
        it is a dictionary that list the required input file names,should at
        least indicate the name of following items:
        sl_nonconnect_lake          : raster
            it is a raster represent all non connected lakes that are selected
            by lake area threstholds
        sl_connected_lake           : raster
            it is a raster represent allconnected lakes that are selected
            by lake area threstholds
        river_without_merging_lakes : raster/vector
            it is the updated river segment for each subbasin
        catchment_without_merging_lakes   : raster/vector
            it is a raster represent updated subbasins after adding lake inflow
            and outflow points as new subbasin outlet.
        snapped_obs_points          : raster/vector
            it is a name of the point gis file represent successfully sanpped
            observation points

    path_bkfwidthdepth             : string
        It is a string to indicate the full path of the
        polyline shapefile that having bankfull width and
        depth data
    bkfwd_attributes               :
        the columns names that indicate following items has to be included
        1) column name for the Bankfull width in m;
        2) column name for the Bankfull depth in m;
        3) column name for the annual mean discharge in m3/s;
    path_landuse                   : string
        It is a string to indicate the full path of the landuse data.
        It will be used to estimate the floodplain roughness
        coefficient. Should have the same projection with the DEM data
        in ".tif" format.
    path_landuse_info              : string
        It is a string to indicate the full path of the table in '.csv'
        format.The table describe the floodplain roughness coefficient
        correspond to a given landuse type. The table should have two
        columns: RasterV and MannV. RasterV is the landuse value in the
        landuse raster for each land use type and the MannV is the
        roughness coefficient value for each landuse type.
    gis_platform                   : string
        It is a string indicate with gis platform is used:
        'qgis'                : the basinmaker is running within QGIS
        'arcgis'              : the basinmaker is running within ArcGIS
    lake_attributes                : list
        the columns names that indicate following items has to be included
        1) column name for the unique Id of each lake within the lake polygon shpfile;
        2) column name for type of the lake should be integer;
        3) column name for the volume of the lake in km3;
        4) column name for the average depth of the lake in m;
        5) column name for the area of the lake in km2.
    obs_attributes                 : list
        the columns names that indicate following items has to be included
        1) column name for the unique Id of each observation point;
        2) column name for the unique name of each observation point;
        3) column name for the drainage area of each observation point in km3;
        4) column name for the source of the observation point:
            'CA' for observation in canada;
            'US' for observation in US;
    outlet_obs_id                  : int
        It is one 'Obs_ID' in the provided observation gauge
        shapefile. If it is larger than zero. Subbasins that
        do not drainage to this gauge will be removed from
        delineation result.
    projection                     : string
        It is a string indicate a projected coordinate system,
        which wiil be used to calcuate area, slope and aspect.
    output_folder                  : string
        The path to a folder to save outputs
    path_sub_reg_outlets_v         : string

    Notes
    -------
    Five vector files will be generated by this function. these files
    can be used to define final routing structure by "Define_Final_Catchment"
    or be used as input for other postprocessing tools. All files
    are stored at self.OutputFolder

    catchment_without_merging_lakes.shp             : shapefile
        It is the subbasin polygon before merging lakes catchments and
        need to be processed before used.
    river_without_merging_lakes.shp                 : shapefile
        It is the subbasin river segment before merging lakes catchments and
        need to be processed before used.
    sl_connected_lake.shp                           : shapefile
        It is the connected lake polygon. Connected lakes are lakes that
        are connected by  Path_final_riv.
    sl_non_connected_lake.shp                       : shapefile
        It is the  non connected lake polygon. Connected lakes are lakes
        that are not connected by Path_final_cat_riv or Path_final_riv.
    obs_gauges                                      : shapefile
        It is the point shapefile that represent the observation gauge
        after snap to river network.

    Returns:
    -------
       None

    Examples
    -------

    """

    columns = COLUMN_NAMES_CONSTANT
    coltypes = COLUMN_TYPES_CONSTANT

    # local geo file names
    cat_ply_info = Internal_Constant_Names["cat_ply_info"]
    cat_riv_info = Internal_Constant_Names["cat_riv_info"]
    outlet_pt_info = Internal_Constant_Names["outlet_pt_info"]

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    if gis_platform == "qgis":
        assert (
            grassdb != "#"
        ), "grass database folder is needed, when gis_platform = qgis"
        assert (
            grass_location != "#"
        ), "grass location name is needed, when gis_platform = qgis"
        assert (
            qgis_prefix_path != "#"
        ), "qgis prefix path is needed, when gis_platform = qgis"
        from addattributes.createattributestemplateqgis import (
            create_catchments_attributes_template_table,
        )
        from addattributes.calculatebasicattributesqgis import (
            calculate_basic_attributes,
        )
        from addattributes.addlakeattributesqgis import add_lake_attributes
        from addattributes.joinpandastoattributesqgis import (
            join_pandas_table_to_vector_attributes,
        )
        from addattributes.exportoutputsqgis import export_files_to_output_folder
        from addattributes.addgaugeattributesqgis import add_gauge_attributes
        from addattributes.calfloodmanningnqgis import calculate_flood_plain_manning_n
        from addattributes.calbkfwidthdepthqgis import (
            calculate_bankfull_width_depth_from_polyline,
        )

        attr_template = create_catchments_attributes_template_table(
            grassdb=grassdb,
            grass_location=grass_location,
            columns=columns,
            input_geo_names=input_geo_names,
        )
        
        attr_basic = calculate_basic_attributes(
            grassdb=grassdb,
            grass_location=grass_location,
            qgis_prefix_path=qgis_prefix_path,
            input_geo_names=input_geo_names,
            projection=projection,
            catinfo=attr_template,
            cat_ply_info=cat_ply_info,
            cat_riv_info=cat_riv_info,
            outlet_pt_info=outlet_pt_info,
        )
        input_geo_names["cat_ply_info"] = cat_ply_info
        input_geo_names["cat_riv_info"] = cat_riv_info
        input_geo_names["outlet_pt_info"] = outlet_pt_info
        
        if len(lake_attributes) > 0:
            attr_lake = add_lake_attributes(
                grassdb=grassdb,
                grass_location=grass_location,
                qgis_prefix_path=qgis_prefix_path,
                input_geo_names=input_geo_names,
                lake_attributes=lake_attributes,
                catinfo=attr_basic,
            )
        else:
            attr_lake = attr_basic
        
        if len(obs_attributes) > 0:
            attr_obs = add_gauge_attributes(
                grassdb=grassdb,
                grass_location=grass_location,
                qgis_prefix_path=qgis_prefix_path,
                input_geo_names=input_geo_names,
                obs_attributes=obs_attributes,
                catinfo=attr_lake,
            )
        else:
            attr_obs = attr_lake
        
        if outlet_obs_id > 0:
            attr_select = return_interest_catchments_info(
                catinfo=attr_obs,
                outlet_obs_id=outlet_obs_id,
                path_sub_reg_outlets_v=path_sub_reg_outlets_v,
            )
        else:
            attr_select = attr_obs
        
        if path_landuse != "#":
            attr_landuse = calculate_flood_plain_manning_n(
                grassdb=grassdb,
                grass_location=grass_location,
                qgis_prefix_path=qgis_prefix_path,
                catinfo=attr_select,
                input_geo_names=input_geo_names,
                path_landuse=path_landuse,
                path_landuse_info=path_landuse_info,
            )
        else:
            attr_landuse = attr_select
        
        attr_da = streamorderanddrainagearea(attr_landuse)
        
        if path_bkfwidthdepth != "#" or k_in != -1:
            attr_bkf = calculate_bankfull_width_depth_from_polyline(
                grassdb=grassdb,
                grass_location=grass_location,
                qgis_prefix_path=qgis_prefix_path,
                path_bkfwidthdepth=path_bkfwidthdepth,
                bkfwd_attributes=bkfwd_attributes,
                catinfo=attr_da,
                input_geo_names=input_geo_names,
                k_in=k_in,
                c_in=k_in,
            )
        else:
            attr_bkf = attr_da
        
        attr_ncl = update_non_connected_catchment_info(attr_bkf)
        attr_ncl.loc[attr_ncl['RivLength'] < 0,'RivLength'] = 0
        
        join_pandas_table_to_vector_attributes(
            grassdb=grassdb,
            grass_location=grass_location,
            qgis_prefix_path=qgis_prefix_path,
            vector_name=cat_ply_info,
            pd_table=attr_ncl,
            column_types=coltypes,
            columns_names=columns,
        )
        
        join_pandas_table_to_vector_attributes(
            grassdb=grassdb,
            grass_location=grass_location,
            qgis_prefix_path=qgis_prefix_path,
            vector_name=cat_riv_info,
            pd_table=attr_ncl,
            column_types=coltypes,
            columns_names=columns,
        )

        export_files_to_output_folder(
            grassdb=grassdb,
            grass_location=grass_location,
            qgis_prefix_path=qgis_prefix_path,
            input_geo_names=input_geo_names,
            output_riv=out_riv_name,
            output_cat=out_cat_name,
            output_folder=output_folder,
        )
