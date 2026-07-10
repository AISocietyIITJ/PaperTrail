import pandas as pd

# for airports.csv file 
# df = pd.read_csv("https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat", 
#                  header=None, names=["Airport ID","Name", "City", "Country", "IATA", "ICAO", "Latitude",
#                                      "Longitude", "Altitude", "TimeZone", "DST", "Tz database timezone","Type", "Source"],
#                                      encoding="utf-8")
# df.to_csv('airports.csv', index=False)
# print(df)


# for airlines.csv file
# df = pd.read_csv("https://raw.githubusercontent.com/jpatokal/openflights/master/data/airlines.dat", header=None,
#                  encoding="utf-8",names=["Airline_ID", "Names", "Alias", "IATA", "ICAO", "Call_Sign","Country","Active"])
# df.to_csv("airlines.csv", index=False)
# print(df.head)