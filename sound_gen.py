from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import datetime
import time


from pyo import *
import time

import math

#Location Variables


province = 'ON'
station = 6016975



def grab_data(prov,station):
    
    url = fr'https://dd.weather.gc.ca/climate/ahccd/geojson/historical/monthly/{prov}'
    
    file_start = []
    for stat_adjust in np.arange(-5,6):
        file_start.append( f'AHCCD_hist_monthly_{prov}_{station+stat_adjust}')
    

    def listFD(url,file_start=''):
        page = requests.get(url).text

        soup = BeautifulSoup(page, 'html.parser')
        return [url + '/' + node.get('href') for node in soup.find_all('a') if node.get('href').startswith(file_start)]
    
    file_list = []
    for file_s in file_start:
        file_list.extend(listFD(url,file_s))


    first = True

    for file in file_list:


        if first:
            raw_data = pd.read_json(file)

            data = []
            for row in raw_data.features:
                year = row['properties']['year']
                month = row['properties']['period']
                data.append([datetime.datetime.strptime(f'{year} {month}' , '%Y %b'),float(row['properties']['value'])])

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
                data.append([datetime.datetime.strptime(f'{year} {month}' , '%Y %b'),float(row['properties']['value'])])

            data_type = raw_data.features[0]['properties']['measure_type']
            df_temp = pd.DataFrame(data,columns =['year',data_type])
            df_temp = df_temp.set_index('year')
            df_temp = df_temp.sort_index()
            df_temo = df_temp.replace(-9999.9,0)
            df = pd.concat([df,df_temp],axis = 1, join_axes=[df.index])
    
    df = df.replace(-9999.9,np.nan)

    df = df[df.index>=datetime.datetime(1970,4,1)]

    return df


def parameter_update_rain(climate_data):
    snds3 = ['snds/alum2.wav']
    tabs = SndTable(snds3)


    beat = Metro(float(climate_data), poly=3).play()
    wav = SquareTable()
    t = CosTable([(0,0), (100,1), (2000,.3), (8191,0)])
    amp = TrigEnv(beat, table=tabs, dur=.25, mul=.3)
    pitch = TrigXnoiseMidi(beat,dist = 4,mrange = (28,48))

    return [wav,pitch,amp]

def parameter_update_snow(climate_data):
    
    ind = LinTable([(0,3), (20,40), (300,10), (1000,5), (8191,3)])
    m = Metro(0.9+climate_data).play()
    tr = TrigEnv(m, table=ind, dur=0.5)


    return tr

def parameter_update_wind(climate_data):
    a = Sine(.25, 0, .1, .1)
    
    noise = PinkNoise(a/100+climate_data).mix(2)

    return noise

recorder = True


# Main Section


df = grab_data(province,station)

num = 0
stop = len(df.index)-1
print(stop)
s = Server()
s.boot().start()




if 'rain' in df.columns.values:

    snds3 = ['snds/alum2.wav']

    tabs = SndTable(snds3)

    beat = Metro(time=0.5, poly=5).play()
    wav = SquareTable()
    t = CosTable([(0,0), (100,1), (2000,.3), (8191,0)])
    amp = TrigEnv(beat, table=tabs, dur=.25, mul=.1)
    pitch = TrigXnoiseMidi(beat,dist = 2,mrange = (24,48))



    rain = Osc(table=wav,freq= pitch ,mul = amp*1.0).out(dur=stop*1.5)



if 'snow' in df.columns.values:
    snow_diff = float(df['snow'].max()) - float(df['snow'].min())
    snow_data = 1.333*(pd.to_numeric(df['snow']) - float(df['snow'].mean()))/float(snow_diff)

    ind = LinTable([(0,3), (20,40), (300,10), (1000,5), (8191,3)])
    m = Metro(.9).play()
    tr = TrigEnv(m, table=ind, dur=0.5)
    snow = FM(carrier=[251,250], ratio=[.2498,.2503], index=tr, mul=.02).out(dur=stop*1.5)


if 'wind_speed' in df.columns.values:

    a = Sine(.25, 0, .1, .1)
    noise = PinkNoise(a/100+0.01).mix(2)
    tone = Tone(noise,1000).out(dur=stop*1.5)



if 'temp_mean' in df.columns.values:
    temp_diff = float(df['temp_mean'].max()) - float(df['temp_mean'].min())
    temp_data = 0.2*(pd.to_numeric(df['temp_mean']) - float(df['temp_mean'].mean()))/float(temp_diff)


    lfo = Sine([2,5], 0, .1, .1)
    sine_loop = Sine(freq=[400], mul=.1).out(dur=stop*1.5)




def pcp_temp():
    
    global num

    #Update Rain Parameters
    
    x_rain = float(df['rain'].values[num])

    if x_rain <= 0.0:
        value_rain = 0.0
    else:
        value_rain = 1-(float(x_rain)/(1.1*float(df['rain'].max())))

   

    if 0< value_rain < 0.1:
        value_rain = 0.1
    

    new_para = parameter_update_rain(value_rain)

    rain.table = new_para[0]
    rain.freq = new_para[1]
    rain.mul = new_para[2]
    
    
    x_snow = float(snow_data[num])

    if x_snow <= 0.0:
        value_snow = -0.9
    else:
        value_snow = x_snow


    
    snow.index=parameter_update_snow(value_snow)
    

    
    x_wind = float(df['wind_speed'].values[num])
    print(x_wind)
    if x_wind <= 0.0 or math.isnan(df['wind_speed'].values[num]):
        value_wind = 0
    else:
        value_wind = (float(x_wind)/(1.1*float(df['wind_speed'].max())))

    print(value_wind)
    
    
    tone.setInput(parameter_update_wind(value_wind/30))
    
    
    x_temp = temp_data[num]
    
    print(x_temp)
    if not math.isnan(x_temp):
        sine_loop.mul = float(0.1+x_temp)
        sine_loop.freq = [200+x_temp*2000]
    print(num)
    num+=1


p =Pattern(pcp_temp,1.5)
x= p.play(stop*1.5)




