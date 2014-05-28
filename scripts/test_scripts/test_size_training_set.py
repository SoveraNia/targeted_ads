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
from util import runCommand;
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

num_pages_per_fresh_profile = 20;

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
  
def getGoogleAdPref(cookies_file):
  command = '~/Lab_TargetedAds/phantomjs/phantomjs--linux-x86_64/bin/phantomjs --cookies-file=' + cookies_file + ' ~/Lab_TargetedAds/src/bin/google_ad_pref.js'
  results = runCommand(command);
  for i in range(len(results)):
    if '<AD_PREF>' in results[i]:
      print results[i]

def identifyAd(input, profile_name, url_list = []):
  if not profile_name in ads:
    ads[profile_name] = {'original':{},'mapped':{},'remarketing':{},'domains':{},'un-categorized':{}};
  line = input.split('\t');
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
      # Record domains
      if landing_domain in ads[profile_name]['domains']:
        ads[profile_name]['domains'][landing_domain] += 1;
      else:
        ads[profile_name]['domains'][landing_domain] = 1;
      # Record remarketing ads
      for k in range(len(url_list)):
        if landing_domain == url2Domain(url_list[k]):
          if landing_domain in ads[profile_name]['remarketing']:
            ads[profile_name]['remarketing'][landing_domain] += 1;
          else:
            ads[profile_name]['remarketing'][landing_domain] = 1;
          stats.increment("Remarketing ad detected", 1);
          break;
      # Detect category
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
        if landing_domain in ads[profile_name]['un-categorized']:
          ads[profile_name]['un-categorized'][landing_domain] += 1;
        else:
          ads[profile_name]['un-categorized'][landing_domain] = 1;
    else:
      stats.increment("Ad missed", 1);
    try: # Encode errors
      print 'Ad detected\t'+landing_url+'\t'+category+'\t'+mapped_category+'\t'+source+'\t'+url+'\t'+text_ad;
    except:
      do_nothing = 1;
      
def testEmptyProfile():
  num_profiles = len(publisher_urls) / num_pages_per_fresh_profile;
  if len(publisher_urls) % num_pages_per_fresh_profile != 0:
    num_profiles += 1
  print "===== Testing on Empty Profile 1 ====="
  ads['EMPTY_PROFILE_1'] = {'original':{},'mapped':{},'remarketing':{},'domains':{},'un-categorized':{}};
  for i in range(num_profiles):
    pages_to_load = ';'.join(publisher_urls[num_pages_per_fresh_profile * i:num_pages_per_fresh_profile * (i + 1)])
    result = loadPublisherPage(pages_to_load, 'NONE');
    result = result.split('\n');
    for j in range(len(result)):
      identifyAd(result[j], 'EMPTY_PROFILE_1');
  printResult('EMPTY_PROFILE_1');
  return;
  print "===== Testing on Empty Profile 2 ====="
  ads['EMPTY_PROFILE_2'] = {'original':{},'mapped':{},'remarketing':{},'domains':{},'un-categorized':{}};
  for i in range(num_profiles):
    pages_to_load = ';'.join(publisher_urls[num_pages_per_fresh_profile * i:num_pages_per_fresh_profile * (i + 1)])
    result = loadPublisherPage(pages_to_load, 'NONE');
    result = result.split('\n');
    for j in range(len(result)):
      identifyAd(result[j], 'EMPTY_PROFILE_2');
  printResult('EMPTY_PROFILE_2');

def processOneProfile(url_list, name):
  print "----- Training Set for Profile " + name + " -----";
  for j in range(len(url_list)):
    print url_list[j].encode('utf-8');
  ads[name] = {'original':{},'mapped':{},'remarketing':{},'domains':{},'un-categorized':{}};
  num_profiles = len(publisher_urls) / num_pages_per_fresh_profile;
  if len(publisher_urls) % num_pages_per_fresh_profile != 0:
    num_profiles += 1
  # Build profiles for all publisher pages
  for i in range(num_profiles):
    cur_profile = name + '_' + str(i) + '.tmp.profile';
    result = buildProfile(';'.join(url_list), cur_profile);
    print "----- Google Interest for profile " + cur_profile + " -----";
    getGoogleAdPref(cur_profile);
  # Load publisher pages
  print "----- Ad detection for profile " + name + " -----";
  for i in range(num_profiles):
    cur_profile = name + '_' + str(i) + '.tmp.profile';
    print "----- Ads List for profile " + cur_profile + " -----";
    pages_to_load = publisher_urls[num_pages_per_fresh_profile * i:num_pages_per_fresh_profile * (i + 1)]
    for j in range(len(pages_to_load)):
      result = loadPublisherPage(pages_to_load[j], cur_profile);
      result = result.split('\n');
      for k in range(len(result)):
        identifyAd(result[k], name, url_list);
    print "----- Google Interest for profile " + cur_profile + " After Publisher Page Loads -----";
    getGoogleAdPref(cur_profile);
    #result = loadPublisherPage(';'.join(pages_to_load), cur_profile);
    #result = result.split('\n');
    #for j in range(len(result)):
    #  identifyAd(result[j], name, url_list);     
  # Remove profiles
  for i in range(num_profiles):
    cur_profile = name + '_' + str(i) + '.tmp.profile';
    removeProfile(cur_profile);

def generateDataset(size):
  ret = [];
  for i in range(len(training_urls)):
    ret.append(training_urls[i]);  
  random.shuffle(ret);
  return ret[:size];

def printResult(key):
  if not key in ads:
    print "ERROR";
    return;
  print "===== Original Result for Profile " + key + " ====="
  for cat in sorted(ads[key]['original']):
    print cat.replace(':', '\t', 1) + '\t' + str(ads[key]['original'][cat]);
  print "===== Mapped Result for Profile " + key + " ====="
  for cat in sorted(ads[key]['mapped']):
    print cat + '\t' + str(ads[key]['mapped'][cat]);
  print "===== Un-categorized Domains for Profile " + key + " ====="
  for dom in sorted(ads[key]['un-categorized']):
    print dom.encode('utf-8') + '\t' + str(ads[key]['un-categorized'][dom]);
  print "===== Domain Result for Profile " + key + " ====="
  for dom in sorted(ads[key]['domains']):
    print dom.encode('utf-8') + '\t' + str(ads[key]['domains'][dom]);
  print "===== Remarketing Ads for Profile " + key + " ====="
  for domain in sorted(ads[key]['remarketing']):
    print domain.encode('utf-8') + '\t' + str(ads[key]['remarketing'][domain]);

def main():
  testEmptyProfile();
  for i in range(len(profile_sizes)):
    print "===== Testing on Profile "+str(i)+" with size "+str(profile_sizes[i])+" =====";
    url_list = generateDataset(profile_sizes[i]);
    name = str(i) + '-' + str(len(url_list));
    processOneProfile(url_list, name);
    printResult(name);
  adExtractor.stats.output();
  stats.output();
  adExtractor.updateDb();
  
def test():
  getGoogleAdPref("test.profile")
  result = buildProfile(';'.join(training_urls), "test.profile");
  getGoogleAdPref("test.profile")

if __name__ == "__main__":
  main();
  # test();
