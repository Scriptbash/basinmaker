import geopandas 
import numpy as np
import os
import pandas as pd 


def save_modified_attributes_to_outputs(mapoldnew_info,tempfolder,OutputFolder,cat_name,riv_name,Path_final_riv,dis_col_name='SubId'):


    NEED_TO_REMOVE_IDS = ["SubId_1", "Id","nsubid2", "nsubid","ndownsubid","Old_SubId","Old_DowSub","Join_Count","TARGET_FID","Id","SubID_Oldr","HRU_ID_N_1","HRU_ID_N_2","facters","Old_DowSubId","SubIdt2"]

    
    
    if riv_name != '#':

        riv_pd = geopandas.read_file(Path_final_riv)
        riv_pd['Old_SubId'] = riv_pd['SubId']
        
        cat_pd = mapoldnew_info.drop(columns = 'geometry').copy(deep=True)
        # remove all columns 
        riv_pd = riv_pd[['geometry','Old_SubId']]        
        riv_pd = pd.merge(riv_pd, cat_pd, on='Old_SubId', how='left')             
        riv_pd = riv_pd.dissolve(by=dis_col_name, aggfunc='first',as_index=False)
        
        
        mapoldnew_info = mapoldnew_info.dissolve(by=dis_col_name, aggfunc='first',as_index=False)
        mapoldnew_info = add_centroid_in_wgs84(mapoldnew_info,"centroid_x","centroid_y")
        
        cat_c_x_y = mapoldnew_info[["centroid_y","centroid_x"]].copy(deep=True)
        riv_pd = riv_pd.drop(columns = ["centroid_y","centroid_x"])
        riv_pd = riv_pd.join(cat_c_x_y) 

        riv_pd_nncls_routing_info = mapoldnew_info[mapoldnew_info['Lake_Cat'] != 2][['SubId','DowSubId']].copy(deep=True)
        remove_channel = []
        for subid in riv_pd_nncls_routing_info['SubId'].values:
            if subid not in riv_pd_nncls_routing_info['DowSubId'].values:
                remove_channel.append(subid)                
        riv_pd = riv_pd[~riv_pd.SubId.isin(remove_channel)]   
        cat_colnms = riv_pd.columns
        drop_cat_colnms = cat_colnms[cat_colnms.isin(NEED_TO_REMOVE_IDS)]
        riv_pd = riv_pd.drop(columns=drop_cat_colnms)
        riv_pd.to_file(os.path.join(OutputFolder,riv_name))
        
        mapoldnew_info.loc[mapoldnew_info.SubId.isin(remove_channel),'RivSlope'] = -1.2345
        mapoldnew_info.loc[mapoldnew_info.SubId.isin(remove_channel),'RivLength'] = -1.2345
        mapoldnew_info.loc[mapoldnew_info.SubId.isin(remove_channel),'FloodP_n'] = -1.2345
        mapoldnew_info.loc[mapoldnew_info.SubId.isin(remove_channel),'Ch_n'] = -1.2345
        mapoldnew_info.loc[mapoldnew_info.SubId.isin(remove_channel),'Max_DEM'] = -1.2345
        mapoldnew_info.loc[mapoldnew_info.SubId.isin(remove_channel),'Min_DEM'] = -1.2345
        
        cat_colnms = mapoldnew_info.columns
        drop_cat_colnms = cat_colnms[cat_colnms.isin(NEED_TO_REMOVE_IDS)]
        mapoldnew_info = mapoldnew_info.drop(columns=drop_cat_colnms)
        mapoldnew_info.to_file(os.path.join(OutputFolder,cat_name))
  
    
    else: 

        mapoldnew_info = mapoldnew_info.dissolve(by=dis_col_name, aggfunc='first',as_index=False)
    
        if "centroid_y" in mapoldnew_info.columns:

            mapoldnew_info = add_centroid_in_wgs84(mapoldnew_info,"centroid_x","centroid_y")
            mapoldnew_info["SubId"] = mapoldnew_info.index
            riv_pd_nncls_routing_info = mapoldnew_info[mapoldnew_info['Lake_Cat'] != 2][['SubId','DowSubId']].copy(deep=True)
            remove_channel = []
            for subid in riv_pd_nncls_routing_info['SubId'].values:
                if subid not in riv_pd_nncls_routing_info['DowSubId'].values:
                    remove_channel.append(subid)                
                            
            mapoldnew_info.loc[mapoldnew_info.SubId.isin(remove_channel),'RivSlope'] = -1.2345
            mapoldnew_info.loc[mapoldnew_info.SubId.isin(remove_channel),'RivLength'] = -1.2345
            mapoldnew_info.loc[mapoldnew_info.SubId.isin(remove_channel),'FloodP_n'] = -1.2345
            mapoldnew_info.loc[mapoldnew_info.SubId.isin(remove_channel),'Ch_n'] = -1.2345
            mapoldnew_info.loc[mapoldnew_info.SubId.isin(remove_channel),'Max_DEM'] = -1.2345
            mapoldnew_info.loc[mapoldnew_info.SubId.isin(remove_channel),'Min_DEM'] = -1.2345
            
                
        cat_colnms = mapoldnew_info.columns
        drop_cat_colnms = cat_colnms[cat_colnms.isin(["SHAPE","SubId_1", "Id","nsubid2", "nsubid","ndownsubid","Old_DowSub","Join_Count","TARGET_FID","Id","SubID_Oldr","HRU_ID_N_1","HRU_ID_N_2","facters","Old_DowSubId"])]
        mapoldnew_info = mapoldnew_info.drop(columns=drop_cat_colnms)
        mapoldnew_info.to_file(os.path.join(OutputFolder,cat_name))
        return mapoldnew_info


