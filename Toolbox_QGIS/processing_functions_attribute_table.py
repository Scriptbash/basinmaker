import numpy as np
import pandas as pd 
import copy 

def Calculate_Longest_flowpath(mainriv_merg_info):
    mainriv_merg_info_sort = mainriv_merg_info.sort_values(["DA"], ascending = (False))
#    print(mainriv_merg_info_sort[['SubId','DowSubId','DA','Strahler','RivLength']])
    longest_flow_pathes = np.full(100,0)
#    print(longest_flow_pathes)
    npath = 1

    #### loop upstream to find longest flow path
    Pathid  = np.full(1000,-1)
    subid = mainriv_merg_info_sort['SubId'].values[0]
    npath_current = 1
    Pathid[npath - 1] = subid
#    print('####################################################################################')
    while len(Pathid[Pathid > 0]) > 0:
        nPathid  =  np.full(1000,-1)
        npath    = npath_current

#        print('###################################')
#        print(npath,Pathid[0:npath])
#        print('###################################')
        for ipath in range(0,npath_current):
            c_subid_ipath = Pathid[ipath]

            if c_subid_ipath < 0:  ### means this path has been closed due to no more subbasin within the lake domain
                continue

            longest_flow_pathes[ipath] = mainriv_merg_info_sort.loc[mainriv_merg_info_sort['SubId'] == c_subid_ipath,'RivLength'] +longest_flow_pathes[ipath] ## add river length to current path
            Strahler_order_ipath = mainriv_merg_info_sort.loc[mainriv_merg_info_sort['SubId'] == c_subid_ipath,'Strahler'].values[0]

            upstream_sub_infos = mainriv_merg_info_sort.loc[mainriv_merg_info_sort['DowSubId'] == c_subid_ipath] ## get upstream info

            if len(upstream_sub_infos) <= 0: ## no more upstream catchment within the domain of the lake
#                print("path        closed        ",ipath)
                continue

            ## look for upstream catchment has the same upstream_sub_infos_eq_Strahler first
#            print(Strahler_order_ipath)
#            print(upstream_sub_infos['Strahler'])
            upstream_sub_infos_eq_Strahler = upstream_sub_infos.loc[upstream_sub_infos['Strahler'] == Strahler_order_ipath]

            if len(upstream_sub_infos_eq_Strahler) > 0: ### has a upstream river has the saem strahler id, no new path will be added
                nPathid[ipath] = upstream_sub_infos_eq_Strahler['SubId'].values[0] ### add this upstream id to nPathid
                continue
            else:
                upstream_sub_infos_eq_Strahler_1 = upstream_sub_infos.loc[upstream_sub_infos['Strahler'] == Strahler_order_ipath - 1]

                for inpath in range(0,len(upstream_sub_infos_eq_Strahler_1)):
                    ### this brance sperate into two or several reaches, the starting river length for all of them are the same
                    if inpath == 0:
                        nPathid[ipath] = upstream_sub_infos_eq_Strahler_1['SubId'].values[inpath]
#                        print(nPathid[ipath],ipath,upstream_sub_infos_eq_Strahler_1['SubId'].values[inpath],'aaaaa',range(0,len(upstream_sub_infos_eq_Strahler_1)))
                    else:
                        nPathid[npath + 1 - 1] = upstream_sub_infos_eq_Strahler_1['SubId'].values[inpath]
                        longest_flow_pathes[npath + 1 - 1] = longest_flow_pathes[ipath]
#                        print(npath + 1 - 1,longest_flow_pathes[npath + 1 - 1],nPathid[npath + 1 - 1],'bbbbb',range(0,len(upstream_sub_infos_eq_Strahler_1)))
                        npath = npath + 1



        Pathid = nPathid
        npath_current = npath
    Longestpath = max(longest_flow_pathes)

    return Longestpath
    
    
    
def New_SubId_To_Dissolve(subid,catchmentinfo,mapoldnew_info,upsubid = -1,ismodifids = -1,modifiidin = [-1],mainriv = [-1],Islake = -1,seg_order = -1):
    sub_colnm = 'SubId'
    routing_info      = catchmentinfo[['SubId','DowSubId']].astype('float').values
    if ismodifids < 0:
        Modify_subids1            = Defcat(routing_info,subid)   ### find all subids drainage to this subid
        if upsubid > 0:
            Modify_subids2        = Defcat(routing_info,upsubid)
            mask = np.in1d(Modify_subids1, Modify_subids2)
            Modify_subids = Modify_subids1[np.logical_not(mask)]
        else:
            Modify_subids =  Modify_subids1

    else:
        Modify_subids =  modifiidin
