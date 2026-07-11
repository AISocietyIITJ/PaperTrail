Datset comprises of 3 .dat files: one about airports, one about airlines and the last one about the routes connecting the airports 
Schema design: This design seemed most intuitive.
<img width="963" height="818" alt="image" src="https://github.com/user-attachments/assets/a80b678d-6760-4d0d-8774-86b9adbc7f98" />

Preprocessing:
1. Data was imported using pandas
2. Missing values(\N) were converted to NaN
3. Columns which were missing were added using the openflights website
4. Missing valued records were mostly removed

Queries:
1. Data was ingested by converting to list of dictionary
2. Nodes and Relationships were created anf their properties were defined using queries
3. Constraints have been setup on the airport id and airline id.
4. Using queries, the top 10 airlines which operate on maximum airports was found. This was done by finidng the relationship between the airline ans airport, then we counted the distinct airports at which each airline operates at.
5. These are the results:
  <img width="995" height="481" alt="image" src="https://github.com/user-attachments/assets/6348b4df-1e88-4d6b-b416-4b843d40192b" />
6. It is also observed that only 4 routes which have 1 stop in between.Remaining routes are non-stop routes
7. The top 10 busiest airports were found by applying optinal match on the CONNECTED_TO relationship, and the count() function was used to count the number of routes connecting a particular airport to other airports
   <img width="995" height="481" alt="image" src="https://github.com/user-attachments/assets/3e8c0c28-6403-47cd-8158-45882fc4bc72" />

 GDS Algorithms:
 1. Page rank was applied and it was found that
    i) Hartsfield Jackson Atlanta International Airport has scored highest though there are 5 more airports which have more routes than this one.
    ii) It implies that this airports is well connected to good number of important airports
    iii) Most of the airports with more connectivity are the ones which have good pagerank scores,implying the importance of these airports.
    iv) <img width="532" height="249" alt="image" src="https://github.com/user-attachments/assets/093b79fc-5728-45ea-80d5-55f50e0345d7" />
  
2. WCC Algorithm:
   <img width="1150" height="477" alt="image" src="https://github.com/user-attachments/assets/5756b64a-a281-4839-b362-fc374298380c" />
    It is observed that componentID =0 has the highest number of airports and forms the largest cluster. The airports with other component ids for relatively much smaller groups




   
