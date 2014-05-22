import sys;
import json;
import time;
import subprocess;
import urllib2;
from HTMLParser import HTMLParser

from os.path import expanduser;
from sys import path
path.append(expanduser('~') + '/Lab_TargetedAds/src/lib/python');

from util import url2Domain;
from util import url2Homepage;
from util import runCommand;
from stats import Stats;

###################################
# Ad Extractor
###################################
class AdExtractor:
  # Ad category db
  ad_db_filename = expanduser('~') + '/Lab_TargetedAds/src/resources/ad_db.json';
  ad_db = {};
  
  # Redirection DB
  redirection_db_filename = expanduser('~') + '/Lab_TargetedAds/src/resources/redirection_db.json'
  redirection_db = {};
  
  ad_providers_filename = expanduser('~') + '/Lab_TargetedAds/src/resources/ad_providers.json'
  ad_providers = [];
  
  category_mapping_alexa_filename = expanduser('~') + '/Lab_TargetedAds/src/resources/category_mapping_alexa.json'
  category_mapping_alexa = {};
  
  category_mapping_yahoo_filename = expanduser('~') + '/Lab_TargetedAds/src/resources/category_mapping_yahoo.json'
  category_mapping_yahoo = {};
  
  category_mapping_alchemy_filename = expanduser('~') + '/Lab_TargetedAds/src/resources/category_mapping_alchemy.json'
  category_mapping_alchemy = {};
  
  def __init__(self):
    f = open(self.ad_db_filename);
    self.ad_db = json.load(f);
    f.close();
    f = open(self.redirection_db_filename);
    self.redirection_db = json.load(f);
    f.close();
    f = open(self.ad_providers_filename);
    self.ad_providers = json.load(f);
    f.close();
    
    f = open(self.category_mapping_alexa_filename);
    self.category_mapping_alexa = json.load(f);
    f.close();
    f = open(self.category_mapping_yahoo_filename);
    self.category_mapping_yahoo = json.load(f);
    f.close();
    f = open(self.category_mapping_alchemy_filename);
    self.category_mapping_alchemy = json.load(f);
    f.close();
    
    self.stats = Stats('Ad Extracting Statistics');
  
  def isAdProvider(self, url):
    host = url.split('?')[0];
    for i in range(len(self.ad_providers)):
      try: # In case of encode error
        if self.ad_providers[i] in host:
          return True;
      except:
        continue;
    return False;
  
  def getAdProviders(self, url):
    ret = [];
    for i in range(len(self.ad_providers)):
      try: # In case of encode error
        if self.ad_providers[i] in url and not self.ad_providers[i] in ret:
          ret.append(self.ad_providers[i]);
      except:
        continue;
    return ret;
  
  def getLandingUrl(self, url):
    if self.isAdProvider(url):
      return self.detectRedirection(url).lower();
    else:
      return url.lower();
    
  def getLandingDomain(self, url):
    return url2Domain(self.getLandingUrl(url));
  
  def detectRedirection(self, url):
    # return "NONE"; # If we don't want to detect redirection
    if url[:4] != "http":
      return 'NONE' # TODO: Handle flashvars, may need decoding.
    
    if url in self.redirection_db:
      self.stats.increment('Redirection DB hit', 1);
      return self.redirection_db[url];
    self.stats.increment('Redirection DB miss', 1);
    
    command = "~/Lab_TargetedAds/phantomjs/phantomjs--linux-x86_64/bin/phantomjs ~/Lab_TargetedAds/src/bin/detect_redirection.js '";
    command += url + "'";
    results = runCommand(command);
    self.stats.increment('Ad link clicked', 1);
    for i in range(len(results)):
      results[i] = results[i].split('\t');
      if len(results[i]) >= 3 and results[i][0] == '<MSG><RESULT>' and results[i][1] == "Destination":
        destination = results[i][2];
        if not self.isAdProvider(destination):
          if not url in self.redirection_db:
            self.redirection_db[url] = destination;
          return results[i][2];
    return "NONE";
  
  def outputRedirectionDb(self):
    f = open(self.redirection_db_filename, 'w');
    f.write(json.dumps(self.redirection_db).replace('], "', '],\n"'));
    f.close();
    
  def outputAdDb(self):
    f = open(self.ad_db_filename, 'w');
    f.write(json.dumps(self.ad_db).replace('], "', '],\n"'));
    f.close();
    
  def updateDb(self):
    self.outputRedirectionDb();
    self.outputAdDb();
  
  def getPageCategory(self, url):
    result = self.getPageRawCategory(url);
    if result == {}:
      return {};
    ret = {'source':'','category':[]};
    # Two levels for Alexa (e.g. Top/Shopping/Music)
    if result['source'] == 'Alexa':
      ret['source'] = 'Alexa';
      try:
        if type(result['category']) == list:
          for i in range(len(result['category'])):
            path = result['category'][i]['AbsolutePath'];
            refined_path = '/'.join(path.split('/')[:3]);
            # Ignore region-based categories
            if 'World' in refined_path or 'Region' in refined_path:
              continue;
            if not refined_path in ret['category']:
              ret['category'].append(refined_path);
        elif type(result['category']) == dict:
          path = result['category']['AbsolutePath'];
          refined_path = '/'.join(path.split('/')[:3]);
          ret['category'].append(refined_path);
      except:
        self.stats.increment('Category detection failed', 1);
        print 'ERROR PARSING:',result;
    # Ignore all scores for Yahoo
    elif result['source'] == 'Yahoo':
      ret['source'] = 'Yahoo';
      try:
        for i in range(len(result['category'])):
          cat = result['category'][i]['category'];
          if not cat in ret['category']:
            ret['category'].append(cat);
      except:
        self.stats.increment('Category detection failed', 1);
        print 'ERROR PARSING:',result;
    elif result['source'] == 'Alchemy':
      ret['source'] = 'Alchemy';
      ret['category'] = [result['category']];
    else:
      ret = {};
    if ret != {} and ret['source'] != '':
      self.stats.increment('Category detection succeeded', 1);
      ret['mapped_category'] = self.mapCategory(ret['source'], ret['category']);
    else:
      self.stats.increment('Category detection failed', 1);
    return ret;
  
  def getPageRawCategory(self, url):
    if url == None:
      return {};
    homepage = url2Homepage(url);
    if (url in self.ad_db) and (self.ad_db[url] != []) and (self.ad_db[url] != {}):
      self.stats.increment('Ad category DB hit', 1);
      return self.ad_db[url];
    if (homepage in self.ad_db) and (self.ad_db[homepage] != []) and (self.ad_db[homepage] != {}):
      self.stats.increment('Ad category DB hit', 1);
      return self.ad_db[homepage];
    self.stats.increment('Ad category DB miss', 1);
    # Alexa
    for i in range(3):
      self.stats.increment('Alexa queried', 1);
      ret = self.queryAlexa(url);
      if ret != {}:
        self.ad_db[url] = ret;
        return ret;
    for i in range(3):
      self.stats.increment('Alexa queried', 1);
      ret = self.queryAlexa(homepage);
      if ret != {}:
        self.ad_db[homepage] = ret;
        return ret;
    # Yahoo
    for i in range(2):
      self.stats.increment('Yahoo queried', 1);
      ret = self.queryYahoo(url);
      if ret != {}:
        self.ad_db[url] = ret;
        return ret;
    for i in range(2):
      self.stats.increment('Yahoo queried', 1);
      ret = self.queryYahoo(homepage);
      if ret != {}:
        self.ad_db[homepage] = ret;
        return ret;
    return ret;
    # Alchemy
    #ret = self.queryAlchemy(url);
    #self.stats.increment('Alchemy queried', 1);
    #if ret != {}:
    #  self.ad_db[url] = ret;
    #  return ret;
    #ret = self.queryAlchemy(url);
    #self.stats.increment('Alchemy queried', 1);
    #if ret != {}:
    #  self.ad_db[homepage] = ret;
    #  return ret;
    #return ret;
    
  def queryAlexa(self, url):
    php_url = "http://localhost/ad_detect/get_url_category.php";
    php_url += '?site=' + urllib2.quote(url);
    try:
      response = urllib2.urlopen(php_url);
      html = response.read();
      ret = json.loads(html)['Response']['UrlInfoResult']['Alexa']['Related']['Categories']['CategoryData'];
      # Check whether it's a single Top/World category
      if type(ret) == dict:
        path = ret['AbsolutePath'];
        refined_path = '/'.join(path.split('/')[:3]);
        if 'World' in refined_path or 'Region' in refined_path:
          return {};
      if type(ret) == list:
        empty = True;
        for i in range(len(ret)):
          path = ret[i]['AbsolutePath'];
          refined_path = '/'.join(path.split('/')[:3]);
          # Ignore region-based categories
          if not 'World' in refined_path and not 'Region' in refined_path:
            empty = False;
        if empty:
          return {};
      return {'source':'Alexa', 'category':ret};
    except:
      return {}
  
  def queryYahoo(self, url):
    try:
      query = 'SELECT * FROM contentanalysis.analyze WHERE url="' + url + '"';
      baseUrl = 'http://query.yahooapis.com/v1/public/yql?q=';
      fullurl = baseUrl + urllib2.quote(query);
      response = urllib2.urlopen(fullurl);
      html = response.read();
      ret = {};
      ret['source'] = 'Yahoo';
      ret['category'] = [];
      # Find all categories
      str = html;
      index = str.find('yctCategory score="');
      while index >= 0:
        str = str[index + 19:];
        category_bgn = str.find('>') + 1;
        category_end = str.find('<');
        category = str[category_bgn:category_end];
        parser = HTMLParser()
        category = parser.unescape(category);
        score = float(str.split('"')[0]);
        ret['category'].append({'category': category, 'score': score});
        index = str.find('yctCategory score="');
      if len(ret['category']) > 0:
        return ret;
      else:
        return {};
    except:
      return {};
  
  def queryAlchemy(self, url):
    alchemy_api_key = "beeb8469c6f7d1a0c7344dcee236d3e8ca71d53c";
    alchemy_api_url = "http://access.alchemyapi.com/calls/url/URLGetCategory";
    call_url = alchemy_api_url + "?apikey=" + alchemy_api_key;
    call_url += "&url=" + urllib2.quote(url);
    call_url += "&outputMode=json";
    try:
      response = urllib2.urlopen(call_url);
      html = response.read();
      ret = {};
      ret['source'] = 'Alchemy';
      ret['category'] = json.loads(html)['category'];
      if ret['category'] == 'unknown':
        return {};
      else:
        return ret;
    except:
      return {};
    
  def mapCategory(self, source, category):
    ret = []
    for i in range(len(category)):
      cat = category[i];
      if source == 'Alexa':
        while not cat in self.category_mapping_alexa and '/' in cat:
          cat = '/'.join(cat.split('/')[:-1]);
        if cat in self.category_mapping_alexa:
          for j in range(len(self.category_mapping_alexa[cat])):
            if not self.category_mapping_alexa[cat][j] in ret:
              ret.append(self.category_mapping_alexa[cat][j])
        else:
          print "MAPPING FAILED\tAlexa\t",cat
      elif source == 'Yahoo':
        if cat in self.category_mapping_yahoo:
          for j in range(len(self.category_mapping_yahoo[cat])):
            if not self.category_mapping_yahoo[cat][j] in ret:
              ret.append(self.category_mapping_yahoo[cat][j])
        else:
          print "MAPPING FAILED\tYahoo\t",cat
      elif source == 'Alchemy':
        if cat in self.category_mapping_alchemy:
          for j in range(len(self.category_mapping_alchemy[cat])):
            if not self.category_mapping_alchemy[cat][j] in ret:
              ret.append(self.category_mapping_alchemy[cat][j])
        else:
          print "MAPPING FAILED\tAlchemy\t",cat
    return ret;
      
  def __test__(self):
    print self.getPageCategory("http://www.microsoft.com");