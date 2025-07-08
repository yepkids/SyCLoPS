#!/bin/bash
# Please direct any questions to the author of this script (Zenodo @ver 6): Yushan Han (yshhan@ucdavis.edu)
# This is an example of shell commands for producing the SyCLoPS catalogs. A detailed TE documentation can be found at: https://climate.ucdavis.edu/tempestextremes.php. 
# We also provide a manual that explains some procedures and usages of SyCLoPS in more details on the Zenodo SyCLoPS dataset at: https://climate.ucdavis.edu/syclops.php.
# Keep checking the manual for updates on SyCLoPS.
# We recommended running the commands in this file one at a time.

# latname and lonname in the commands below only need to be specified when the latitude and longitude variables in the given dataset use different names other than the standard “lat” and “lon”. 
# Specify logdir to store temporary log files in the desired folder.

# Point to your TempestExtremes directory by specifying: 
TEMPESTEXTREMESDIR=~/tempestextremes/bin

# Define your input and output files (or file lists), for example:
inputfile="ERA5_lpsnode_in.txt"
outputfile="ERA5_lpsnode_out.txt"

# The input file here includes a list of files containing all the required ERA5 variables listed below for each time slice (i.e., per day, month, or year) in a txt file (see an example on Zenodo):
## MSLP/MSL/SLP; U: 925,850,200/250 hPa; V:925,850,200/250 hPa; 
## T(tempeature):850 hPa; R(relative humidity): 850, 100(daily-average or higher frequency OK); 
## Z(geopotential)/H(height): Surface(invariant), 925, 850 (optional if your data has NaNs or missing values), 700, 500, 300/250 hPa;
## VO(relative vorticty): 500 hPa(optional, can be subsituted by using the "_CURL{8,2.5}(U(500hPa),V(500hPa))" operator in DetectNodes (see below). If used, 500 hPa is needed for U and V);

# If there's a time dimension in some invariant surface geopotential (ZS) files, it needs to be removed (averaged) prior to the following procedures, which can be achived by sth like: "ncwa -a time ZS_in.nc ZS_out.nc".
# Please remember to change the variable names below according to your model data.

# The first TE command is to detect LPS nodes and output parameters for classification using DetectNodes:
# TE can parallel files by each time slice in the list when computing.
# Parameters are calculated under DetectNodes' outputcmd using variables in ERA5 in the following order: 
# MSLP, MSLPCC20, MSLPCC55, DEEPSHEAR, UPPTKCC, MIDTKCC, LOWTKCC, Z500CC, VO500AVG, RH100MAX, RH850AVG, T850, Z850, ZS, U850DIFF, WS200PMX.
# 300 hPa and 200 hPa data used in DetectNodes can be replaced by 250 hPa data (See SyCLoPS Appendix A & B). If using 250 hPa data, It is recommended to change the parameter name "WS200PMX" to "WS250PMX".
$TEMPESTEXTREMESDIR/DetectNodes \
--in_data_list $inputfile --out_file_list $outputfile \
--searchbymin MSL --closedcontourcmd "MSL,10,5.5,0" --mergedist 6.0 \
--outputcmd "MSL,min,0;MSL,posclosedcontour,2.0,0;MSL,posclosedcontour,5.5,0;\
_DIFF(_VECMAG(U(200hPa),V(200hPa)),_VECMAG(U(850hPa),V(850hPa))),avg,10.0;\
_DIFF(Z(300hPa),Z(500hPa)),negclosedcontour,6.5,1.0;\
_DIFF(Z(500hPa),Z(700hPa)),negclosedcontour,3.5,1.0;\
_DIFF(Z(700hPa),Z(925hPa)),negclosedcontour,3.5,1.0;\
Z(500hPa),posclosedcontour,3.5,1.0;VO(500hPa),avg,2.5;\
R(100hPa),max,2.5;R(850hPa),avg,2.5;T(850hPa),max,0.0;Z(850hPa),min,0;ZS,min,0;\
U(850hPa),posminusnegwtarea,5.5;_VECMAG(U(200hPa),V(200hPa)),maxpoleward,1.0" \
--timefilter "3hr" --latname "latitude" --lonname "longitude" --mergeequal --logdir "./TE_log"
#"_VECMAG(VAR_10U,VAR_10V),max,2.0" can be added to "--outputcmd" to calculate the optional "WS" parameter. If you add this, you will also need to add "WS" to the codes below and in the Python classifier.
#"Z(850hPa),min,0" for Z850 is not needed if the dataset contains NaNs or missing values (e.g. 1e20) where 850 hPa level is below the surface.
#"_CURL{8,2.5}(U(500hPa),V(500hPa)),min,0" can replace "VO(500hPa),avg,2.5" for VO500AVG if the relative vorticity (VO) is not directly available. The results will be slightly different, but close enough. Another option is to calculate VO at 500 hPa through 500 hPa U and V.
#It is suggested to add the "--mergeequal" argument if you are using ERA5 dataset. This argument merge nodes that have the exact same MSLP values nearby in rare scinarios. ERA5 tends to have more of these cases because it has a relatively low precision (2 decimal places).

