import pyarrow.parquet as pq
import pandas as pd
import numpy as np
from math import sqrt, nan, isnan
from mpl_toolkits import mplot3d
from matplotlib.animation import FuncAnimation, writers
import matplotlib.pyplot as plt

inFile = './DFW_valuable.csv'
outPref = './DFW_flight'        # prefix for output file
isRed = True

table = pd.read_csv(inFile)
flights = set(table['flightID'])
# Find dropouts using RMS
outliers_cumulative = []
outliers = []
K = 2
for flight in flights:
    interval = list(table.loc[table['flightID'] == flight, 'timeInterval'])
    index = list(table.loc[table['flightID'] == flight, 'index'])
    while True:
        RMSE = 0.0
        mean = 0.0
        for item in interval:
            item = float(item)
            if (not isnan(item)):
                mean += item
        mean = mean / (len(interval)-1)
        for item in interval:
            item = float(item)
            if (not isnan(item)):
                RMSE += (item - mean)**2
        RMSE = sqrt(RMSE/(len(interval)-1))
        upBound = mean + K*RMSE
        i = 0
        while (i < len(interval)):
            if (not isnan(interval[i])):
                if (float(interval[i]) > upBound):
                    outliers.append(index[i])
                    interval.pop(i)
                    index.pop(i)
            i += 1
        if (len(outliers) == 0):
            break
        outliers_cumulative += outliers
        outliers = []

table['outlier'] = 'NO'
for outlier in outliers_cumulative:
    table.loc[table['index'] == outlier, 'outlier'] = 'YES'
table.to_csv(inFile, index=False)

for flight in flights:
    latitude = list(table.loc[table['flightID'] == flight, 'latitude'])
    longitude = list(table.loc[table['flightID'] == flight, 'longitude'])
    altitude = list(table.loc[table['flightID'] == flight, 'altitude_m'])
    time = list(table.loc[table['flightID'] == flight, 'timeEDT'])
    time0 = int(time[0])
    for j in range(0, len(time)-1):
        time[j] = int(time[j]) - time0

    x_data = []
    y_data = []
    z_data = []

    fig = plt.figure()
    ax = plt.axes(projection='3d')
    ax.set_xlim(min(longitude), max(longitude))
    ax.set_ylim(min(latitude), max(latitude))
    ax.set_zlim(min(altitude), max(altitude))
    ax.set_xlabel('Longitude (Deg)')
    ax.set_ylabel('Latitude (Deg)')
    ax.set_zlabel('Altitude (m)')
    y_data.append(latitude[0])
    x_data.append(longitude[0])
    z_data.append(altitude[0])
    line, = ax.plot3D(x_data, y_data, z_data, 'blue', linewidth=1)

    def animation_frame(i):
        global isRed
        y_data.append(latitude[i])
        x_data.append(longitude[i])
        z_data.append(altitude[i])
        
        #line.set_xdata(x_data)
        #line.set_ydata(y_data)
        #line.set_zdata(z_data)
        if isRed:
            color = 'red'
            isRed = False
        else:
            color = 'blue'
            isRed = True
        ax.plot3D(x_data, y_data, z_data, color, linewidth=1)
        ax.set_title(str(time[i]) + ' sec')

        y_data.pop(0)
        x_data.pop(0)
        z_data.pop(0)

        return line, 

    animation = FuncAnimation(fig, func=animation_frame, frames=np.arange(1, len(latitude)-1, 1), interval=10)
    # setting up wrtiers object
    Writer = writers['ffmpeg']
    writer = Writer(fps=1, metadata={'artist': 'Me'}, bitrate=1800)
    animation.save(outPref + str(flight) + '.mp4', writer)
    # plt.show()
    plt.close()
