def Nextcell(N_dir,N_row,N_col):
    if N_dir[N_row,N_col] == 1:
        N_nrow = N_row + 0
        N_ncol = N_col + 1
    elif N_dir[N_row,N_col] == 2:
        N_nrow = N_row + 1
        N_ncol = N_col + 1
    elif N_dir[N_row,N_col] == 4:
        N_nrow = N_row + 1
        N_ncol = N_col + 0
    elif N_dir[N_row,N_col] == 8:
        N_nrow = N_row + 1
        N_ncol = N_col - 1
    elif N_dir[N_row,N_col] == 16:
        N_nrow = N_row + 0
        N_ncol = N_col - 1
    elif N_dir[N_row,N_col] == 32:
        N_nrow = N_row - 1
        N_ncol = N_col - 1
    elif N_dir[N_row,N_col] == 64:
        N_nrow = N_row - 1
        N_ncol = N_col + 0
    elif N_dir[N_row,N_col] == 128:
        N_nrow = N_row - 1
        N_ncol = N_col + 1
    else:
        N_nrow = -9999
        N_ncol = -9999
    return N_nrow,N_ncol

##################################################################3  
def Generaterivnetwork(hydir,cat,allsubinfo,fac,OutputFoldersub):
    flenriv = copy.copy(hydir)
    flenriv[:,:] = -9999   ##### generate empty river raster
    arcatid = np.unique(cat) #### cat all cat id in target small basin
    arcatid = arcatid[arcatid>=0]
    for i in range(0,len(arcatid)):  #### loop for each catchmant in small basin
        lfid = arcatid[i] ### get the fid in large cat file
#        arcpy.AddMessage(lfid)
        lcatinfo = allsubinfo.loc[allsubinfo['FID'] == lfid] ### Get the cat info in large basin info file
#        arcpy.AddMessage(lcatinfo)
        hyid = lcatinfo['HYBAS_ID'].iloc[0]
        Inhyid = allsubinfo.loc[allsubinfo['NEXT_DOWN'] == hyid]
        if len(Inhyid) > 0:
            for in_i in range(0,len(Inhyid)):
                in_FID = Inhyid['FID'].iloc[in_i]
                pp = np.argwhere(cat == in_FID)
                if len(pp) <= 0:
                    continue
                orow,ocol = Getbasinoutlet(in_FID,cat,fac)
                nrow,ncol = Nextcell(hydir,orow,ocol)
                rowcol = np.full((10000,2),-9999) ### creat two dimension array to store route form beginning to outlet of target catchment 
                rowcol [0,0] = nrow
                rowcol [0,1] = ncol
                flen_k = 0
                trow,tcol = Getbasinoutlet(lfid,cat,fac)
                while nrow != trow or ncol != tcol:
                    flen_orow,flen_ocol = nrow,ncol
                    if flen_orow < 0 or flen_ocol<0:
                        break
                    nrow,ncol = Nextcell(hydir,int(flen_orow),int(flen_ocol))
                    flen_k = flen_k + 1
                    rowcol [flen_k,0] = nrow
                    rowcol [flen_k,1] = ncol
                rowcol [flen_k+1,0] = trow
                rowcol [flen_k+1,1] = tcol
                rowcol = rowcol[rowcol[:,0]>=0].astype(int)
                flenriv[rowcol[:,0],rowcol[:,1]] = 1
        else: ### for head watersheds
            if lcatinfo['COAST'].iloc[0] == 1:
                continue
            in_FID = lfid
            trow,tcol = Getbasinoutlet(lfid,cat,fac)
            catrowcol = np.argwhere(cat==in_FID).astype(int)
            catacc = np.full((len(catrowcol),6),-9999)
            catacc[:,0] = catrowcol[:,0]
            catacc[:,1] = catrowcol[:,1]
            catacc[:,2] = fac[catrowcol[:,0],catrowcol[:,1]]
            catacc[:,3] = trow
            catacc[:,4] = tcol
            catacc = catacc[catacc[:,2] > 100]
            if len(catacc) > 0:
                catacc[:,5] = (catacc[:,0] - catacc[:,3])*(catacc[:,0] - catacc[:,3]) + (catacc[:,1] - catacc[:,4])*(catacc[:,1] - catacc[:,4])
                catacc = catacc[catacc[:,5].argsort()]
                nrow,ncol = catacc[len(catacc) - 1,0],catacc[len(catacc) - 1,1]
                rowcol = np.full((10000,2),-9999) ### creat two dimension array to store route form beginning to outlet of target catchment 
                rowcol [0,0] = nrow
                rowcol [0,1] = ncol
                flen_k = 0
                while nrow != trow or ncol != tcol:
                    orow,ocol = nrow,ncol
                    if orow < 0 or ocol<0:
                        break
                    nrow,ncol = Nextcell(hydir,orow,ocol)
                    flen_k = flen_k + 1
                    rowcol [flen_k,0] = nrow
                    rowcol [flen_k,1] = ncol
                rowcol [flen_k+1,0] = trow
                rowcol [flen_k+1,1] = tcol
                rowcol = rowcol[rowcol[:,0]>=0].astype(int)
                flenriv[rowcol[:,0],rowcol[:,1]] = 1
    return flenriv