#    print("##########################################")
#    print(subid)
#    print(Modify_subids)
    cbranch                  = catchmentinfo[catchmentinfo[sub_colnm].isin(Modify_subids)].copy()
    tarinfo                  = catchmentinfo[catchmentinfo[sub_colnm] == subid].copy()   ### define these subs attributes
    ### average river slope info

    mainriv_merg_info = mainriv.loc[mainriv['SubId'].isin(Modify_subids)].copy()
    mainriv_merg_info = mainriv_merg_info.loc[mainriv_merg_info['RivLength'] > 0].copy()
    idx = tarinfo.index[0]
#    print(tarinfo.loc[idx,'BasArea'],"1")
    if len(mainriv_merg_info) > 0:
        tarinfo.loc[idx,'RivLength'] = np.sum(mainriv_merg_info['RivLength'].values)
        tarinfo.loc[idx,'RivSlope']  = np.average(mainriv_merg_info['RivSlope'].values ,weights = mainriv_merg_info['RivLength'].values)
        tarinfo.loc[idx,'FloodP_n']  = np.average(mainriv_merg_info['FloodP_n'].values ,weights = mainriv_merg_info['RivLength'].values)
        tarinfo.loc[idx,'Q_Mean']    = np.average(mainriv_merg_info['Q_Mean'].values   ,weights = mainriv_merg_info['RivLength'].values)
        tarinfo.loc[idx,'Ch_n']      = np.average(mainriv_merg_info['Ch_n'].values     ,weights = mainriv_merg_info['RivLength'].values)
        tarinfo.loc[idx,'BkfWidth']  = np.max(mainriv_merg_info['BkfWidth'].values)
        tarinfo.loc[idx,'BkfDepth']  = np.max(mainriv_merg_info['BkfDepth'].values)

    tarinfo.loc[idx,'BasArea']       = np.sum(cbranch['BasArea'].values)
#    tarinfo.loc[idx,'NonLDArea']     = np.sum(cbranch['NonLDArea'].values)
    if len(cbranch) > 0:
        tarinfo.loc[idx,'BasSlope']      = np.average(cbranch['BasSlope'].values,  weights = cbranch['BasArea'].values)
        tarinfo.loc[idx,'MeanElev']      = np.average(cbranch['MeanElev'].values,  weights = cbranch['BasArea'].values)
        tarinfo.loc[idx,'BasAspect']     = np.average(cbranch['BasAspect'].values, weights = cbranch['BasArea'].values)

        tarinfo.loc[idx,'Max_DEM']       = np.max(cbranch['Max_DEM'].values)
        tarinfo.loc[idx,'Min_DEM']       = np.min(cbranch['Min_DEM'].values)
#    print(tarinfo.loc[idx,'BasArea'],"2")
    if Islake == 1:   ## Meger subbasin covered by lakes, Keep lake outlet catchment  DA, stream order info
        Longestpath = Calculate_Longest_flowpath(mainriv_merg_info)
        tarinfo.loc[idx,'RivLength'] = Longestpath

    elif Islake == 2:
        tarinfo.loc[idx,'RivLength'] = 0.0
        tarinfo.loc[idx,'IsLake']    = 2
    elif Islake < 0:
#        tarinfo.loc[idx,'Strahler']      = -1.2345
#        tarinfo.loc[idx,'Seg_ID']        = -1.2345
#        tarinfo.loc[idx,'Seg_order']     = -1.2345
#        tarinfo.loc[idx,'DA']            = -1.2345
        tarinfo.loc[idx,'HyLakeId']      = -1.2345
        tarinfo.loc[idx,'LakeVol']       = -1.2345
        tarinfo.loc[idx,'LakeArea']      = -1.2345
        tarinfo.loc[idx,'LakeDepth']     = -1.2345
        tarinfo.loc[idx,'Laketype']      = -1.2345
        tarinfo.loc[idx,'IsLake']        = -1.2345

    tarinfo.loc[idx,'centroid_x']    = -1.2345
    tarinfo.loc[idx,'centroid_y']    = -1.2345

    if seg_order >0 :
        tarinfo.loc[idx,'Seg_order']      = seg_order

    mask1 = mapoldnew_info['SubId'].isin(Modify_subids) ## catchment newly determined to be merged to target catchment
    mask2 = mapoldnew_info['nsubid'] == subid ###for subbasin already processed to drainage into this target catchment
    mask  = np.logical_or(mask1,mask2)


    ### the old downsub id of the dissolved polygon is stored in DowSubId
    for col in tarinfo.columns:
        if col == 'SubId':
#            print(tarinfo[col].values[0])
            mapoldnew_info.loc[mask,'nsubid']     = tarinfo[col].values[0]
#            print(mapoldnew_info.loc[mask,'nsubid'])
        elif col == 'nsubid' or col == 'ndownsubid' or col == 'Old_SubId' or col == 'Old_DowSubId':
            continue
        else:
            mapoldnew_info.loc[mask, col]         = tarinfo[col].values[0]
