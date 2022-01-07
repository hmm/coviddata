


all: thl wom

thl: thl-alueet thl-kunnat thl-testit thl-iat thl-tartunnat thl-kuolemat thl-kuolemaiat thl-ageweeks thl-sairaalat

wom: wom-countries wom-details

ttr: ttr-ages

vax: vax-coverage vax-weeks vax-product vax-population vax-municipalities vax-productareas vax-days

vaxinc: vaxinc-cases vaxinc-patients vaxinc-icu vaxinc-deaths
vaxstat: vaxstat-cases vaxstat-patients vaxstat-icu vaxstat-deaths vaxstat-personmonths


thl-%:
	./thldata.py $*

wom-%:
	./womparser.py $*

ttr-%:
	./ttrdata.py $*

vax-%:
	./vaxdata.py vax$*

vaxstat-%:
	./vaxincdata.py vaxstat$*

vaxinc-%:
	./vaxincdata.py vaxinc$*
