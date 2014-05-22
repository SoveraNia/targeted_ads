import sys;
import json;
import time;
import subprocess;
from os.path import expanduser;
from sys import path
path.append(expanduser('~') + '/Lab_TargetedAds/src/lib/python');

from util import url2Domain;
from util import getInternalPages;
from stats import Stats;
from ad_extract import AdExtractor;

def checkArguments():
  if (len(sys.argv) < 3):
    print "Usage:"
    print "python test_detect_remarketing.py TRAINING_URLS PUBLISHER_URLS [OPTIONS]";
    print ""
    print "Determine whether web pages in TRAINING_URLS contains is a remarketing page by loading PUBLISHER_URLS."
    print "[OPTIONS] is used to pass configuration parameters to PhantomJS"
    sys.exit(0);
    
checkArguments();

stats = Stats();
  
adExtractor = AdExtractor();
    
###################################
# Experiment part
###################################

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
  
options = None;
if len(sys.argv) >= 4:
  options = sys.argv[3];
  
# Constants
build_script = "~/Lab_TargetedAds/src/bin/build_profile.py";
exec_script = "~/Lab_TargetedAds/src/bin/run_experiment.py";
num_o_page_loads = 5; # Number of page loads to build a profile
num_o_remarketing_ads = 5; # Number of remarketing ads we need to see
num_pages_per_fresh_profile = 20;

ads_empty = {}; # Set of ads detected using an empty profile
remarketing_pages = [];
non_remarketing_pages = [];

def buildProfile(url, profile):
  command = 'python ' + build_script + ' "' + url + '" ' + ' ' + profile;
  if options != None and options != '':
    command += ' ' + options;
  p = subprocess.Popen(command, shell = True, stdout = subprocess.PIPE);
  stats.increment('Num of page loads', 1);
  results = p.communicate()[0];
  return results;

def loadPublisherPage(url, profile):
  temp = url.split(';');
  command = 'python ' + exec_script + ' "' + url + '" 1 ' + profile;
  if options != None and options != '':
    command += ' identify_ads=1,' + options;
  else:
    command += ' identify_ads=1';
  p = subprocess.Popen(command, shell = True, stdout = subprocess.PIPE);
  stats.increment('Num of page loads', len(temp));
  results = p.communicate()[0];
  return results;

def removeProfile(temp_cookie_file):
  command = "rm " + temp_cookie_file;
  p = subprocess.Popen(command, shell = True);
  p.wait();
  sys.stderr.write("Cookie removed: " + temp_cookie_file + '\n'); 

# Load publisher pages using an empty profile, record ads detected
def testEmptyProfile():
  num_of_profiles = len(publisher_urls) / num_pages_per_fresh_profile;
  if len(publisher_urls) % num_pages_per_fresh_profile != 0:
    num_of_profiles += 1
  for i in range(num_of_profiles):
    pages_to_load = publisher_urls[10 * i:10 * i + 10];
    result = loadPublisherPage(';'.join(pages_to_load), 'NONE');
    result = result.split('\n');
    for j in range(len(result)):
      line = result[j].split('\t');
      if line[0] == '<AD>' and len(line) >= 3:
        stats.increment("Ads detected", 1);
        landing_url = 'NONE';
        # If the scraper failed, detect redirection
        if line[1] != 'NONE':
          landing_url = adExtractor.getLandingUrl(line[1]).lower();
        else:
          landing_url = adExtractor.getLandingUrl(line[2]).lower();
        print landing_url;
        if landing_url != 'NONE':
          stats.increment("Landing url extracted", 1);
          landing_domain = url2Domain(landing_url);
          ad_url = line[2];
          if landing_domain in ads_empty:
            ads_empty[landing_domain] += 1;
          else:
            ads_empty[landing_domain] = 1;
        else:
          stats.increment("Ad missed", 1);
          
