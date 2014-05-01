#!/bin/python

import sys;
import json;

f = open(sys.argv[1]);
data = json.load(f);
f.close();

dict = {};

for category in data:
  cat_data = data[category];
  for tracker in cat_data:
    if not tracker in dict:
      dict[tracker] = {};
      dict[tracker]['num_pages'] = len(cat_data[tracker]);
      dict[tracker]['num_categories'] = 1;
    else:
      dict[tracker]['num_pages'] += len(cat_data[tracker]);
      dict[tracker]['num_categories'] += 1;

for key in dict:
  print key,'\t',dict[key]['num_categories'],'\t',dict[key]['num_pages'];