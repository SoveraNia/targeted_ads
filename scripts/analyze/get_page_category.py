#!/bin/python

import glob;
import sys;
import json;
import urllib2;

def checkArguments():
  if (len(sys.argv) < 2):
    print "Usage:";
    print "python get_page_category.py URL_FILE";
    print "";
    print "Detect the categories of a list of web pages"
    sys.exit(0);
checkArguments();

def getPageCategory(url):
  php_url = "http://localhost/ad_detect/get_url_category.php";
  php_url += '?site=' + urllib2.quote(url);
  
  alchemy_api_key = "beeb8469c6f7d1a0c7344dcee236d3e8ca71d53c";
  alchemy_api_url = "http://access.alchemyapi.com/calls/url/URLGetCategory";
  call_url = alchemy_api_url + "?apikey=" + alchemy_api_key;
  call_url += "&url=" + urllib2.quote(url);
  call_url += "&outputMode=json";
  
  numRetries = 1;
  while numRetries > 0:
    response = urllib2.urlopen(php_url);
    html = response.read();
    try:
      ret = json.loads(html)['Response']['UrlInfoResult']['Alexa']['Related']['Categories']['CategoryData'];
      return ret;
    except:
      # print call_url;
      response = urllib2.urlopen(call_url);
      html = response.read();
      try:
        ret = {};
        ret['source'] = 'Alchemy';
        ret['category'] = json.loads(html)['category'];
        return ret;
      except:
        numRetries -= 1;

  return {};

def detectCategories(categories):
  ret = [];
  if type(categories) == list:
    for i in range(len(categories)):
      category = categories[i]['AbsolutePath'];
      if category.find("World") >=0 or category.find("Regional") >= 0:
        continue;
      ret.append(category.replace('Top/', ''));
  elif type(categories) == dict:
    if 'source' in categories and categories['source'] == 'Alchemy':
      ret.append(categories['category'].title());
    elif 'AbsolutePath' in categories:
      category = categories['AbsolutePath'];
      if category.find("World") < 0 or category.find("Regional") < 0:
        ret.append(category.replace('Top/', ''));
  return ret;

f = open(sys.argv[1]);
lines = f.readlines();
f.close();

for i in range(len(lines)):
  lines[i] = lines[i].replace('\n', '');
  category = detectCategories(getPageCategory(lines[i]));
  print lines[i] + '\t' + ','.join(category)