#######################################
# TEST_1 one parse
#######################################
def processOneUrl(url):
  domain = url2Domain(url);
  bottom_line = 0;
  if domain in ads_empty:
    bottom_line = ads_empty[domain];
  bottom_line += 10; # 5 more ads than using an empty profile
  count = 0;
  num_of_profiles = len(publisher_urls) / num_pages_per_fresh_profile;
  if len(publisher_urls) % num_pages_per_fresh_profile != 0:
    num_of_profiles += 1
  # Build all profiles
  urls_for_profile = [url];
  urls_for_profile += getInternalPages(url, 4);
  for i in range(num_of_profiles):
    cur_profile = url.replace('/','').replace(':','') + '_' + str(i) + '.tmp.profile';
    for j in range(len(urls_for_profile)):    
      result = buildProfile(urls_for_profile[j], cur_profile);
      result = result.split('\n');
      # Eliminate pages during profile generation
      for j in range(len(result)):
        line = result[j].split('\t');
        if line[0] == '<MSG><RESULT>' and len(line) >= 2:
          if line[1] == 'Remarketing script detected':
            remarketing_pages.append(url);
            for k in range(0, i + 1):
              rm_profile = url.replace('/','').replace(':','') + '_' + str(k) + '.tmp.profile';
              removeProfile(rm_profile);
            return;
  
  # Second pass, build profle for next load and load pages
  for i in range(num_of_profiles):
    cur_profile = url.replace('/','').replace(':','') + '_' + str(i) + '.tmp.profile';    
    pages_to_load = publisher_urls[10 * i:10 * i + 10];
    result = loadPublisherPage(';'.join(pages_to_load), cur_profile);
    result = result.split('\n');
    for j in range(len(result)):
      line = result[j].split('\t');
      if line[0] == '<AD>' and len(line) >= 3:
        stats.increment("Ads detected", 1);
        landing_url = 'NONE';
        # If the scraper failed, detect redirection
        if line[1] != 'NONE':
          landing_url = adExtractor.getLandingUrl(line[1]);
        else:
          landing_url = adExtractor.getLandingUrl(line[2]);
        if landing_url != 'NONE':
          stats.increment("Landing url extracted", 1);
          landing_domain = url2Domain(landing_url);
          print landing_url;
          if landing_domain == domain:
            count += 1;
          # If we've seen too many remarketing ads already
          if count >= bottom_line:
            remarketing_pages.append(url);
            # Remove remaining profiles
            for k in range(i, num_of_profiles):
              rm_profile = url.replace('/','').replace(':','') + '_' + str(k) + '.tmp.profile';
              removeProfile(rm_profile);
            return;
        else:
          stats.increment("Ad missed", 1);
    removeProfile(cur_profile);
  non_remarketing_pages.append(url);

def test_1():
  print "===== Testing on Empty Profile ====="
  testEmptyProfile();
  # print ads_empty;
  for i in range(len(training_urls)):
    print "===== Testing on " + training_urls[i] + " ====="
    processOneUrl(training_urls[i]);
  print "===== Remarketing Pages ====="
  for i in range(len(remarketing_pages)):
    print remarketing_pages[i];
  print "===== Non-Remarketing Pages ====="
  for i in range(len(non_remarketing_pages)):
    print non_remarketing_pages[i];

#######################################
# TEST_2 iterative
#######################################

