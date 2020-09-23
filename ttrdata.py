#!/usr/bin/env python3

import sys, os, json, csv, argparse, datetime, urllib, codecs
import requests

requestheaders = {'User-Agent': 'ttrdata'}


class UrlGen:
    csvurl = "https://sampo.thl.fi/pivot/prod/fi/ttr/shp/fact_shp.csv"

    # covid-19
    reportgroup = 'reportgroup-438231'

    agegroups = {
        'all': 'agegroup-12046',
        '00-04': 'agegroup-12299',
        '05-09': 'agegroup-12188',
        '10-14': 'agegroup-12433',
        '15-19': 'agegroup-12171',
        '20-24': 'agegroup-12096',
        '25-29': 'agegroup-12071',
        '30-34': 'agegroup-12345',
        '35-39': 'agegroup-12395',
        '40-44': 'agegroup-12399',
        '45-49': 'agegroup-12462',
        '50-54': 'agegroup-12223',
        '55-59': 'agegroup-12269',
        '60-64': 'agegroup-12397',
        '65-69': 'agegroup-12405',
        '70-74': 'agegroup-12239',
        '75-': 'agegroup-12297',
    }

    areas = {
        'all': 'area-12260',
        'ahvenanmaa': 'area-12327',
    }

    measure = {
        'cases': 'measure-73006',
        'incidence': 'measure-73008',
    }

    sex = {
        'women': 'sex-12424',
        'men': 'sex-12449',
    }

    time = {
        '2020-09': 'time-429386',
        '2020': 'time-429400',
    }

    @classmethod
    def genurl(cls,
               time='2020',
               measure='cases',
               agegroup='all',
               area='all',
               sex='all',
    ):
        params = []
        params.append(('row', cls.areas[area]))
        params.append(('column', cls.time[time]))
        params.append(('filter', cls.reportgroup))
        params.append(('filter', cls.agegroups[agegroup]))
        params.append(('filter', cls.measure[measure]))
        if sex != 'all':
            params.append(('filter', cls.sex[sex]))

        url = "%s?%s" % (cls.csvurl, urllib.parse.urlencode(params))
        return url


class AgeParser:
    name = "ttrages"

    def __init__(self, offset = 0):
        self.datadate = datetime.date.today() - datetime.timedelta(days=offset)
        self.data = {}

    def run(self, output):
        for agegroup in UrlGen.agegroups:
            for sex in ['all', 'men', 'women']:
                for measure in ['cases', 'incidence']:
                    url = UrlGen.genurl(agegroup=agegroup, sex=sex, measure=measure)
                    print(agegroup, sex, measure, url)
                    data = requests.get(url, headers=requestheaders)
                    data.raise_for_status()
                    self.parse(agegroup, sex, measure, data)

        for d in self.generate():
            print(d, file=output)

    def agegroup_to_attr(self, agegroup):
        if agegroup == '5v-ikäryhmät':
            return "all"
        return agegroup.replace('-', '_')

    def parse(self, agegroup, sex, measure, pagedata):
        reader = csv.DictReader(codecs.iterdecode(pagedata.iter_lines(), 'utf-8'), delimiter=';')
        #csvdata = [l for l in reader]

        for l in reader:
            if l['val']:
                if measure == 'incidence':
                    value = float(l['val'])
                else:
                    value = int(l['val'])
            else:
                value = 0
            #print(l)

            attrname = "{}_{}".format(measure, self.agegroup_to_attr(agegroup))
            #print(attrname, value)
            self.data.setdefault(l['Alue'], {}) \
                .setdefault(l['time'], {}) \
                .setdefault(sex, {}) \
                [attrname] = value

    def generate(self):
        for area in self.data:
            for time in self.data[area]:
                for sex in self.data[area][time]:
                    #agesum = sum(self.data[area][time][sex].values())
                    d = dict(
                        type = 'ttrages',
                        area = area.replace('sairaanhoitopiiri', 'SHP'),
                        time = time,
                        sex = sex,
                        datadate = str(self.datadate),
                    )
                    d.update(self.data[area][time][sex])
                    yield json.dumps(d, sort_keys=True, ensure_ascii=False)

    def getfilename(self):
        datestr = self.datadate.strftime("%Y%m%d")
        return "%s-%s.json" % (self.name, datestr)


datasets = {
    'ages': AgeParser,
}

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
        if args.write_stdout:
            ds.run(sys.stdout)
        else:
            if args.outputfile:
                outputfile = args.outputfile
            else:
                outputfile = ds.getfilename()
            if os.path.exists(outputfile) and not args.overwrite:
                print("%s exists" % outputfile)
                return
            with open(outputfile, 'w') as fp:
                ds.run(fp)
    else:
        usage()


if __name__ == "__main__":
    main()
