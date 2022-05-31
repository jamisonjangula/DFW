import pyarrow.parquet as pq
import pandas as pd
from numpy import nan
from math import pi, cos, sin, sqrt
import matplotlib.pyplot as plt

speed_threshold = 100 * 10**3 / 3600    # assuming max drone speed is 100 kph -> convert to m/s
time_threshold = 5                      # assuming 5 seconds max between messages
cutoff = 100                            # a flight must contain at least as many entries as the cutoff #

inFile = './DFW.xlsx'
outFile = './DFW_mod.csv'
outFile_valuable = './DFW_valuable.csv'
ro = 6378.137*1000.0      # radius of earth @ sea level in meters

table = pd.read_excel(inFile, usecols=[0,3,4,5,6,7])
for i in range(0, len(table.timeEDT)):
    tmp = (table['timeEDT'][i].split())[1]
    H_M_S = tmp.split(':')
    for j in range(0,len(H_M_S)):
        H_M_S[j] = int(H_M_S[j])*60**(2-j)
    table.loc[i, 'timeEDT'] = str(H_M_S[0] + H_M_S[1] + H_M_S[2])

table.sort_values(by = ['flightID', 'timeEDT'], ascending=[True,True], inplace=True)
#table.reset_index(inplace=True)
i = 0
while (i < (len(table.timeEDT)-1)):
    if (int(table.loc[i,'timeEDT']) == int(table.loc[i+1,'timeEDT'])):
        if (int(table.loc[i,'flightID']) == int(table.loc[i+1,'flightID'])):
            table.drop(table.index[i], inplace=True)
            table.reset_index(drop=True, inplace=True)
            i -= 2
    if ((float(table.loc[i,'longitude']) == 0.0) or (float(table.loc[i,'latitude']) == 0.0)):
        table.drop(table.index[i], inplace=True)
        table.reset_index(drop=True, inplace=True)
        i -= 2
    i += 1

table['radius'] = 0.0
table['phi'] = 0.0
table['theta'] = 0.0
table['distance'] = 0.0
table['timeInterval'] = nan
table['avgSpeed'] = nan
table.loc[:, 'radius'] = float(ro) + table.loc[:, 'altitude_m']
table.loc[:,'phi'] = pi + table.loc[:,'longitude'] * pi/180 # convert to radians
table.loc[:,'theta'] = pi/2 + table.loc[:,'latitude'] * pi/180 # convert to radians
valuableFlights = []  # flights with more entries than the specified cutoff

flights = set(table['flightID'])
for flight in flights:
    tmpIDs = table['flightID'] == flight
    ids = []
    for i in range(0, len(tmpIDs)):
        if (tmpIDs[i]==True):
            ids.append(i)
    if (len(ids) >= cutoff):
        valuableFlights.append(flight)
    for i in range(0, len(ids)-1):
        mag = table.loc[ids[i], 'radius']**2 + table.loc[ids[i+1], 'radius']**2 - 2*table.loc[ids[i], 'radius']*table.loc[ids[i+1], 'radius']*(sin(table.loc[ids[i], 'theta'])*sin(table.loc[ids[i+1], 'theta'])*cos(table.loc[ids[i], 'phi'] - table.loc[ids[i+1], 'phi']) + cos(table.loc[ids[i], 'theta'])*cos(table.loc[ids[i+1], 'theta']))
        mag = (mag*mag)**0.5
        table.loc[ids[i],'distance'] = mag
        dt = (float(table.loc[ids[i+1],'timeEDT']) - float(table.loc[ids[i],'timeEDT']))
        table.loc[ids[i],'timeInterval'] = dt
        table.loc[ids[i],'avgSpeed'] = float(table.loc[ids[i],'distance']) / float(dt)

val = []
for i in range(0,len(table['flightID'][:])):
    if (table['flightID'][i] in valuableFlights):
        val.append(i)
valTable = table.loc[val, :]
valTable.to_csv(outFile_valuable)

for i in range(0, len(table.timeEDT)):
    table.loc[i,'speed'] = float(table.loc[i,'speed'])
    table.loc[i,'latitude'] = float(table.loc[i,'latitude'])
    table.loc[i,'longitude'] = float(table.loc[i,'longitude'])

min_lat = min(table['latitude'][:])
max_lat = max(table['latitude'][:])
min_lon = min(table['longitude'][:])
max_lon = max(table['longitude'][:])

print(str(min_lat) + '  < latitude  < ' + str(max_lat))
print(str(min_lon) + ' < longitude < ' + str(max_lon))

dropoutSpeed = table['avgSpeed'][:] >= speed_threshold
dropoutTime = table['timeInterval'][:] >= time_threshold
dropSpeed = []
dropTime = []
dropBoth = []
for i in range(0, len(dropoutSpeed)):
    if (dropoutSpeed[i] == True):
        dropSpeed.append(i)
    if (dropoutTime[i] == True):
        dropTime.append(i)
for i in dropTime:
    if i in dropSpeed:
        dropBoth.append(i)
print('# of flights with > ' + str(cutoff) + ' entries = ' + str(len(valuableFlights)))
print('# of dropouts detected by speed    = ' + str(len(dropSpeed)))
print('# of dropouts detected by interval = ' + str(len(dropTime)))
print('# of dropouts detected by both     = ' + str(len(dropBoth)))
"""
ax1 = plt.subplot(311)
ax1.scatter(table.loc[dropSpeed,'longitude'], table.loc[dropSpeed,'latitude'], 3, label='speed')
ax1.legend()
plt.xlim([min_lon, max_lon])
plt.ylim([min_lat, max_lat])
plt.ylabel('Latitude (Deg)')
ax2 = plt.subplot(312, sharex=ax1)
ax2.scatter(table.loc[dropTime,'longitude'], table.loc[dropTime,'latitude'], 3, label='time')
ax2.legend()
plt.xlim([min_lon, max_lon])
plt.ylim([min_lat, max_lat])
plt.ylabel('Latitude (Deg)')
ax3 = plt.subplot(313, sharex=ax2)
ax3.scatter(table.loc[dropBoth,'longitude'], table.loc[dropBoth,'latitude'], 3, label='both')
ax3.legend()
plt.xlim([min_lon, max_lon])
plt.ylim([min_lat, max_lat])
plt.xlabel('Longitude (Deg)')
plt.ylabel('Latitude (Deg)')
plt.show()
"""
