#! /usr/bin/env requires-python

# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "googlemaps",
#     "openpyxl",
#     "pandas",
# ]
# ///

import os
import sys
import datetime
import googlemaps
import pandas as pd
import warnings

if len(sys.argv) > 3:
    print("\nToo many arguments\n\nRequire 'API_KEY' 'INPUT_FILE'\n\nExiting...")
    sys.exit()
if len(sys.argv) < 3:
    print("Not enough arguments\n\nRequire 'API_KEY' 'INPUT_FILE'\n\nExiting...")
    sys.exit()

API_KEY = sys.argv[1]
INPUT = sys.argv[2]
if os.path.exists(INPUT) == False:
    print("Argument INPUT_FILE not a valid path and or file\n\nExiting...")
    sys.exit()
INPUT_FQFN = os.path.abspath(INPUT)
INPUT_DIR = os.path.split(INPUT_FQFN)[0]
INPUT_FILE = os.path.split(INPUT_FQFN)[1]

NORTH_BOUNDING_COORD = -8.000
SOUTH_BOUNDING_COORD = -45.000
EAST_BOUNDING_COORD = 156.000
WEST_BOUNDING_COORD = 104.000
BOUNDING_COORDS = {
    "northeast": [NORTH_BOUNDING_COORD, EAST_BOUNDING_COORD],
    "southwest": [SOUTH_BOUNDING_COORD, WEST_BOUNDING_COORD]
}

gmaps = googlemaps.Client(key=API_KEY)
row = 0
errors = []
with warnings.catch_warnings(record=True):
    warnings.simplefilter("always")
    df = pd.read_excel(INPUT_FQFN, index_col=0, dtype=str)


class bcolors:
    if os.name == 'nt':
        BLUE = 'echo ^<ESC^>[34m [34mBlue[0m'
        GREEN = 'echo ^<ESC^>[32m [32mGreen[0m'
        RED = 'echo ^<ESC^>[31m [31mRed[0m'
        YELLOW = 'echo ^<ESC^>[33m [33mYellow[0m'
        RESET = 'echo ^<ESC^>[0m [0mReset[0m'
        UNDERLINE = 'echo ^<ESC^>[4m [4mUnderline[0m'
    if os.name == 'posix':
        BLUE = '\033[34m'
        GREEN = '\033[92m'
        RED = '\033[91m'
        YELLOW = '\033[33m'
        RESET = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'

while row < len(df.index):

    # Y = lat, X = lon
    cell_lat = float(df['Latitude'].iloc[row])
    cell_lat_isnull = df['Latitude'].isnull().iloc[row]

    cell_lon = float(df['Longitude'].iloc[row])
    cell_lon_isnull = df['Longitude'].isnull().iloc[row]

    address = f"{df['Address 1'].iloc[row]}, {df['Address 2'].iloc[row]}, {df['Address 3'].iloc[row]}, {df['City'].iloc[row]} {df['State Or Province'].iloc[row]} {df['Postal Code'].iloc[row]}"
    address_encode = address.replace("nan, ", "").strip()
    print("")
    print(f'Row {row+2} - {address_encode}')

        # Check if LAT/LON value is already present
    if cell_lat_isnull == False or cell_lon_isnull == False:
        if WEST_BOUNDING_COORD <= cell_lon <= EAST_BOUNDING_COORD and SOUTH_BOUNDING_COORD <= cell_lat <= NORTH_BOUNDING_COORD:
            print(f'    {bcolors.BLUE}SKIPPING - LAT/LON EXISTS WITHIN BOUNDS{bcolors.RESET}')
            row+=1
            continue
        else: # If LAT/LON exists but out of bounds, evaluate address and update LAT/LON
            print(f'    {bcolors.YELLOW}RE-EVALUATING - LAT/LON EXISTS OUTSIDE BOUNDS{bcolors.RESET}')

    ### Google maps geocode import method
    response = gmaps.geocode(address_encode, bounds=BOUNDING_COORDS)
    if not response: # if response list is empty
        print(f'    {bcolors.RED}ERROR - ADDRESS NOT READABLE{bcolors.RESET}')
        errors.append(f'Row {row+2} - {address_encode}')
        row+=1
        continue
    response_json_payload = response[0]

    ### Set values
    set_lat = response_json_payload.get('geometry').get('location').get('lat')
    set_lon = response_json_payload.get('geometry').get('location').get('lng')

    df.iloc[row].at['Latitude'] = set_lat
    df.iloc[row].at['Longitude'] = set_lon

    print(f'    {bcolors.GREEN}GOT COORDS: {set_lat}, {set_lon}{bcolors.RESET}')

    row+=1

ext = ".csv"
save_file = '/lat-lon-gmaps-api'
save_fqfn = f'{INPUT_DIR}{save_file}{ext}'
if os.path.isfile(save_fqfn) == False:
    df.to_csv(save_fqfn)
else:
    append_num = 1
    while os.path.isfile(f'{INPUT_DIR}{save_file}({append_num}){ext}') == True:
        append_num+=1
    save_fqfn = f'{INPUT_DIR}{save_file}({append_num}){ext}'
    df.to_csv(save_fqfn)

print("\n")
if len(errors) > 0:
    print(f'{bcolors.RED}{bcolors.UNDERLINE}ERRORS{bcolors.RESET}')
    print(*errors,sep='\n')
    print("\n")
print(f'{bcolors.GREEN}{bcolors.BOLD}COMPLETE{bcolors.RESET}  file saved to {bcolors.BOLD}{save_fqfn}{bcolors.RESET}')