#    print(mapoldnew_info.loc[mask1,['BasArea','nsubid','SubId']])
#    print(mapoldnew_info.loc[mapoldnew_info['nsubid'] == subid,['BasArea','nsubid','SubId']])
    return mapoldnew_info

def Evaluate_Two_Dataframes(Expected,Result,Check_Col_NM = 'SubId'):
    ## check if two have the same column names 
    if (Expected.columns != Result.columns).all():
        print(Expected.columns)
        print(Result.columns)
        return False 
    neql = 0
    ## check for each column two dataframe has the same value 
    for col in Expected.columns:
        if col == 'HRU_ID':
            neql = neql + 1
            continue 
        Array_expect = Expected[col].values
        Array_result = Result[col].values
        if (Array_expect != Array_result).all():
            print(col)
            mask = Array_expect !=Array_result
            print(Expected[Check_Col_NM].values[mask])
        else:
            neql = neql + 1 
            
    return neql == len(Expected.columns) 
            


def UpdateTopology(mapoldnew_info,UpdateStreamorder = 1,UpdateSubId = 1):
    """ Functions will update subid,downsubid, calcuate stream order and 
        update drainage area in the attribute table mapoldnew_info
    ----------

    Notes
    -------

    Returns:
    -------
        mapoldnew_info
    """

    idx = mapoldnew_info.index

    if UpdateSubId > 0:
        for i in range(0,len(idx)):
            nsubid     = mapoldnew_info.loc[idx[i],'nsubid']
            subid      = mapoldnew_info.loc[idx[i],'SubId']
            odownsubid = mapoldnew_info.loc[idx[i],'DowSubId']

            donsubidinfo = mapoldnew_info.loc[mapoldnew_info['SubId'] == odownsubid].copy()

            if (len(donsubidinfo) >0):
                mapoldnew_info.loc[idx[i],'ndownsubid'] = donsubidinfo['nsubid'].values[0]
            else:
                mapoldnew_info.loc[idx[i],'ndownsubid'] = -1

        mapoldnew_info['Old_SubId']    = mapoldnew_info['SubId'].values
        mapoldnew_info['Old_DowSubId'] = mapoldnew_info['DowSubId'].values
        mapoldnew_info['SubId']        = mapoldnew_info['nsubid'].values

        mapoldnew_info['DowSubId'] = mapoldnew_info['ndownsubid'].values

    if UpdateStreamorder < 0:
        return mapoldnew_info

    mapoldnew_info_unique      = mapoldnew_info.drop_duplicates('SubId', keep='first')

    mapoldnew_info_unique      = Streamorderanddrainagearea(mapoldnew_info_unique)

    for i in range(0,len(mapoldnew_info_unique)):
        isubid    =  mapoldnew_info_unique['SubId'].values[i]
        mapoldnew_info.loc[mapoldnew_info['SubId'] == isubid,'Strahler']  = mapoldnew_info_unique['Strahler'].values[i]
        mapoldnew_info.loc[mapoldnew_info['SubId'] == isubid,'Seg_ID']    = mapoldnew_info_unique['Seg_ID'].values[i]
        mapoldnew_info.loc[mapoldnew_info['SubId'] == isubid,'Seg_order'] = mapoldnew_info_unique['Seg_order'].values[i]
        mapoldnew_info.loc[mapoldnew_info['SubId'] == isubid,'DA']        = mapoldnew_info_unique['DA'].values[i]

    return mapoldnew_info



def Streamorderanddrainagearea(catinfoall):
    """ Functions will  calcuate stream order and 
        update drainage area in the attribute table catinfoall
    ----------

    Notes
    -------

    Returns:
    -------
        catinfoall
    """
    catinfo                 = catinfoall.loc[catinfoall['IsLake'] != 2].copy()  ### remove none connected lake catchments, which do not connected to the river system
    catinfo_ncl             = catinfoall.loc[catinfoall['IsLake'] == 2].copy()
    routing_ncl             = catinfo_ncl[['SubId','DowSubId']].astype('float').values

    catlist = np.full((len(catinfo)), -9)
    icat = 0
    iseg = 1
    ### find first segments of all reaches, no upstream reaches
    for i in range(0,len(catinfo)):
        idx = catinfo.index[i]
        if catinfo['SubId'].values[i] == catinfo['DowSubId'].values[i]:
            catinfo.loc[idx,'DowSubId'] = -1
        catid = catinfo['SubId'].values[i]
        if len(catinfo[catinfo['DowSubId'] == catid]) == 0: ### the river seg has no upstream segment
            catlist[icat] = int(catinfo['DowSubId'].values[i])   #### store next reach segment

            #### calculate DA of head watershed include None connected lakes
            if len(routing_ncl) == 0:
                 DA_ncl = 0.0
            else:
                Upstreamcats      = Defcat(routing_ncl,catid)     ### alll subuds
                Up_cat_info       = catinfo_ncl.loc[catinfo_ncl['SubId'].isin(Upstreamcats)].copy()

                if len(Up_cat_info) > 0:
                    DA_ncl            = sum(Up_cat_info['BasArea'].values)
                else:
                    DA_ncl            = 0.0

            catinfo.loc[idx,'DA'] = DA_ncl + catinfo['BasArea'].values[i]
            catinfo.loc[idx,'Strahler'] = 1
            catinfo.loc[idx,'Seg_order'] = 1
            catinfo.loc[idx,'Seg_ID'] = iseg
            icat = icat + 1
            iseg = iseg +1

    catlist = np.unique(catlist)
    catlist = catlist[catlist > 0]
