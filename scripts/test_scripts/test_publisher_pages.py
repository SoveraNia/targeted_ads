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
  if (len(sys.argv) < 3):
    print "Usage:"
    print "python test_publisher_page.py PUBLISHER_URLS COUNT [OPTIONS]";
    print ""
    print "Load publisher urls and see what ads are being shown on them."
    print "[OPTIONS] is used to pass configuration parameters to PhantomJS"
    sys.exit(0);
    
checkArguments();
stats = Stats();
adExtractor = AdExtractor();

# Read parameters
f = open(sys.argv[1]);
publisher_urls = f.readlines();
f.close();
for i in range(len(publisher_urls)):
  publisher_urls[i] = publisher_urls[i].replace('\n','');
  
count = int(sys.argv[2]);

options = None;
if len(sys.argv) >= 4:
  options = sys.argv[3];

# Constants
exec_script = "~/Lab_TargetedAds/src/bin/run_experiment.py";

def loadPublisherPage(url):
  command = 'python ' + exec_script + ' "' + url + '" ' + str(count) + ' NONE';
  if options != None and options != '':
    command += ' identify_ads=1,' + options;
  else:
    command += ' identify_ads=1';
  p = subprocess.Popen(command, shell = True, stdout = subprocess.PIPE);
  stats.increment('Num of page loads', 1);
  results = p.communicate()[0];
  return results;
    
provider_mapping = {};
    
def identifyAd(input, publisher_url):
  line = input.split('\t');
  if line[0] == '<AD>' and len(line) >= 3:
    stats.increment("Ads detected", 1);
    landing_url = 'NONE';
    source = 'NONE';
    providers = 'NONE';
    url = line[2];
    # If the scraper failed, detect redirection
    if line[1] != 'NONE':
      landing_url = adExtractor.getLandingUrl(line[1]);
    else:
      landing_url = adExtractor.getLandingUrl(line[2]);
    if landing_url != 'NONE':
      stats.increment("Landing url extracted", 1);
    else:
      stats.increment("Ad missed", 1);
    # Get providers
    provider_list = adExtractor.getAdProviders(url);
    if len(provider_list) > 0:
      providers = ';'.join(provider_list);
      for j in range(len(provider_list)):
        if provider_list[j] in provider_mapping and not publisher_url in provider_mapping[provider_list[j]]:
          provider_mapping[provider_list[j]].append(publisher_url);
        elif not provider_list[j] in provider_mapping:
          provider_mapping[provider_list[j]] = [publisher_url];
    print 'Ad detected','\t',landing_url,'\t',providers,'\t',url;

def main():
  for i in range(len(publisher_urls)):
    print "===== Testing on ",publisher_urls[i]," =====";
    result = loadPublisherPage(publisher_urls[i]);
    result = result.split('\n');
    for j in range(len(result)):
      identifyAd(result[j], publisher_urls[i]);
  print "===== Provider Mapping =====";
  for key in sorted(provider_mapping):
    provider_mapping[key].sort();
    print '----- ' + key + ' -----'
    for j in range(len(provider_mapping[key])):
      print provider_mapping[key][j];
  print "===== Provider Mapping JSON =====";
  print json.dumps(provider_mapping);
  adExtractor.stats.output();
  stats.output();

if __name__ == "__main__":
  main();