# Next, detected nodes are stitched in consecutive time with parameters’ name formatted using StitchNodes. The output is a csv file.
inputfile="ERA5_lpsnode_out.txt"
outputfile="ERA5_lps_tracks.csv"
$TEMPESTEXTREMESDIR/StitchNodes \
--in_list $inputfile --out $outputfile \
--in_fmt "lon,lat,MSLP,MSLPCC20,MSLPCC55,DEEPSHEAR,UPPTKCC,MIDTKCC,LOWTKCC,\
Z500CC,VO500AVG,RH100MAX,RH850AVG,T850,Z850,ZS,U850DIFF,WS200PMX" \
--range 4.0 --mintime "18h" --maxgap "12h" --threshold "MSLPCC55,>=,100.0,5" --out_file_format "csv"
# If you are using a different time resolution (e.g. 6hrs), please refer to the "Other Tips" section for information on how to set specific argument parameters.

# Now, to detect LPS size blobs for calculating LPS size (LPSAREA), we first need to use VariableProcessor to produce smoothed cyclonic relative vorticity from 850 hPa U and V. 
# The _CURL{8,3} operator is used below to smooth the vorticity field by evaluating the curl of the wind field using 8 equiangular points at a distance of 3° GCD. 
# You may skip the following TE commands for calculating LPS size if you are only interested in tropical systems.
inputfile="ERA5_sizeblob_in.txt" # This list should include files of 850 hPa U and V for the desired time frames
outputfile="ERA5_smoothed_850RV.txt"
$TEMPESTEXTREMESDIR/VariableProcessor --in_data_list $inputfile \
--out_data_list $outputfile --var "_CURL{8,3}(U(850hPa),V(850hPa))" \
--varout "Vorticity" --latname latitude --lonname longitude --timefilter "3hr"

# The cyclonic vorticity is defined to be always positive. Thus, we need to flip the sign of the relative vorticity field in the Southern Hemisphere.
inputfile="ERA5_smoothed_850RV.txt" 
outputfile="ERA5_smoothed_cyclonic_850RV.txt"
$TEMPESTEXTREMESDIR/VariableProcessor --in_data_list $inputfile --out_data_list $outputfile \
--var "_COND(_LAT(),Vorticity,_PROD(Vorticity,-1))" --varout "Cyclonic_Vorticity" --latname latitude --lonname longitude

