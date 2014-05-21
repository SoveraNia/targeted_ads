import sys;
import json;
import time;
import random;
import subprocess;
from os.path import expanduser;
from sys import path
path.append(expanduser('~') + '/Lab_TargetedAds/src/lib/python');

from util import url2Domain;
from util import getInternalPages;
from stats import Stats;
from ad_extract import AdExtractor;

def checkArguments():
  if (len(sys.argv) < 2):
    print "Usage:"
    print "python update_results.py AD_FILE";
    print ""
    print "Redo ad extraction on a list of ads detected";
    sys.exit(0);

checkArguments();

stats = Stats();
  
adExtractor = AdExtractor();

ads = {};

f = open(sys.argv[1]);
lines = f.readlines();
f.close()

def identifyAd(input, profile_name):
  if not profile_name in ads:
    ads[profile_name] = {'original':{},'mapped':{}};
  line = input.split('\t');
  # <AD>  LANDING_URL  AD_URL  TEXT_AD
  if line[0] == '<AD>' and len(line) >= 3:
    stats.increment("Ads detected", 1);
    landing_url = 'NONE';
    source = 'NONE';
    category = 'NONE';
    mapped_category = 'NONE';
    text_ad = 'VISUAL_AD';
    url = line[2];
    if len(line) >= 4 and line[3] == 'TEXT_AD':
      # TODO: Maybe we should treat them differently since there might be lots of duplicates here
      text_ad = 'TEXT_AD';
      stats.increment("Text ads detected", 1);
    # If the scraper failed, detect redirection
    if line[1] != 'NONE':
      landing_url = adExtractor.getLandingUrl(line[1]);
    else:
      landing_url = adExtractor.getLandingUrl(line[2]);
    if landing_url != 'NONE':
      stats.increment("Landing url extracted", 1);
      landing_domain = url2Domain(landing_url);
      ad_url = line[2];
      landing_category = adExtractor.getPageCategory(landing_url);
      if landing_category != {}:
        source = landing_category['source'];
        category = ';'.join(landing_category['category']);
        mapped_category = ';'.join(landing_category['mapped_category']);
        # Record categories seen
        for k in range(len(landing_category['category'])):
          cat = source + ':' + landing_category['category'][k];
          if cat in ads[profile_name]['original']:
            ads[profile_name]['original'][cat] += 1;
          else:
            ads[profile_name]['original'][cat] = 1;
        # Record mapped categories seen
        for k in range(len(landing_category['mapped_category'])):
          cat = landing_category['mapped_category'][k];
          if cat in ads[profile_name]['mapped']:
            ads[profile_name]['mapped'][cat] += 1;
          else:
            ads[profile_name]['mapped'][cat] = 1;
    else:
      stats.increment("Ad missed", 1);
    print 'Ad detected','\t',landing_url,'\t',category,'\t',mapped_category,'\t',source,'\t',url,'\t',text_ad;


for i in range(len(lines)):
  lines[i] = lines[i].replace('\n','').split('\t');
  if len(lines[i]) >= 7:
    temp = '<AD>\t' + lines[i][1] + '\t' + lines[i][5] + '\t' + lines[i][6];
    profile_name = sys.argv[1];
    if lines[i][1] != 'NONE' and adExtractor.getLandingUrl(lines[i][1]) == lines[i][1] and lines[i][2].strip() != 'unknown' and lines[i][2].strip() != 'NONE' and lines[i][2] != '' and lines[i][3].strip() != 'NONE' and lines[i][3] != '' and lines[i][4].strip() != 'NONE' and lines[i][4] != '':
      print '\t'.join(lines[i]);
      if not profile_name in ads:
        ads[profile_name] = {'original':{},'mapped':{}};
      category = lines[i][2].split(';')
      mapped_category =  lines[i][3].split(';')
      source = lines[i][4];
      # Record categories seen
      for k in range(len(category)):
        cat = source.strip() + ':' + category[k].strip();
        if cat in ads[profile_name]['original']:
          ads[profile_name]['original'][cat] += 1;
        else:
          ads[profile_name]['original'][cat] = 1;
      # Record mapped categories seen
      for k in range(len(mapped_category)):
        cat = mapped_category[k].strip();
        if cat == '':
          print "WTF\t" + '\t'.join(lines[i]);
        if cat in ads[profile_name]['mapped']:
          ads[profile_name]['mapped'][cat] += 1;
        else:
          ads[profile_name]['mapped'][cat] = 1;
    else:
      identifyAd(temp, sys.argv[1]);
for key in ads:
  print "===== Original Result for Profile ",key," ====="
  for cat in sorted(ads[key]['original']):
    print cat.replace(':','\t',1),'\t',ads[key]['original'][cat];
  print "===== Mapped Result for Profile ",key," ====="
  for cat in sorted(ads[key]['mapped']):
    print cat,'\t',ads[key]['mapped'][cat];
adExtractor.stats.output();
stats.output();