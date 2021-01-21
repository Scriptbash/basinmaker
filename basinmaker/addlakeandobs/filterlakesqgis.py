from func.grassgis import *
from func.qgis import *
from func.pdtable import *
from func.rarray import *
from utilities.utilities import *
import sqlite3


def select_lakes_by_area_r(
    grass,
    con,
    garray,
    str_r,
    threshold_con_lake,
    threshold_non_con_lake,
    lake_attributes,
    lakes="alllake",
    connected_lake="connect_lake",
    non_connected_lake="nonconnect_lake",
    str_connected_lake="str_connected_lake",
    sl_connected_lake="sl_connect_lake",
    sl_non_connected_lake="sl_nonconnect_lake",
    sl_lakes="selected_lakes",
    sl_str_connected_lake="str_sl_connected_lake",
):
    # get lake attributes
    sqlstat = "SELECT %s,%s FROM %s" % (
        lake_attributes[0],
        lake_attributes[2],
        lakes,
    )

    lake_info = pd.read_sql_query(sqlstat, con)
    lake_info = lake_info.fillna(-9999)
    un_sl_con_lakeids = lake_info.loc[
        lake_info[lake_attributes[2]] < threshold_con_lake
    ][lake_attributes[0]].values
    un_sl_noncon_lakeids = lake_info.loc[
        lake_info[lake_attributes[2]] < threshold_non_con_lake
    ][lake_attributes[0]].values
    all_lake_ids = lake_info[lake_attributes[0]].values

    all_connected_lake_array = garray.array(mapname=connected_lake)
    all_non_connected_lake_array = garray.array(mapname=non_connected_lake)

    # remove lakes eixst in raster but not in polygon
    cl_lake_ids = np.unique(all_connected_lake_array)
    cl_lake_ids = cl_lake_ids[cl_lake_ids > 0]
    cl_lake_in_polygon = np.isin(cl_lake_ids, all_lake_ids)
    cl_lake_ids_not_in_ply = cl_lake_ids[np.logical_not(cl_lake_in_polygon)]
    if len(cl_lake_ids_not_in_ply) > 0:
        mask = np.isin(all_connected_lake_array, cl_lake_ids_not_in_ply)
        all_connected_lake_array[mask] = -9999

    # change unselected connected lake to -999
    if len(un_sl_con_lakeids) > 0:
        mask = np.isin(all_connected_lake_array, un_sl_con_lakeids)
        all_connected_lake_array[mask] = -9999

    # remove lakes eixst in raster but not in polygon
    ncl_lake_ids = np.unique(all_non_connected_lake_array)
    ncl_lake_ids = ncl_lake_ids[ncl_lake_ids > 0]
    ncl_lake_in_polygon = np.isin(ncl_lake_ids, all_lake_ids)
    ncl_lake_ids_not_in_ply = ncl_lake_ids[np.logical_not(ncl_lake_in_polygon)]
    if len(ncl_lake_ids_not_in_ply) > 0:
        mask = np.isin(all_non_connected_lake_array, ncl_lake_ids_not_in_ply)
        all_non_connected_lake_array[mask] = -9999

    # change unselected connected lake to -9999
    if len(un_sl_noncon_lakeids) > 0:
        mask = np.isin(all_non_connected_lake_array, un_sl_noncon_lakeids)
        all_non_connected_lake_array[mask] = -9999

    temparray = garray.array()

    temparray[:, :] = all_connected_lake_array[:, :]
    temparray.write(mapname=sl_connected_lake, overwrite=True)
    grass.run_command("r.null", map=sl_connected_lake, setnull=[-9999, 0])
    exp = "%s = int(%s)" % (
        sl_connected_lake,
        sl_connected_lake,
    )
    grass.run_command("r.mapcalc", expression=exp, overwrite=True)

    temparray[:, :] = all_non_connected_lake_array[:, :]
    temparray.write(mapname=sl_non_connected_lake, overwrite=True)
    grass.run_command("r.null", map=sl_non_connected_lake, setnull=[-9999, 0])
    exp = "%s = int(%s)" % (
        sl_non_connected_lake,
        sl_non_connected_lake,
    )
    grass.run_command("r.mapcalc", expression=exp, overwrite=True)

    exp = "%s = if(isnull(%s),int(%s),int(%s))" % (
        sl_lakes,
        sl_connected_lake,
        sl_non_connected_lake,
        sl_connected_lake,
    )
    grass.run_command("r.mapcalc", expression=exp, overwrite=True)
    exp = "%s = if(isnull(int(%s)),null(),%s)" % (
        sl_str_connected_lake,
        str_r,
        sl_connected_lake,
    )
    grass.run_command("r.mapcalc", expression=exp, overwrite=True)

    return
