print("\nThis is the SyCLoPS main program for executing TempestExtremes (TE) commands and run the Python classifier program.\n")
print("Please direct any questions to the author of this script: Yushan Han (yshhan@ucdavis.edu)\n")
print("Version: 2025-12-01 \n")
print("The SyCLoPS manual might be helpful if you run into issues with the srcipts.")
import os
import subprocess
import glob
import time

print("Please remember to review the code and comments in this file and modify accordingly before running. \n\
Activate an appropriate Python environment that has Xarray, Pandas, PyArrow, multiprocess, and Scipy installed.\n")

# Point to your TempestExtremes (TE) directory by specifying:
TEMPESTEXTREMESDIR = os.path.expanduser('~/tempestextremes/bin')
model_data_name = "ERA5" # Change this to your model or dataset name used in the input and output file lists.

print("Please change the following specifications according to your requirements. The default is for ERA5 data at 3-hourly interval.\n")
# Define your time interval.
timefilter = "6hr"
# Define the merge distance for DetectNodes and the range distance for StitchNodes. Below is the recommendation for 3-hourly data.
# If your time interval is different from the default 3-hour, please change the MergeDist and RangeDist variables accordingly.
# A range distance of 6.0 degree is recommended for 6-hourly data if you only focus on tropical systems. If you care about extratropical systems at 6-hourly interval, a range distance of 8.0 degree is recommended.
MergeDist = 4.000001 #DetectNodes argument. We recommend adding 0.000001 to the distance when your MergeDist = RangeDist to avoid floating point precision issues in some rare cases.
RangeDist = 6.00000 #StitchNodes argument. 
MinTime = "18h" #StitchNodes argument
MaxGap = "12h" #StitchNodes argument. This can be shortened if you are using a very high-resolution dataset to avoid excessive noise.
MSLP55CCStep = 5 #Steps for the MSLPCC55 threshold in StitchNodes to remove too-short and too-weak tracks. If you use 6-hourly data, you may lower this value to 3 or 2.
latname = 'lat' #Name of the latitude variable in your dataset.
lonname = 'lon' #Name of the longitude variable in your dataset.
print("Note: If your RangeDist is larger than MergeDist, the program will automatically use the 'prioritize' flag in StitchNodes. See the manual 2.2 for details.\n")
# Tips for detecting tropical-like cyclones (TLCs: polar lows and subtropical storms) specifically (prioritizing detection of TLCs): 
# Because they are very small and transient, it's better to use a MergeDist <=3 degrees and a RangeDist of a equal distance at 1-hour or 3-hour intervals.

# Set this to True if you want to use parallel processing with srun when applicable.
use_srun = True # Change to True if you want to use srun. Also see line 183 to verify if "srun" works on your machine.
use_250hPa_only = False # Set to True if your dataset only contains 250 hPa level for upper-level wind (U and V) and geopotential height.
srun_n = "256"    # Number of tasks (threads) for srun
uv_level_value = "250hPa" if use_250hPa_only else "200hPa"
z_level_value = "250hPa" if use_250hPa_only else "300hPa"

# Create a log directory if it doesn't exist (for storing temporary logs of TempestExtremes). You may change the path and name of this log directory.
log_dir= "./TE_log"
os.makedirs(log_dir, exist_ok=True)

#If your dataset is not on a unstructured grid (i.e., not lon-lat grid), you should specify a connectivity file below and set use_connect to True.
use_connect = False 
connectivity_file = "connect_healpix_grid_zoom_8_example_filename.txt"


# Mode choice by user
while True:
    mode=input("Do you want to classify tropical-like cyclones (y/n)? Default is 'y'. If you only focus on tropical systems or typical extratropical systems, you may enter 'n' to save time: ")
    if mode == '':
        mode='Y'
    if mode in ['Y', 'N', 'y', 'n']:
        print("You entered:",mode)
        break
    else:
        print("Invalid Entry. Please read the insturction and enter again.")

while True:
    step=input("\nFrom which step do you want to start running? (1: DetectNodes (from beginning), 2: StitchNodes, 3: VariableProcessor, 4: DetectBlobs, 5: BlobStats, 6: Classifier). Default is 1: ")
    if step == '':
        step = '1'
    if step not in ['1', '2', '3', '4', '5', '6']:
        print("Invalid step. Please enter a number between 1 and 6.")
    else:
        print("You chose to start from step", step)
        step = int(step)
        break

