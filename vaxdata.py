#!/usr/bin/env python3

import sys, os, json, inspect, argparse, datetime
import requests

from thldata import Parser, THLData, ParserData

requestheaders = {'User-Agent': 'thldata'}

    
class VaxWeekData(ParserData):
    type = "vaxweek"

class VaxCovData(ParserData):
    type = "vaxcoverage"
    
class VaxPopData(ParserData):
    type = "vaxpopulation"

class VaxProdData(ParserData):
    type = "vaxproduct"

class VaxProdAreaData(ParserData):
    type = "vaxproductarea"

class VaxMunicipalityData(ParserData):
    type = "vaxmunicipalities"

class VaxDayData(ParserData):
    type = "vaxdays"

class VaxAreaDayData(ParserData):
    type = "vaxareadays"

class VaxWeeks(THLData):
    name = "vaxweeks"
    
    url = "https://sampo.thl.fi/pivot/prod/fi/vaccreg/cov19cov/fact_cov19cov.json?row=area-518362&column=dateweek20201226-525425&column=cov_vac_dose-533174.533170.533164.639082.&column=measure-533175&column=cov_vac_age-518413L&column=cov_vac_age-660962L"

    fieldmap = {
        "dateweek20201226": "week",
        "hcdmunicipality2020": "area",
        "cov_vac_age": "age",
        "cov_vac_age1": "age2",
        "cov_vac_dose": "dose",
    }

    valuemap = {
        "Kaikki alueet": "Koko maa",
        "Kaikki iät": "all",
        "Kaikki ajat": "Yhteensä",
        "Ensimmäinen annos": "first",
        "Toinen annos": "second",
        "Kolmas annos": "third",
        "Kaikki annokset": "all",
    }

    def run(self, output):
        data = requests.get(self.url, headers=requestheaders)
        data.raise_for_status()
        p = Parser(data=data.json())
        lastweekareadose = None
        combined = VaxWeekData()
        for data in p.parse(mapper=self):
            #print(data.tojson())
            if lastweekareadose and (data.week, data.area, data.dose) != lastweekareadose:
                print(combined.tojson(), file=output)
                combined = VaxWeekData()

            lastweekareadose = (data.week, data.area, data.dose)
            combined.week = data.week
            combined.area = data.area
            combined.dose = data.dose
            combined.datadate = str(self.datadate)
            if data.age2 == 'Yhteensä':
                agefield = data.age
            else:
                agefield = data.age2
            if data.value == '..':
                setattr(combined, "doses-"+agefield, None)
            else:
                setattr(combined, "doses-"+agefield, int(data.value))
            
        print(combined.tojson(), file=output)

        
class VaxCoverage(THLData):
    name = "vaxcoverage"
    
    url = "https://sampo.thl.fi/pivot/prod/fi/vaccreg/cov19cov/fact_cov19cov.json?row=area-518362&column=cov_vac_dose-533170.533164.639082.&column=measure-533175.533172.533185.433796.&column=cov_vac_age-518413L&column=cov_vac_age-660962L"
    
    
    fieldmap = {
        "dateweek20201226": "week",
        "hcdmunicipality2020": "area",
        "cov_vac_age": "age",
        "cov_vac_age1": "age2",
        "cov_vac_dose": "dose",
    }

    valuemap = {
        "Kaikki alueet": "Koko maa",
        "Kaikki iät": "all",
        "Aika": "Yhteensä",
        "Ensimmäinen annos": "first",
        "Toinen annos": "second",
        "Kolmas annos": "third",
        "Kaikki annokset": "all",
    }

    def run(self, output):
        data = requests.get(self.url, headers=requestheaders)
        data.raise_for_status()
        p = Parser(data=data.json())
        lastareadose = None
        combined = VaxCovData()
        for data in p.parse(mapper=self):
            if lastareadose and (data.area, data.dose) != lastareadose:
                print(combined.tojson(), file=output)
                combined = VaxCovData()

            lastareadose = (data.area, data.dose)
            combined.area = data.area
            combined.dose = data.dose
            combined.datadate = str(self.datadate)
            if data.age2 == 'Yhteensä':
                agefield = data.age
            else:
                agefield = data.age2
            if data.measure == "Rokotettuja henkilöitä":
                setattr(combined, "persons-"+agefield, int(data.value))
            elif data.measure == "Annettuja annoksia":
                setattr(combined, "doses-"+agefield, int(data.value))
            elif data.measure == "Rokotuskattavuus":
                setattr(combined, "coverage-"+agefield, data.value.replace(',', '.'))
            elif data.measure == "Asukkaita":
                setattr(combined, "population-"+agefield, int(data.value))
            else:
                raise Exception("Unknown measure %s" % data.measure)
            
        print(combined.tojson(), file=output)


