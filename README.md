# coviddata

Python utilities for fetching covid data from THL (Finnish Health Institute) and worldometers web page.

Result is written to a file as jsonp (json separated by newlines). Default outputfile is <dataset>-YYYYMMDD.json.



## THLDATA

Fetches data from Finnish Health Institutes open data interface: https://thl.fi/fi/tilastot-ja-data/aineistot-ja-palvelut/avoin-data/varmistetut-koronatapaukset-suomessa-covid-19-

### thldata.py tartunnat

Detected confirmed daily infections per area (sairaanhoitopiiri)

### thldata.py kunnat

Detected confirmed infections per municipality

### thldata.py alueet

Summary of infections per area (sairaanhoitopiiri)

### thldata.py testit

Daily number of performed tests

### thldata.py iat

Ages of the people with confirmed infections


## WOMPARSER

Fetches data from https://worldometers.info/coronavirus


### womparser.py countries

Fetches current information from all countries:
 - country
 - continent
 - population
 - total_cases
 - total_deaths
 - total_deaths_per_1m
 - total_tests
 - total_tests_per_1m
 - total_recovered
 - new_cases
 - new_deaths
 - serious_critical

### womparser.py details

Fetches daily information per country:
 - cases
 - deaths
 - active

