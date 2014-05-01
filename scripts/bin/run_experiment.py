#!/bin/python

import sys;
import json;
import time;
import signal;
import datetime;
import subprocess;

def checkArguments():
  if (len(sys.argv) < 4):
    print "Usage:";
    print "python run_experiment.py URL_TO_LOAD NUM_OF_LOADS COOKIES_FILE [OPTIONS]";
    print "";
    print "Load web pages using pre-constructed PhantomJS cookie files. Output logging informations to std output.";
    print "[OPTIONS] is used to pass configuration parameters to PhantomJS";
    print "COOKIES_FILE can be set to 'NONE' if an empty profile is desired";
    sys.exit(0);

phantomjs_bin = "~/Lab_TargetedAds/phantomjs/phantomjs--linux-x86_64/bin/phantomjs";
phantomjs_script = "~/Lab_TargetedAds/src/bin/phantomjs_start.js";

def msfromepoch():
  return long(round(float(datetime.datetime.now().strftime('%s.%f')) * 1000));

class TimeoutFunctionException(Exception): 
  """Exception to raise on a timeout""" 
  pass 

class TimeoutFunction: 
  def __init__(self, function, timeout): 
    self.timeout = timeout 
    self.function = function 

  def handle_timeout(self, signum, frame): 
    raise TimeoutFunctionException()

  def __call__(self, *args): 
    old = signal.signal(signal.SIGALRM, self.handle_timeout) 
    signal.alarm(self.timeout) 
    try: 
      result = self.function(*args)
    finally: 
      signal.signal(signal.SIGALRM, old)
    signal.alarm(0)
    return result 

def startPhantomJS(url, cookie_file, options):
  if cookie_file != "NONE":
    command = phantomjs_bin + " --load-plugins=true --disk-cache=no --web-security=no --cookies-file=" + cookie_file;
  else:
    command = phantomjs_bin + " --load-plugins=true --disk-cache=no --web-security=no";
  command += " " + phantomjs_script + " '" + url + "'";
  if options != None and options != "":
    command += ' ' + options;
  print command;
  p = subprocess.Popen(command, shell = True, stdout = subprocess.PIPE);
  results = p.communicate()[0];
  return results;

def abortPhantomJS():
  command = "killall phantomjs";
  p = subprocess.Popen(command, shell = True);
  p.wait();

def resetCookie(cookie_file, temp_cookie_file):
  command = "cp " + cookie_file + ' ' + temp_cookie_file;
  p = subprocess.Popen(command, shell = True);
  p.wait();
  
def removeCookie(temp_cookie_file):
  command = "rm " + temp_cookie_file;
  p = subprocess.Popen(command, shell = True);
  p.wait();
  sys.stderr.write("Cookie removed: " + temp_cookie_file + '\n'); 
  
def analyzeResult(result):
  result = result.split('\n');
  output = "";
  error = True;
  for i in range(len(result)):
    result[i] = result[i].split('\t');
    if (result[i][0] == '<MSG><RESULT>'):
      if result[i][1] == "Ad Detected:" and len(result) >= 4:
        output += "<AD>\t" + result[i][2] + '\t' + result[i][3] + '\n';
        error = False;
      elif result[i][1] == "Tracker Detected:":
        output += "<TRACKER>\t" + result[i][2] + '\n';
        error = False;
      elif result[i][1] == "Request Detected:":
        output += "<REQUEST>\t" + result[i][2] + '\n';
        error = False;
      # data = json.loads(result[i][2]);
      # for j in range(len(data)):
      #   output += "<AD>\t" + data[j]['landing_url'] + '\t'
      #   categories = data[j]['landing_url_category'];
      #   if type(categories) == list:
      #     temp = []
      #     for k in range(len(categories)):
      #       temp.append(categories[k]['AbsolutePath']);
      #     output += ';'.join(temp);
      #   elif type(categories) == dict and 'AbsolutePath' in categories:
      #     output += categories['AbsolutePath'];
      #   else:
      #     output += 'N/A';
      #   output += "\n";
  if error == True:
    output += "ERROR\n";
  return output;

def main():
  checkArguments();

  options = None;
  url_to_load = str(sys.argv[1]);
  num_of_loads = int(sys.argv[2])
  cookie_file = str(sys.argv[3]);
  
  if cookie_file != "NONE":
    temp_cookie_file = url_to_load.replace(':', '').replace('/', '').replace('?', '').replace('&', '').replace('=', '');
    temp_cookie_file += '-' + cookie_file.replace('/', '') + '-' + str(time.time()) + '.tmp';
  
  if len(sys.argv) == 5:
    options = sys.argv[4];
    
  output = ""
  
  loadPage = TimeoutFunction(startPhantomJS, 60);
  if cookie_file != "NONE":
    for i in range(num_of_loads):
      resetCookie(cookie_file, temp_cookie_file);
      sys.stderr.write('Cookie Reset:\t' + temp_cookie_file + '\n')
      start_time = msfromepoch();
      sys.stderr.write('Loading:\t' + url_to_load + '\t[' + str(i) + ']. ');
      try:
        ret = loadPage(url_to_load, temp_cookie_file, options);
        load_time = msfromepoch() - start_time;
        sys.stderr.write('Finished in: ' + str(load_time) + '\n');
        # output += '[' + str(i) + ']\n';
        # output += ret;
        output += analyzeResult(ret);
      except:
        sys.stderr.write('Timesout');
        abortPhantomJS();
    removeCookie(temp_cookie_file);
  else:
    for i in range(num_of_loads):
      sys.stderr.write('Loading:\t' + url_to_load + '\t[' + str(i) + ']. ')
      start_time = msfromepoch();
      try:
        ret = loadPage(url_to_load, "NONE", options);
        load_time = msfromepoch() - start_time;
        sys.stderr.write('Finished in: ' + str(load_time) + '\n');
        # output += '[' + str(i) + ']\n';
        # output += ret;
        output += analyzeResult(ret);
      except:
        sys.stderr.write('Timesout');
        abortPhantomJS();
  
  print output;
  
if __name__ == "__main__":
  main();
