import json;
import sys;

def checkArguments():
  if (len(sys.argv) < 4):
    print "Usage:";
    print "python query_mapping.py MAPPING CATEGORY TRACKER [OUTPUT_DIR]";
    print "";
    print "Query the reverse mapping of trackers -> urls. Located all web pages under CATEGORY that contains TRACKER."
    print "If CATEGORY is set to 'ANY' then return web pages in all categories";
    print "If [OUTPUT_DIR] is set, then write to files instead of std out";
    sys.exit(0);
checkArguments();

f = open(sys.argv[1]);
data = json.load(f);
f.close();

category = sys.argv[2];

domain = sys.argv[3];

output_dir = None;
if len(sys.argv) >= 5:
  output_dir = sys.argv[4];

def writeToFile(url, category, lines):
  if output_dir != None:
    filename = output_dir + '/' + category.replace('/','-') + '_' + url.replace('/', '$').replace(':', '-') + '.txt';
    print "Writing " + filename;
    f = open(filename, 'w');
    for i in range(len(lines)):
      f.write(lines[i] + '\n');
    f.close();
  else:
    for i in range(len(lines)):
      print lines[i]

if category == 'ANY':
  for cat in data:
    if domain in data[cat]:
      if output_dir == None:
        print '=====',cat,'====='
      results = []
      for i in range(len(data[cat][domain])):
        results.append(data[cat][domain][i]);
      writeToFile(domain, cat, results);
else:
  if category in data and domain in data[category]:
    results = [];
    for i in range(len(data[category][domain])):
      results.append(data[category][domain][i]);
    writeToFile(domain, category, results);