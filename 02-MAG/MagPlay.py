import matplotlib.pyplot as plt
import obspy
import glob
import numpy as np

def download_data(cat, downloaded=True):

    import obspy
    from obspy.clients.fdsn.mass_downloader import CircularDomain, \
        Restrictions, MassDownloader


    if downloaded == False:
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
    else:
        print('Data has been downloaded')

def load_data():

    inv = obspy.Inventory(networks=[], source="")

    # First read all station files.
    for filename in glob.glob("./stations/*.xml"):
        inv += obspy.read_inventory(filename)

    # Now read the waveform files.
    st = obspy.read("./waveforms/*.mseed")

    # Define Wood-Anderson Response
    paz_wa = {'sensitivity': 2800, 'zeros': [0j], 'gain': 1,
              'poles': [-6.2832 - 4.7124j, -6.2832 + 4.7124j]}
    #https://docs.obspy.org/tutorial/advanced_exercise/advanced_exercise.html

    st.remove_response(inventory=inv, water_level=60) # Remove instrument response
    st.simulate(paz_simulate=paz_wa, water_level=60) # Simulate Wood-Anderson

    st.detrend("linear") # Linear Detrend
    st.taper(max_percentage=0.05) # Taper
    #st.filter("bandpass", freqmin=0.001, freqmax=0.1, zerophase=True, corners=6) # Filter Response

    max_starttime = max(tr.stats.starttime for tr in st)
    min_endtime = min(tr.stats.endtime for tr in st)
    npts = int((min_endtime - max_starttime)  / 0.04)

    for tr in st:
        tr.data = np.require(tr.data, requirements=["C_CONTIGUOUS"])
        tr.data = tr.data*1000

    print('Data has been loaded')

    return st, inv

def plot_stations(cat):

    import glob

    # In the master you don't have to do the looping.
    for i,filename in enumerate(glob.glob("stations/*.xml")):
        if i==0:
            inv = obspy.read_inventory(filename)
        else:
            inv+=obspy.read_inventory(filename)

    fig = inv.plot(projection="local", resolution='i',show=False, size=70)
    fig = cat.plot(fig=fig,projection="local", resolution='i',show=False);
    fig.suptitle('Stations Available for South Napa Quake', fontsize=30)

    plt.show()

def plot_seismograms(Stations, st):

    fig,axes = plt.subplots(3,1, sharex=True, sharey=True)

    # find max amplitude
    max_vals = []
    for station in Stations:
        max_vals.append( max(abs(st.select(station=station)[0].data)) )
    ylims = [-max(max_vals)*1.1, max(max_vals)*1.1]

    colors = ['r','g','b']

    for i, station in enumerate(Stations):
        data = st.select(station=station)[0].data # unnormalized data
        trace = axes[i].plot(st.select(station=station)[0].times(),data, label=station, alpha =0.6, color=colors[i])
        #colors[i] = trace[0].get_color()
        axes[i].axhline(y=max(data), xmin=min(st.select(station=station)[0].times()), xmax=max(st.select(station=station)[0].times()), ls=':', c=colors[i], alpha=0.7)
        axes[i].axhline(y=min(data), xmin=min(st.select(station=station)[0].times()), xmax=max(st.select(station=station)[0].times()), ls=':', c=colors[i], alpha=0.7)
        axes[i].set_ylabel('Amplitude [mm]')
        axes[i].set_ylim(ylims)
        axes[i].set_title(station)

    fig.suptitle('Amplitude Comparison')
    axes[2].set_xlabel('Time [s]')

def calculate_amplitudes(st, Stations, output=False):

    amplitudes = []

    for station in Stations:
        amplitude = max(abs(st.select(station=station)[0].data))
        amplitudes.append(amplitude)

    if output == True:
        print('Ampltiudes: \n\n \
                Station A - {} mm\n \
                Station B - {} mm\n \
                Station C - {} mm\n'.format(amplitudes[0], amplitudes[1], amplitudes[2]))

    return amplitudes

def get_stat_lat_long(station, st, inv):

    stats = st.select(station=station)[0].stats
    ID = '{}.{}.{}.{}'.format(stats.network, stats.station, stats.location, stats.channel)
    lat = inv.get_coordinates(seed_id=ID)['latitude']
    longit = inv.get_coordinates(seed_id=ID)['longitude']

    return lat, longit

def calculate_epicentral_distance(event_lat, event_lon, sta_lat, sta_lon):

    from obspy.geodetics import gps2dist_azimuth

    epi_dist, az, baz = gps2dist_azimuth(event_lat, event_lon, sta_lat, sta_lon)
    epi_dist = epi_dist / 1000 # Convert to km

    return epi_dist

def calculate_distances(st, Stations, cat, inv, output=False):

    event_lat = cat[0].__dict__['origins'][0]['latitude']
    event_lon = cat[0].__dict__['origins'][0]['longitude']

    epi_dists = []

    for station in Stations:
        lat, longit = get_stat_lat_long(station, st, inv)
        epi_dist = calculate_epicentral_distance(event_lat, event_lon, lat, longit)
        epi_dists.append(epi_dist)

    if output == True:
        print('Epicentral Distances: \n\n \
                Station A - {} km\n \
                Station B - {} km\n \
                Station C - {} km\n'.format(epi_dists[0], epi_dists[1], epi_dists[2]))

    return epi_dists

def print_station_dist_amp(Stations, st, cat, inv):

    amplitudes = calculate_amplitudes(st, Stations)
    distances = calculate_distances(st, Stations, cat, inv)

    import pandas as pd

    results = pd.DataFrame(
        {'Station': Stations,
         'Distance [km]': distances,
         'Amplitude [mm]': amplitudes
        })

    results[['Station', 'Distance [km]', 'Amplitude [mm]']]

    print(results[['Station', 'Distance [km]', 'Amplitude [mm]']])
