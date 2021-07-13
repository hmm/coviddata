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

class VaxMunicipalityData(ParserData):
    type = "vaxmunicipalities"

class VaxWeeks(THLData):
    name = "vaxweeks"
    
    url = "https://sampo.thl.fi/pivot/prod/fi/vaccreg/cov19cov/fact_cov19cov.json?row=area-518362&column=dateweek20201226-525425&column=cov_vac_dose-533174.533170.533164.&column=measure-533175&column=cov_vac_age-518413"    

    fieldmap = {
        "dateweek20201226": "week",
        "hcdmunicipality2020": "area",
        "cov_vac_age": "age",
        "cov_vac_dose": "dose",
    }

    valuemap = {
        "Kaikki alueet": "Koko maa",
        "Kaikki iät": "all",
        "Kaikki ajat": "Yhteensä",
        "Ensimmäinen annos": "first",
        "Toinen annos": "second",
        "Kaikki annokset": "all",
    }

    def run(self, output):
        data = requests.get(self.url, headers=requestheaders)
        data.raise_for_status()
        p = Parser(data=data.json())
        lastweekareadose = None
        combined = VaxWeekData()
        for data in p.parse(mapper=self):
            if lastweekareadose and (data.week, data.area, data.dose) != lastweekareadose:
                print(combined.tojson(), file=output)
                combined = VaxWeekData()

            lastweekareadose = (data.week, data.area, data.dose)
            combined.week = data.week
            combined.area = data.area
            combined.dose = data.dose
            combined.datadate = str(self.datadate)
            setattr(combined, data.age, int(data.value))
            
        print(combined.tojson(), file=output)

        
class VaxCoverage(THLData):
    name = "vaxcoverage"
    
    url = "https://sampo.thl.fi/pivot/prod/fi/vaccreg/cov19cov/fact_cov19cov.json?row=area-518362&column=cov_vac_dose-533170.533164.&column=measure-533172.533185.&column=cov_vac_age-518413"    

    fieldmap = {
        "dateweek20201226": "week",
        "hcdmunicipality2020": "area",
        "cov_vac_age": "age",
        "cov_vac_dose": "dose",
    }

    valuemap = {
        "Kaikki alueet": "Koko maa",
        "Kaikki iät": "all",
        "Aika": "Yhteensä",
        "Ensimmäinen annos": "first",
        "Toinen annos": "second",
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
            if data.measure == "Rokotettuja henkilöitä":
                setattr(combined, "doses-"+data.age, int(data.value))
            elif data.measure == "Rokotuskattavuus":
                setattr(combined, "coverage-"+data.age, data.value.replace(',', '.'))
            else:
                raise Exception("Unknown measure %s" % data.measure)
            
        print(combined.tojson(), file=output)


class VaxPopulation(THLData):
    name = "vaxpopulation"
    
    url = "https://sampo.thl.fi/pivot/prod/fi/vaccreg/cov19cov/fact_cov19cov.json?row=area-518362&column=measure-433796&column=cov_vac_age-518413"    

    fieldmap = {
        "dateweek20201226": "week",
        "hcdmunicipality2020": "area",
        "cov_vac_age": "age",
        "cov_vac_dose": "dose",
    }

    valuemap = {
        "Kaikki alueet": "Koko maa",
        "Kaikki iät": "all",
        "Aika": "Yhteensä",
        "Ensimmäinen annos": "first",
        "Toinen annos": "second",
        "Kaikki annokset": "all",
    }

    def run(self, output):
        data = requests.get(self.url, headers=requestheaders)
        data.raise_for_status()
        p = Parser(data=data.json())
        lastarea = None
        combined = VaxPopData()
        for data in p.parse(mapper=self):
            if lastarea and data.area != lastarea:
                print(combined.tojson(), file=output)
                combined = VaxPopData()

            lastarea = data.area
            combined.area = data.area
            combined.datadate = str(self.datadate)
            setattr(combined, data.age, int(data.value))
            
        print(combined.tojson(), file=output)

        
class VaxProduct(THLData):
    name = "vaxproduct"

    url = "https://sampo.thl.fi/pivot/prod/fi/vaccreg/cov19cov/fact_cov19cov.json?row=area-518362&column=dateweek20201226-525425&column=vacprod-533729.533761.547315.533741.&column=measure-533175&column=cov_vac_age-518413"    

    fieldmap = {
        "dateweek20201226": "week",
        "hcdmunicipality2020": "area",
        "cov_vac_age": "age",
        "vacprod": "product",
    }

    valuemap = {
        "Kaikki alueet": "Koko maa",
        "Kaikki ajat": "Yhteensä",
        "Kaikki iät": "all",
        "Comirnaty (BioNTech)": "Pfizer",
        "COVID-19 Vaccine Moderna (MODERNA)": "Moderna",
        "Vaxzevria (AstraZeneca)": "AstraZeneca",
        "COVID-19 Vaccine Janssen (JANSSEN-CILAG)": "Janssen",
    }

    def run(self, output):
        data = requests.get(self.url, headers=requestheaders)
        data.raise_for_status()
        p = Parser(data=data.json())
        lastweekareaprod = None
        combined = VaxProdData()
        for data in p.parse(mapper=self):
            if lastweekareaprod and (data.week, data.area, data.product) != lastweekareaprod:
                print(combined.tojson(), file=output)
                combined = VaxProdData()

            lastweekareaprod = (data.week, data.area, data.product)
            combined.week = data.week
            combined.area = data.area
            combined.product = data.product
            combined.datadate = str(self.datadate)
            setattr(combined, data.age, int(data.value))
            
        print(combined.tojson(), file=output)


class VaxMunicipalities(THLData):
    name = "vaxmunicipalities"

    url = "https://sampo.thl.fi/pivot/prod/fi/vaccreg/cov19cov/fact_cov19cov.json?row=area-518376L&column=cov_vac_dose-533174.533170.533164.&column=measure-533175.533172.533185.433796.&column=cov_vac_age-518413"

    fieldmap = {
        "dateweek20201226": "week",
        "hcdmunicipality2020": "area",
        "cov_vac_age": "age",
        "cov_vac_dose": "dose",
    }

    valuemap = {
        "Kaikki alueet": "Koko maa",
        "Kaikki iät": "all",
        "Aika": "Yhteensä",
        "Ensimmäinen annos": "first",
        "Toinen annos": "second",
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
            if data.measure == "Rokotettuja henkilöitä":
                setattr(combined, "doses-"+data.age, int(data.value))
            elif data.measure == "Rokotuskattavuus":
                setattr(combined, "coverage-"+data.age, data.value.replace(',', '.'))
            elif data.measure == "Annettuja annoksia":
                setattr(combined, "persons-"+data.age, int(data.value))
            elif data.measure == "Asukkaita":
                setattr(combined, "population-"+data.age, int(data.value))
            else:
                print(data.tojson())
                raise Exception("Unknown measure %s" % data.measure)
           
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