#    print(catlist)
    ### Loop for each first reach, until go to reach intersection
    newcatlist = np.full((len(catinfo)), -9)
    inewstart = 0

    for i in range(0,len(catlist)):
        catid = catlist[i]
        F_intersect = 1
#        print("new start            ",i,catid)
        while F_intersect == 1 and catid > 0:
            Up_Reaches_info = catinfo.loc[catinfo['DowSubId'] == catid].copy()
            cur_Reach_info = catinfo.loc[catinfo['SubId'] == catid].copy()
            curcat_idx = catinfo['SubId'] == catid

            #### calculate DA of None connected lakes
            if len(routing_ncl) == 0:
                DA_ncl = 0.0
            else:
#                print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
#                print(catid)
#                print(routing_ncl)
                Upstreamcats      = Defcat(routing_ncl,catid)     ### alll subuds
                Up_cat_info       = catinfo_ncl.loc[catinfo_ncl['SubId'].isin(Upstreamcats)].copy()
                if len(Up_cat_info) > 0:
                    DA_ncl            = sum(Up_cat_info['BasArea'].values)
                else:
                    DA_ncl            = 0.0


            if(len(cur_Reach_info) <= 0):  ### reach the most downstream of the watersheds
                break

            if len(Up_Reaches_info) == 1:   ### only have one upstream
                catinfo.loc[curcat_idx,'DA'] = cur_Reach_info['BasArea'].values[0] + Up_Reaches_info['DA'].values[0] + DA_ncl
                catinfo.loc[curcat_idx,'Strahler'] = Up_Reaches_info['Strahler'].values[0]
                catinfo.loc[curcat_idx,'Seg_order'] = Up_Reaches_info['Seg_order'].values[0] + 1
                catinfo.loc[curcat_idx,'Seg_ID'] = Up_Reaches_info['Seg_ID'].values[0]
#                print('1',catid,catinfo.loc[curcat_idx,'DA'].values,catinfo.loc[curcat_idx,'Strahler'].values,catinfo.loc[curcat_idx,'Sub_order'].values)
                catid =  int(cur_Reach_info['DowSubId'].values[0])
            else:  ### has mutiple upstram
                if np.min(Up_Reaches_info['Strahler'].values) > 0: ### all upstream has been processed
                    catinfo.loc[catinfo['SubId'] == catid,'DA'] = cur_Reach_info['BasArea'].values[0] + np.sum(Up_Reaches_info['DA'].values) + DA_ncl
                    if np.min(Up_Reaches_info['Strahler'].values) == np.max(Up_Reaches_info['Strahler'].values): ### two reach has the same order
                        catinfo.loc[curcat_idx,'Strahler'] = Up_Reaches_info['Strahler'].values[0] + 1
                        catinfo.loc[curcat_idx,'Seg_order'] = 1
                        catinfo.loc[curcat_idx,'Seg_ID'] = iseg +1
                        iseg = iseg +1
#                        print('2',catid,catinfo.loc[catinfo['SubId'] == catid,'DA'].values,catinfo.loc[catinfo['SubId'] == catid,'Strahler'].values,catinfo.loc[catinfo['SubId'] == catid,'Sub_order'].values)
                    else:
                        max_straorder = np.max(Up_Reaches_info['Strahler'].values)
                        catinfo.loc[curcat_idx,'Strahler']  = max_straorder
                        catinfo.loc[curcat_idx,'Seg_order'] = 1
                        catinfo.loc[curcat_idx,'Seg_ID'] = iseg +1
                        iseg = iseg +1
