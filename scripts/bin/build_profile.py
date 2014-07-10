#!/bin/python

import os;
import sys;
import json;
import signal;
import subprocess;

def checkArguments():
  if (len(sys.argv) < 3):
    print "Usage:"
    print "python build_profile.py URLS_TO_PRELOAD COOKIES_FILE [OPTIONS]";
    print ""
    print "Load web pages using PhantomJS to build profile and store the resulting cookies in COOKIES_FILE."
    print "[OPTIONS] is used to pass configuration parameters to PhantomJS"
    print "URLS_TO_PRELOAD can be passed as a file name as well as a list of urls separated by ';'"
    sys.exit(0);

phantomjs_bin = "~/Lab_TargetedAds/phantomjs/phantomjs--linux-x86_64/bin/phantomjs";
phantomjs_script = "~/Lab_TargetedAds/src/bin/phantomjs_start.js";

phantomjs_proc = None;

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
  command = "exec " + phantomjs_bin + " --load-plugins=true --disk-cache=no --web-security=no --cookies-file=" + cookie_file;
  # command = "--load-plugins=true --disk-cache=no --web-security=no --cookies-file=" + cookie_file;
  command += " " + phantomjs_script + " '" + url + "'";
  if options != None:
    command += " " + options;
  global phantomjs_proc;
  phantomjs_proc = subprocess.Popen(command, shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE);
  results, log = phantomjs_proc.communicate();
  log = log.split('\n');
  for i in range(len(log)):
    if "phantomjs: cannot connect to X server :" in log[i]:
      port = int(log[i].split("phantomjs: cannot connect to X server :")[1]);
      sys.stderr.write("Xvfb crashed. Restarting on port " + str(port) + '\n'); 
      restartXvfb(port);
      phantomjs_proc = None;
      return startPhantomJS(url, cookie_file, options);
  phantomjs_proc = None;
  return results;

def abortPhantomJS():
  #command = "killall phantomjs";
  #p = subprocess.Popen(command, shell = True);
  #p.wait();
  global phantomjs_proc;
  if phantomjs_proc != None:
    phantomjs_proc.terminate();
  phantomjs_proc = None;

def restartXvfb(port):
  command = "Xvfb :" + str(port) + " -screen 0 1280x1024x24 &";
  p = subprocess.Popen(command, shell = True);
  time.sleep(3);
  
def clearCookies(cookie_file):
  command = "echo '' > " + cookie_file;
  p = subprocess.Popen(command, shell = True);
  p.wait();

def main():
  checkArguments();
  
  input_file = str(sys.argv[1]);
  urls_to_preload = [];
  if (input_file != "" and not '://' in input_file):
    f = open(input_file);
    urls_to_preload = f.readlines();
    f.close();
  if '://' in input_file:
    urls_to_preload = input_file.split(';');
    
  cookie_file = sys.argv[2];
  # clearCookies(cookie_file);
  
  options = None;
  if len(sys.argv) == 4:
    options =  sys.argv[3];
      
  output = ""
  
  for i in range(len(urls_to_preload)):
    urls_to_preload[i] = urls_to_preload[i].replace('\n', '');
    loadPage = TimeoutFunction(startPhantomJS, 60);
    try:
      sys.stderr.write('Loading:\t' + urls_to_preload[i] + '\n');
      ret = loadPage(urls_to_preload[i], cookie_file, options);
      sys.stderr.write('Load Finished:\t' + urls_to_preload[i] + '\n');
      output += ret;
    except:
      sys.stderr.write('Timesout\n');
      abortPhantomJS();
  
  sys.stderr.write("Cookies saved in: " + cookie_file + '\n');
  print output;
  
def test():
  loadPage = TimeoutFunction(startPhantomJS, 2);
  try:
    sys.stderr.write('Loading:\t' + "http://www.sina.com.cn/" + '\n');
    ret = loadPage("http://www.sina.com.cn/", "NONE", "");
    sys.stderr.write('Load Finished:\t' + "http://www.sina.com.cn/" + '\n');
    output += ret;
  except:
    sys.stderr.write('Timesout\n');
    abortPhantomJS();
  
if __name__ == "__main__":
  main();
  # test();