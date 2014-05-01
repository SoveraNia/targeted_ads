#!/bin/python

import glob;
import json;
import sys;
import subprocess;

exec_script = "~/Lab_TargetedAds/src/bin/run_experiment.py";

output_dir = "/home/ubuntu/Tests/021814/results"

def loadPage(url, count, options):
  command = "python " + exec_script + " " + url + " " + str(count) + " NONE";
  if options != None and options != "":
    command += " " + options;
  p = subprocess.Popen(command, shell = True, stdout = subprocess.PIPE);
  results = p.communicate()[0];
  lines = results.split('\n');
  ret = [];
  error = True;
  for i in range(len(lines)):
    if (lines[i] != ""):
      ret.append(lines[i]);
  return ret;

def writeToFile(url, category, lines):
  filename = output_dir + '/' + category + '_' + url.replace('/', '$').replace(':', '-') + '.txt';
  print "Writing " + filename;
  f = open(filename, 'w');
  f.write(url + '\n');
  for i in range(len(lines)):
    f.write(lines[i] + '\n');
  f.close();

def processOneUrl(url, category, count, options):
  result = [];
  if count > 10:
    # Load a web page 10 times and see what happens
    initial_result = loadPage(url, 10, options);
    skip = True;
    for i in range(len(initial_result)):
      if (initial_result[i] != "" and initial_result[i] != "<AD>\t[]" and initial_result[i] != "ERROR"):
        skip = False;
    # If works, then load more
    result = initial_result;
    if skip == False:
      result += loadPage(url, count - 10, options);
    writeToFile(url, category, result);
  else:
    result = loadPage(url, count, options);
    writeToFile(url, category, result);
  return result;

def main():
  if (len(sys.argv) < 3):
    print ("Usage:")
    print ("python generate_dataset.py URL_FILES LOADS_PER_URL [OPTIONS]");
    sys.exit(0);

  url_files = glob.glob(sys.argv[1]);
  count = int(sys.argv[2]);
  options = None;
  if len(sys.argv) >= 4:
    options = sys.argv[3];
  for i in range(len(url_files)):
    url_file = url_files[i];
    temp = url_file.split('/');
    category = temp[len(temp) - 1].split('_100')[0];
    print category;
    f = open(url_file);
    lines = f.readlines();
    f.close();
    for j in range(100):
      lines[j] = lines[j].replace('\n', '');
      processOneUrl(lines[j], category, count, options);

if __name__ == "__main__":
  main();