#                        print('3',catid,catinfo.loc[catinfo['SubId'] == catid,'DA'].values,catinfo.loc[catinfo['SubId'] == catid,'Strahler'].values,catinfo.loc[catinfo['SubId'] == catid,'Sub_order'].values)
                    catid =  int(cur_Reach_info['DowSubId'].values[0])
                else:  ## there are some reach has not been processed, save id to the list and wait for another loob
                    newcatlist[inewstart]  =  int(catid)
                    inewstart = inewstart + 1
                    F_intersect = 0

    mask = catinfoall['SubId'].isin(catinfo['SubId'].values)
    catinfoall.loc[mask,'Seg_ID']    = catinfo['Seg_ID'].values
    catinfoall.loc[mask,'Seg_order'] = catinfo['Seg_order'].values
    catinfoall.loc[mask,'Strahler']  = catinfo['Strahler'].values
    catinfoall.loc[mask,'Seg_ID']    = catinfo['Seg_ID'].values
    catinfoall.loc[mask,'DA']        = catinfo['DA'].values

    ### calcuate channel manning's coefficient
    for i in range(0,len(catinfoall)):
        idx =  catinfoall.index[i]
        # if catinfo['BkfWidth'].values[i] > 0 and catinfo['RivSlope'].values[i] > 0 :
        #     catinfo.loc[idx,'Ch_n'] = calculateChannaln(catinfo['BkfWidth'].values[i],catinfo['BkfDepth'].values[i],
        #                       catinfo['Q_Mean'].values[i],catinfo['RivSlope'].values[i])
        if catinfoall['IsObs'].values[i] > 0:
            if catinfoall['DA_Obs'].values[i] >0:
                catinfoall.loc[idx,'DA_error'] = (catinfoall['DA'].values[i]/1000.0/1000.0 - catinfoall['DA_Obs'].values[i])/catinfoall['DA_Obs'].values[i]
    return catinfoall


def Defcat(out,outletid):
    """ Functions will return upstream ids in out taht drainage 
        to outletid
    ----------

    Notes
    -------

    Returns:
    -------
        Shedid
    """
    otsheds = np.full((1,1),outletid)
    Shedid = np.full((len(out)+1,1),-99999999999)
    psid = 0
    rout = copy.copy(out)
    while len(otsheds) > 0:
        noutshd = np.full((len(out)+1,1),-99999999999)
        poshdid = 0
#        print("################################################a")
        for i in range(0,len(otsheds)):
#            print(otsheds)
#            print(psid,outletid)
            Shedid[psid] = otsheds[i]
#            print(Shedid[psid],otsheds[i])
#            print("##################################################b")
            psid = psid + 1
            irow = np.argwhere(rout[:,1]==otsheds[i]).astype(int)
#            print(len(irow))
            for j in range(0,len(irow)):
                #### if the catchment id already processed skip
                if rout[irow[j],0] in Shedid:
                    continue
                noutshd[poshdid] = rout[irow[j],0]
                poshdid = poshdid + 1
        noutshd = np.unique(noutshd)
        otsheds = noutshd[noutshd>=0]
    Shedid = np.unique(Shedid)
    Shedid = Shedid[Shedid>=0]
    return Shedid
    


