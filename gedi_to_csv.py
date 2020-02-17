# from https://gist.github.com/KMarkert/d4c792c6ae566939f4c1851987e2361a
import os
import fire
import h5py
import glob
import tqdm
import numpy as np
import pandas as pd
# requires h5py, tqdm, fire, numpy, and pandas to run


def gedi_to_csv(file,variables=None):
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
          # loop through all of the variables defined earlier
          d = {}
          for var in variables:
              # create a new temporary df of variable array
              d[var] = np.array(geo[var])
      tdf = pd.DataFrame(d)
      # concat to larger dataframe
      df = pd.concat([df,tdf],axis=0,sort=False)

    # save dataframe of parsed variables to CSV file
    df.to_csv('{}.csv'.format(name),index=False)

    return

def main(path,variables=None,verbose=False):
    if variables is None:
        raise ValueError("please provide variables from the GEDI file to convert")

    # check if path provided is a file or folder
    if os.path.isfile(path):
        flist = [path]
    else:
        # only search for h5 files in the path that begin with GEDI
        flist = glob.glob(os.path.join(path,'*.h5'))

    if verbose:
        t = tqdm.tqdm(total=len(flist))

    # loop through the files
    for i,f in enumerate(flist):
        if verbose:
            t.set_description(desc="Processing {}".format(f))

        gedi_to_csv(f,variables)

        if verbose:
            t.update(i+1)

    return

# run main function as CLI
if __name__ == "__main__":
    fire.Fire(main)