#!/bin/python

import sys;
import glob;
import subprocess;

def checkArguments():
  if (len(sys.argv) <= 2):
    print "Usage:"
    print "python add_internal_pagest.py URL_FILES NUM_OF_PAGES";
    print ""
    print "For each url in each file in URL_FILES, add NUM_OF_PAGES first-party web pages into the file."
    sys.exit(0);

phantomjs_bin = "/home/soverania/Lab_TargetedAds/phantomjs/phantomjs--linux-x86_64/bin/phantomjs";
get_internal_pages_js = "/home/soverania/Lab_TargetedAds/src/bin/get_internal_pages.js"

def getInternalPages(url, count):
  command = phantomjs_bin + ' ' + get_internal_pages_js + ' "' + url + '" ' + str(count);
  p = subprocess.Popen(command, shell = True, stdout = subprocess.PIPE);
  results = p.communicate()[0].split('\n');
  
  ret = []
  for i in range(len(results)):
    results[i] = results[i].split('\t');
    if results[i][0] == "<MSG><RESULT>":
      ret.append(results[i][1]);
      
  return ret;

def main():
  checkArguments();
  
  files = glob.glob(sys.argv[1]);
  count = int(sys.argv[2]);  
  
  for i in range(len(files)):
    f = open(files[i]);
    lines = f.readlines();
    
    out_file_name = files[i] + ".expanded-" + str(count) + '.txt';
    w = open(out_file_name, 'w');
    print("Writing " + out_file_name);
    
    for j in range(len(lines)):
      lines[j] = lines[j].replace('\n', '');
      print "Getting internal pages for: " + lines[j];
      w.write(lines[j] + '\n');
      internal_pages = getInternalPages(lines[j], count);
      for k in range(len(internal_pages)):
        w.write(internal_pages[k] + '\n');
      
    w.close(); 
    f.close();

if __name__ == "__main__":
  main();