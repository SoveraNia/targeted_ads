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
  if (len(sys.argv) < 4):
    print "Usage:"
    print "python test_size_training_sets.py TRAINING_URLS PUBLISHER_URLS COUNTS [OPTIONS]";
    print ""
    print "Determine whether web pages in TRAINING_URLS contains is a remarketing page by loading PUBLISHER_URLS."
    print "COUNTS are a list of integers split by ','"
    print "[OPTIONS] is used to pass configuration parameters to PhantomJS"
    sys.exit(0);
    
checkArguments();

stats = Stats();
  
adExtractor = AdExtractor();

# Read url files
f = open(sys.argv[1]);
training_urls = f.readlines();
f.close();
for i in range(len(training_urls)):
  training_urls[i] = training_urls[i].replace('\n','');
  
f = open(sys.argv[2]);
publisher_urls = f.readlines();
f.close();
for i in range(len(publisher_urls)):
  publisher_urls[i] = publisher_urls[i].replace('\n','');

profile_sizes = sys.argv[3].split(',')
for i in range(len(profile_sizes)):
  profile_sizes[i] = int(profile_sizes[i]);

options = None;
if len(sys.argv) >= 5:
  options = sys.argv[4];
  
# Constants
build_script = "~/Lab_TargetedAds/src/bin/build_profile.py";
exec_script = "~/Lab_TargetedAds/src/bin/run_experiment.py";

ads = {};

def buildProfile(url, profile):
  command = 'python ' + build_script + ' "' + url + '" ' + ' ' + profile;
  if options != None and options != '':
    command += ' ' + options;
  p = subprocess.Popen(command, shell = True, stdout = subprocess.PIPE);
  stats.increment('Num of page loads', 1);
  results = p.communicate()[0];
  return results;

def loadPublisherPage(url, profile):
  command = 'python ' + exec_script + ' "' + url + '" 1 ' + profile;
  if options != None and options != '':
    command += ' identify_ads=1,' + options;
  else:
    command += ' identify_ads=1';
  p = subprocess.Popen(command, shell = True, stdout = subprocess.PIPE);
  stats.increment('Num of page loads', 1);
  results = p.communicate()[0];
  return results;

def removeProfile(temp_cookie_file):
  command = "rm " + temp_cookie_file;
  p = subprocess.Popen(command, shell = True);
  p.wait();
  sys.stderr.write("Cookie removed: " + temp_cookie_file + '\n'); 

def identifyAd(input, profile_name):
  if not profile_name in ads:
    ads[profile_name] = {};
  line = input.split('\t');
  if line[0] == '<AD>' and len(line) >= 3:
    stats.increment("Ads detected", 1);
    landing_url = 'NONE';
    source = 'NONE';
    category = 'NONE';
    url = line[2];
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
        # Record categories seen
        for k in range(len(landing_category['category'])):
          cat = source + ':' + landing_category['category'][k];
          if cat in ads[profile_name]:
            ads[profile_name][cat] += 1;
          else:
            ads[profile_name][cat] = 1;
    else:
      stats.increment("Ad missed", 1);
    print 'Ad detected','\t',landing_url,'\t',category,'\t',source,'\t',url;

def testEmptyProfile():
  ads['EMPTY_PROFILE'] = {};
  for i in range(len(publisher_urls)):
    result = loadPublisherPage(publisher_urls[i], 'NONE');
    result = result.split('\n');
    for j in range(len(result)):
      identifyAd(result[j], 'EMPTY_PROFILE');

def processOneProfile(url_list, name):
  ads[name] = {};
  # Build profiles for all publisher pages
  for i in range(len(publisher_urls)):
    cur_profile = name + '_' + str(i) + '.tmp.profile';
    for j in range(len(url_list)):
      result = buildProfile(url_list[j], cur_profile);
  # Load publisher pages
  for i in range(len(publisher_urls)):
    cur_profile = name + '_' + str(i) + '.tmp.profile';
    result = loadPublisherPage(publisher_urls[i], cur_profile);
    result = result.split('\n');
    for j in range(len(result)):
      identifyAd(result[j], name);
      
  # Remove profiles
  for i in range(len(publisher_urls)):
    cur_profile = name + '_' + str(i) + '.tmp.profile';
    removeProfile(cur_profile);

def generateDataset(size):
  ret = [];
  for i in range(len(training_urls)):
    ret.append(training_urls[i]);  
  random.shuffle(ret);
  return ret[:size];

def main():
  print "===== Testing on Empty Profile ====="
  testEmptyProfile();
  for i in range(len(profile_sizes)):
    print "===== Testing on Profile ",i," with size ",profile_sizes[i]," =====";
    url_list = generateDataset(profile_sizes[i]);
    # print url_list;
    name = str(i) + '-' + str(len(url_list));
    processOneProfile(url_list, name);
  for key in ads:
    print "===== Result for Profile ",key," ====="
    for cat in sorted(ads[key]):
      print cat.replace(':','\t',1),'\t',ads[key][cat];
  adExtractor.stats.output();
  stats.output();

if __name__ == "__main__":
  main();