##################################################################3  

def dbftocsv(filename,outname):
    if filename.endswith('.dbf'):
#        print "Converting %s to csv" % filename
        csv_fn = outname
        with open(csv_fn,'wb') as csvfile:
            in_db = dbf.Dbf(filename)
            out_csv = csv.writer(csvfile)
            names = []
            for field in in_db.header.fields:
                names.append(field.name)
            out_csv.writerow(names)
            for rec in in_db:
                out_csv.writerow(rec.fieldData)
            in_db.close()
#            print "Done..."
    else:
        print "Filename does not end with .dbf"


def Getbasinoutlet(ID,basin,fac):
    catrowcol = np.argwhere(basin==ID).astype(int)
    catacc = np.full((len(catrowcol),3),-9999)
    catacc[:,0] = catrowcol[:,0]
    catacc[:,1] = catrowcol[:,1]
    catacc[:,2] = fac[catrowcol[:,0],catrowcol[:,1]]
    catacc = catacc[catacc[:,2].argsort()]
    return catacc[len(catrowcol)-1,0],catacc[len(catrowcol)-1,1]

def writeraster(w_filname,nraster,dataset):   
    orvh = open(w_filname,"w")
    ncols = arcpy.GetRasterProperties_management(dataset, "COLUMNCOUNT")
    nrows = arcpy.GetRasterProperties_management(dataset, "ROWCOUNT")
    xllcorner = arcpy.GetRasterProperties_management(dataset, "LEFT")
    yllcorner = arcpy.GetRasterProperties_management(dataset, "BOTTOM")
    orvh.write("ncols      "+str(ncols) + "\n")
    orvh.write("nrows      "+ str(nrows) + "\n")
    orvh.write("xllcorner    "+str(xllcorner) + "\n")
    orvh.write("yllcorner    "+str(yllcorner) + "\n")
    orvh.write("cellsize     "+str(cellSize) + "\n")
    orvh.write("NODATA_value  -9999" + "\n")
    orvh.close()
    f_handle = open(w_filname, 'a')
    np.savetxt(f_handle,nraster,fmt='%i')
    f_handle.close()
    
import numpy as np
from scipy.optimize import curve_fit
import arcpy
from arcpy import env
from arcpy.sa import *
import copy
import sys
import shutil
import os
import csv
from simpledbf import Dbf5
from dbfpy import dbf
import pandas as pd
from shutil import copyfile
arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("Spatial")
##### Readed inputs
OutputFolder = sys.argv[1]
Thresholdacc = int(sys.argv[2])
hyshedply = sys.argv[3]

cellSize = float(arcpy.GetRasterProperties_management(OutputFolder + "/" + "dir", "CELLSIZEX").getOutput(0))

SptailRef = arcpy.Describe(OutputFolder + "/" + "dir").spatialReference

