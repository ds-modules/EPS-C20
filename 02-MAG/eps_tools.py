# Author: George Khalilieh
# These tools download the earthquake data, 

import obspy
from obspy.clients.fdsn.mass_downloader import CircularDomain, \
    Restrictions, MassDownloader
    
import glob
import os
import numpy as np

    
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

    inv = obspy.Inventory(networks=[], source="")

    # First read all station files.
    for filename in glob.glob("./stations/*.xml"):
        inv += obspy.read_inventory(filename)
    
    # Now read the waveform files.
    st = obspy.read("./waveforms/*.mseed")

    st.remove_response(inventory=inv, water_level=60)
    st.detrend("linear")
    st.taper(max_percentage=0.05)
    st.filter("bandpass", freqmin=0.001, freqmax=0.1,
          zerophase=True, corners=6)

    max_starttime = max(tr.stats.starttime for tr in st)
    min_endtime = min(tr.stats.endtime for tr in st)
    npts = int((min_endtime - max_starttime)  / 2.0)

    for tr in st:
        tr.data = np.require(tr.data,
                             requirements=["C_CONTIGUOUS"])
    
    # Remove instrument response
    st.remove_response(inventory=inv)

    st.interpolate(sampling_rate=0.5, method="lanczos",
                   starttime=max_starttime, npts=npts, a=12)
    return st
def plot_traces(Stations):
    fig,ax = plt.subplots(1,1)

    # Find maximum amplitude for normailzation
    max_amp = 0
    for station in Stations: 
        max_amp_temp = max(abs(st.select(station=station)[0].data))
        max_amp = max(max_amp_temp, max_amp)
    
    for station in Stations: 
        data = st.select(station=station)[0].data/max_amp# normalize data
        trace = ax.plot(st.select(station=station)[0].times(),data, label=station)
        color = trace[0].get_color()
        ax.axhline(y=max(data), xmin=min(st.select(station=station)[0].times()), xmax=max(st.select(station=station)[0].times()),     ls=':', c=color, alpha=0.7)
        ax.axhline(y=min(data), xmin=min(st.select(station=station)[0].times()), xmax=max(st.select(station=station)[0].times()),     ls=':', c=color, alpha=0.7)
    

    ax.legend()
    ax.set_ylim([-1,1])
    ax.set_title('Amplitude Comparison')
    ax.set_ylabel('Normalizes Amplitude')
    ax.set_xlabel('Time [s]')
    
    
def calculate_distance_amplitude():
    import pandas as pd
    global cat
    event_lat = cat[0].__dict__['origins'][0]['latitude']
    event_lon = cat[0].__dict__['origins'][0]['longitude']

    epi_dists = []

    for station in Stations:
        lat, long = get_stat_lat_long(station)
        epi_dist = calculate_epicentral_distance(event_lat, event_lon, lat, long)
        epi_dists.append(epi_dist)
    amplitudes = []

    for station in Stations:
        amplitude = max(abs(st.select(station=station)[0].data))
        amplitudes.append(amplitude)
    results = pd.DataFrame(
    {'Station': Stations,
     'Distance [km]': epi_dists,
     'Amplitude [mm]': amplitudes
    })
    return results   


def plot_separate_traces(Stations):
    # find max amplitude
    max_vals = []
    for station in Stations:
        max_vals.append( max(abs(st.select(station=station)[0].data)) )
    ylims = [-max(max_vals)*1.1, max(max_vals)*1.1]

    for i, station in enumerate(Stations): 
        data = st.select(station=station)[0].data # unnormalized data
        color = colors[i]
        trace = axes[i].plot(st.select(station=station)[0].times(),data, label=station, alpha =0.6, color=color)
        axes[i].axhline(y=max(data), xmin=min(st.select(station=station)[0].times()), xmax=max(st.select(station=station)[0].times()), ls=':', c=color, alpha=0.7)
        axes[i].axhline(y=min(data), xmin=min(st.select(station=station)[0].times()), xmax=max(st.select(station=station)[0].times()), ls=':', c=color, alpha=0.7)
        axes[i].set_ylabel('Amplitude [mm]')
        axes[i].set_ylim(ylims)
        axes[i].set_title(station)

    fig.suptitle('Amplitude Comparison')
    axes[2].set_xlabel('Time [s]')
        
    
    
