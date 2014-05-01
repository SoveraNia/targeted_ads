#!/bin/python

import glob;
import json;
import sys;
import subprocess;

exec_script = "~/Lab_TargetedAds/src/bin/run_experiment.py";

output_dir = "/home/soverania/Lab_TargetedAds/tests/030714/results"

temp_cookie_file = "~/temp.profile";

def loadPage(url, count, cookie_file, options):
  if (cookie_file == None):
    command = "python " + exec_script + " " + url + " " + str(count) + " NONE";
  else:
    command = "python " + exec_script + " " + url + " " + str(count) + " " + cookie_file;
  if options != None and options != "":
    command += ' ' + options;
  p = subprocess.Popen(command, shell = True, stdout = subprocess.PIPE);
  results = p.communicate()[0];
  lines = results.split('\n');
  ret = [];
  for i in range(len(lines)):
    if (lines[i] != ""):
      ret.append(lines[i]);
  return ret;

def writeToFile(url, category, lines, iterationNum, options):
  filename = output_dir + '/' + url.replace('/', '@').replace(':', '-') + '_' + category + '_' + str(iterationNum) + '_' + options.replace('=','-') + '.txt';
  print "Writing " + filename;
  f = open(filename, 'w');
  for i in range(len(lines)):
    f.write(lines[i] + '\n');
  f.close();

def processOneUrl(url, cookie_files, iterationNum, options):
  result = loadPage(url, 1, None, options);
  writeToFile(url, "None", result, iterationNum, options);
  for i in range(len(cookie_files)):
    temp = cookie_files[i].split('/');
    category = temp[len(temp) - 1].split('_')[0];
    result = loadPage(url, 1, cookie_files[i], options);
    writeToFile(url, category, result, iterationNum, options);
  return result;

def main():
  if (len(sys.argv) < 4):
    print ("Usage:")
    print ("python generate_dataset.py URL_FILE COOKIE_FILES COUNT [OPTIONS]");
    sys.exit(0);
  
  options = None;
  if len(sys.argv) == 5:
    options = sys.argv[4];
  
  cookie_files = glob.glob(sys.argv[2]);
  
  f = open(sys.argv[1]);
  urls = f.readlines();
  f.close();
  
  count = int(sys.argv[3]);
  
  for j in range(count):
    for i in range(len(urls)):
      urls[i] = urls[i].replace('\n', '');
      processOneUrl(urls[i], cookie_files, j, options);

if __name__ == "__main__":
  main();