# Now, detect LPS size blobs for calculating LPS size using DetectBlobs. This command outputs detected features marked by binary masks:
inputfile="DetectBlobs_size_input.txt" 
outputfile="DetectBlobs_size_output.txt"
# The inputfile here should include the cyclonic vorticity files output by the last command (files in "ERA5_smoothed_cyclonic_850RV.txt") and files of U and V at 925 hPa for the desired time frame.
$TEMPESTEXTREMESDIR/DetectBlobs --in_data_list $inputfile --out_list $outputfile \
--thresholdcmd "((Cyclonic_Vorticity,>=,2e-5,0) & (_VECMAG(U(925hPa),V(925hPa)),>=,12.0,0)) | (Cyclonic_Vorticity,>=,4e-5,0)" \
--geofiltercmd "area,>=,1e4km2" --tagvar "blobid" --latname latitude --lonname longitude --timefilter "3hr" --logdir "./TE_log"

# Lastly, derive properties of blobs using BlobStats for LPS node pairing and LPSAREA computation in the Python classifier.
# This command will output a list of information about blob's centroid, lat/lon maximum extent, and size along with their IDs.
# One can opt to calculate blobs’ IKE by the sumvar operation in the command (this is slow if single-threaded):
inputfile="DetectBlobs_size_output.txt"
outputfile="ERA5_size_blob_stats.txt"
$TEMPESTEXTREMESDIR/BlobStats --in_list $inputfile --out_file $outputfile \
--findblobs --var "blobid" --out "centlon,centlat,minlat,maxlat,minlon,maxlon,area" \
--latname latitude --lonname longitude --out_fulltime
# add this optional line to calculate IKE for each blob/node: --sumvar "_PROD(_SUM(_POW(U(925hPa),2),_POW(V(925hPa),2)),0.5)" 

# After completing all the necessary steps of TE commands, 
# the last step is to execute the classifier python script to compute the final RAWAREA and LOWAREA values, form the input LPS catalog for the classification and output the final classified LPS catalog:

python SyCLoPS_classifier.py

#-----------------------------------Other Tips---------------------------------------#

# Note that the above TE commands are designed for 3-hourly data frequency. If a
# If the 6-hourly frequency detection rate is adopted, the following changes are required/recommended (follow the same logic for other frequencies):

# 1. In the DetectNodes and DetectBlobs commands, the time_filter argument should be tuned to “6hr" or just delete the argument.”
# 2. In the StitchNodes command, the range argument, which represents the maximum distance in GCD an LPS candidate can move between two consecutive time steps, should be
#   doubled to “8.0” or changed to “6.0” (a 6.0◦ GCD range should be enough to cover the vast majority of fast-moving LPSs).
# 3. In the StitchNodes command, a new argument “ --prioritize MSLP” should be added if the above range argument is set to “8.0”. (This method is experimental and preferred.)
# 4. Recommended: In the --threshold argument of the StitchNodes command, "5" means 5 steps which is equivalent to a (5-1)*3=12 hrs interval.
#   Thus, "MSLPCC55,>=,100.0,5" should be changed to --threshold "MSLPCC55,>=,100.0,3" if using 6-hourly detection rate.

# A sample code for specialized regional (Nordic Sea) PL detection (using 1-hour detection rate):

# $TEMPESTEXTREMESDIR/DetectNodes
# -–in_data_list $inputfile -–out_file_list $outputfile
# -–searchbymin MSL -–closedcontourcmd "MSL,10,5.5,0"
# -–mergedist 1.5
# -–outputcmd "..."
# -–minlat 45 -–maxlat 85 -–minlon 320 -–maxlon 70
# -–latname "latitude" -–lonname "longitude" -–logdir "./TE_log"

# $TEMPESTEXTREMESDIR/StitchNodes
# -–in_list $inputfile -–out $outputfile
# -–in_fmt "lon,lat,MSLP,MSLPCC20,MSLPCC55,DEEPSHEAR,UPPTKCC,MIDTKCC,LOWTKCC,\
# Z500CC,VO500AVG,RH100MAX,RH850AVG,T850,Z850,ZS,U850DIFF,WS200PMX" \
# -–range 1.4 -–mintime "6h" -–maxgap "6h" -–threshold "MSLPCC55,>=,100.0,5"
## Since some TLCs can be very short-lived, it is recommended to keep the step/hour requirements low in the --mintime, --maxgap and --threshold arguments here.