def Connect_SubRegion_Update_DownSubId(AllCatinfo,DownCatinfo,Sub_Region_info):
    """ Modify outlet subbasin's downstream subbasin ID for each subregion
    Parameters
    ----------
    AllCatinfo                        : dataframe
        it is a dataframe of the attribute table readed from finalcat_info
        .shp or finalrivply_info.shp
    DownCatinfo                       : dataframe
        It is a dataframe includes two columns:
        'Sub_Reg_ID': the subregion id
        'Dow_Sub_Reg_Id': downstream subbasin id of the outlet subbasin in
        this subregion
    Sub_Region_info                   : dataframe
        It is a dataframe includes subregion informations, with following
        columns:
        'Sub_Reg_ID' : the subregion id
        'Dow_Sub_Reg_Id': the downstream subregion id

    Notes
    -------

    Returns:
    -------
        Sub_Region_info      : dataframe
            An new columns indicate the outlet subbasin id of the sub region
            will be added
        AllCatinfo           : dataframe
            Downstream subbasin ID of each subregion's outlet subbasin will
            be updated.
    """

    ### update downsteam subbasin id for each subregion outlet subbasins
    ### current value is -1, updated to connected downstream subbasin ID
    ###loop for each subregion
    routing_info      = Sub_Region_info[['Sub_Reg_ID','Dow_Sub_Reg_Id']].astype('float').values
    for i in range(0,len(Sub_Region_info)):

        ### obtain all subbasin data for i isubregion
        isubregion = Sub_Region_info['Sub_Reg_ID'].values[i]
        Sub_Region_cat_info = AllCatinfo.loc[AllCatinfo['Region_ID'] == isubregion].copy()

        Sub_Region_info.loc[Sub_Region_info['Sub_Reg_ID'] == isubregion,'N_Up_SubRegion'] = len(Defcat(routing_info,isubregion))

        ### check if this subregion exist in merged data
        if len(Sub_Region_cat_info) <= 0:
            continue

        ### Subregion outlet subbasin ID
        outlet_mask = Sub_Region_cat_info['DowSubId'] == -1
        iReg_Outlet_Subid = Sub_Region_cat_info.loc[outlet_mask,'SubId'].values[0]    #(isubregion - 80000) * 200000 - 1
        Sub_Region_info.loc[Sub_Region_info['Sub_Reg_ID'] == isubregion,'Outlet_SubId'] = iReg_Outlet_Subid
        ### find downstream subregion id of current subregion
        Dow_Sub_Region_id = Sub_Region_info['Dow_Sub_Reg_Id'].values[i]

        ### if this region has no down subregions. do not need to
        ### modify the dowsubid of the outlet subbasin of this subregion
        if Dow_Sub_Region_id < 0:
            continue

        ### find downstrem subbasin id of outlet subbasin
        Down_Sub_info = DownCatinfo.loc[DownCatinfo['value'] == isubregion].copy()

        if len(Down_Sub_info) == 1:###
            DownSubid   = Down_Sub_info['SubId'].values[0]
            AllCatinfo.loc[AllCatinfo['SubId'] == iReg_Outlet_Subid,'DowSubId'] = DownSubid
        ### two subregion drainage to the same downstream subregion,
        ### the Down_Sub_info only contains one upper subregion
        ### the rest do not exist in Down_Sub_info
        elif Dow_Sub_Region_id == 79999:
            AllCatinfo.loc[AllCatinfo['SubId'] == iReg_Outlet_Subid,'DowSubId'] = -1
        else:
            ### find if there is other subabsin drainage to this watershed
            AllUpper_Subregions = DownCatinfo.loc[DownCatinfo['Region_ID'] == Dow_Sub_Region_id].copy()
            if len(AllUpper_Subregions) == 1:
                DownSubid   = AllUpper_Subregions['SubId'].values[0] ### share the same points
                AllCatinfo.loc[AllCatinfo['SubId'] == iReg_Outlet_Subid,'DowSubId'] = DownSubid
            else:
                print("##################################################")
                print("Subregion : ",isubregion,"   To  ",Dow_Sub_Region_id)
                print("Need be manually connected")
                print("##################################################")
    return AllCatinfo,Sub_Region_info


