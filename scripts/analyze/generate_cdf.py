#/bin/python

import sys;

def checkArguments():
  if (len(sys.argv) < 3):
    print "Usage:";
    print "python generate_cdf.py DATA_FILE COLUMN_NUM";
    print "";
    print "Generate CDF data based on the COLUMN_NUM column of the DATA_FILE. Columns split by \\t";
    sys.exit(0);

def main():    
  checkArguments();
  f = open(sys.argv[1]);
  lines = f.readlines();
  f.close();
  column_num = int(sys.argv[2]);
  result = [];
  for i in range(len(lines)):
    lines[i] = lines[i].replace('\n','').split('\t');
    if len(lines[i]) <= column_num:
      continue;
    result.append(int(lines[i][column_num]));

  result.sort();
  length = len(result)
  for i in range(len(result)):
    print result[i],'\t',float(i+1)/float(length)  
  
if __name__ == "__main__":
  main();