def Remove_Unselected_Lake_Attribute_In_Finalcatinfo_purepy(finalcat_ply, Conn_Lake_Ids):
    """Functions will set lake id not in Conn_Lake_Ids to -1.2345 in attribute
        table of Path_Finalcatinfo
    ----------

    Notes
    -------

    Returns:
    -------
        None, the attribute table of Path_shpfile will be updated
    """
    
    mask1 = np.logical_not(finalcat_ply['HyLakeId'].isin(Conn_Lake_Ids))
    mask2 = finalcat_ply['Lake_Cat'] != 2
    mask = np.logical_and(mask1,mask2)
    
    finalcat_ply.loc[mask,'HyLakeId'] = 0
    finalcat_ply.loc[mask,'LakeVol'] = 0
    finalcat_ply.loc[mask,'LakeArea'] = 0
    finalcat_ply.loc[mask,'LakeDepth'] = 0
    finalcat_ply.loc[mask,'Laketype'] =0
    finalcat_ply.loc[mask,'Lake_Cat'] = 0
    
    return finalcat_ply
    
def clean_attribute_name_purepy(table,names):
    remove_column_names = table.columns[np.logical_not(np.isin(table.columns,names))]
    table = table.drop(columns=remove_column_names)
    return table 
    
def clean_geometry_purepy(data):
    narow = ~data['geometry'].isna()
    emrow = ~data.is_empty
    arearow = data.area > 0.00000001

    row1 = np.logical_and(narow,emrow)
    rowselect = np.logical_and(arearow,row1)
    data = data.loc[rowselect]

    return data   
    
def add_area_in_m2(data,prj_crs,area_col):
    src_src = data.crs
    tost = data.copy()

    tost= data.to_crs(prj_crs)
    tost[area_col] = tost.area
    
    out= tost.copy(deep=True).to_crs(src_src)

    return out 

def add_centroid_in_wgs84(data,colx,coly):
    src_src = data.crs
    tost = data.copy()
    
    tost= tost.to_crs('EPSG:4326')

    tost[coly] = tost.geometry.centroid.y
    tost[colx] = tost.geometry.centroid.x
    
    out= tost.copy(deep=True).to_crs(src_src)
    
    return out
    

    
    
    
    