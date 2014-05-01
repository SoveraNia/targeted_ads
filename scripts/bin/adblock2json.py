#!/bin/python

import sys;
import json;
import subprocess;

def checkArguments():
  if (len(sys.argv) < 2):
    print "Usage:"
    print "python adblock2json.py INPUT_FILE";
    print "";
    print "Transform Adblock's filter rules to JSON objects";
    sys.exit(0);

checkArguments();

input_file = str(sys.argv[1]);
f = open(input_file);
lines = f.readlines();
f.close();

result = {}
result["url-matcher"] = [];
result["element-matcher"] = [];
result["url-exception"] = [];
result["element-exception"] = [];
result["elemhide"] = [];

def filter2RegExp(filter):
  ret = filter.replace('.', '\\.').replace('*', '.*').replace('+', '.+').replace('^', '\\b');
  return ret;

def extractElement(element):
  ret = {};
  
  selector = "";
  attributes = [];
  
  if (element.find("[") >= 0):
    selector = element[:element.find("[")];
    attributes = element[element.find("["):].replace('[', '').split(']');
  else:
    selector = element;
  
  # Selector
  if (selector != ""):
    if (selector[0] == "."):
      ret['class'] = selector[1:];
    elif (selector[0] == "#"):
      ret['id'] = selector[1:];
    else:
      ret['tag'] = selector;
  
  # Attributes
  ret["attributes"] = [];
  for i in range(len(attributes)):
    key = attributes[i][:attributes[i].find('=')];
    value = attributes[i][attributes[i].find('=') + 1:];
    if (attributes[i].find('=') < 0):
      key = attributes[i];
      value = "";
    
    if (key == ""):
      continue;
    if (value != "" and value[0] == '"' and value[-1:] == '"'):
      value = value[1:-1];
    
    attr = {};
    
    if (key[-1:] == "^"):
      key = key[:-1];
      attr["first"] = True;
    elif (key[-1:] == "$"):
      key = key[:-1];
      attr["last"] = True;
    elif (key[-1:] == "*"):
      key = key[:-1];
      attr["include"] = True;
    
    attr['key'] = key;
    attr['value'] = value;
    ret['attributes'].append(attr);
  
  return ret;

def extractFilter(line, exception):
  ret = {};
  
  addresses = [];
  options = [];
  element = "";
  element_filter = False;
  elemhide_filter = False;
  
  # Element exceptions
  if (line.find('#@#') >= 0):
    line = line.replace('#@#', '##');
    exception = True; 
  
  if (line.find('##') >= 0):
    addresses = line.split('##')[0].split(',');
    element = line.split('##')[1];
    ret['element'] = {};
  elif (line.find('$') >= 0):
    addresses = line.split('$')[0].split(',');
    options = line.split('$')[1].split(',');
    ret['options'] = {};
  else:
    addresses = [line];
  
  # Address
  for i in range(len(addresses)):
    address = addresses[i];
    if (address == ""):
      continue;
    # By address part
    ret['address-part'] = [];
    ret['address-exception'] = [];
    if address[0] != "|" and address[0] != "@":
      if address[0] != "~":
        ret['address-part'].append(filter2RegExp(address));
      else:
        ret['address-exception'].append(filter2RegExp(address));
    # By domain
    elif address[:2] == "||":
      ret['domain'] = filter2RegExp(address[2:]);
    # By exact address
    elif line[0] == "|" and line[len(line) - 1] == "|":
      ret['address-exact'] = address[1:-1];
  
  # Elements
  if (element != ""):
    element_filter = True;
    if (element.find(' > ') >= 0):
      ret['element']['enclosed-in'] = [];
      elements = element.split(' > ');
      for j in range(len(elements)):
        ret['element']['enclosed-in'].append(extractElement(elements[j]));
    elif (element.find(' + ') >= 0):
      ret['element']['preceded-by'] = [];
      elements = element.split(' + ');
      for j in range(len(elements)):
        ret['element']['preceded-by'].append(extractElement(elements[j]));
    else:
      ret['element']['selector'] = extractElement(element);
  
  # Options
  for i in range(len(options)):
    option = options[i];
    if (option[:7] == "domain="):
      domains = option[7:].split('|');
      ret["options"]["domains"] = [];
      ret["options"]["domains-exception"] = [];
      for k in range(len(domains)):
        if domains[k][0] == '~':
          ret["options"]["domains-exception"].append(domains[k][1:]);
        else:
          ret["options"]["domains"].append(domains[k]);
    else:
      if (option[0] == '~'):
        ret["options"][option[1:]] = False;
      else:
        ret["options"][option] = True;
        if (option == "elemhide"):
          elemhide_filter = True;        
  
  if (elemhide_filter == False):
    if (exception == True and element_filter == True):
      result["element-exception"].append(ret);
    elif (exception == False and element_filter == True):
      result["element-matcher"].append(ret);
    elif (exception == True and element_filter == False):
      result["url-exception"].append(ret);
    elif (exception == False and element_filter == False):
      result["url-matcher"].append(ret);
  else:
    result["elemhide"].append(ret);
  
  return ret;

def main():
  for i in range(len(lines)):
    line = lines[i].replace('\n', '');
    
    # Comment line
    if line[0] == "!" or line[0] == "[":
      continue;
    # Exceptions
    if line[:2] == "@@":
      isException = True;
      line = line[2:];
      extractFilter(line, True);
    else:
      extractFilter(line, False);
  
  print json.dumps(result);
  
main();
  