class VaxPopulation(THLData):
    name = "vaxpopulation"
    
    url = "https://sampo.thl.fi/pivot/prod/fi/vaccreg/cov19cov/fact_cov19cov.json?row=area-518362&column=measure-433796&column=cov_vac_age-518413L&column=cov_vac_age-660962L"

    fieldmap = {
        "dateweek20201226": "week",
        "hcdmunicipality2020": "area",
        "cov_vac_age": "age",
        "cov_vac_age1": "age2",
        "cov_vac_dose": "dose",
    }

    valuemap = {
        "Kaikki alueet": "Koko maa",
        "Kaikki iät": "all",
        "Aika": "Yhteensä",
        "Ensimmäinen annos": "first",
        "Toinen annos": "second",
        "Kolmas annos": "third",
        "Kaikki annokset": "all",
    }

    def run(self, output):
        data = requests.get(self.url, headers=requestheaders)
        data.raise_for_status()
        p = Parser(data=data.json())
        lastarea = None
        combined = VaxPopData()
        for data in p.parse(mapper=self):
            #print(data.tojson())
            if lastarea and data.area != lastarea:
                print(combined.tojson(), file=output)
                combined = VaxPopData()

            lastarea = data.area
            combined.area = data.area
            combined.datadate = str(self.datadate)
            if data.age2 == 'Yhteensä':
                setattr(combined, data.age, int(data.value))
            else:
                setattr(combined, data.age2, int(data.value))
                
            
        print(combined.tojson(), file=output)

        
class VaxProduct(THLData):
    name = "vaxproduct"

    url = "https://sampo.thl.fi/pivot/prod/fi/vaccreg/cov19cov/fact_cov19cov.json?row=area-518362&column=dateweek20201226-525425&column=vacprod-533729.533761.547315.533741.&column=measure-533175&column=cov_vac_dose-533170L&column=cov_vac_age-518413."

    fieldmap = {
        "dateweek20201226": "week",
        "hcdmunicipality2020": "area",
        "cov_vac_age": "age",
        "cov_vac_dose": "dose",
        "vacprod": "product",
    }

    valuemap = {
        "Kaikki alueet": "Koko maa",
        "Kaikki ajat": "Yhteensä",
        "Kaikki iät": "all",
        "Ensimmäinen annos": "first",
        "Toinen annos": "second",
        "Kolmas annos": "third",
        "Kaikki annokset": "all",
        "Comirnaty (BioNTech)": "Pfizer",
        "COVID-19 Vaccine Moderna (MODERNA)": "Moderna",
        "Spikevax (MODERNA)": "Moderna",
        "Vaxzevria (AstraZeneca)": "AstraZeneca",
        "COVID-19 Vaccine Janssen (JANSSEN-CILAG)": "Janssen",
    }

    def run(self, output):
        data = requests.get(self.url, headers=requestheaders)
        data.raise_for_status()
        p = Parser(data=data.json())
        lastdata = None
        combined = VaxProdData()
        for data in p.parse(mapper=self):
            if lastdata and (data.week, data.area, data.product, data.dose) != lastdata:
                print(combined.tojson(), file=output)
                combined = VaxProdData()

            lastdata = (data.week, data.area, data.product, data.dose)
            combined.week = data.week
            combined.area = data.area
            combined.product = data.product
            combined.dose = data.dose
            combined.datadate = str(self.datadate)
            setattr(combined, data.age, int(data.value))
            
        print(combined.tojson(), file=output)


