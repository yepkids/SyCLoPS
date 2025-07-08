#!/bin/bash
# Please direct any questions to the author of this script: Yushan Han (yshhan@ucdavis.edu)
# Version: 2024-12-10

TEMPESTEXTREMESDIR=~/tempestextremes/bin #Change this if necessary
# We recommended running the commands in this file one at a time.

# Optionally, one can use StitchBlobs to first give each detected precipitation/size blob a Blob ID (1-based) in the output nc file
# and then implement the "Blob_idtag.py" to alter the tag numbers of each blob in the nc file according to a tagging system arranged
# by the users. For example, All blobs that are paired with a TC node is tagged 1, and all the blobs paried with a TLC node is tagged 2, etc.
# This tagged blob nc file can then be used in potential applications such as calculating the IKE accumulation of a type of LPS
# or the precipitation contribution percentage of a type of LPS.

# Since the SyCLoPS program does not require detecting precipitaiton blob, we need to first detect precipitation blobs following the
# method we mentioned in the SyCLoPS manuscript:
inputfile="DetectBlobs_preci_input.txt"  # The inputfile here should include the cyclonic vorticity files previously generated in "ERA5_smoothed_cyclonic_850RV.txt" (see "TE_commands.sh" for details) and files of 3-hourly (or other freqeuncies that match the DetectNodes detection rate) precipitation for the desired time frame.
outpufile="DetectBlobs_preci_output.txt"
$TEMPESTEXTREMESDIR/DetectBlobs --in_data_list $inputfile --out_list $outputfile \
--thresholdcmd "Cyclonic_Vorticity,>=,0.00002,0;tp,>=,0.0003,0.0" --geofiltercmd "area,>=,1e4km2" \
--tagvar "lps_tag" --latname latitude --lonname longitude --logdir "./TE_log" 

# Derive properties of precipitation blobs using BlobStats for LPS node pairing.
# This command will output a list of information about blob's centroid and lat/lon maximum extent along with their IDs.
inputfile="DetectBlobs_preci_output.txt"
$TEMPESTEXTREMESDIR/BlobStats --in_list 'DetectBlobs_preci_output.txt' --findblobs --out_file Blob_preci_stats.txt \
--var 'lps_tag' --out 'centlon,centlat,minlat,maxlat,minlon,maxlon' \
--out_fulltime --latname latitude --lonname longitude

# Then, assign uniquely-indexed (1-based,e.g., 1,2,3,4,5,6...) masks to each detected blob using TE's Stitchblob with the argument "--tagonly".
# For size blobs we already detected in the "TE_commands.sh":
inputfile="DetectBlobs_size_output.txt"
outputfile="StitchBlobs_size_output.txt"
$TEMPESTEXTREMESDIR/StitchBlobs --in_list $inputfile --out_list $outputfile \
--var "blobid" --tagonly --latname latitude --lonname longitude

# For precipitation blobs we just detected:
inputfile="DetectBlobs_preci_output.txt"
outputfile="StitchBlobs_preci_output.txt"
$TEMPESTEXTREMESDIR/StitchBlobs --in_list $inputfile --out_list $outputfile \
--var "blobid" --tagonly --latname latitude --lonname longitude

#---------------------------------Other Optional Steps--------------------------------------#

## An example TE code to extract the 3-hourly precipitation for each grid point contained within each precipitation blob that are tagged "1":
## The "ERA5_precip_in.txt" file should contain 3-hourly (or other frequency) precipitation (tp) files 
# and the tagged precipitation blob nc files output by "Blob_idtag.py"
# $TEMPESTEXTREMESDIR/VariableProcessor --in_data_list "ERA5_precip_in.txt" --out_data_list "ERA5_precip_out.txt" \
# --var "_PROD(_EQUALS(blobid,1),_PROD(tp,1000))" --varout "tp_lps" \
# --timefilter "3hr" --latname latitude --lonname longitude --logdir "./TE_log"

## An example TE code to calculate 925 hPa integrated knetic energy (IKE) at each grid point contained within each size blob that are tagged “1”: 
## The "ERA5_size_in.txt" file should contain 925 U and V files and the tagged size blob nc files output by "Blobs_idtag_app.py"
# $TEMPESTEXTREMESDIR/VariableProcessor --in_data_list "ERA5_ike_in.txt" --out_list ""ERA5_ike_out.txt"" \
# --var "_PROD(_EQUALS(blobid,1), _PROD(_SUM(_POW(U(925hPa),2),_POW(V(925hPa),2)),0.5),_AREA())" \
#--timefilter "3hr"  --varout "ike_lps" --latname latitude --lonname longitude --logdir "./TE_log"

## If you have multiple tags, please change the tag number accordingly within the "..._EQUALS(blobid,1)..." argument. For example,
## If you are running the command for blobs that are tagged (masked) "2", change this argument to   "..._EQUALS(blobid,2)..."