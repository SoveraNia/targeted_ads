#!/bin/python

import glob;
import sys;
import json;
import urllib2;
import subprocess;
from urlparse import urlparse;

def checkArguments():
  if (len(sys.argv) < 2):
    print "Usage:";
    print "python count_ads.py LOG_FILES [PROFILE_URLS]";
    print "";
    print "From the logs generated by run_experiment.py, extract all Ads and determine their categories."
    print "[PROFILE_URLS] parameter is used to determine how many ads are remarketing ads."
    sys.exit(0);

ad_db_filename = '/home/soverania/Lab_TargetedAds/src/resources/ad_db.json';
ad_db = {};

f = open(ad_db_filename);
ad_db = json.load(f);
f.close();

ad_providers_filename = '/home/soverania/Lab_TargetedAds/src/resources/ad_providers.json'
ad_providers = [];

f = open(ad_providers_filename);
ad_providers = json.load(f);
f.close();

redirection_db_filename = '/home/soverania/Lab_TargetedAds/src/resources/redirection_db.json'
redirection_db = {};

f = open(redirection_db_filename);
redirection_db = json.load(f);
f.close();

country_code = ['ac','ad','ae','af','ag','ai','al','am','an','ao','aq','ar','as','at','au','aw','az','ba','bb','bd','be','bf','bg','bh','bi','bj','bm','bn','bo','br','bs','bt','bv','bw','by','by','bz','ca','cc','cd','cf','cg','ch','ci','ck','cl','cm','cn','co','cr','cs','cu','cv','cx','cy','cz','de','dj','dk','dm','do','dz','ec','ee','eg','eh','er','es','et','eu','fi','fj','fk','fm','fo','fr','ga','gd','ge','gf','gh','gi','gl','gm','gn','gp','gq','gr','gu','gt','gw','gy','hk','hm','hn','hr','ht','hu','id','ie','il','in','io','iq','ir','is','it','jm','jo','jp','ke','kg','kh','ki','km','kn','kp','kr','kw','ky','kz','la','lb','lc','li','lk','lr','ls','lt','lu','lv','ly','ma','mc','md','mg','mh','mk','ml','mm','mn','mo','mp','mq','mr','ms','mt','mu','mv','mw','mx','my','mz','na','nc','ne','nf','ng','ni','nl','no','np','nr','nt','nu','nz','om','pa','pe','pf','pg','ph','pk','pl','pm','pn','pr','ps','pt','pw','py','re','ro','ru','rw','sa','sb','sc','sd','se','sg','sh','si','sj','sl','sm','sn','so','sr','st','su','sv','sy','sz','tc','td','tf','tg','th','tj','tk','tm','tn','to','tp','tr','tt','tv','tw','tz','ua','ug','uk','um','us','uy','uz','va','vc','ve','vg','vi','vn','vu','ws','yu','za','zm','zr','zw'];

def detectRedirection(url):
  return "NONE"; # If we don't want to detect redirection
  if url[:4] != "http":
    if url.find('http') < 0:
      return "NONE";
    temp = url.split('http')[1].split(';')[0].split(',')[0];
    url = 'http' + temp;
  
  if url in redirection_db:
    return redirection_db[url];
  
  command = "~/Lab_TargetedAds/phantomjs/phantomjs--linux-x86_64/bin/phantomjs ~/Lab_TargetedAds/src/bin/detect_redirection.js '";
  command += url + "'";
  p = subprocess.Popen(command, shell = True, stdout = subprocess.PIPE);
  results = p.communicate()[0];
  results = results.split('\n');
  for i in range(len(results)):
    results[i] = results[i].split('\t');
    if len(results[i]) >= 3 and results[i][0] == '<MSG><RESULT>' and results[i][1] == "Destination":
      if not url in redirection_db:
        redirection_db[url] = results[i][2];
      return results[i][2];
  return "NONE";
  

