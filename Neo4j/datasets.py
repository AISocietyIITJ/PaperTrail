import pandas as pd

# ==================================================================================================================================================
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


# for routes.csv file
# df = pd.read_csv("https://raw.githubusercontent.com/jpatokal/openflights/master/data/routes.dat", header=None,
#                  encoding="utf-8",names=["Airline","Airline_ID","Source_airport","Source airport_ID",
#                                          "Destination_airport","Destination airport_ID","Codeshare","Stops","Equipment"])
# df.to_csv("routes.csv", index=False)
# print(df.head())
# ===========================================================================================================================================================

airport = pd.read_csv("airports.csv")
airport = airport.replace('-', "Unknown")
airport.to_csv("airports.csv",index=False)
airlines = pd.read_csv("airlines.csv")
airlines = airlines.replace('-', "Unknown")
airlines.to_csv("airlines.csv", index=False)
routes = pd.read_csv("routes.csv")
routes = routes.replace('-', "Unknown")
routes.to_csv("routes.csv", index=False)

print(airport.sample(5))

# missing_value = ((airport['TimeZone'] == '\\N').sum())
# print(missing_value)
# airport = airport[airport['TimeZone'] != '\\N']
# print((airport['TimeZone'] == '\\N').sum())
# print(airport.sample(5))

# port_col_name = ["Airport ID","Name", "City", "Country", "IATA", "ICAO", "Latitude","Longitude", "Altitude", "TimeZone", "DST", "Tz database timezone","Type", "Source"]
# print(airport.info())
# for col in port_col_name:
#     missing_value = ((airport[col] == '\\N').sum())
#     print(f"{col} ==> {missing_value} missing values")


# print("=========================================================================================================================================")


# lines_col_name = ["Airline_ID", "Names", "Alias", "IATA", "ICAO", "Call_Sign","Country","Active"]
# print(airlines.info())
# for col in lines_col_name:
#     missing_value = ((airlines[col] == '\\N').sum())
#     print(f"{col} ==> {missing_value} missing values")



# print(routes.shape)
# print(routes.sample(5))


# # print(airport[airport["Airport ID"] == 135])
# # print(airlines[airlines['Airline_ID'] == 135])

# x = routes.iloc[5]
# print(airport[airport['Airport ID'] == int(x['Source airport_ID'])])
# print(airlines[airlines['Airline_ID'] == int(x['Airline_ID'])])

