## Other potential applications of SyCLoPS datasets (Size and Precipitation Blob tagging)

# Please direct any questions to the author of this script: Yushan Han (yshhan@ucdavis.edu)
import os
import numpy as np
import xarray as xr
import pandas as pd
import multiprocessing as ma
from scipy.spatial import cKDTree
import time

#-----------Additional TE commands-----------#
#Optional: exercute the additional TE commands in Python. One can also run these commands in a terminal.
TEcommand="sh TE_optional.sh"
os.system(TEcommand)

#---------Constants and File Names----------#
nthread=64 # Number of threads to use for parallel computing in this program
ClassCatalog="SyCLoPS_classified.parquet" #The SyCLoPS classified catalog output by SyCLoPS_classifier.py
SizeBlobStat="Size_blob_stats.parquet" #The size blob statistics previously saved by SyCLoPS_classifier.py
PreciBlobStat="ERA5_preci_blob_stats.txt"  #The preci blob statistics file output by BlobStats

#The filename of the size blob outputfile of TE's StitchBlobs (the first TE command in "TE_optional.sh"):
SizeStitchFile="StitchBlobs_size_output.txt" 
#The filename of the size blob outputfile of TE's StitchBlobs (the second TE command in "TE_optional.sh"):
PreciStitchFile="StitchBlobs_preci_output.txt"#The filename of the preci blob outputfile of TE's StitchBlobs

#------------------Functions----------------#
#The blobpairing function below outputs a blob index and a node index in tuples
def blobpairing(k):
    nodepair=[]
    T=cKDTree(list(zip(X[NodeTime[k]],Y[NodeTime[k]],Z[NodeTime[k]])))
    dft=dfc.iloc[NodeTime[k]] #At the same timestep for blobs and nodes
    for i2 in BlobTime[k]: 
        #First pair blobs with nodes that are within 5 degrees GCD of their centroids:
        idx=T.query_ball_point((x[i2],y[i2],z[i2]),r=5*(np.pi/180))
        if len(idx)>1:        
            node=dfc.MSLP.iloc[np.array(NodeTime[k])[idx]].idxmin()
            nodepair.append((i2,node))
        elif len(idx)==1:
            node=NodeTime[k][idx[0]]
            nodepair.append((i2,node))
        else:
            #If blobs are not paired with any nodes at this point, pairing nodes that are bounded by the extent of the blobs:
            if dfblob.maxlon[i2]-dfblob.minlon[i2]>180:
                nid=dft[((dft.LON>=350)&(dft.LON<360))|((dft.LON>=0)&(dft.LON<=10))\
                    &(dft.LAT>=dfblob.minlat[i2])&(dft.LAT<=dfblob.maxlat[i2])].index.values
            else:
                nid=dft[(dft.LON>=dfblob.minlon[i2])&(dft.LON<=dfblob.maxlon[i2])\
                    &(dft.LAT>=dfblob.minlat[i2])&(dft.LAT<=dfblob.maxlat[i2])].index.values
            if len(nid)>0:
                node=dfc.MSLP.iloc[nid].idxmin()
                nodepair.append((i2,node))
    return nodepair
#---------------Data Preparation----------------#
#Load the classified catalog in parquet format (PyArrow may be needed. See https://arrow.apache.org/docs/python/install.html)
dfc=pd.read_parquet(ClassCatalog)
#Load the size blob stats file previously saved in the classification process ("SyCLoPS_classifier.py")
dfsb=pd.read_parquet(SizeBlobStat)

#Open and format the preci blob statistics file output by TE's BlobStats
dfblob=pd.read_csv(PreciBlobStat,sep="\t", header=None)
dfblob=dfblob.drop(dfblob.columns[[1]], axis=1)
dfblob.columns=["blobid","time","centlon","centlat","minlat","maxlat","minlon","maxlon"]
#Generate a list of LPS node and preci blob index for each time step.
temp_index1=np.arange(0,len(dfc),1);temp_index2=np.arange(0,len(dfblob),1)
dfc['ind']=temp_index1;dfblob['ind']=temp_index2
NodeTime=dfc.groupby(dfc['ISOTIME'])['ind'].apply(list)
temp_index=np.arange(0,len(dfblob),1)
BlobTime=dfblob.groupby(dfblob['time'])['ind'].apply(list)

#Convert longitudes and latitudes in both the input LPS catalog and blob stats dataset to the spherical coordinates (x,y,z):
#This is for implementing KDTrees in the function
LAT=np.array(dfc.LAT)
LON=np.array(dfc.LON)
X=np.cos(LON*(np.pi/180))*np.cos(LAT*(np.pi/180))
Y=np.sin(LON*(np.pi/180))*np.cos(LAT*(np.pi/180))
Z=np.sin(LAT*(np.pi/180))
lon=np.array(dfblob.centlon)
lat=np.array(dfblob.centlat)
x=np.cos(lon*(np.pi/180))*np.cos(lat*(np.pi/180))
y=np.sin(lon*(np.pi/180))*np.cos(lat*(np.pi/180))
z=np.sin(lat*(np.pi/180))

#---------------Preci Blob Pairing--------------#
#Perform the function to pair preci blobs to LPS node
#To save time, multiprocessing is recommended. Single-threaded may take ~1.5hrs for 12.5 million blobs.
#Multiprocessing may take up more physical memroy (~ 43GB with 64 threads)
startt = time.time()
pool_obj = ma.Pool(nthread)
nodepair_list=pool_obj.map(blobpairing,range(len(BlobTime)))
pool_obj.close()

