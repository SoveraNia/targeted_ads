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

def checkArguments():
  if (len(sys.argv) < 3):
    print "Usage:"
    print "python test_training_pages.py URLS COUNT [OPTIONS]";
    print ""
    print "Load urls and see what trackers are present on them and whether they contain remarketing scripts."
    print "[OPTIONS] is used to pass configuration parameters to PhantomJS"
    sys.exit(0);

checkArguments();
stats = Stats();

# Read parameters
f = open(sys.argv[1]);
urls = f.readlines();
f.close();
for i in range(len(urls)):
  urls[i] = urls[i].replace('\n','');
  
count = int(sys.argv[2]);

options = None;
if len(sys.argv) >= 4:
  options = sys.argv[3];

# Constants
exec_script = "~/Lab_TargetedAds/src/bin/run_experiment.py";

def loadPage(url):
  command = 'python ' + exec_script + ' "' + url + '" ' + str(count) + ' NONE';
  if options != None and options != '':
    command += ' log_requests=trackers,' + options;
  else:
    command += ' log_requests=trackers';
  p = subprocess.Popen(command, shell = True, stdout = subprocess.PIPE);
  stats.increment('Num of page loads', 1);
  results = p.communicate()[0];
  return results;

tracker_mapping = {};
non_remarketing_pages = [];
remarketing_pages = [];

def main():
  for i in range(len(urls)):
    print "===== Testing on ",urls[i]," =====";
    result = loadPage(urls[i]);
    result = result.split('\n');
    for j in range(len(result)):
      line = result[j].split('\t');
      if line[0] == '<TRACKER>' and len(line) >= 2:
        tracker_url = line[1];
        tracker_domain = url2Domain(tracker_url);
        if tracker_domain in tracker_mapping and not urls[i] in tracker_mapping[tracker_domain]:
          tracker_mapping[tracker_domain].append(urls[i]);
        elif not tracker_domain in tracker_mapping:
          tracker_mapping[tracker_domain] = [urls[i]];
      elif line[0] == '<REMARKETING>' and len(line) >= 2:
        if line[1] == 'Detected':
          remarketing_pages.append(urls[i]);
        elif line[1] == 'Not Detected':
          non_remarketing_pages.append(urls[i]);
  print "===== Remarketing Pages ====="
  for i in range(len(remarketing_pages)):
    print remarketing_pages[i];
  print "===== Non-Remarketing Pages ====="
  for i in range(len(non_remarketing_pages)):
    print non_remarketing_pages[i];
  print "===== Tracker Mapping =====";
  for key in sorted(tracker_mapping):
    tracker_mapping[key].sort();
    print '----- ' + key + ' -----'
    for j in range(len(tracker_mapping[key])):
      print tracker_mapping[key][j];
  print "===== Tracker Mapping JSON ====="
  print json.dumps(tracker_mapping);
  stats.output();
  
if __name__ == "__main__":
  main();