def url2Domain(url):
  domain = url.split('&')[0];
  if domain.find('://') >= 0:
    domain = domain.split('://')[1];
  domain = domain.split('/')[0];
  if domain.count('.') >= 2:
    temp = domain.split('.');
    if temp[len(temp) - 1] in country_code and len(temp) > 2:
      domain = temp[len(temp) - 3] + '.' + temp[len(temp) - 2] + '.' + temp[len(temp) - 1];
    else:
      domain = temp[len(temp) - 2] + '.' + temp[len(temp) - 1];
  return domain

def outputAdDb():
  f = open(ad_db_filename, 'w');
  f.write(json.dumps(ad_db));
  f.close();
  
def outputRedirectionDb():
  f = open(redirection_db_filename, 'w');
  f.write(json.dumps(redirection_db));
  f.close();
  
def url2AdProviders(url):
  result = []
  for i in range(len(ad_providers)):
    if url.find(ad_providers[i]) >= 0:
      result.append(ad_providers[i]);
  return result;

def getPageCategory(url):
  if url == None:
    return {};
  if (url in ad_db) and (ad_db[url] != []) and (ad_db[url] != {}):
    # print "<DEBUG>\tAd found in database";
    return ad_db[url];
  
  php_url = "http://localhost/ad_detect/get_url_category.php";
  php_url += '?site=' + urllib2.quote(url);
  
  alchemy_api_key = "beeb8469c6f7d1a0c7344dcee236d3e8ca71d53c";
  alchemy_api_url = "http://access.alchemyapi.com/calls/url/URLGetCategory";
  call_url = alchemy_api_url + "?apikey=" + alchemy_api_key;
  call_url += "&url=" + urllib2.quote(url);
  call_url += "&outputMode=json";
  
  # 3 tries to Alexa
  numRetries = 3;
  while numRetries > 0:
    try:
      response = urllib2.urlopen(php_url);
      html = response.read();
      ret = json.loads(html)['Response']['UrlInfoResult']['Alexa']['Related']['Categories']['CategoryData'];
      ad_db[url] = ret;
      return ret;
    except:
      numRetries -= 1;
      
  # 1 try to Alchemy
  try:
    response = urllib2.urlopen(call_url);
    html = response.read();
    ret = {};
    ret['source'] = 'Alchemy';
    ret['category'] = json.loads(html)['category'];
    ad_db[url] = ret;
    return ret;
  except:
    return {};

def detectCategories(categories):
  ret = [];
  if type(categories) == list:
    for i in range(len(categories)):
      category = categories[i]['AbsolutePath'];
      if category.find("World") >=0 or category.find("Regional") >= 0:
        continue;
      # if category.count('/') >= 3:
      #   temp = category.split('/');
      #   category = temp[1] + '/' + temp[2];
      #   ret.append(category);
      # else:
      ret.append(category.replace('Top/', ''));
  elif type(categories) == dict:
    if 'source' in categories and categories['source'] == 'Alchemy':
      ret.append(categories['category'].title());
    elif 'AbsolutePath' in categories:
      category = categories['AbsolutePath'];
      if category.find("World") < 0 or category.find("Regional") < 0:
        # if category.count('/') >= 3:
        #   temp = category.split('/');
        #   category = temp[1] + '/' + temp[2];
        #   ret.append(category);
        # else:
        ret.append(category.replace('Top/', ''));
  return ret;