# Define your input and output file lists and filenames.
inputfile_DN = f"file_list/{model_data_name}_lpsnode_in.txt" #"This txt file should contain the list of existing input files that contains all the necessary variables for DetectNodes. \
# Please refer to "Manual/Required_Variables.png" for the list of required variables.")
outputfile_DN = f"file_list/{model_data_name}_lpsnode_out.txt" #This txt file should contain a list of output path and filenames that will be generated by DetectNodes and should have the same number of lines as the inputfiles.")
outputfile_SN = f"out_track/{model_data_name}_tracks_range60.csv" #This is the single output track file's filename in StitchNodes.
inputfile_VP = f"{model_data_name}_sizeblob_in.txt" #This txt file should contain the list of U and V at 850 hPa and 925 hPa levels.")
outputfile_VP = f"{model_data_name}_crvort_out.txt" #This txt file should contain the list of output cyclonic relative vorticity path and filenames that will be generated by VariableProcessor \
# and should have the same number of lines as the inputfiles.")
outputfile_DB = f"{model_data_name}_sizeblob_out.txt" #This txt file should contain the list of output path and filenames that will be generated by DetectBlobs and should have the same number of lines as the inputfiles.")
outputfile_BS = f"{model_data_name}_size_blob_stats.txt" #This is the single output file of BlobStats which contains the blob statistics.

# Define atmospheric variable names in your dataset. Change them if necessary.
mslp_name = 'MSL'
z_name = 'Z'
u_name = 'U'
v_name = 'V'
r_name = 'R'
t_name = 'T'
zs_name = 'ZS'
#vo_name = 'VO' # Relative vorticity is no longer needed. It can be calculated via TE using U and V.

if os.path.exists(log_dir):
    for f in glob.glob(os.path.join(log_dir, "*.txt")):
        os.remove(f)
# Check for "EXCEPTION" in the last line of the last log file in ./TE_log
def check_log_dir(log_dir,t0):
    log_files = sorted(glob.glob(os.path.join(log_dir, "*")))
    if log_files:
        mod_time = os.path.getmtime(log_files[0])
        if mod_time - t0 < 0:
             print("No log files were generated in the log directory. Check the error message output by TempestExtremes.")
             exit(1)
        with open(log_files[0], "r") as f:
            lines = f.readlines()
            last_line = lines[-1].strip() if lines else ''
            if "EXCEPTION" in last_line:
                print("Error found in this TE command:", last_line)
                exit(1)
    else:
        print("No log files were generated in the log directory. Check the error message output by TempestExtremes.")
        exit(1)

# Build the TempestExtremes commands. Feel free to modify the atmospheric variable names and levels.
print("\nRemember to change the atmospheric variable names in the TE commands if necessary.\n")
print("If you run into issues with TE commands and can't solve them here in the main program, you may use 'TE_commands.sh' (which contains original TE bash codes) for further debugging.\n\
You may also check the TE documentation and the SyCLoPS manual.")

detect_nodes_cmd = [
    f"{TEMPESTEXTREMESDIR}/DetectNodes",
    "--in_data_list", inputfile_DN,
    "--out_file_list", outputfile_DN,
    "--searchbymin", f"{mslp_name}",
    "--closedcontourcmd", f"{mslp_name},10,5.5,0",
    #"--thresholdcmd", f"{mask_name},=,1,0",
    "--mergedist", str(MergeDist),
    "--outputcmd", #Output the following parameters for classification.
    f"{mslp_name},min,0;" #MSLP
    f"{mslp_name},posclosedcontour,2.0,0;" #MSLPCC20
    f"{mslp_name},posclosedcontour,5.5,0;" #MSLPCC55
    f"_VECMAG(uas,vas),max,3.0;" #WS ##This is an optional parameter (10m max wind speed) for reference purpose.
    f"_DIFF(_VECMAG({u_name}({uv_level_value}),{v_name}({uv_level_value})),_VECMAG({u_name}(850hPa),{v_name}(850hPa))),avg,10.0;" #DEEPSHEAR
    ##If variables in your inputfiles are on a single level, e.g., U200 representing U at 200 hPa, then directly use "U200."
    f"_DIFF({z_name}({z_level_value}),{z_name}(500hPa)),negclosedcontour,6.5,1;" #UPPTKCC
    f"_DIFF({z_name}(500hPa),{z_name}(700hPa)),negclosedcontour,3.5,1;" #MIDTKCC
    f"_DIFF({z_name}(700hPa),{z_name}(925hPa)),negclosedcontour,3.5,1;" #LOWTKCC
    f"{z_name}(500hPa),posclosedcontour,3.5,1;" #Z500CC
    f"_CURL{{8,3.0}}({u_name}(500hPa),{v_name}(500hPa)),min,0;" #VO500AVG 
    f"{r_name}(100hPa),max,2.5;" #RH100MAX
    f"{r_name}(850hPa),avg,2.5;" #RH850AVG
    f"{t_name}(850hPa),max,0.0;" #T850
    f"{z_name}(850hPa),min,0;" #Z850 ##This parameter is not necessary if the dataset contains NaNs or missing values where 850 hPa level is below the surface. If you removed this, please also remove "Z850" in the StitchNodes command below
    f"{zs_name},min,0;" #ZS ##This parameter is not necessary if the dataset contains NaNs or missing values where 850 hPa level is below the surface, but we recommend keeping it for other useful information. If you removed this, please also remove "ZS" in the StitchNodes command below
    f"{u_name}(850hPa),posminusnegwtarea,5.5;" #U850DIFF
    f"_VECMAG({u_name}({uv_level_value}),{v_name}({uv_level_value})),maxpoleward,1.0", #WS200PMX
    "--timefilter", timefilter,
    "--latname", latname,
    "--lonname", lonname,
    "--mergeequal",
    "--logdir", "./TE_log"
]