def Update_DA_Strahler_For_Combined_Result(AllCatinfo,Sub_Region_info):
    """ Update Drainage area, strahler order of subbains

    Update drainage area and strahler order for combined routing product
    of each subregions
    Parameters
    ----------
    AllCatinfo                        : dataframe
        it is a dataframe of the attribute table readed from finalcat_info
        .shp or finalrivply_info.shp
    Sub_Region_info                   : dataframe
        It is a dataframe includes subregion informations, with following
        columns:
        'Sub_Reg_ID' : the subregion id
        'Dow_Sub_Reg_Id': the downstream subregion id

    Notes
    -------

    Returns:
    -------
    AllCatinfo           : dataframe
        Downstream DA and strahler order of each subregion along the flow
        pathway between subregions will be updated.
    """
    ### start from head subregions with no upstream subregion
    Subregion_list=Sub_Region_info[Sub_Region_info['N_Up_SubRegion'] == 1]['Sub_Reg_ID'].values
    Subregion_list = np.unique(Subregion_list)
    Subregion_list = Subregion_list.tolist()

    #loop until Subregion_list has no subregions
    # Subregion_list will be updated with downstream subregions of
    # current subregion in Subregion_list
    if len(AllCatinfo.loc[AllCatinfo['DowSubId'] == -1]) > 1:
        print('Wathersed has multiple outlet  ')
        print(AllCatinfo.loc[AllCatinfo['DowSubId'] == -1])
        return AllCatinfo
    elif len(AllCatinfo.loc[AllCatinfo['DowSubId'] == -1]) == 0:
        print('Watershed has no outlet')
        return AllCatinfo
    else:
        Watershedoutletsubid = AllCatinfo.loc[AllCatinfo['DowSubId'] == -1]['SubId'].values[0].astype(int)

    ### Area and DA check
    Total_DA_Subregion = 0.0
    for i in range(0,len(Sub_Region_info)):
        Outletsubid_csubr = Sub_Region_info['Outlet_SubId'].values[i]
        Total_DA_Subregion = Total_DA_Subregion + AllCatinfo.loc[AllCatinfo['SubId'] == Outletsubid_csubr]['DA'].values[0]
        print('######Area and DA check for subregion ',Sub_Region_info['Sub_Reg_ID'].values[i])
        print('DA at the subregion outlet is    ',AllCatinfo.loc[AllCatinfo['SubId'] == Outletsubid_csubr]['DA'].values[0])
        print('Total subregion area is          ',sum(AllCatinfo.loc[AllCatinfo['Region_ID'] == Sub_Region_info['Sub_Reg_ID'].values[i]]['BasArea'].values))

    iloop = 1
    while len(Subregion_list) > 0:
        print("loop  ", iloop)
        print(Subregion_list)
        current_loop_list = copy.copy(Subregion_list)
        Subregion_list = []
        ### loop for current subregion list
        for i in range(0,len(current_loop_list)):
            ### current subregion id
            c_subr_id =  current_loop_list[i]

            ### down subregion id of current subregion
            if c_subr_id == 79999:
                continue

            d_subr_id =  Sub_Region_info[Sub_Region_info['Sub_Reg_ID'] == c_subr_id]['Dow_Sub_Reg_Id'].values[0]
            ### add down subregon id to the list for next while loop
            Subregion_list.append(d_subr_id)

            ### obtain outlet subid of this region
            Outletsubid_csubr = Sub_Region_info[Sub_Region_info['Sub_Reg_ID'] == c_subr_id]['Outlet_SubId'].values[0]
            ### obtain outlet sub info
            Outletsub_info = AllCatinfo.loc[AllCatinfo['SubId'] == Outletsubid_csubr].copy()
            ### obtain down subid of the outlet subbasin
            downsubid = Outletsub_info['DowSubId'].values[0]

            ### downsubid did not exist.....
            if len(AllCatinfo.loc[AllCatinfo['SubId'] == downsubid]) <= 0:
                if int(c_subr_id) != int(Watershedoutletsubid):
                    print('Subregion:   ',c_subr_id)
                    print('SubId is ',Outletsubid_csubr,' DownSubId is  ',downsubid, Watershedoutletsubid,int(c_subr_id) != int(Watershedoutletsubid))
                continue

            downsub_reg_id =  AllCatinfo.loc[AllCatinfo['SubId'] == downsubid]['Region_ID'].values[0]

            if downsub_reg_id != d_subr_id:
                print('Subregion:   ',c_subr_id,'  did not connected with    ',d_subr_id)
                continue

            while downsub_reg_id == d_subr_id:
                csubid = downsubid ### update DA and Strahler for this subbasin

                ### current subid info
                C_sub_info = AllCatinfo.loc[AllCatinfo['SubId'] == csubid].copy()
                ### find all subbasin drainge to this csubid
                Upper_sub_info = AllCatinfo.loc[AllCatinfo['DowSubId'] == csubid].copy()

                ### ## new DA = basin area + DA of upper subregions

                NewDA = C_sub_info['BasArea'].values[0] + sum(Upper_sub_info['DA'].values)

                ### calculate new Strahler orders
                ## up stream Strahler orders
                Strahlers = Upper_sub_info['Strahler'].values
                maxStrahler = max(Strahlers)
                if np.sum(Strahlers == maxStrahler) >=2:
                    newStrahler = maxStrahler + 1
                else:
                    newStrahler = maxStrahler
                #### updateAllCatinfo
                AllCatinfo.loc[AllCatinfo['SubId'] == csubid,'Strahler'] = newStrahler
                AllCatinfo.loc[AllCatinfo['SubId'] == csubid,'DA'] = NewDA

                ####find next downsubbasin id
                downsubid      = C_sub_info['DowSubId'].values[0]

                ### downsubid did not exist.....
                if len(AllCatinfo.loc[AllCatinfo['SubId'] == downsubid]) <= 0:
                    if int(csubid) != int(Watershedoutletsubid):
                        print('Subregion:   ',d_subr_id)
                        print('SubId is ',csubid,' DownSubId is  ',downsubid,Watershedoutletsubid,int(csubid) != int(Watershedoutletsubid))
                    break

                downsub_reg_id = AllCatinfo.loc[AllCatinfo['SubId'] == downsubid]['Region_ID'].values[0]

            ### update list for next loop
        Subregion_list = list(set(Subregion_list))
        iloop = iloop + 1
    print("Check drainage area:")
    print("Total basin area is              ",sum(AllCatinfo['BasArea'].values))
    print("DA of the watersehd outlet is    ",AllCatinfo.loc[AllCatinfo['SubId'] == int(Watershedoutletsubid)]['DA'].values[0])
    print("Total DA of each subregion       ",Total_DA_Subregion)
    return AllCatinfo
    

