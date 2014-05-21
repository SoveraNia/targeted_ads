import sys;
import json;
import time;
import subprocess;

def checkArguments():
  if (len(sys.argv) < 2):
    print "Usage:"
    print "python extract_data.py FILE";
    print ""
    print "Transform data from FILE into JSON format. Key is stored in the first column";
    sys.exit(0);

checkArguments();

f = open(sys.argv[1]);
lines = f.readlines();
f.close();

data = {};

for i in range(len(lines)):
  lines[i] = lines[i].replace('\n','').split('\t');
  key = lines[i][0];
  if not key in data:
    data[key] = [];
  for j in range(1,len(lines[i])):
    if not lines[i][j] in data[key] and lines[i][j] != '':
      data[key].append(lines[i][j]);
      
print json.dumps(data);