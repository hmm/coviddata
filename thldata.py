#!/usr/bin/env python3

import sys, os, json, inspect, optparse, datetime
import requests

requestheaders = {'User-Agent': 'thldata'}

class ParserData():
    type = None

    def __init__(self, data=None):
        if not data:
            data = {}
        self._data = data
        if self.type:
            self._data['type'] = self.type
        for attr in data:
            value = data[attr]
            if isinstance(value, dict):
                value = ParserData(value)
            setattr(self, attr, value)

    def __setattr__(self, attr, value):
        if not attr.startswith('_'):
            self._data[attr] = value
        super(ParserData, self).__setattr__(attr, value)

    def values(self):
        return self._data

    def tojson(self):
        return json.dumps(self._data, sort_keys=True, ensure_ascii=False)


    
class AreaData(ParserData):
    type = "area"

class MunicipalityData(ParserData):
    type = "municipality"

class DemographyData(ParserData):
    type = "demography"

class DeathDemographyData(ParserData):
    type = "deathdemography"

class AgeWeekData(ParserData):
    type = "ageweeks"

class TestsData(ParserData):
    type = "tests"

class InfectionData(ParserData):
    type = "infection"

class DeathsData(ParserData):
    type = "deaths"

class HospitalData(ParserData):
    type = "hospital"

class Dimension():
    def __init__(self, name, size):
        self.name = name
        self.size = size

    def __repr__(self):
        return "Dimension <%s:%d>" % (self.name, self.size)


class Parser():
    def __init__(self, path=None, data=None):
        if path:
            with open(path) as fp:
                data = json.load(fp)
                self.dataset = data["dataset"]
        else:
            self.dataset = data["dataset"]

    def parse(self, mapper=None):
        self.dimensions = [
            Dimension(name, size)
            for (name, size) in zip(
                self.dataset["dimension"]["id"], self.dataset["dimension"]["size"]
            )
        ]

        for d in self.dimensions:
            data = self.dataset["dimension"][d.name]["category"]
            indexes = data["index"]
            labels = data["label"]

            values = [(indexes[k], labels[k]) for k in indexes.keys()]
            values.sort()
            d.categories = [v[1] for v in values]

        values = self.dataset["value"]
        for v in values.keys():
            # print(v, values[v])
            idx = int(v)
            labels = []
            jd = {}
            for d in self.dimensions[::-1]:
                # print(d, d.size, idx, d.categories[idx % d.size])
                label = d.categories[idx % d.size]
                labels.append(label)
                jd[mapper.mapfield(d.name)] = mapper.mapvalue(label)
                idx = int(idx / d.size)
            jd[mapper.mapfield("value")] = mapper.mapvalue(values[v])
            # print(labels, values[v])
            d = ParserData(jd)
            # print(d.tojson())
            yield d


class THLData():
    name = None
    url = None

    valuemap = {}
    fieldmap = {}

    def setdatadate(self, offset = 0):
        self.datadate = datetime.date.today() - datetime.timedelta(days=offset)

    def run(self, output):
        data = requests.get(self.url, headers=requestheaders)
        data.raise_for_status()
        p = Parser(data=data.json())
        for data in p.parse(mapper=self):
            ddata = self.datatype(data.values())
            ddata.datadate = str(self.datadate)
            print(ddata.tojson(), file=output)

    def mapvalue(self, value):
        return self.valuemap.get(value, value)

    def mapfield(self, value):
        return self.fieldmap.get(value, value)

    def getfilename(self):
        datestr = self.datadate.strftime("%Y%m%d")
        return "%s-%s.json" % (self.name, datestr)