class VaxProductAreas(THLData):
    name = "vaxproductareas"

    url = "https://sampo.thl.fi/pivot/prod/fi/vaccreg/cov19cov/fact_cov19cov.json?row=area-518376L&column=vacprod-533729.533761.547315.533741.&column=cov_vac_dose-533170L&column=measure-533175&column=cov_vac_age-518413."

    fieldmap = {
        "hcdmunicipality2020": "area",
        "cov_vac_age": "age",
        "cov_vac_dose": "dose",
        "vacprod": "product",
    }

    valuemap = {
        "Kaikki Tuotteet": "all",
        "Kaikki iät": "all",
        "Comirnaty (BioNTech)": "Pfizer",
        "COVID-19 Vaccine Moderna (MODERNA)": "Moderna",
        "Spikevax (MODERNA)": "Moderna",
        "Vaxzevria (AstraZeneca)": "AstraZeneca",
        "COVID-19 Vaccine Janssen (JANSSEN-CILAG)": "Janssen",
        "Ensimmäinen annos": "first",
        "Toinen annos": "second",
        "Kolmas annos": "third",
        "Kaikki annokset": "all",
    }

    def run(self, output):
        data = requests.get(self.url, headers=requestheaders)
        data.raise_for_status()
        p = Parser(data=data.json())
        lastdoseareaprod = None
        combined = VaxProdAreaData()
        for data in p.parse(mapper=self):
            if lastdoseareaprod and (data.dose, data.area, data.product) != lastdoseareaprod:
                print(combined.tojson(), file=output)
                combined = VaxProdAreaData()

            lastdoseareaprod = (data.dose, data.area, data.product)
            combined.area = data.area
            combined.product = data.product
            combined.dose = data.dose
            combined.datadate = str(self.datadate)
            setattr(combined, data.age, int(data.value))
            
        print(combined.tojson(), file=output)


class VaxMunicipalities(THLData):
    name = "vaxmunicipalities"

    url = "https://sampo.thl.fi/pivot/prod/fi/vaccreg/cov19cov/fact_cov19cov.json?row=area-518376L&column=cov_vac_dose-533174.533170.533164.639082.&column=measure-533175.533172.533185.433796.&column=cov_vac_age-518413L&column=cov_vac_age-660962L"

    fieldmap = {
        "dateweek20201226": "week",
        "hcdmunicipality2020": "area",
        "cov_vac_age": "age",
        "cov_vac_age1": "age2",
        "cov_vac_dose": "dose",
    }

    valuemap = {
        "Kaikki alueet": "Koko maa",
        "Kaikki iät": "all",
        "Aika": "Yhteensä",
        "Ensimmäinen annos": "first",
        "Toinen annos": "second",
        "Kolmas annos": "third",
        "Kaikki annokset": "all",
    }

    def run(self, output):
        data = requests.get(self.url, headers=requestheaders)
        data.raise_for_status()
        p = Parser(data=data.json())
        lastareadose = None
        combined = VaxMunicipalityData()
        for data in p.parse(mapper=self):
            if lastareadose and (data.area, data.dose) != lastareadose:
                print(combined.tojson(), file=output)
                combined = VaxMunicipalityData()

            lastareadose = (data.area, data.dose)
            combined.area = data.area
            combined.dose = data.dose
            combined.datadate = str(self.datadate)
            if data.age2 == 'Yhteensä':
                agefield = data.age
            else:
                agefield = data.age2
            if data.measure == "Rokotettuja henkilöitä":
                setattr(combined, "persons-"+agefield, int(data.value))
            elif data.measure == "Rokotuskattavuus":
                setattr(combined, "coverage-"+agefield, data.value.replace(',', '.'))
            elif data.measure == "Annettuja annoksia":
                setattr(combined, "doses-"+agefield, int(data.value))
            elif data.measure == "Asukkaita":
                setattr(combined, "population-"+agefield, int(data.value))
            else:
                print(data.tojson())
                raise Exception("Unknown measure %s" % data.measure)
           
        print(combined.tojson(), file=output)

