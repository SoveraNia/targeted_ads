#!/bin/python

import sys;
import json;
import signal;
import time;
import datetime;
import subprocess;

if (len(sys.argv) < 5):
  print ("Usage:")
  print ("sudo python chrome_driver_start.py INPUT_FILE HAR_OUTPUT_DIR NUM_OF_LOADS");
  sys.exit(0);

dummyPage = "chrome://cache/";
if (len(sys.argv) == 7):
  proxy_ip = str(sys.argv[6]);
  dummyPage = "http://" + proxy_ip + "/testsite/blank.html";

input_file = str(sys.argv[1]);
output_dir = str(sys.argv[2]);
num_of_loads = int(sys.argv[3]);

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

def msfromepoch():
  return long(round(float(datetime.datetime.now().strftime('%s.%f')) * 1000));

#def clearBrowserCache():
#  command = "";
#  p = subprocess.Popen(command, shell = True);
#  p.wait();

#def startTcpDump(filename):
#  # command = "sudo tcpdump -i " + network + " -n -s 0 -w '" + output_dir + "/" + filename + "' '(port 80 or port 53 or port 44300)' &";
#  command = adb_directory + "/adb -s " + device_id + ' shell su -c "tcpdump -i ' + network + " -n -s 0 -w '" + android_pcap_output_dir + "/" + filename + "' '(port 80 or port 53 or port 44300)'\" &";
#  p = subprocess.Popen(command, shell = True);
#  p.wait();

#def stopTcpDump():
#  # command = "sudo killall tcpdump";  
#  command = adb_directory + "/adb -s " + device_id + " shell su -c 'killall tcpdump'";  
#  p = subprocess.Popen(command, shell = True);
#  p.wait();

# Start Chrome on Android
def startChrome():
  #command = adb_directory + "/adb -s " + device_id + " shell am start -a android.intent.action.VIEW -n " + chrome_package + "/com.android.chrome.Main";# -d " + dummyPage;
  command = "google-chrome --remote-debugging-port=9222 --enable-benchmarking --enable-net-benchmarking &"
  p = subprocess.Popen(command, shell = True);
  # p.wait();
  
# Stop Chrome on Android
def stopChrome():
  #command = adb_directory + "/adb -s " + device_id + " shell am force-stop " + chrome_package;
  command = "killall chrome";
  p = subprocess.Popen(command, shell = True);
  p.wait();

# Load Url and capture HAR file
def loadUrl(url, output, clearCache):
  if (clearCache == True):
    # clearBrowserCache();
    command = 'chrome-har-capturer -p 9222 -r temp.res -o "' + output + '" "' + url + '"';# "' + dummyPage + '"';
  else:
    command = 'chrome-har-capturer -p 9222 -r temp.res -o "' + output + '" "' + url + '"';# "' + dummyPage + '"';
  print command;
  p = subprocess.Popen(command, shell = True);
  p.wait();
  
def main():
  # Read Input File
  f = open(input_file);
  urls = f.readlines();
  f.close();
  
  maxNumberOfRetries = 3;
  
  for i in range(len(urls)):
    urls[i] = urls[i].replace('\n', '');
    
  # setupChrome();
    
  visitSite = TimeoutFunction(loadUrl, 90);
    
  for i in range(num_of_loads):
    for j in range(len(urls)):
      for x in range(len(settings)):
        if (settings[x] != ""):
          url_to_load = urls[j] + '?' + settings[x];
        else:
          url_to_load = urls[j];
        
        for k in range(maxNumberOfRetries):
          # clearCache();
          startChrome();
          time.sleep(5);
          
          starttime = msfromepoch();
          filename = settings[x] + '_' + urls[j].replace('/', '').replace(':', '') + "-" + str(i) + ".har";
          # pcap_filename = settings[x] + '_' + urls[j].replace('/', '').replace(':', '') + "-" + str(i) + ".pcap";
          # print "TCPDUMP STARTED\t" + pcap_filename + "\t" + str(starttime);
          # startTcpDump(pcap_filename);
          # time.sleep(5);
          try:
            visitSite(url_to_load, output_dir + '/' + filename, True);
          except TimeoutFunctionException:
            print ("Website load too slow: " + urls[j]);
          
          time.sleep(2);
          stopChrome();
          # time.sleep(2);
          # stopTcpDump();      
          time.sleep(5);
          
          # Check whether har is correctly captured
          try:
            json_data = open(output_dir + '/' + filename);
            data = json.load(json_data);
            if (len(data['log']['entries']) > 0):
              json_data.close();
              break;
            else:
              command = 'rm "' + output_dir + '/' + filename + '"';
              p = subprocess.Popen(command, shell = True);
              p.wait();
              json_data.close();
          except:
            wtf = 0;
        
if __name__ == "__main__":
  main();