class THLKunnat(THLData):
    name = "kunnat"
    url = "https://sampo.thl.fi/pivot/prod/fi/epirapo/covid19case/fact_epirapo_covid19case.json?column=hcdmunicipality2020-445268L&column=measure-141082"

    fieldmap = {
        "dateweek20200101": "date",
        "hcdmunicipality2020": "area",
    }

    def run(self, output):
        data = requests.get(self.url, headers=requestheaders)
        data.raise_for_status()
        p = Parser(data=data.json())
        lastarea = None
        combined = MunicipalityData()
        for data in p.parse(mapper=self):
            if lastarea and data.area != lastarea:
                print(combined.tojson(), file=output)
                combined = MunicipalityData()
            lastarea = data.area
            combined.area = data.area
            if data.measure == "Tapausten lukumäärä":
                if data.value != "..":
                    combined.cases = int(data.value)
                else:
                    combined.cases = None
            elif data.measure == "Asukaslukumäärä":
                combined.population = int(data.value)

            combined.datadate = str(self.datadate)

        print(combined.tojson(), file=output)


class THLAlueet(THLData):
    name = "alueet"
    url = "https://sampo.thl.fi/pivot/prod/fi/epirapo/covid19case/fact_epirapo_covid19case.json?row=dateweek20200101-509030&row=hcdmunicipality2020-445222&column=measure-141082"

    fieldmap = {
        "dateweek20200101": "week",
        "hcdmunicipality2020": "area",
    }

    valuemap = {
        "Kaikki Alueet": "Koko maa",
        "Aika": "Yhteensä",
        "Kaikki ajat": "Yhteensä",
    }

    def run(self, output):
        data = requests.get(self.url, headers=requestheaders)
        data.raise_for_status()
        p = Parser(data=data.json())
        lastweekarea = None
        combined = AreaData()
        for data in p.parse(mapper=self):
            if lastweekarea and (data.week, data.area) != lastweekarea:
                print(combined.tojson(), file=output)
                combined = AreaData()
            lastweekarea = (data.week, data.area)
            combined.week = data.week
            combined.area = data.area
            if data.measure == "Tapausten lukumäärä":
                combined.cases = int(data.value)
            elif data.measure == "Asukaslukumäärä":
                combined.population = int(data.value)
            elif data.measure == "Testausmäärä":
                combined.tests = int(data.value)
            elif data.measure == "Kuolemantapausten lukumäärä":
                combined.deaths = int(data.value)

            combined.datadate = str(self.datadate)

        print(combined.tojson(), file=output)


class THLTestit(THLData):
    name = "testit"
    url = "https://sampo.thl.fi/pivot/prod/fi/epirapo/covid19case/fact_epirapo_covid19case.json?row=dateweek20200101-509093L&column=measure-141082"

    fieldmap = {
        "dateweek20200101": "date",
        "hcdmunicipality2020": "area",
    }

    valuemap = {
        "Kaikki Alueet": "Koko maa",
    }

    def run(self, output):
        data = requests.get(self.url, headers=requestheaders)
        data.raise_for_status()
        p = Parser(data=data.json())
        lastdate = None
        combined = TestsData()
        for data in p.parse(mapper=self):
            if lastdate and data.date != lastdate:
                print(combined.tojson(), file=output)
                combined = TestsData()
            lastdate = data.date
            combined.date = data.date
            combined.datadate = str(self.datadate)
            if data.measure == "Tapausten lukumäärä":
                combined.cases = int(data.value)
            elif data.measure == "Testausmäärä":
                combined.tests = int(data.value)

        print(combined.tojson(), file=output)


class THLTartunnat(THLData):
    name = "tartunnat"
    datatype = InfectionData
    url = "https://sampo.thl.fi/pivot/prod/fi/epirapo/covid19case/fact_epirapo_covid19case.json?row=dateweek20200101-509093L&column=hcdmunicipality2020-445222L"

    fieldmap = {
        "dateweek20200101": "date",
        "hcdmunicipality2020": "area",
    }

    valuemap = {
        "Kaikki Alueet": "Koko maa",
    }


