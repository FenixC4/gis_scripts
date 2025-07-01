# gis_scripts

collection of usefull qgis scripts


- multi_stop_route.py
you must have a road network layer and a layer of sequential points
  
- multi_stop_route_cost.py
you must have a road network layer and a layer of sequential points. Additionally your network layer has to have a field cost which needs to be calculated like that:
```
length($geometry) <- very important detail
* (
	CASE
		WHEN 'TYP' = 'trasa na wałach' THEN 100 <- most deired type of road
		WHEN 'TYP' = 'trasa przez park' THEN 50
		WHEN 'TYP' = 'droga dla rowerów' THEN 25
		WHEN 'TYP' = 'droga dla pieszych i rowerów' THEN 12.5
		ELSE 0.1 <- least desired type of road
	END
)
```

in both cases the road network must not have 'dangles' which can be easily checked with topology checker
