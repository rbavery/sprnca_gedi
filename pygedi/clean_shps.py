import geopandas as gpd
import pandas as pd
from datetime import datetime
from astral.sun import sun
from astral import LocationInfo
import pytz

def convert_float_to_datetime(timestamp):
    delta_time_reference = "Jan 1 00:00 2018" # from the data dictionary

    utc_time = pd.to_datetime(timestamp, unit="s", origin=pd.to_datetime(delta_time_reference))
    
    return (utc_time- pd.Timedelta(hours=7)).tz_localize("America/Phoenix")

def preprocess_gedi_gdf(path):
    """
    Takes a pathlib Path to a subsetted GEDI file that was processed by 
    gedi_to_vector into shapefile format. Returns a geodataframe that has been 
    quality filtered and with quality flags for sundown, beam type, and any other 
    variables that were used with gedi_to_vector.py
    """
    gdf = gpd.read_file(path)
    gdf['name'] = path.name
    power_test = lambda x: x in ["BEAM0101", "BEAM0110", "BEAM1000", "BEAM1011"]
    gdf["is_power_beam"] = gdf['BEAM'].apply(power_test)
    gdf['delta_time'] = gdf['delta_time'].apply(convert_float_to_datetime)# UTC is 7 hours ahead of Arizona
    gdf = gdf.set_index("delta_time")
    gdf = gdf.rename({"longitude_":"longitude", "latitude_b":"latitude"}, axis=1)
    gdf = gdf[(gdf["l2a_qualit"]==1) & (gdf["l2b_qualit"]==1)]
    # it's suggested in the GEDI L2B product doc to use nightime samples to reduce solar illumination bias. We add a flag here based
    # on local sunrise and sunset for the first sample in each track (the study area is small enough for this)
    city = LocationInfo("Phoenix", "Arizona", timezone = pytz.timezone("America/Phoenix"), latitude = gdf.latitude[0], longitude = gdf.longitude[0])
    s = sun(city.observer, date=datetime(gdf.index[0].year, gdf.index[0].month, gdf.index[0].day), tzinfo=pytz.timezone("America/Phoenix"))
    gdf["is_sundown"] = (gdf.index < s['sunrise']) & (gdf.index > s['sunset'])
    return gdf