class THLIat(THLData):
    name = "iat"
    url = "https://sampo.thl.fi/pivot/prod/fi/epirapo/covid19case/fact_epirapo_covid19case.json?column=ttr10yage-444309,sex-444328"

    def run(self, output):
        data = requests.get(self.url, headers=requestheaders)
        data.raise_for_status()
        p = Parser(data=data.json())
        combined = DemographyData()
        for data in p.parse(mapper=self):
            if data.sex == "Kaikki sukupuolet":
                setattr(combined, data.ttr10yage, int(data.value))
            elif data.ttr10yage == "Kaikki ikäryhmät":
                setattr(combined, data.sex, int(data.value))

        combined.datadate = str(self.datadate)

        print(combined.tojson(), file=output)


class THLIkaviikot(THLData):
    name = "ageweeks"
    url = "https://sampo.thl.fi/pivot/prod/fi/epirapo/covid19case/fact_epirapo_covid19case.json?row=dateweek20200101-509030&row=ttr10yage-444309&column=measure-444833"

    fieldmap = {
        "dateweek20200101": "week",
    }

    valuemap = {
        "Kaikki ikäryhmät": "total",
    }
    
    def run(self, output):
        data = requests.get(self.url, headers=requestheaders)
        data.raise_for_status()
        p = Parser(data=data.json())
        combined = AgeWeekData()
        lastweek = None
        for data in p.parse(mapper=self):
            if lastweek and data.week != lastweek:
                print(combined.tojson(), file=output)
                combined = AgeWeekData()
            lastweek = data.week
            if data.week == 'Aika' or data.week == 'Kaikki ajat':
                continue
            try:
                value = int(data.value)
            except ValueError:
                value = None
            setattr(combined, data.ttr10yage, value)
            combined.datadate = str(self.datadate)
            combined.week = self.parseweek(data.week)

        if hasattr(combined, 'total'):
            print(combined.tojson(), file=output)

    def parseweek(self, week):
        (_, year, _, weeknum) = week.split()
        return str(datetime.date.fromisocalendar(int(year), int(weeknum), 1))


class THLKuolemat(THLData):
    name = "kuolemat"
    datatype = DeathsData

    #url = "https://sampo.thl.fi/pivot/prod/fi/epirapo/covid19case/fact_epirapo_covid19case.json?row=dateweek20200101-443702L&column=measure-492118"
    url = "https://sampo.thl.fi/pivot/prod/fi/epirapo/covid19case/fact_epirapo_covid19case.json?row=dateweek20200101-509093L&column=measure-492118"

    fieldmap = {
        "dateweek20200101": "date",
        "hcdmunicipality2020": "area",
    }

    valuemap = {
        "Kaikki Alueet": "Koko maa",
    }

    def run(self, output):
        data = requests.get(self.url, headers=requestheaders)
        data.raise_for_status()
        p = Parser(data=data.json())
        lastdate = None
        combined = DeathsData()
        for data in p.parse(mapper=self):
            if lastdate and data.date != lastdate:
                print(combined.tojson(), file=output)
                combined = DeathsData()
            lastdate = data.date
            combined.date = data.date
            combined.datadate = str(self.datadate)
            if data.measure == "Tapausten lukumäärä":
                combined.cases = int(data.value)
            elif data.measure == "Kuolemantapausten lukumäärä":
                combined.deaths = int(data.value)

            

        print(combined.tojson(), file=output)

class THLIat2(THLData):
    name = "kuolemaiat"
    url = "https://sampo.thl.fi/pivot/prod/fi/epirapo/covid19case/fact_epirapo_covid19case.json?column=ttr10yage-444309,sex-444328&row=measure-492118"

    def run(self, output):
        data = requests.get(self.url, headers=requestheaders)
        data.raise_for_status()
        p = Parser(data=data.json())
        combined = DeathDemographyData()
        for data in p.parse(mapper=self):
            try:
                datavalue = int(data.value)
            except ValueError:
                datavalue = None
                
            if data.sex == "Kaikki sukupuolet":
                setattr(combined, data.ttr10yage, datavalue)
            elif data.ttr10yage == "Kaikki ikäryhmät":
                setattr(combined, data.sex, datavalue)

        combined.datadate = str(self.datadate)

        print(combined.tojson(), file=output)

