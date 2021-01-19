from func.grassgis import *
from func.qgis import *
from func.pdtable import *
from func.rarray import *
from utilities.utilities import *
import sqlite3


def define_connected_and_non_connected_lake_type(
    grass,
    con,
    garray,
    str_r="str_grass_r",
    lake="alllake",
    connected_lake="connect_lake",
    non_connected_lake="nonconnect_lake",
    str_connected_lake="str_connected_lake",
):

    #### overlay str and lakes
    exp = "%s = if(isnull('%s'),null(),%s)" % (str_connected_lake, str_r, lake)
    grass.run_command("r.mapcalc", expression=exp, overwrite=True)

    ### obtain connected lake ids
    Connect_Lake_Ids, temp = generate_stats_list_from_grass_raster(
        grass, mode=1, input_a=str_connected_lake
    )
    #### create non connected lake raster
    grass.run_command("g.copy", rast=(lake, non_connected_lake), overwrite=True)
    grass.run_command(
        "r.null", map=non_connected_lake, setnull=Connect_Lake_Ids, overwrite=True
    )
    #### create potential connected lake raster
    exp = "%s = if(isnull('%s'),%s,null())" % (connected_lake, non_connected_lake, lake)
    grass.run_command("r.mapcalc", expression=exp, overwrite=True)

    return