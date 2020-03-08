import collections
from collections import Counter
import numpy as np
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET
import csv
import requests
from argparse import ArgumentParser
from argparse import RawTextHelpFormatter

#XML_FILE = 'MonthYieldCurve.txt'
#XML_FILE = 'DailyTreasuryYieldCurveRateData.xml'
XML_FILE = 'From_Site.xml'
CSV_FILE = 'out.csv'
# 2019 data
# URL = 'https://data.treasury.gov/feed.svc/DailyTreasuryYieldCurveRateData?$filter=year(NEW_DATE)%20eq%202019'
# 2020 data
URL = 'https://data.treasury.gov/feed.svc/DailyTreasuryYieldCurveRateData?$filter=year(NEW_DATE)%20eq%202020'
#URL = 'https://data.treasury.gov/feed.svc/DailyTreasuryYieldCurveRateData?$filter=month(NEW_DATE)%20eq%204%20and%20year(NEW_DATE)%20eq%202019'
headers = [
    'DATE',
    '1MONTH',
    '2MONTH',
    '3MONTH',
    '6MONTH',
    '1YEAR',
    '2YEAR',
    '3YEAR',
    '5YEAR',
    '7YEAR',
    '10YEAR',
    '20YEAR',
    '30YEAR',
]
maturities = headers[1:] # i.e. everything except 'Date'

def debug(s):
    if options.debug:
        print s

def parse_options():
    """ Leverage the argparse module to pass in command line arguments. A brief
    description of each supported parameter can be viewed by using the -h option.
    """
    global options
    parser = ArgumentParser(formatter_class=RawTextHelpFormatter)
    parser.add_argument('--interval', type=int, help='The number of days to calculate the average', default=1)
    parser.add_argument('--legend', default=False)
    parser.add_argument('--url',type=str, default=URL)
    parser.add_argument('--csv', default=False)
    parser.add_argument('--debug', default=False)
    options = parser.parse_args()
    options.debug = options.debug in ['True', 'true', True]

def get_raw_data(url):
    # creating HTTP response object from given url
    response = requests.get(url)
    # saving the xml file
    with open(XML_FILE, 'wb') as f:
        f.write(response.content)

def strip_prefix(string):
    return string.split('}')[1]

def get_tag(node):
    return strip_prefix(node.tag)

def parse_date(datestring):
    return datestring.split('T')[0]

def parse_maturity(maturity):
    return maturity.split('_')[1] if '_' in maturity else None

def parse_yield(yield_val):
    return float(yield_val) if yield_val else None

def parse_xml(xmlfile):
    yield_curves = []
    # create element tree object
    tree = ET.parse(xmlfile)
    root = tree.getroot()

    for entry in root:
        # ignore the initial header stuff
        if get_tag(entry) != 'entry':
            continue

        # handle totally unnecessary nesting
        content = entry[6]
        properties = content[0]

        yield_curve = {}

        # add date
        date = parse_date(properties[1].text)
        yield_curve['DATE'] = date

        # parse yield curve
        for yield_entry in properties:
            tag = strip_prefix(yield_entry.tag)
            maturity = parse_maturity(tag)

            if maturity in maturities:
                yield_val = parse_yield(yield_entry.text)
                yield_curve[maturity] = float(yield_val)

        yield_curves.append(yield_curve)

    return sorted(yield_curves, key=lambda curve: curve['DATE'])

# un-used for now
def hasInversion(yield_curve):
    num_maturities = len(maturities)
    for i in range(num_maturities):
        for j in range(i, num_maturities):
            if yield_curve[maturities[i]] > yield_curve[maturities[j]] + tolerance:
                return True
    return False

def save_to_csv(yield_curves, filename):
    # writing to csv file
    with open(filename, 'w') as csvfile:
        # creating a csv dict writer object
        writer = csv.DictWriter(csvfile, fieldnames = headers)
        # writing headers (field names)
        writer.writeheader()
        # writing data rows
        writer.writerows(yield_curves)

# plot the map { "date" : [maturities] }
def plot_yield_curve_map( yield_curves ):
    width_step = 0.9/float(len(yield_curves))
    width = 0.0
    index = np.arange( len(maturities) )
    for date, curve_data in yield_curves.iteritems():
        #plt.plot(maturities, curve_data, label=date)
        plt.bar(index + width, curve_data, width_step, label=date)
        width = width + width_step
    plt.xlabel('Maturities')
    plt.ylabel('Percent')
    #plt.legend(loc='upper left')
    #plt.legend(bbox_to_anchor=(1.04,1), borderaxespad=0)
    if options.legend:
        plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.1), ncol=4, fancybox=True, shadow=True)
    plt.xticks(index + 0.45, maturities)
    plt.gca().yaxis.grid(True)
    plt.show()

def parse_result_curves_list( yield_curves_list, interval=1 ):
    ret = collections.OrderedDict()
    counter = interval;
    sum_map = Counter({});
    for entry in yield_curves_list:
        sum_map = sum_map + Counter(entry)
        counter = counter - 1
        if counter == 0:
            ret[entry['DATE']] = [(sum_map[x]/interval) for x in maturities]
            counter = interval
            sum_map = Counter({});
    return ret;

def main():
    parse_options()
    # get the raw data from treasury.gov
    get_raw_data( options.url )

    # parse xml file
    newsitems = parse_xml(XML_FILE)
    if options.csv:
        # store news items in a csv file
        save_to_csv(newsitems, CSV_FILE)

    # Convert the curve format to plot
    map_to_plot = parse_result_curves_list( newsitems, options.interval )
    plot_yield_curve_map( map_to_plot )

if __name__ == "__main__":
    main()