class THLSairaalat(THLData):
    name = "sairaalat"
    datatype = HospitalData

    url = "https://sampo.thl.fi/pivot/prod/fi/epirapo/covid19care/fact_epirapo_covid19care.json?row=dateweek20200101-509093L&row=erva-456367L&column=measure-547523.547516.456732.547531"

    fieldmap = {
        "dateweek20200101": "date",
        "erva": "area",
    }

    valuemap = {
        "Kaikki erityisvastuualueet": "Koko maa",
        "Helsingin yliopistollisen keskussairaalan erityisvastuualue": "HYKS",
        "Kuopion yliopistollisen sairaalan erityisvastuualue": "KYS",
        "Oulun yliopistollisen sairaalan erityisvastuualue": "OYS",
        "Tampereen yliopistollisen sairaalan erityisvastuualue": "TAYS",
        "Turun yliopistollisen sairaalan erityisvastuualue": "TYKS",

        "Käynnissä olevat osastojaksot perusterveydenhuollon osastolla": "perus",
        "Käynnissä olevat osastojaksot erikoissairaanhoidon osastoilla": "erikois",
        "Käynnissä olevat tehohoitojaksot": "teho",
        "Käynnissä olevat vuodeosastojaksot (ennen 7.12.2020)": "vuode",
    }

    def run(self, output):
        data = requests.get(self.url, headers=requestheaders)
        data.raise_for_status()
        p = Parser(data=data.json())
        lastdate = None
        lastarea = None
        combined = HospitalData()
        for data in p.parse(mapper=self):
            if lastdate and (data.date != lastdate or data.area != lastarea):
                print(combined.tojson(), file=output)
                combined = HospitalData()
            lastdate = data.date
            lastarea = data.area
            combined.date = data.date
            combined.datadate = str(self.datadate)
            combined.area = data.area
            #print(data.tojson())
            if data.measure == "perus":
                combined.basic = int(data.value)
            elif data.measure == "erikois":
                combined.special = int(data.value)
            elif data.measure == "teho":
                combined.intensive = int(data.value)
            elif data.measure == "vuode":
                combined.normal = int(data.value)

        print(combined.tojson(), file=output)


datasets = {}
for ds in list(locals().values()):
    # print v, type(v), types.ClassType
    if inspect.isclass(ds) and issubclass(ds, THLData) and ds.name:
        datasets[ds.name] = ds


def usage():
    l = list(datasets.keys())
    l.sort()

    print("CMDS: ", ", ".join(l))


def main():

    p = optparse.OptionParser()
    p.add_option(
        "-s",
        "--stdout",
        action="store_true",
        dest="write_stdout",
        default=False,
        help="output to stdout",
    )
    p.add_option(
        "-C", "--csv", action="store_true", dest="csv", default=False, help="csv mode"
    )
    p.add_option(
        "-f",
        "--outputfile",
        action="store",
        dest="outputfile",
        default=None,
        help="outputfile name",
    )
    p.add_option(
        "-d",
        "--date",
        action="store",
        type="int",
        dest="dateoffset",
        default=0,
        help="Offset date by X days",
    )
    p.add_option(
        "-o",
        "--overwrite",
        action="store_true",
        dest="overwrite",
        default=False,
        help="overwrite existing outputfile",
    )

    (options, args) = p.parse_args()
    if not args:
        usage()
        return
    dataset = datasets.get(args[0])
    if dataset:
        ds = dataset()
        ds.setdatadate(offset=options.dateoffset)
        if options.write_stdout:
            ds.run(sys.stdout)
        else:
            if options.outputfile:
                outputfile = options.outputfile
            else:
                outputfile = ds.getfilename()
            if os.path.exists(outputfile) and os.path.getsize(outputfile) > 0 and not options.overwrite:
                print("%s exists" % outputfile)
                return
            with open(outputfile, 'w') as fp:
                ds.run(fp)
    else:
        usage()


if __name__ == "__main__":
    main()
