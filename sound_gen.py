from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import datetime



def grab_data(prov,station):

    url = fr'https://dd.weather.gc.ca/climate/ahccd/geojson/historical/monthly/{prov}'
    file_start = f'AHCCD_hist_monthly_{prov}_{station}'
    print(url)

    def listFD(url,file_start=''):
        page = requests.get(url).text

        soup = BeautifulSoup(page, 'html.parser')
        return [url + '/' + node.get('href') for node in soup.find_all('a') if node.get('href').startswith(file_start)]

    file_list = listFD(url,file_start)


    first = True

    for file in file_list:


        if first:
            raw_data = pd.read_json(file)

            data = []
            for row in raw_data.features:
                year = row['properties']['year']
                month = row['properties']['period']
                data.append([datetime.datetime.strptime(f'{year} {month}' , '%Y %b'),row['properties']['value']])

            data_type = raw_data.features[0]['properties']['measure_type']
            df = pd.DataFrame(data,columns =['year',data_type])
            df = df.set_index('year')
            df = df.sort_index()
            first = False
        else:
            raw_data = pd.read_json(file)
            data = []
            for row in raw_data.features:
                year = row['properties']['year']
                month = row['properties']['period']
                data.append([datetime.datetime.strptime(f'{year} {month}' , '%Y %b'),row['properties']['value']])

            data_type = raw_data.features[0]['properties']['measure_type']
            df_temp = pd.DataFrame(data,columns =['year',data_type])
            df_temp = df_temp.set_index('year')
            df_temp = df_temp.sort_index()
            df = pd.concat([df,df_temp],axis = 1, join_axes=[df.index])
    
    df = df.replace(-9999.9,np.nan)



    return df


def parameter_update(climate_data):
    snds3 = ['snds/alum1.wav', 'snds/alum2.wav',
        'snds/alum3.wav', 'snds/alum4.wav']
    tabs = SndTable(snds3)


    beat = Metro(time=float(value), poly=3).play()
    wav = SquareTable()
    t = CosTable([(0,0), (100,1), (2000,.3), (8191,0)])
    amp = TrigEnv(beat, table=tabs, dur=.25, mul=.3)
    pitch = TrigXnoiseMidi(beat,dist = 4,mrange = (48,48))

    return [wav,pitch,amp]



from pyo import *
import time
import numpy as np

num = 0


s = Server().boot().start()
snds3 = ['snds/alum1.wav', 'snds/alum2.wav',
        'snds/alum3.wav', 'snds/alum4.wav']

tabs = SndTable(snds3)
'''
beat = Metro(time=0.5, poly=3).play()
wav = SquareTable()
t = CosTable([(0,0), (100,1), (2000,.3), (8191,0)])
amp = TrigEnv(beat, table=tabs, dur=.25, mul=.3)
pitch = TrigXnoiseMidi(beat,dist = 4,mrange = (48,48))



rain = Osc(table=wav,freq= pitch ,mul = amp).out()
'''

tabs = SndTable(snds3)

beat_snow = Metro(time=0.5, poly=3).play()
wav_snow = SquareTable()
t_snow = CosTable([(0,0), (100,1), (2000,.3), (8191,0)])
amp_snow = TrigEnv(beat_snow, table=tabs, dur=.25, mul=.1)
pitch_snow = TrigXnoiseMidi(beat_snow,dist = 4,mrange = (100,100))



snow = Osc(table=wav_snow,freq= pitch_snow ,mul = amp_snow).out()



def pcp_temp():
    
    global num
    
    #Update Rain Parameters

    x = df['Rain'].values[num]

    if x != np.nan:
        value = x
    else:
        value = 1

    new_para = parameter_update(1-value)

    rain.table = new_para[0]
    rain.freq = new_para[1]
    rain.mul = new_para[2]
    
    
    x_snow = df_snow['Snow'].values[num]

    if x_snow != np.nan:
        value_snow = x_snow
    else:
        value_snow = 1
    print(1-value_snow)

    new_para = parameter_update(1-value_snow)
    snow.table = new_para[0]
    snow.freq = new_para[1]
    snow.mul = new_para[2]
    
    
    num+=1


p =Pattern(pcp_temp,2).play()
