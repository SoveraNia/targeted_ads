#!/bin/python

import sys;
import math;
import glob;

def checkArguments():
  if (len(sys.argv) < 2):
    print "Usage:";
    print "python merge.py DATA_FILES";
    print "";
    print "Merge multiple files, first columns as keys. Columns separated by \\t"
    sys.exit(0);

files = glob.glob(sys.argv[1]);

keys = [];
dict = {};

log_files = glob.glob(sys.argv[1]);
for i in range(len(log_files)):
  dict[log_files[i]] = {};
  
for i in range(len(log_files)):
  f = open(log_files[i]);
  lines = f.readlines();
  f.close();
  for j in range(len(lines)):
    lines[j] = lines[j].replace('\n', '').split('\t');
    if len(lines[j]) >= 2:
      domain = lines[j][0];
      if not domain in keys:
        keys.append(domain);
      for k in dict:
        if not domain in dict[k]:
          dict[k][domain] = 0;
      dict[log_files[i]][domain] = int(lines[j][1]);
      
keys.sort();
output = [''];
for j in range(len(log_files)):
  output.append(log_files[j]);
print '\t'.join(output);  

for i in range(len(keys)):
  output = [keys[i]];
  for j in range(len(log_files)):
    output.append(str(dict[log_files[j]][keys[i]]));
  print '\t'.join(output);