if Thresholdacc > 0:
    arcpy.env.workspace =OutputFolder
    hyshddir = "dir"
    hyshdacc = "acc"
    arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(int(SptailRef.factoryCode)) ### WGS84
    StreamRaster = SetNull(Raster(hyshdacc) < Thresholdacc, Raster(hyshdacc))#Con(Raster(hyshdacc) > Thresholdacc, 1, 0)
    dirraster = SetNull(Raster(hyshddir) < 1, Raster(hyshddir))
    StreamRaster = Con(StreamRaster >= 0, 1, 0)
    StreamRaster.save("str")
    copyfile( OutputFolder + "/"+"dir.prj" ,  OutputFolder + "/"+"str.prj")
    arcpy.env.XYTolerance = cellSize
    arcpy.arcpy.env.cellSize = cellSize
    arcpy.env.extent = arcpy.Describe( "dir").extent
    arcpy.env.snapRaster =  "dir"
    Strlink = StreamLink(StreamRaster, dirraster)
    Strlink.save( "strlnk")
    copyfile( OutputFolder + "/"+"dir.prj" ,  OutputFolder + "/"+"strlnk.prj")
    arcpy.RasterToASCII_conversion("strlnk","strlnk.asc")
    Catchment = Watershed(dirraster,Strlink)
    Catchment.save("Cat1")
    copyfile( OutputFolder + "/"+"dir.prj" ,  OutputFolder + "/"+"Cat1.prj")
    StreamToFeature(Strlink, dirraster, "DrainL1","NO_SIMPLIFY")
    copyfile( OutputFolder + "/"+"HyMask.prj" ,  OutputFolder + "/"+"DrainL1.prj")
    arcpy.RasterToPolygon_conversion("Cat1", "Cattemp.shp", "NO_SIMPLIFY")
    copyfile( OutputFolder + "/"+"HyMask.prj" ,  OutputFolder + "/"+"Cattemp.prj")
    arcpy.Dissolve_management("Cattemp.shp", "Cat1.shp", ["gridcode"])
    copyfile( OutputFolder + "/"+"HyMask.prj" ,  OutputFolder + "/"+"Cat1.prj")
    arcpy.AddField_management("Cat1.shp", "COAST", "LONG",10,"","", "", "NULLABLE")
    arcpy.AddField_management("Cat1.shp", "HYBAS_ID", "LONG",10,"","", "", "NULLABLE")
    arcpy.AddField_management("Cat1.shp", "NEXT_DOWN", "LONG",10,"","", "", "NULLABLE")
    fieldList = ["GRID_CODE", "FROM_NODE","TO_NODE"]
    arcpy.JoinField_management("Cat1.shp", "gridcode", "DrainL1.shp", "GRID_CODE", fieldList)
    arcpy.CalculateField_management("Cat1.shp", "HYBAS_ID", '!FROM_NODE! * 1', "PYTHON")
    arcpy.CalculateField_management("Cat1.shp", "NEXT_DOWN", '!TO_NODE! * 1', "PYTHON")
    dbftocsv( OutputFolder + "/"+ "Cat1.dbf",OutputFolder + "/"+"hybinfo.csv")
else:
    arcpy.env.workspace =OutputFolder
    arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(int(SptailRef.factoryCode)) ### WGS84    
    arcpy.Clip_analysis(hyshedply, OutputFolder + "/"+"HyMask.shp", OutputFolder + "/"+"Cat1.shp", "")
    copyfile( OutputFolder + "/"+"HyMask.prj" ,  OutputFolder + "/"+"Cat1.prj")
    dbftocsv( OutputFolder + "/"+ "Cat1.dbf",OutputFolder + "/"+"hybinfo.csv")
    arcpy.env.extent = arcpy.Describe( "dir").extent
    arcpy.env.snapRaster =  "dir"
    arcpy.PolygonToRaster_conversion( OutputFolder + "/"+"Cat1.shp", "FID",  OutputFolder + "/"+
                                      "Cat1", "CELL_CENTER","NONE", cellSize)
#    arcpy.FeatureToRaster_conversion("Cat1.shp", "HYBAS_ID", "Cat1",cellSize)
    arcpy.RasterToASCII_conversion("Cat1", "hybasinfid.asc")
    allsubinfo = pd.read_csv(OutputFolder+"/"+'hybinfo.csv',sep=",",low_memory=False)
    hydir =  arcpy.RasterToNumPyArray(OutputFolder + "/"+'dir.asc',nodata_to_value=-9999)#np.loadtxt(OutputFolder+"/"+ 'dir.asc',dtype = 'i4',skiprows = 6)
    fac =  arcpy.RasterToNumPyArray(OutputFolder + "/"+'acc.asc',nodata_to_value=-9999)#np.loadtxt(OutputFolder+"/"+'acc.asc',dtype = 'i4',skiprows = 6)
    cat =  arcpy.RasterToNumPyArray(OutputFolder + "/"+'hybasinfid.asc',nodata_to_value=-9999)#np.loadtxt(OutputFolder+"/"+'hybasinfid.asc',skiprows = 6)
    allsubinfo['FID'] = pd.Series(allsubinfo.index, index=allsubinfo.index)
    rivsys1 = Generaterivnetwork(hydir,cat,allsubinfo,fac,OutputFolder)
    writeraster(OutputFolder+"/"+'riv1.asc',rivsys1,"dir")
    outStreamLink = StreamLink(OutputFolder+"/"+'riv1.asc', OutputFolder+"/"+ 'dir')
    outStreamLink.save(OutputFolder+"/"+'strlnk')
    Strlink = outStreamLink
    StreamRaster = OutputFolder+"/"+'riv1.asc'
    arcpy.RasterToASCII_conversion( OutputFolder+"/"+'strlnk', OutputFolder+"/"+'strlnk.asc')
    StreamToFeature(outStreamLink, "dir", "DrainL1","NO_SIMPLIFY")
    copyfile( OutputFolder + "/"+"HyMask.prj" ,  OutputFolder + "/"+"DrainL1.prj")

