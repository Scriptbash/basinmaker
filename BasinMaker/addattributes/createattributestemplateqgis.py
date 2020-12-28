from processing_functions_raster_array import *
from processing_functions_raster_grass import *
from processing_functions_raster_qgis import *
from processing_functions_vector_grass import *
from processing_functions_vector_qgis import *
from utilities import *
import sqlite3
from addlakeandobs.definelaketypeqgis import generate_stats_list_from_grass_raster


def create_catchments_attributes_template_table(
    grassdb,
    grass_location,
    catchments,
    columns,
):

    import grass.script as grass
    import grass.script.setup as gsetup
    from grass.pygrass.modules import Module
    from grass.pygrass.modules.shortcuts import general as g
    from grass.pygrass.modules.shortcuts import raster as r
    from grass.script import array as garray
    from grass.script import core as gcore
    from grass_session import Session

    os.environ.update(
        dict(GRASS_COMPRESS_NULLS="1", GRASS_COMPRESSOR="ZSTD", GRASS_VERBOSE="1")
    )
    PERMANENT = Session()
    PERMANENT.open(gisdb=grassdb, location=grass_location, create_opts="")

    con = sqlite3.connect(
        os.path.join(grassdb, grass_location, "PERMANENT", "sqlite", "sqlite.db")
    )

    catids, temp = generate_stats_list_from_grass_raster(
        grass, mode=1, input_a=catchments
    )
    catids = np.array(catids)
    attr_template = pd.DataFrame(
        np.full((len(catids), len(columns)), -9999), columns=columns
    )

    attr_template["SubId"] = catids

    return attr_template