def Determine_Lake_HRU_Id(Attribute_Table):
    """ Function to determin hruid after combine lake polygon 
    and subbasin polygon 
    ----------

    Notes
    -------

    Returns:
    -------
        None, 
    """
    Attribute_Table = Attribute_Table.fillna(-1)
    Attribute_Table = Attribute_Table.replace(to_replace="NULL",value=-1)
    
    Sub_ID='SubId'
    Sub_Lake_ID = 'HyLakeId'
    Lake_Id = 'Hylak_id'
       
    # get current maximum subbasin Id 
    max_subbasin_id = max(Attribute_Table[Sub_ID].values)
    # total number of new feature by overaly two polygon 
    N_new_features = len(Attribute_Table)
    new_hruid = 1
    new_hruid_list = np.full(N_new_features + 100,np.nan)
    old_newhruid_list = np.full(N_new_features + 100,np.nan)
    
    #The new hru id is determined by following rules
    #1 if subbasin hylake id < 0, means this feature do not have lake 
    #  then, the new hru id  = old subid 
    #2 if subbasin hylke >0 and subbasin hylake = overlayied hyalke id 
    #  then this feature is a lake hru 
    #  the hru id is the hru id  = old subid + max_subbasin_id + 10
    #3 if the subbasin hylakeid >0, but subbasin hylake id != overlaied lake id 
    #  then this feature is not covered by the lake the new hru id  = old subid
     
    for i in range(0,len(Attribute_Table)):
        subid_sf_obj = Attribute_Table[Sub_ID].values[i]
        lakelakeid_sf_obj   = Attribute_Table[Lake_Id].values[i]
        Sub_Lakeid_sf_obj   = Attribute_Table[Sub_Lake_ID].values[i]
        
        ### the null value in the attribute table is not convertable try and set 
        ### to -1 
        try:
            subid_sf = float(subid_sf_obj)
        except:
            subid_sf = -1
            Attribute_Table.loc[i,Sub_ID] = -1
            pass

        try:
            lakelakeid_sf = float(lakelakeid_sf_obj)
        except:
            lakelakeid_sf = -1
            Attribute_Table.loc[i,Lake_Id] = -1
            pass

        try:
            Sub_Lakeid_sf = float(Sub_Lakeid_sf_obj)
        except:
            Sub_Lakeid_sf = -1
            Attribute_Table.loc[i,Sub_Lake_ID] = -1
            pass

        
        # first skip feature with subbasin id < 0
        # deal with this later 
        if subid_sf < 0:
            continue 
            
        # feature is not lake 
        if Sub_Lakeid_sf < 0:
            old_new_hruid     = subid_sf
            Attribute_Table.loc[i,'HRU_IsLake']  = -1
 
        if Sub_Lakeid_sf > 0:
            if lakelakeid_sf == Sub_Lakeid_sf: ### the lakeid from lake polygon = lake id in subbasin polygon
                old_new_hruid     = subid_sf + max_subbasin_id + 10
                Attribute_Table.loc[i,'HRU_IsLake']  = 1
            else: ### the lakeid from lake polygon != lake id in subbasin polygon, this lake do not belong to this subbasin, this part of subbasin treat as non lake hru
                old_new_hruid     = float(subid_sf)
                Attribute_Table.loc[i,'HRU_IsLake']  = -1
        
        # if it is a new hru id         
        if old_new_hruid not in old_newhruid_list:
            Attribute_Table.loc[i,'HRULake_ID'] = new_hruid
            old_newhruid_list[new_hruid] = old_new_hruid
            new_hruid        = new_hruid + 1
        # if it is not new hru id 
        else:
            Attribute_Table.loc[i,'HRULake_ID'] = int(np.argwhere(old_newhruid_list == old_new_hruid)[0])

    # deal with feature with negative subbasin id  
    # use the Sub_Lake_ID to find subbasin id, 
    # if Sub_Lake_ID from lake polygon is also sammller than zero 
    #    report an error 
    for i in range(0,len(Attribute_Table)):
        subid_sf = Attribute_Table[Sub_ID].values[i]
        lakelakeid_sf   = Attribute_Table[Lake_Id].values[i]
        Sub_Lakeid_sf   = Attribute_Table[Sub_Lake_ID].values[i]
        if subid_sf > 0:
            continue 
        if lakelakeid_sf < 0:
            print("lake has unexpected holes ")
            print(Attribute_Table.loc[i,:])
            continue 
        ### find the subid of lakelakeid_sf
        tar_info = Attri_table.loc[(Attri_table[Lake_Id]==lakelakeid_sf) & (Attri_table['HRU_IsLake'] > 0)]
        
        Attribute_Table.loc[i,Sub_ID] = tar_info[Sub_ID].values[0]
        Attribute_Table.loc[i,'HRU_IsLake']  = tar_info['HRU_IsLake'].values[0]
        Attribute_Table.loc[i,'HRULake_ID']  = tar_info['HRULake_ID'].values[0]
        Attribute_Table.loc[i,Sub_Lake_ID] = tar_info[Sub_Lake_ID].values[0]
    
    return Attribute_Table
    