def oneParse():  
  pages_to_be_moved = [];
  
  num_of_profiles = len(publisher_urls) / num_pages_per_fresh_profile;
  if len(publisher_urls) % num_pages_per_fresh_profile != 0:
    num_of_profiles += 1
  # Build all profiles
  for i in range(num_of_profiles):
    cur_profile = 'profile_' + str(i) + '.tmp.profile';
    for j in range(len(non_remarketing_pages)):    
      result = buildProfile(non_remarketing_pages[j], cur_profile);
      result = result.split('\n');
      # Eliminate pages during profile generation
      for k in range(len(result)):
        line = result[k].split('\t');
        if line[0] == '<MSG><RESULT>' and len(line) >= 2:
          if line[1] == 'Remarketing script detected' and not non_remarketing_pages[j] in pages_to_be_moved:
            pages_to_be_moved.append(non_remarketing_pages[j]);
  
  # Load publisher pages
  ads_profile = {};
  for i in range(num_of_profiles):
    cur_profile = 'profile_' + str(i) + '.tmp.profile';
    pages_to_load = publisher_urls[i*num_pages_per_fresh_profile:(i+1)*num_pages_per_fresh_profile]
    result = loadPublisherPage(';'.join(pages_to_load), cur_profile);
    result = result.split('\n');
    for j in range(len(result)):
      line = result[j].split('\t');
      if line[0] == '<AD>' and len(line) >= 3:
        stats.increment("Ads detected", 1);
        landing_url = 'NONE';
        # If the scraper failed, detect redirection
        if line[1] != 'NONE':
          landing_url = adExtractor.getLandingUrl(line[1]).lower();
        else:
          landing_url = adExtractor.getLandingUrl(line[2]).lower();
        print landing_url.encode('utf-8');
        if landing_url != 'NONE':
          stats.increment("Landing url extracted", 1);
          landing_domain = url2Domain(landing_url);
          ad_url = line[2];
          if landing_domain in ads_profile:
            ads_profile[landing_domain] += 1;
          else:
            ads_profile[landing_domain] = 1;
        else:
          stats.increment("Ad missed", 1);
  
  # Locate pages containing remarketing scripts
  for i in range(len(non_remarketing_pages)):
    domain = url2Domain(non_remarketing_pages[i]);
    count_empty = 0;
    if domain in ads_empty:
      count_empty = ads_empty[domain];
    count_profile = 0;
    if domain in ads_profile:
      count_profile = ads_profile[domain];
    if count_profile - count_empty >= 5 and not non_remarketing_pages[i] in pages_to_be_moved:
      pages_to_be_moved.append(non_remarketing_pages[i]);
    # In case there's redirection
    redirect_url = adExtractor.detectRedirection(non_remarketing_pages[i]).lower();
    if redirect_url != non_remarketing_pages[i]:
      redirect_domain = url2Domain(redirect_url);
      count_empty = 0;
      if redirect_domain in ads_empty:
        count_empty = ads_empty[redirect_domain];
      count_profile = 0;
      if redirect_domain in ads_profile:
        count_profile = ads_profile[redirect_domain];
      if count_profile - count_empty >= 1 and not non_remarketing_pages[i] in pages_to_be_moved:
        pages_to_be_moved.append(non_remarketing_pages[i]);
      
  # Move pages
  for i in range(len(pages_to_be_moved)):
    remarketing_pages.append(pages_to_be_moved[i]);
    try:
      non_remarketing_pages.remove(pages_to_be_moved[i]);
    except:
      do_nothing = 1;
  
  # Remove profile
  for i in range(num_of_profiles):
    cur_profile = 'profile_' + str(i) + '.tmp.profile';
    removeProfile(cur_profile);
  return;

def test_2():
  print "===== Testing on Empty Profile ====="
  testEmptyProfile();
  # Initiate pages
  for i in range(len(training_urls)):
    non_remarketing_pages.append(training_urls[i]);
  prev_count = 0;
  max_num_iteration = 5;
  for i in range(max_num_iteration):
    print '===== Round ' + str(i) + ' =====';
    prev_count = len(non_remarketing_pages);
    oneParse();
    cur_count = len(non_remarketing_pages);
    print 'Number of Remarketing Pages Detected: ' + str(len(remarketing_pages));
    for j in range(len(remarketing_pages)):
      print remarketing_pages[j];
    if cur_count == prev_count:
      break;
  print '===== Remarketing Pages ====='
  for i in range(len(remarketing_pages)):
    print remarketing_pages[i];
  print '===== Non-remarketing Pages ====='
  for i in range(len(non_remarketing_pages)):
    print non_remarketing_pages[i];
  return;

def main():
  test_2();
  adExtractor.stats.output();
  stats.output();

if __name__ == "__main__":
  main();
  
