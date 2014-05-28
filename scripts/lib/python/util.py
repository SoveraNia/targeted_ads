import sys;
import json;
import subprocess;
import signal;
from os.path import expanduser;

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

def runCommand(cmd, timeout = 60):
  def run(cmd):
    p = subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE);
    results = p.communicate()[0].split('\n');
    return results;
  timedRun = TimeoutFunction(run, timeout);
  try:
    ret = timedRun(cmd);
    return ret;
  except:
    return ['TIMEOUT'];

def url2Domain(url):
  country_code = ['ac','ad','ae','af','ag','ai','al','am','an','ao','aq','ar','as','at','au','aw','az','ba','bb','bd','be','bf','bg','bh','bi','bj','bm','bn','bo','br','bs','bt','bv','bw','by','by','bz','ca','cc','cd','cf','cg','ch','ci','ck','cl','cm','cn','co','cr','cs','cu','cv','cx','cy','cz','de','dj','dk','dm','do','dz','ec','ee','eg','eh','er','es','et','eu','fi','fj','fk','fm','fo','fr','ga','gd','ge','gf','gh','gi','gl','gm','gn','gp','gq','gr','gu','gt','gw','gy','hk','hm','hn','hr','ht','hu','id','ie','il','in','io','iq','ir','is','it','jm','jo','jp','ke','kg','kh','ki','km','kn','kp','kr','kw','ky','kz','la','lb','lc','li','lk','lr','ls','lt','lu','lv','ly','ma','mc','md','mg','mh','mk','ml','mm','mn','mo','mp','mq','mr','ms','mt','mu','mv','mw','mx','my','mz','na','nc','ne','nf','ng','ni','nl','no','np','nr','nt','nu','nz','om','pa','pe','pf','pg','ph','pk','pl','pm','pn','pr','ps','pt','pw','py','re','ro','ru','rw','sa','sb','sc','sd','se','sg','sh','si','sj','sl','sm','sn','so','sr','st','su','sv','sy','sz','tc','td','tf','tg','th','tj','tk','tm','tn','to','tp','tr','tt','tv','tw','tz','ua','ug','uk','um','us','uy','uz','va','vc','ve','vg','vi','vn','vu','ws','yu','za','zm','zr','zw'];
  domain = url.split('&')[0].split('?')[0];
  if domain.find('://') >= 0:
    domain = domain.split('://')[1];
  domain = domain.split('/')[0];
  if domain.count('.') >= 2:
    temp = domain.split('.');
    if temp[len(temp) - 1] in country_code and len(temp) > 2:
      domain = temp[len(temp) - 3] + '.' + temp[len(temp) - 2] + '.' + temp[len(temp) - 1];
    else:
      domain = temp[len(temp) - 2] + '.' + temp[len(temp) - 1];
  return domain.lower();

def url2Homepage(url):
  if '://' in url:
    host = url.split('://')[1].split('/')[0];
    scheme = url.split('://')[0];
    return scheme + '://' + host + '/';
  else:
    scheme = 'http'
    host = url.split('/')[0];
    return scheme + '://' + host + '/';

def getInternalPages(url, count):
  get_internal_pages_js = expanduser('~') + "/Lab_TargetedAds/src/bin/get_internal_pages.js"
  command = '~/Lab_TargetedAds/phantomjs/phantomjs--linux-x86_64/bin/phantomjs ' + get_internal_pages_js + ' "' + url + '" ' + str(count);
  results = runCommand(command);
  ret = []
  for i in range(len(results)):
    results[i] = results[i].split('\t');
    if results[i][0] == "<MSG><RESULT>":
      ret.append(results[i][1]);
  return ret;