stitch_nodes_cmd = [
    f"{TEMPESTEXTREMESDIR}/StitchNodes",
    "--in_list", outputfile_DN,
    "--out", outputfile_SN,
    "--in_fmt", "lon,lat,MSLP,MSLPCC20,MSLPCC55,WS,DEEPSHEAR,UPPTKCC,MIDTKCC,LOWTKCC,"
                "Z500CC,VO500AVG,RH100MAX,RH850AVG,T850,Z850,ZS,U850DIFF,WS200PMX",
    # Change the parameter (names) in this argument according to the outputcmd in DetectNodes if applicable. If using 250 hPa data, it's recommended to change the parameter name "WS200PMX" to "WS250PMX".
    "--range", str(RangeDist),
    "--mintime", MinTime,
    "--maxgap", MaxGap,
    "--threshold", f"MSLPCC55,>=,100.0,{MSLP55CCStep}",
    "--out_file_format", "csv",
    #"--caltype","360_day"
]
if MergeDist > RangeDist:
     stitch_nodes_cmd.extend(["--prioritize", "MSLP"])

variable_processor_cmd = [
    f"{TEMPESTEXTREMESDIR}/VariableProcessor",
    "--in_data_list", inputfile_VP,
    "--out_data_list", outputfile_VP,
    "--var", f"_COND(_LAT(),_CURL{{8,3}}({u_name}(850hPa),{v_name}(850hPa)),_PROD(_CURL{{8,3}}({u_name}(850hPa),{v_name}(850hPa)),-1)),{u_name}(925hPa),{v_name}(925hPa)",
    "--varout", "Cyclonic_Vorticity,U925,V925", # U and V at 925 hPa (U925 & V925) will be used in the next step.
    "--latname", latname,
    "--lonname", lonname,
    "--logdir", "./TE_log",
    "--timefilter", timefilter
]

detect_blobs_cmd = [
    f"{TEMPESTEXTREMESDIR}/DetectBlobs",
    "--in_data_list", outputfile_VP, 
    "--out_list", outputfile_DB, 
    "--thresholdcmd", "((Cyclonic_Vorticity,>=,2e-5,0) & (_VECMAG(U925,V925),>=,12.0,0)) | (Cyclonic_Vorticity,>=,4e-5,0)",
    "--geofiltercmd", "area,>=,1e4km2",
    "--tagvar", "blobid",
    "--latname", latname,
    "--lonname", lonname,
    "--timefilter", timefilter,
    "--logdir", "./TE_log"
]

blobstats_cmd = [
    f"{TEMPESTEXTREMESDIR}/BlobStats",
    "--in_list", outputfile_DB,
    "--out_file", outputfile_BS,
    "--findblobs",
    "--var", "blobid",
    "--out", "centlon,centlat,minlat,maxlat,minlon,maxlon,area",
    "--latname", latname,
    "--lonname", lonname,
    #"--sumvar", "_PROD(_SUM(_POW(U(925hPa),2),_POW(V(925hPa),2)),0.5)", 
    # This is an optional argument to calculate IKE (Integrated Kinetic Energy) for each blob. Note this computation takes a long time with one thread. 
    # One may use GNU Parallel to split the output file and speed up the process (See the manual 2.2 for details).
    "--out_fulltime"
]

if use_srun:
    detect_nodes_cmd = ["srun", "-n", srun_n] + detect_nodes_cmd # It's possible that your machine use a different command for parallel processing, \
    # such as `mpirun` or `mpiexec`. Adjust accordingly.
    variable_processor_cmd = ["srun", "-n", srun_n] + variable_processor_cmd
    detect_blobs_cmd = ["srun", "-n", srun_n] + detect_blobs_cmd
    
if use_connect:
    detect_nodes_cmd.extend(["--in_connect", connectivity_file])
    stitch_nodes_cmd.extend(["--in_connect", connectivity_file])
    variable_processor_cmd.extend(["--in_connect", connectivity_file])
    detect_blobs_cmd.extend(["--in_connect", connectivity_file])
    blobstats_cmd.extend(["--in_connect", connectivity_file])
    