# Python is having trouble parsing JSON strings longer than 4k
def forceParseJSON(str):
  ret = {};
  ret['obj_count'] = 0;
  ret['ad_count'] = 0;
  ret['missed_ads'] = [];
  ret['missed_ads_from_url'] = 0;
  ret['missed_ads_from_flashvars'] = 0;
  ret['ads'] = [];
  
  if (str == '[]'):
    return ret;
  
  data = None;
  try:
    data = json.loads(str);
  except:
    if str[0] == '"' and str[len(str)-1] == '"':
      str = str[1:-1].replace('\\"', '"').replace(' ', '');
    
    ads = str[1:-1].replace(',{"url"', '\n{"url"').split('\n');
    ret['obj_count'] = len(ads);
    for i in range(len(ads)):
      url = ads[i][ads[i].find('"url":') + 7:].split('"')[0];
      landing_url = "NONE";
      if ads[i].find('"landing_url":') < 0:
         landing_url = detectRedirection(url);
      
      if ads[i].find('"landing_url":') < 0 and landing_url == "NONE":
        ret['missed_ads'].append(url);
        ret['ad_count'] += 1;
        if url[:7] == "http://" or url[:8] == "https://":
          ret['missed_ads_from_url'] += 1;
        else:
          ret['missed_ads_from_flashvars'] += 1;
        
        ad = {};
        ad['url'] = url;
        ad['providers'] = url2AdProviders(url);
        ad['landing_url'] = "NONE";
        ad['landing_url_category'] = {};
        ret['ads'].append(ad);
      else:
        ret['ad_count'] += 1;
        ad = {};
        ad['url'] = url;
        ad['providers'] = url2AdProviders(url);
        if landing_url == "NONE":
          ad['landing_url'] = ads[i].split('"landing_url":"')[1].split('"')[0];
        else:
          ad['landing_url'] = landing_url;
        ad['landing_domain'] = urlparse(ad['landing_url']).hostname;
        landing_domain = url2Domain(ad['landing_url']);
        if not landing_domain in ad_providers:
          if ads[i].find('"landing_url_category":') >= 0:
            try:
              categories = json.loads(ads[i].split('"landing_url_category":')[1][:-1]);
              if categories == [] or categories == {}:
                categories = getPageCategory(ad['landing_domain']);
              ad['landing_url_category'] = detectCategories(categories);
            except:
              ad['landing_url_category'] = [];
          else:
            categories = getPageCategory(ad['landing_domain']);
            ad['landing_url_category'] = detectCategories(categories);
          ret['ads'].append(ad);
          ret['ad_count'] += 1;
        else:
          ret['missed_ads'].append(ad['landing_url']);
          ad['landing_url_category'] = [];
            
  if (data != None):
    ret['obj_count'] += len(data);
    for j in range(len(data)):
      # Remove redirections
      if (not 'landing_url' in data[j]) and ('url' in data[j]):
        landing_url = detectRedirection(data[j]['url']);
        if landing_url != "NONE":
          data[j]['landing_url'] = landing_url;
      
      if (not 'landing_url' in data[j]) and ('url' in data[j]):
        ret['missed_ads'].append(data[j]['url']);
        if data[j]['url'][:7] == "http://" or data[j]['url'][:8] == "https://":
          ret['missed_ads_from_url'] += 1;
        else:
          ret['missed_ads_from_flashvars'] += 1;
        
        ad = {};
        ad['url'] = data[j]['url'];
        ad['providers'] = url2AdProviders(data[j]['url']);
        ad['landing_url'] = "NONE";
        ad['landing_url_category'] = {};
        ret['ads'].append(ad);
      elif 'url' in data[j]:
        ad = {};
        ad['url'] = data[j]['url'];
        ad['providers'] = url2AdProviders(data[j]['url']);
        ad['landing_url'] = data[j]['landing_url'];
        ad['landing_domain'] = urlparse(data[j]['landing_url']).hostname;
        landing_domain = url2Domain(ad['landing_url']);
        if not landing_domain in ad_providers:
          if 'landing_url_category' in data[j]:
            categories = data[j]['landing_url_category'];
            if categories == [] or categories == {}:
              categories = getPageCategory(ad['landing_domain']);
            ad['landing_url_category'] = detectCategories(categories);
          else:
            categories = getPageCategory(ad['landing_domain']);
            ad['landing_url_category'] = detectCategories(categories);
          ret['ads'].append(ad);
          ret['ad_count'] += 1;
        else:
          ret['missed_ads'].append(data[j]['landing_url']);
          ad['landing_url_category'] = {};
  
  return ret;

