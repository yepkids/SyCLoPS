import os
import glob

# Create directories dictionary to store file paths
file_dirs = {
    'u': '/global/cfs/projectdirs/m3522/cmip6/ERA5/e5.oper.an.pl/2021*/*_u.*.nc',
    'v': '/global/cfs/projectdirs/m3522/cmip6/ERA5/e5.oper.an.pl/2021*/*_v.*.nc',
    'z': '/global/cfs/projectdirs/m3522/cmip6/ERA5/e5.oper.an.pl/2021*/*_z.*.nc',
    't': '/global/cfs/projectdirs/m3522/cmip6/ERA5/e5.oper.an.pl/2021*/*_t.*.nc',
    'r': '/global/cfs/projectdirs/m3522/cmip6/ERA5/e5.oper.an.pl/2021*/*_r.*.nc',
    'msl': '/global/cfs/projectdirs/m3522/cmip6/ERA5/e5.oper.an.sfc/2021*/*_msl.*.nc'
}

# Get list of all dates from u files
u_list = glob.glob(f'{file_dirs["u"]}')
ymd = [os.path.basename(f).split('_')[-1][:8] for f in u_list]
ymd = sorted(list(set(ymd)))

# Pre-load all files by type and organize by date or month
daily_files = {'u': {}, 'v': {}, 'z': {}, 't': {}, 'r': {}}
#monthly_files = {'msl': {}, 'u10': {}, 'v10': {}}
monthly_files = {'msl': {}}

# Load daily files
for var, var_dir in {k: file_dirs[k] for k in daily_files.keys()}.items():
    all_files = glob.glob(f'{var_dir}')
    for f in all_files:
        date = os.path.basename(f).split('_')[-1][:8]
        daily_files[var][date] = f

# Load monthly files
for var, var_dir in {k: file_dirs[k] for k in monthly_files.keys()}.items():
    all_files = glob.glob(f'{var_dir}')
    for f in all_files:
        month = os.path.basename(f).split('_')[-1][:6]
        monthly_files[var][month] = f

# Write output file
infilename = 'file_list/ERA5_2021_lpsnode_in.txt'
outfilename='file_list/ERA5_2021_lpsnode_out.txt'
zsfile = 'ZSfile_general.nc'
maskfile='/pscratch/sd/y/ykh5116/FIKE/mask.nc'

with open(infilename, "w") as f:
    for date in ymd:
        ym = date[:6]
        
        # Skip dates where not all necessary files are available
        if (date not in daily_files['u'] or date not in daily_files['v'] or 
            date not in daily_files['z'] or date not in daily_files['t'] or 
            date not in daily_files['r'] or ym not in monthly_files['msl']): #or 
            #ym not in monthly_files['u10'] or ym not in monthly_files['v10']):
            continue
        
        line = f"{daily_files['u'][date]};{daily_files['v'][date]};{daily_files['z'][date]};" \
               f"{daily_files['t'][date]};{daily_files['r'][date]};{monthly_files['msl'][ym]};{zsfile};{maskfile}\n" 
               #f"{monthly_files['u10'][ym]};{monthly_files['v10'][ym]};{zsfile}\n"
        
        f.write(line)

with open(outfilename, "w") as f_out:
    for date in ymd:
        f_out.write(f"./nodes/ERA52021/ERA5_lpsnode_{date}.txt\n")
        
print(f"File {infilename} created successfully")