copyfile( OutputFolder + "/"+"HyMask.prj" ,  OutputFolder + "/"+"HyLake.prj")
arcpy.SpatialJoin_analysis(OutputFolder + "/"+"HyLake.shp", OutputFolder + "/"+"DrainL1.shp", OutputFolder + "/"+"LAKE_Riv.shp","JOIN_ONE_TO_ONE","KEEP_ALL","","INTERSECT")
copyfile( OutputFolder + "/"+"HyMask.prj" ,  OutputFolder + "/"+"LAKE_Riv.prj")
arcpy.Select_analysis("LAKE_Riv.shp", "Connect_Lake.shp", '"ARCID" > 0')
arcpy.Select_analysis("LAKE_Riv.shp", "nonConnect_Lake.shp", '"ARCID" <= 0')
copyfile( OutputFolder + "/"+"HyMask.prj" ,  OutputFolder + "/"+"Connect_Lake.prj")
copyfile( OutputFolder + "/"+"HyMask.prj" ,  OutputFolder + "/"+"nonConnect_Lake.prj")

arcpy.env.XYTolerance = cellSize
arcpy.arcpy.env.cellSize = cellSize
arcpy.env.extent = arcpy.Describe( "dir").extent 
arcpy.env.snapRaster =  "dir"
arcpy.RasterToASCII_conversion("Cat1", "hybasinfid.asc")
arcpy.RasterToASCII_conversion(Strlink, 'strlink.asc')
if(Thresholdacc > 0):
    arcpy.RasterToASCII_conversion(StreamRaster, 'riv1.asc')
else:
    arcpy.ASCIIToRaster_conversion(StreamRaster, "str", "INTEGER")
arcpy.DefineProjection_management("hybasinfid.asc", int(SptailRef.factoryCode))
arcpy.DefineProjection_management('strlink.asc', int(SptailRef.factoryCode))
arcpy.DefineProjection_management('riv1.asc', int(SptailRef.factoryCode))
arcpy.PolygonToRaster_conversion( OutputFolder + "/"+"Connect_Lake.shp", "Hylak_id",  OutputFolder + "/"+ "cnlake", "MAXIMUM_COMBINED_AREA","Hylak_id", cellSize)
copyfile( OutputFolder + "/"+"dir.prj" ,  OutputFolder + "/"+"cnlake.prj")
arcpy.RasterToASCII_conversion( OutputFolder + "/"+ "cnlake",  OutputFolder + "/"+ "cnlake.asc")

arcpy.PolygonToRaster_conversion( OutputFolder + "/"+"nonConnect_Lake.shp", "Hylak_id",  OutputFolder + "/"+ "noncnLake", "MAXIMUM_COMBINED_AREA","Hylak_id", cellSize)
copyfile( OutputFolder + "/"+"dir.prj" ,  OutputFolder + "/"+"noncnLake.prj")
arcpy.RasterToASCII_conversion( OutputFolder + "/"+ "noncnLake",  OutputFolder + "/"+ "noncnLake.asc")

arcpy.AddMessage("The generated catchment without lake is located at OutputFolder with name cat1.shp")




#tdbf = Dbf5(OutputFolder +"/"+'DrainL1.dbf')
#Routinfo = tdbf.to_dataframe()
#idata = df.loc[df['Unnamed: 0'] == county[i]]
#### modified from
####http://www.caee.utexas.edu/prof/maidment/giswr2015/Ex5/Ex52015.pdf