def getAdCount(filename):
  f = open(filename);
  lines = f.readlines();
  f.close();
  ret = {};
  ret['obj_count'] = 0;
  ret['ad_count'] = 0;
  ret['ads'] = [];
  ret['missed_ads'] = [];
  ret['missed_ads_from_url'] = 0;
  ret['missed_ads_from_flashvars'] = 0;
  for i in range(len(lines)):
    lines[i] = lines[i].replace('\n', '').split('\t');
    if len(lines[i]) >= 2 and lines[i][0] == "<AD>":
      item = forceParseJSON(lines[i][1]);
      ret['obj_count'] += item['obj_count'];
      ret['ad_count'] += item['ad_count'];
      ret['ads'].append(item['ads']);
      ret['missed_ads'] += item['missed_ads'];
      ret['missed_ads_from_url'] += item['missed_ads_from_url'];
      ret['missed_ads_from_flashvars'] += item['missed_ads_from_flashvars']
  return ret;

def main():
  checkArguments();
  
  profile_urls = []
  if len(sys.argv) >= 3:
    f = open(sys.argv[2]);
    profile_urls = f.readlines();
    f.close();
    for i in range(len(profile_urls)):
      profile_urls[i] = url2Domain(profile_urls[i].replace('\n', ''));
  
  log_files = glob.glob(sys.argv[1]);
  total_obj_count = 0;
  total_ad_count = 0;
  sites_contain_ads = [];
  missed_ads = [];
  missed_ads_from_url = 0;
  missed_ads_from_flashvars = 0;
  ads_from_profile = 0;
  
  for i in range(len(log_files)):
    sys.stderr.write('Processing:\t' + log_files[i] + '\n')
    url = log_files[i].split('_')[1].replace('---', '://').replace('-.txt', '/');
    ret = getAdCount(log_files[i]);
    total_obj_count += ret['obj_count'];
    total_ad_count += ret['ad_count'];
    if ret['obj_count'] > 0:
      sites_contain_ads.append(url);
    missed_ads += ret['missed_ads'];
    missed_ads_from_url += ret['missed_ads_from_url'];
    missed_ads_from_flashvars += ret['missed_ads_from_flashvars'];
    
    # print "URL:\t" + url;
    for j in range(len(ret['ads'])):
      for k in range(len(ret['ads'][j])):
        try:
          ad_out = str(j) + '\t' + ret['ads'][j][k]['landing_url'] + '\t';
          if len(ret['ads'][j][k]['landing_url_category']) == 0:
            ad_out += 'CATEGORY_UNKNOWN';
          else:
            ad_out += ';'.join(ret['ads'][j][k]['landing_url_category']);
          ad_out += '\t';
          if len(ret['ads'][j][k]['providers']) == 0:
            ad_out += 'NONE';
          else:
            ad_out += ','.join(ret['ads'][j][k]['providers']);
          ad_out += '\t' + ret['ads'][j][k]['url'];
          print ad_out;
          
          # Count ads from profile
          if url2Domain(ret['ads'][j][k]['landing_url']) in profile_urls:
            ads_from_profile += 1;
            
        except:
          wtf = 1;
  
  outputAdDb();
  outputRedirectionDb()
    
  print "============================================"
  print "Object detected:\t",total_obj_count;
  print "Sites contain ads:\t",len(sites_contain_ads);
  # for i in range(len(sites_contain_ads)):
  #   print sites_contain_ads[i];
  print "Ad detected:\t",total_ad_count;
  print "Missed Ads:\t",len(missed_ads);
  print "Ads from profile:\t",ads_from_profile;
  # print "Missed Ads from URL:\t",missed_ads_from_url;
  # print "Missed Ads from Flashvars:\t",missed_ads_from_flashvars;
  # for i in range(len(missed_ads)):
    # print missed_ads[i];

if __name__ == "__main__":
  main();