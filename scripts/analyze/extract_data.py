import sys;
import json;
import time;
import subprocess;

def checkArguments():
  if (len(sys.argv) < 4):
    print "Usage:"
    print "python extract_data.py LOG_FILE START END";
    print ""
    print "Extract data from LOG_FILE";
    sys.exit(0);

checkArguments();

f = open(sys.argv[1]);
lines = f.readlines();
f.close();

start = sys.argv[2];
end = sys.argv[3];

started = False;
ended = False;
for i in range(len(lines)):
  lines[i] = lines[i].replace('\n','');
  if not started and not ended and start in lines[i]:
    started = True;
  elif started and not ended and end in lines[i]:
    ended = True;
  elif started and not ended:
    print lines[i];
    
