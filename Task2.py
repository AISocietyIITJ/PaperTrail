import pandas as pd
import numpy as np

airline_df= pd.read_csv('/home/sreehari1729/PaperTrail /datasets/airlines.dat', header=None)
airline_df.columns=['Airline ID', 'Name', 'Alias','IATA','ICAO','Callsign','Country','Active']
# print(airline_df.head())

airport_df= pd.read_csv('/home/sreehari1729/PaperTrail /datasets/airports.dat', header=None)
airport_df.columns=['Airport ID', 'Name', 'City','Country','IATA','ICAO','Latitude','Longitude','Altitude','Timezone','DST','Tz database timezone','Type','Source']
# print(airport_df.head())

routes_df= pd.read_csv('/home/sreehari1729/PaperTrail /datasets/routes.dat', header=None)
routes_df.columns=['Airline', 'Airline ID','Source Airport', 'Source Airport ID','Destination Airport','Destination Airport ID','Codeshare','Stops','Equipment']
# print(routes_df.head())

airport_df['Airport ID']=airport_df['Airport ID'].astype('string')
routes_df['Source Airport ID']=routes_df['Source Airport ID'].astype('string')
routes_df['Destination Airport ID']=routes_df['Destination Airport ID'].astype('string')
airline_df['Airline ID']=airline_df['Airline ID'].astype('string')
routes_df['Airline ID']=routes_df['Airline ID'].astype('string')


for col in airline_df.columns:
    airline_df[col]=airline_df[col].replace(to_replace='\\N', value=np.nan)

for col in routes_df.columns:
    routes_df[col]=routes_df[col].replace(to_replace='\\N', value=np.nan)

for col in airport_df.columns:
    airport_df[col]= airport_df[col].replace(to_replace='\\N', value=np.nan)

print(airport_df.head())


missing_airport_ids=[]
missing_name_df=airport_df[airport_df['Name'].isna()]
for airport_id in missing_name_df['Airport ID']:
    missing_airport_ids.append(airport_id)

airport_df=airport_df.dropna(subset=['Name'])


routes_df = routes_df[
    ~routes_df['Source Airport ID'].isin(missing_airport_ids) & 
    ~routes_df['Destination Airport ID'].isin(missing_airport_ids)
]


airport_df.to_csv('airport_fin.csv', index=False)
airline_df.to_csv('airline_fin.csv', index=False)
routes_df.to_csv('routes_fin.csv', index=False)


