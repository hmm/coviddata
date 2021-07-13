


all: thl wom

thl: thl-alueet thl-kunnat thl-testit thl-iat thl-tartunnat thl-kuolemat thl-kuolemaiat thl-ageweeks thl-sairaalat

wom: wom-countries wom-details

ttr: ttr-ages

vax: vax-coverage vax-weeks vax-product vax-population vax-municipalities


thl-%:
	./thldata.py $*

wom-%:
	./womparser.py $*

ttr-%:
	./ttrdata.py $*

vax-%:
	./vaxdata.py vax$*