try:
    if step == 1:
        t0 = time.time()
        # Check if outputfile_DN has only one row. If true then a different check for TE errors is needed.
        with open(outputfile_DN, 'r') as f:
            lines = f.readlines()
            linelen=len(lines)
        if linelen > 1 and use_srun:
            print("Running DetectNodes...")
            subprocess.run(detect_nodes_cmd, check=True)
            check_log_dir(log_dir,t0)
        else:
            print("Running DetectNodes with a single line of inputfiles...")
            result=subprocess.run(detect_nodes_cmd, capture_output=True, check=True)
            # Capture the output and check for errors
            lines = result.stdout.decode('utf-8').strip().split('\n')
            last_line = lines[-1] if lines else ''
            if "EXCEPTION" in last_line:
                print("Error in DetectNodes command:", last_line)
                exit(1)
        t1 = time.time()
        print(f"DetectNodes command executed successfully in {t1 - t0:.2f} seconds.")

    if step <= 2:
        t0 = time.time()
        print("Running StitchNodes...")
        subprocess.run(stitch_nodes_cmd, check=True)
        mod_time = os.path.getmtime(outputfile_SN)
        if not os.path.isfile(outputfile_SN) or time.time() - mod_time > 10:
            print(f"Error: Output file {outputfile_SN} was not correctly created by StitchNodes. Please check if StitchNodes ran correctly.")
            exit(1)
        t1 = time.time()
        print(f"StitchNodes command executed successfully in {t1 - t0:.2f} seconds.")

    if mode.lower() == 'y' and step <= 5:
        print("You chose to classify tropical-like cyclones. The program will now run additional steps for calculating LPSAREA.\n")
        
        if step <= 3:
            t0 = time.time()
            print("Running VariableProcessor...")
            if use_srun:
                subprocess.run(variable_processor_cmd, check=True)
                check_log_dir(log_dir)   
            else:    
                result=subprocess.run(variable_processor_cmd, capture_output=True, check=True)
                # Capture the output and check for errors
                lines = result.stdout.decode('utf-8').strip().split('\n')
                last_line = lines[-1] if lines else ''
                if "EXCEPTION" in last_line:
                    print("Error in VariableProcessor command:", last_line)
                    exit(1)
            t1 = time.time()
            print(f"VariableProcessor command executed successfully in {t1 - t0:.2f} seconds.")
            
        if step <= 4:
            t0 = time.time()
            print("Running DetectBlobs...")
            if use_srun:
                subprocess.run(detect_blobs_cmd, check=True)
                check_log_dir(log_dir)   
            else:    
                result=subprocess.run(detect_blobs_cmd, capture_output=True, check=True)
                # Capture the output and check for errors
                lines = result.stdout.decode('utf-8').strip().split('\n')
                last_line = lines[-1] if lines else ''
                if "EXCEPTION" in last_line:
                    print("Error in DetectBlobs command:", last_line)
                    exit(1)
            t1 = time.time()
            print(f"DetectBlobs command executed successfully in {t1 - t0:.2f} seconds.")

        if step <= 5:
            t0 = time.time()
            print("Running BlobStats...")
            result=subprocess.run(blobstats_cmd, capture_output=True, check=True)
            # Capture the output and check for errors
            lines = result.stdout.decode('utf-8').strip().split('\n')
            last_line = lines[-1] if lines else ''
            if "EXCEPTION" in last_line:
                print("Error in BlobStats command:", last_line)
                exit(1)
            t1 = time.time()
            print(f"BlobStats command executed successfully in {t1 - t0:.2f} seconds.")

    elif mode.lower() != 'y' and step <= 5:
        print("You chose not to classify tropical-like cyclones. The program will skip the additional steps for calculating LPSAREA.")
        
except subprocess.CalledProcessError as e:
    print("Error running TE commands. Please refer to the error messages given by TempestExtremes for details:", e)
    
print("\nAll TempestExtremes commands executed successfully. Now running SyCLoPS_classifier.py to classify LPSs.\n")

confirm=input("Please review the code and comments in SyCLoPS_classifier.py and modify accordingly before running. Are you ready to run SyCLoPS_classifier.py now? (y/n). Default is 'n': ")
if confirm.lower() != 'y':
    print("You chose not to run SyCLoPS_classifier.py now. you can always run it later by entering step '6' when prompted at the beginning of this program or just executing 'python SyCLoPS_classifier.py' in the terminal.")
    exit()
    
try:
    subprocess.run(["python", "SyCLoPS_Classifier.py"], check=True) 
    print("\nSyCLoPS_classifier.py executed successfully.")
except subprocess.CalledProcessError as e:
    print("\nError running SyCLoPS_classifier.py:", e)