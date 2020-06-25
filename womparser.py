#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, os, json, datetime, re, urllib, time, optparse

import requests

from lxml import html


class ParserData(object):
    
    def __init__(self, **values):
        self.__values = values
        self.__values['type'] = self.type
        for attr in values:
            setattr(self, attr, values[attr])

    def __setattr__(self, attr, value):
        if not attr.startswith('_'):
            self.__values[attr] = value
        super(ParserData, self).__setattr__(attr, value)
    
    def tojson(self):
        return json.dumps(self.__values, sort_keys=True)

    def __str__(self):
        return str(self.values)

class CountryData(ParserData):
    type = 'countrydata'

class DetailData(ParserData):
    type = 'detaildata'

class PopulationData(ParserData):
   type = 'populationdata'


class WOMParser(object):

    def __init__(self, url):
        self.url = url

    def parsenumber(self, text):
        if text is None:
            return text
        try:
            return int(text.replace(',',''))
        except ValueError:
            return text
        
    def parsecountries(self):
        r = requests.get(self.url)
        r.raise_for_status()
        page = html.fromstring(r.content)

        #table = page.xpath('//*[@id="main_table_countries_today"]/tbody[1]')[0]
        table = page.xpath('//*[@id="main_table_countries_yesterday"]/tbody[1]')[0]
        #country_element = table.xpath("//td[contains(., 'USA')]")[0]
        #print(html.tostring(country_element))
        #row = country_element.xpath("./..")[0]
        for row in table.xpath("tr"):
            #print(html.tostring(row))
            if row.attrib.get("class") in ["total_row_world row_continent", "total_row_world"]:
                continue
            links = row.xpath("td/a")
            if not links:
                continue
            country = links[0].text
            
            data = [self.parsenumber(td.text) for td in row.xpath("td")]

            baseidx = 1
            
            total_cases = data[baseidx+1]
            new_cases = data[baseidx+2]
            total_deaths = data[baseidx+3]
            new_deaths = data[baseidx+4]
            total_recovered = data[baseidx+5]
            active_cases = data[baseidx+6]
            new_recovered = data[baseidx+7]
            serious_critical = data[baseidx+8]
            total_per_1m = data[baseidx+9]
            total_deaths_per_1m = data[baseidx+10]
            total_tests = data[baseidx+11]
            total_tests_per_1m = data[baseidx+12]
            continent = data[baseidx+14]
            
            if len(links) > 1:
                population = self.parsenumber(links[1].text)
            else:
                population = data[baseidx+13]
                

            if False:
                print("Country: ", country)
                print("Total cases: ", total_cases)
                print("New cases: ", new_cases)
                print("Total deaths: ", total_deaths)
                print("New deaths: ", new_deaths)
                print("Active cases: ", active_cases)
                print("Total recovered: ", total_recovered)
                print("Serious, critical cases: ", serious_critical)


            countrydata = CountryData(
                country=country,
                total_cases = total_cases,
                new_cases = new_cases,
                total_deaths = total_deaths,
                new_deaths = new_deaths,
                active_cases = active_cases,
                total_recovered = total_recovered,
                #new_recovered = new_recovered,
                serious_critical = serious_critical,
                total_per_1m = total_per_1m,
                total_deaths_per_1m = total_deaths_per_1m,
                total_tests = total_tests,
                total_tests_per_1m = total_tests_per_1m,
                date = str(datetime.date.today()-datetime.timedelta(days=1)),
                continent = continent,
                population = population,
                #data = str(data),
            )
            yield countrydata

    def parsepopulation(self):
        r = requests.get(self.url)
        r.raise_for_status()
        page = html.fromstring(r.content)

        table = page.xpath('//*[@id="example2"]/tbody[1]')[0]
        for row in table.xpath("tr"):
            #print(html.tostring(row))
            if row.attrib.get("class") in ["total_row_world row_continent", "total_row_world"]:
                continue
            country_elem = row.xpath("td/a")
            if not country_elem:
                continue
            country = country_elem[0].text

            data = [self.parsenumber(td.text) for td in row.xpath("td")]

            population = data[2]

            if 0:
                print("Country: ", country)
                print("Population: ", population)


            popdata = PopulationData(
                country=country,
                population=data[2]
            )
            yield popdata


    def parsedetails(self):
        r = requests.get(self.url)
        r.raise_for_status()
        page = html.fromstring(r.content)

        table = page.xpath('//*[@id="main_table_countries_yesterday"]/tbody[1]')[0]

        for row in table.xpath("tr"):
            if row.attrib.get("class") in ["total_row_world row_continent", "total_row_world"]:
                continue
            country_elem = row.xpath("td/a")
            if not country_elem:
                continue

            country = country_elem[0].text
            url = country_elem[0].attrib.get('href')
            (cases, deaths, active) = self.parsecountry(country, url)

            detaildata = DetailData(
                country=country,
                cases = cases,
                deaths = deaths,
                active = active,
            )
 
            yield detaildata

    def parsecountry(self, country, url):
        r = requests.get(urllib.parse.urljoin(self.url, url))
        r.raise_for_status()
        page = html.fromstring(r.content)
        
        script = page.xpath('//div[@class="tabbable-panel-cases"]/following-sibling::script[1]')
        if script:
            cases = self.parsescript(script[0], "Cases")
        else:
            cases = []

        script = page.xpath('//div[@class="tabbable-panel-deaths"]/following-sibling::script[1]')
        if script:
            deaths = self.parsescript(script[0], "Deaths")
        else:
            deaths = []

        script = page.xpath('//div[@id="graph-active-cases-total"]/following-sibling::script[1]')
        if script:
            active = self.parsescript(script[0], "Currently Infected")
        else:
            active = []

        return cases, deaths, active
            
    def parsescript(self, elem, attribute):
        lines = elem.text.split('\n')

        try:
            xaxis = lines.index('        xAxis: {')
        except ValueError:
            xaxis = lines.index('            xAxis: {')
        datevalues = self.parsevalues(lines[xaxis+1])
        dates = [self.parsedate(d) for d in datevalues]
        try:
            vidx = lines.index("            name: '%s'," % attribute)
        except ValueError:
            vidx = lines.index("                name: '%s'," % attribute)
            
        values = self.parsevalues(lines[vidx+3])
        #print(dates)
        #print(values)
        return list(zip(dates, values))

    def parsevalues(self, line):
        r = re.compile(".*(\[.*?\]).*")
        v = r.match(line)
        parsed = json.loads(v.group(1))
        return parsed

    def parsedate(self, text):
        ts = time.strptime(text, '%b %d')
        d = datetime.date(2020, ts.tm_mon, ts.tm_mday)
        return d.strftime('%Y-%m-%d')


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
    dataset = args[0]

    cov_url = 'https://www.worldometers.info/coronavirus/'
    pop_url = 'https://www.worldometers.info/world-population/population-by-country/'


    if options.outputfile:
        outputfile = options.outputfile
    else:
        datestr = datetime.date.today().strftime("%Y%m%d")
        outputfile = "%s-%s.json" % (dataset, datestr)

    if dataset == 'countries':
        parser = WOMParser(cov_url)
        parsermethod = parser.parsecountries

    elif dataset == 'details':
        parser = WOMParser(cov_url)
        parsermethod = parser.parsedetails

    elif dataset == 'population':
        parser = WOMParser(pop_url)
        parsermethod = parser.parsepopulation

    else:
        usage()
        return

    if parsermethod:
        if options.write_stdout:
            for event in parsermethod():
                print(event.tojson())

        else:
            if os.path.exists(outputfile) and not options.overwrite:
                print("%s exists" % outputfile)
                return

            with open(outputfile, 'w') as fp:
                for event in parsermethod():
                    print(event.tojson(), file=fp)


if __name__ == "__main__":
    main()

