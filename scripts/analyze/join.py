#!/bin/python

import sys;
import math;
import glob;

def checkArguments():
  if (len(sys.argv) < 2):
    print "Usage:";
    print "python join.py DATA_FILES";
    print "";
    print "Join multiple files, first columns as keys. Columns separated by \\t"
    sys.exit(0);

files = glob.glob(sys.argv[1]);
files.sort();

if len(sys.argv) == 3:
  files = [sys.argv[1],sys.argv[2]];
  files.sort();

dict = {};

for i in range(len(files)):
  f = open(files[i]);
  lines = f.readlines();
  f.close();
  
  for j in range(len(lines)):
    lines[j] = lines[j].replace('\n','').split('\t');
    if len(lines[j]) < 2:
      continue;
    key = lines[j][0];
    value = lines[j][1];
    if not key in dict:
      dict[key] = [];
    for k in range(len(dict[key]), i):
      dict[key].append('0');
    dict[key].append(value);

print '<FILES>\t','\t'.join(files);
for key in dict:
  for j in range(len(dict[key]), len(files)):
    dict[key].append('0');
  print key,'\t','\t'.join(dict[key]);