#processing the output tuple list and pair LSP nodes to preci blobs.
nodepair_list=np.concatenate(nodepair_list)
dfblob['paired_node']=-1
blobidx=[i[0] for i in nodepair_list] 
nodematched=[i[1] for i in nodepair_list]
dfblob.loc[blobidx,'paired_node']=nodematched #Indices of paried nodes of each blob
endt = time.time()
print("Time lapsed (s) for the preci blob pairing section: "+ str(endt-startt))
#----------------Blob Tagging-------------------#
#This is the default blob tagging system used in the SyCLoPS manuscript. 
# Users may alter this arrangement to assign LPS tags of their choice.
tcid=dfc[(dfc.Short_Label=='TC') & (dfc.Track_Info.str.contains('TC'))].index.values 
msid=dfc[((dfc.Short_Label.str.contains('TLO'))|(dfc.Short_Label.str.contains('TD'))) & (dfc.Track_Info.str.contains('MS'))].index.values 
ssid=dfc[(dfc.Short_Label=='SS(STLC)')&(dfc.Track_Info.str.contains('SS'))].index.values 
plid=dfc[(dfc.Short_Label=='PL(PTLC)')&(dfc.Track_Info.str.contains('PL'))].index.values 
blobtag=np.ones(len(dfc))*5 #5= Other systems
blobtag[tcid]=1 #1=TC tags
blobtag[msid]=2 #2=MS tags
blobtag[ssid]=3 #3=SS tags
blobtag[plid]=4 #4=PL tags
#Generate a new column in both the size and preci blob dataframe for assigning LPS tags defined above
dfsb['blobtag']=0
dfsb.loc[dfsb.paired_node>=0,'blobtag']=blobtag[[dfsb[dfsb.paired_node>=0].paired_node.to_numpy()]][0]
dfblob['blobtag']=0
dfblob.loc[dfblob.paired_node>=0,'blobtag']=blobtag[[dfblob[dfblob.paired_node>=0].paired_node.to_numpy()]][0]

#Save the preci blob stats file future uses
dfblob.to_parquet("Preci_blob_stats.parquet")

#Group the LPS tags with their blobids generated by TE's StitchBlobs. Note that the blobids are 1-based.
preciblob_class=dfblob.groupby('blobtag')['blobid'].apply(list)
print('precipitation blob tag groups:')
print(preciblob_class)
sizeblob_class=dfsb.groupby('blobtag')['blobid'].apply(list)
print('size blob tag groups:')
print(sizeblob_class)
#exit()

#---------------Blob Mask Tagging---------------#
'''
## Example codes to utilize dask to elevate processing speed of the section below:

from mpi4py import MPI
import time
from dask_mpi import initialize

initialize(memory_limit=0.05)

from distributed import Client
client = Client()


## If you are testing this script in an intereactive mode (e.g., ipynb), you can start dask with this instead:
import dask
from distributed import Client

#This point to the scheduler_file generated by dask mpi
scheduler_file = os.path.join(os.environ["PSCRATCH"], "DetectLow/submission/scheduler_file.json") 
print(scheduler_file)

dask.config.config["distributed"]["dashboard"]["link"] = "{JUPYTERHUB_SERVICE_PREFIX}proxy/{host}:{port}/status"
client = Client(scheduler_file=scheduler_file)
client
'''

#For the final blob mask tagging process, we highly recommend users to use dask for fast processing with large-scale datasets 
#See the comment section above for initializing dask in Python script
#Read the stitchblob outputfile list in parallel using dask:
dfpreci=xr.open_mfdataset(PreciStitchFile,parallel=True).object_id
dfsize=xr.open_mfdataset(SizeStitchFile,parallel=True).object_id

#If SizeStitchFile or PreciStitchFile is a single nc file, use:
#dfpreci=xr.open_mfdataset(PreciStitchFile).object_id
#dfsize=xr.open_mfdataset(SizeStitchFile).object_id

#Alter the original indexed blob masks in the original StitchBlobs files to the new tagged masks:
dfpreci=dfpreci.where(~(dfpreci.isin(preciblob_class[0])),0)
dfpreci=dfpreci.where(~(dfpreci.isin(preciblob_class[1])),1)
dfpreci=dfpreci.where(~(dfpreci.isin(preciblob_class[2])),2)
dfpreci=dfpreci.where(~(dfpreci.isin(preciblob_class[3])),3)
dfpreci=dfpreci.where(~(dfpreci.isin(preciblob_class[4])),4)
dfpreci=dfpreci.where(~(dfpreci.isin(preciblob_class[5])),5)

dfsize=dfsize.where(~(dfsize.isin(sizeblob_class[0])),0)
dfsize=dfsize.where(~(dfsize.isin(sizeblob_class[1])),1)
dfsize=dfsize.where(~(dfsize.isin(sizeblob_class[2])),2)
dfsize=dfsize.where(~(dfsize.isin(sizeblob_class[3])),3)
dfsize=dfsize.where(~(dfsize.isin(sizeblob_class[4])),4)
dfsize=dfsize.where(~(dfsize.isin(sizeblob_class[5])),5)


#Then output the altered StitchBlobs files (by year):
years, datasets = zip(*dsb1.groupby("time.year"))
paths = [f"sizeblob_out/size_blobs_{y}.nc" for y in years]
xr.save_mfdataset(datasets,paths)
#The output nc files can be used in the optional stpes documented in "TE_optional.sh" to produce several applications
#associated with the tagged precipitation and size blobs.