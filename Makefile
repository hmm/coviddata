


all: thl wom

thl: thl-alueet thl-kunnat thl-testit thl-iat thl-tartunnat

wom: wom-countries wom-details

ttr: ttr-ages


thl-%:
	./thldata.py $*

wom-%:
	./womparser.py $*

ttr-%:
	./ttrdata.py $*
