def add_lakes_and_obs_into_existing_watershed_delineation(
    input_geo_names,
    path_lakefile_in="#",
    lake_attributes = [],
    path_obsfile_in="#",
    obs_attributes = [],
    path_sub_reg_outlets_v = '#',
    threshold_con_lake = 0,
    threshold_non_con_lake = 0,
    search_radius = 100,
    alllake = 'all_lakes',
    lake_boundary ='lake_boundary',
    connected_lake = 'connect_lake', 
    non_connected_lake = 'nonconnect_lake',
    str_connected_lake = 'str_connected_lake', 
    sl_connected_lake = 'sl_connected_lake',  
    sl_non_connected_lake = 'sl_nonconnect_lake', 
    sl_lakes = 'selected_lakes' ,
    sl_str_connected_lake = 'str_sl_connected_lake',
    nfdr_arcgis = 'nfdr_arcgis',
    nfdr_grass = 'nfdr_grass',
    max_memroy=1024 * 4,
    grassdb="#",
    grass_location="#",
    qgis_prefix_path="#",
    gis_platform="qgis",
):    
    cat_add_lake = 'cat_add_lake'
    lake_pourpoints = 'lake_pourpoints'
    lake_new_cat_ids = []
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
        from addlakeandobs.addlakesqgis import add_lakes_into_existing_watershed_delineation
        from addlakeandobs.addobsqgis import add_obs_into_existing_watershed_delineation
    if path_lakefile_in != '#':
        add_lakes_into_existing_watershed_delineation(
            grassdb,
            grass_location,
            qgis_prefix_path,
            input_geo_names,
            path_lakefile_in,
            lake_attributes,
            threshold_con_lake,
            threshold_non_con_lake,
            alllake = alllake,
            lake_boundary = lake_boundary,
            connected_lake = connected_lake, 
            non_connected_lake = non_connected_lake,
            str_connected_lake = str_connected_lake, 
            sl_connected_lake = sl_connected_lake,  
            sl_non_connected_lake = sl_non_connected_lake, 
            sl_lakes = sl_lakes ,
            sl_str_connected_lake = sl_str_connected_lake,
            nfdr_arcgis = nfdr_arcgis,
            nfdr_grass = nfdr_grass,
            cat_add_lake = cat_add_lake,
            lake_pourpoints = lake_pourpoints,
            max_memroy = max_memroy,
        )
    if path_obsfile_in !='#':
        add_obs_into_existing_watershed_delineation(
            grassdb = grassdb,
            grass_location = grass_location,
            qgis_prefix_path = qgis_prefix_path,
            input_geo_names = input_geo_names,
            path_obsfile_in = path_obsfile_in,
            path_lakefile_in = path_lakefile_in,
            obs_attributes = obs_attributes,
            search_radius = search_radius,
            lake_pourpoints = lake_pourpoints,
            path_sub_reg_outlets_v = path_sub_reg_outlets_v,
            max_memroy = 1024*4,
            obsname = 'obs',
            pourpoints_add_obs ='pourpoints_add_obs', 
        )        









