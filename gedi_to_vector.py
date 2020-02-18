import os
import fire
import h5py
import glob
import tqdm
import numpy as np
import pandas as pd
import geopandas as gpd
# requires fire, h5py, tqdm, numpy, pandas, and geopandas

def gedi_to_vector(file,variables=None,outFormat='CSV',filterBounds=None):
    # open hdf5 file
    data = h5py.File(file,'r')

    # get full file name and extension
    name,_ = os.path.splitext(file)

    # create empty dataframe to append data to
    df = pd.DataFrame()

    # loop over all of the hdf5 groups
    for k in list(data.keys()):
        # if BEAM in the group name
        if 'BEAM' in k:
            # get the geolocation subgroup
            geo = data[k]['geolocation']
            d = {}
            # loop through all of the variables defined earlier
            for var in variables:
                # assign variable array to dict key
                if var in list(data[k]["geolocation"].keys()):
                    d[var] = np.array(geo[var])
                elif var in list(data[k].keys()):
                    d[var] = np.array(data[k][var])
                else:
                    raise ValueError(f"The variable {var} is not in the geolocation or BEAM group of the file {file}.")
            # convert dict of varaibles to dataframe
            tdf = pd.DataFrame(d)
            # concat to larger dataframe
            df = pd.concat([df,tdf],axis=0,sort=False)

    # check if the the filterBounds is provided
    if filterBounds is not None:
        w,s,e,n = filterBounds # expand list to individual variables
        # select features on X axis
        horizontalMask = (df.longitude_bin0 >= w) & (df.longitude_bin0 <= e)
        # select features on Y axis
        verticalMask = (df.latitude_bin0 >= s) & (df.latitude_bin0 <= n)
        # combines masks to select features that intersect
        spatialMask = verticalMask & horizontalMask
        # grab only masked values within the bounds provided
        df = df.loc[spatialMask]

    # check to make sure that the dataframe has values.
    # if not, then return from function without saving df
    if df.size == 0:
        return

    if outFormat in ['CSV','csv']:
        # save dataframe of parsed variables to CSV file
        df.to_csv('{}.{}'.format(name,outFormat.lower()),index=False)

    else:
        # check if df has the geoinformation
        if ('latitude_bin0' not in df.columns) or ('longitude_bin0' not in df.columns):
            raise KeyError("Geospatial variables 'latitude_bin0' and/or 'longitude_bin0' were not found, "
                "please specify these variables to be extracted when writing to geospatial format")

        # convert to geodataframe
        gdf = gpd.GeoDataFrame(
            df, geometry=gpd.points_from_xy(df.longitude_bin0, df.latitude_bin0))
        # save the geodataframe of variables to file
        gdf.to_file('{}.{}'.format(name,outFormat.lower()))

    return

def main(path,variables=None,verbose=False,outFormat='CSV',filterBounds=None):
    # check if the variables to extract have been defined
    if variables is None:
        raise ValueError("Please provide variables from the GEDI file to convert")

    # if variables have been defined, check if provided in correct datetype
    if type(variables) is not list:
        raise TypeError("Provided variables is not list, please provide argument as '[<var1>,<var2>,<var3>]'")

    # check if filterBounds have been provided and in correct datatype
    if (filterBounds is not None) and (type(filterBounds) is not list):
        raise TypeError("Provided filterBounds is not list, please provide argument as '[W,S,E,N]'")

    # check if the output format provided is supported by script
    availableFormats = ['CSV','SHP','GeoJSON','GPKG','csv','shp','geojson','gpkg']
    if outFormat not in availableFormats:
        raise NotImplementedError('Selected output format is not support please select one of the following: "CSV","SHP","GeoJSON","GPKG"')

    # check if path provided is a file or folder
    if os.path.isfile(path):
        flist = [path]
    else:
        # only search for h5 files in the path provided
        flist = glob.glob(os.path.join(path,'*.h5'))

    if verbose:
        print('\n')
        t = tqdm.tqdm(total=len(flist))

    # loop through the files and do the conversion
    for i,f in enumerate(flist):
        if verbose:
            _, desc = os.path.split(f)
            t.set_description(desc="Processing {}".format(desc))

        gedi_to_vector(f,variables,outFormat,filterBounds)

        if verbose:
            t.update(i+1)

    return

if __name__ == "__main__":
    fire.Fire(main)
