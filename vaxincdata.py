#!/usr/bin/env python3

import sys, os, json, inspect, argparse, datetime
import requests

from thldata import Parser, THLData, ParserData

requestheaders = {'User-Agent': 'thldata'}


class VaxStatData(ParserData):

    def __init__(self, data=None, datatype=None):
        super().__init__(data)
        if datatype:
            self.type = datatype

def tofloat(self, v):
    return float(v.replace(',', '.'))

class VaxStatBase(THLData):

    valuemap = {
        "Ei rokotussuojaa": "none",
        "Osittainen rokotussuoja": "partial",
        "Täysi rokotussuoja": "full",
        "Täysi rokotussuoja ilman tehostetta": "full",
        "Täysi rokotussuoja ja tehoste": "booster",
        "Koko väestö": "all",
        "12-29 vuotiaat": "12-29",
        "30-49 vuotiaat": "30-49",
        "50-69 vuotiaat": "50-69",
        "70+ vuotiaat": "70+",
        "Ikäryhmät yhdessä": "all",
    }

    fieldmap = {
        "inciagegroup": "agegroup",
        "incivacstatus": "vaxstatus",
        "quadrimestermonth": "month",
    }

    groupfields = ("month",)
    valuetype = int

    months = [
        'tammikuu',
        'helmikuu',
        'maaliskuu',
        'huhtikuu',
        'toukokuu',
        'kesäkuu',
        'heinäkuu',
        'elokuu',
        'syyskuu',
        'lokakuu',
        'marraskuu',
        'joulukuu',
    ]


    def getgroupvalue(self, data):
        return [getattr(data, attr) for attr in self.groupfields]

    def getmonth(self, monthyear):
        (month, year) = monthyear.split()
        return f"{year}-{self.months.index(month)+1:02d}"

    def run(self, output):
        data = requests.get(self.url, headers=requestheaders)
        data.raise_for_status()
        p = Parser(data=data.json())
        combined = VaxStatData(datatype=self.datatype)
        lastvalue = None
        for data in p.parse(mapper=self):
            #print(data.tojson())
            groupvalue = self.getgroupvalue(data)
            if lastvalue and groupvalue != lastvalue:
                print(combined.tojson(), file=output)
                combined = VaxStatData(datatype=self.datatype)

            lastvalue = groupvalue
            combined.month = self.getmonth(data.month)
                
            combined.datadate = str(self.datadate)
            setattr(combined, f"{data.vaxstatus}-{data.agegroup}", self.valuetype(data.value))
            
        print(combined.tojson(), file=output)

    
class VaxStatPatients(VaxStatBase):
    name = "vaxstatpatients"

    url = "https://sampo.thl.fi/pivot/prod/fi/epirapo/covid19inci/fact_epirapo_covid19inci.json?row=quadrimestermonth-642743L&column=inciagegroup-639348&row=incivacstatus-639350&filter=measure-639169"
    datatype = "vaxstatpatients"
    

class VaxStatICU(VaxStatBase):
    name = "vaxstaticu"

    url = "https://sampo.thl.fi/pivot/prod/fi/epirapo/covid19inci/fact_epirapo_covid19inci.json?row=quadrimestermonth-642743L&column=inciagegroup-639348&row=incivacstatus-639350&filter=measure-639171"
    datatype = "vaxstaticu"
    
class VaxStatDeaths(VaxStatBase):
    name = "vaxstatdeaths"

    url = "https://sampo.thl.fi/pivot/prod/fi/epirapo/covid19inci/fact_epirapo_covid19inci.json?row=quadrimestermonth-642743L&column=inciagegroup-639348&row=incivacstatus-639350&filter=measure-639168"
    datatype = "vaxstatdeaths"
    
class VaxStatCases(VaxStatBase):
    name = "vaxstatcases"

    url = "https://sampo.thl.fi/pivot/prod/fi/epirapo/covid19inci/fact_epirapo_covid19inci.json?row=quadrimestermonth-642743L&column=inciagegroup-639348&row=incivacstatus-639350&filter=measure-639170"
    datatype = "vaxstatcases"

class VaxStatPersonMonths(VaxStatBase):
    name = "vaxstatpersonmonths"

    url = "https://sampo.thl.fi/pivot/prod/fi/epirapo/covid19inci/fact_epirapo_covid19inci.json?row=quadrimestermonth-642743L&column=inciagegroup-639348&row=incivacstatus-639350&filter=measure-650912"
    datatype = "vaxstatpersonmonths"
    valuetype = tofloat
    

class VaxIncPatients(VaxStatBase):
    name = "vaxincpatients"

    url = "https://sampo.thl.fi/pivot/prod/fi/epirapo/covid19inci/fact_epirapo_covid19inci.json?row=quadrimestermonth-642743L&column=inciagegroup-639348&row=incivacstatus-639350&filter=measure-642065"

    datatype = "vaxincpatients"
    valuetype = tofloat
    

class VaxIncICU(VaxStatBase):
    name = "vaxincicu"

    url = "https://sampo.thl.fi/pivot/prod/fi/epirapo/covid19inci/fact_epirapo_covid19inci.json?row=quadrimestermonth-642743L&column=inciagegroup-639348&row=incivacstatus-639350&filter=measure-642062"
    datatype = "vaxincicu"
    valuetype = tofloat

    
class VaxIncDeaths(VaxStatBase):
    name = "vaxincdeaths"

    url = "https://sampo.thl.fi/pivot/prod/fi/epirapo/covid19inci/fact_epirapo_covid19inci.json?row=quadrimestermonth-642743L&column=inciagegroup-639348&row=incivacstatus-639350&filter=measure-642064"
    datatype = "vaxincdeaths"
    valuetype = tofloat

    
class VaxIncCases(VaxStatBase):
    name = "vaxinccases"

    url = "https://sampo.thl.fi/pivot/prod/fi/epirapo/covid19inci/fact_epirapo_covid19inci.json?row=quadrimestermonth-642743L&column=inciagegroup-639348&row=incivacstatus-639350&filter=measure-642063"
    datatype = "vaxinccases"
    valuetype = tofloat

    
    
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
    