class VaxDays(THLData):
    name = "vaxdays"

    url = "https://sampo.thl.fi/pivot/prod/fi/vaccreg/cov19cov/fact_cov19cov.json?row=dateweek20201226-525459L&filter=measure-533175&column=vacprod-533726&column=cov_vac_dose-533170L"

    fieldmap = {
        "dateweek20201226": "date",
        "cov_vac_dose": "dose",
        "vacprod": "product",
    }

    valuemap = {
        "Ensimmäinen annos": "first",
        "Toinen annos": "second",
        "Kolmas annos": "third",
        "Comirnaty (BioNTech)": "Pfizer",
        "COVID-19 Vaccine Moderna (MODERNA)": "Moderna",
        "Spikevax (MODERNA)": "Moderna",
        "Vaxzevria (AstraZeneca)": "AstraZeneca",
        "COVID-19 Vaccine Janssen (JANSSEN-CILAG)": "Janssen",
        "Kaikki tuotteet": "all",
    }

    def run(self, output):
        data = requests.get(self.url, headers=requestheaders)
        data.raise_for_status()
        p = Parser(data=data.json())
        lastdata = None
        combined = VaxDayData()
        for data in p.parse(mapper=self):
            if lastdata and (data.date, data.product) != lastdata:
                print(combined.tojson(), file=output)
                combined = VaxDayData()

            lastdata = (data.date, data.product)
            combined.date = data.date
            combined.product = data.product
            combined.datadate = str(self.datadate)
            if data.dose == "first":
                combined.first = int(data.value)
            elif data.dose == "second":
                combined.second = int(data.value)
            elif data.dose == "third":
                combined.third = int(data.value)
            else:
                print(data.tojson())
                raise Exception("Unknown dose %s" % data.dose)

        print(combined.tojson(), file=output)

class VaxAreaDays(THLData):
    name = "vaxareadays"

    url = "https://sampo.thl.fi/pivot/prod/fi/vaccreg/cov19cov/fact_cov19cov.json?row=dateweek20201226-525459L&filter=measure-533175&column=area-518362&column=cov_vac_dose-533170L"

    fieldmap = {
        "dateweek20201226": "date",
        "cov_vac_dose": "dose",
        "vacprod": "product",
    }

    valuemap = {
        "Ensimmäinen annos": "first",
        "Toinen annos": "second",
        "Kolmas annos": "third",
        "Kaikki tuotteet": "all",
    }

    def run(self, output):
        data = requests.get(self.url, headers=requestheaders)
        data.raise_for_status()
        p = Parser(data=data.json())
        lastdata = None
        combined = VaxAreaDayData()
        for data in p.parse(mapper=self):
            if lastdata and (data.date, data.area) != lastdata:
                print(combined.tojson(), file=output)
                combined = VaxAreaDayData()

            lastdata = (data.date, data.area)
            combined.date = data.date
            combined.area = data.area
            combined.datadate = str(self.datadate)
            if data.dose == "first":
                combined.first = int(data.value)
            elif data.dose == "second":
                combined.second = int(data.value)
            elif data.dose == "third":
                combined.third = int(data.value)
            else:
                print(data.tojson())
                raise Exception("Unknown dose %s" % data.dose)

        print(combined.tojson(), file=output)



datasets = {}
for dsc in list(locals().values()):
    # print v, type(v), types.ClassType
    if inspect.isclass(dsc) and issubclass(dsc, THLData) and dsc.name:
        datasets[dsc.name] = dsc


def usage():
    l = list(datasets.keys())
    l.sort()

    print("CMDS: ", ", ".join(l))


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument(
        "-s",
        "--stdout",
        action="store_true",
        dest="write_stdout",
        default=False,
        help="output to stdout",
    )
    p.add_argument(
        "-C", "--csv", action="store_true", dest="csv", default=False, help="csv mode"
    )
    p.add_argument(
        "-f",
        "--outputfile",
        action="store",
        dest="outputfile",
        default=None,
        help="outputfile name",
    )
    p.add_argument(
        "-d",
        "--date",
        action="store",
        type=int,
        dest="dateoffset",
        default=0,
        help="Offset date by X days",
    )
    p.add_argument(
        "-o",
        "--overwrite",
        action="store_true",
        dest="overwrite",
        default=False,
        help="overwrite existing outputfile",
    )
    p.add_argument("cmd", choices=datasets.keys())

    return p.parse_args()


def main():
    args = parse_args()
    if not args:
        usage()
        return
    dataset = datasets.get(args.cmd)
    if dataset:
        ds = dataset()
        ds.setdatadate(offset=args.dateoffset)
        if args.write_stdout:
            ds.run(sys.stdout)
        else:
            if args.outputfile:
                outputfile = args.outputfile
            else:
                outputfile = ds.getfilename()
            if os.path.exists(outputfile) and os.path.getsize(outputfile) > 0 and not args.overwrite:
                print("%s exists" % outputfile)
                return
            with open(outputfile, 'w') as fp:
                ds.run(fp)


if __name__ == "__main__":
    main()
