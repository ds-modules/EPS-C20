# Author: George Khalilieh
# These tools download the earthquake data, 

import obspy
from obspy.clients.fdsn.mass_downloader import CircularDomain, \
    Restrictions, MassDownloader

    
def download_data(downloaded = True):
    if not downloaded:
        # First, define a domain.
        domain = CircularDomain(latitude=cat[0].origins[0].latitude,
                            longitude=cat[0].origins[0].longitude,
                            minradius=0.25, maxradius=5.0)

        # Second, define some additional restrictions.
        restrictions = Restrictions(starttime=cat[0].origins[0].time - 0.5 * 60,
                            endtime=cat[0].origins[0].time + 5 * 60,
                            minimum_interstation_distance_in_m=100E3,channel="BHZ",)

    # If you leave the providers empty it will loop through
    # all data centers it knows.
    # It will prefer data from the first providers.
        mdl = MassDownloader(providers=["SCEDC", "NCEDC", "IRIS"])

    # Finally launch it.
        mdl.download(domain, restrictions,
                 mseed_storage="waveforms",
                 stationxml_storage="stations")
    print("Data is already downloaded")
    

    
def load_data():
    pass