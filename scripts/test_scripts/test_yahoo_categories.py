import sys;
import json;
import time;
import random;
import subprocess;
from os.path import expanduser;
from sys import path
path.append(expanduser('~') + '/Lab_TargetedAds/src/lib/python');

from util import url2Domain;
from stats import Stats;
from ad_extract import AdExtractor;

def checkArguments():
  if (len(sys.argv) < 2):
    print "Usage:"
    print "python test_yahoo_categories.py URLS [OPTIONS]";
    print ""
    print "Load urls and record Yahoo's categorization of them."
    print "[OPTIONS] is used to pass configuration parameters to PhantomJS"
    sys.exit(0);
    
checkArguments();
stats = Stats();
adExtractor = AdExtractor();

f = open(sys.argv[1]);
urls = f.readlines();
f.close();

categories = [];

for i in range(len(urls)):
  urls[i] = urls[i].replace('\n','');
  result = adExtractor.queryYahoo(urls[i]);
  try:
    for i in range(len(result['category'])):
      cat = result['category'][i]['category'];
      if not cat in categories:
        categories.append(cat);
  except:
    stats.increment('Category detection failed', 1);
    
categories.sort();
for i in range(len(categories)):
  print categories[i];