#!/bin/python

import sys;
import json;
import time;
import subprocess;

def checkArguments():
  if (len(sys.argv) < 5):
    print "Usage:";
    print "python generate_dataset.py BASE_CATEGORY LEVEL_OF_CATEGORIES COUNT OUTPUT_DIR";
    print "";
    print "For each Alexa's LEVEL_OF_CATEGORIES-level sub-categories of the BASE_CATEGORY, write COUNT urls into a file for each sub-category. Files are stored in OUTPUT_DIR";
    sys.exit(0);

getCategoryListingPhp = "~/Lab_TargetedAds/src/bin/get_category_listing.php";
getCategoriesPhp = "~/Lab_TargetedAds/src/bin/get_categories.php";
minListings = 1000;

def getCategoryListing(category, start, count):
  success = False;
  numRetries = 0;
  data = None;
  while (success == False) and (numRetries < 3):
    command = "php " + getCategoryListingPhp + " " + category + " " + str(start) + " " + str(count);
    print command;
    p = subprocess.Popen(command, shell = True, stdout = subprocess.PIPE);
    temp = p.communicate()[0];
    try:
      data = json.loads(temp);
      success = True;
    except:
      numRetries += 1;
      print "Retry: " + str(numRetries);
  
    ret = [];
  if data != None:
    listings = data['Response']['CategoryListingsResult']["Alexa"]["CategoryListings"]["Listings"];
    
    if 'Listing' in listings:
      listings = listings['Listing'];
    else:
      return [];
    if type(listings) != list:
      listings = [listings];
  
    for i in range(len(listings)):
      ret.append(listings[i]['DataUrl']);
  
  return ret;
 
def getTopSitesInCategory(category, count, output_dir):
  if count == 0:
    print category.encode('utf8');
    return "";
  # Compute result
  start = 1;
  result = [];
  for i in range(count/20 + 1):
    num = 20;
    if count - (20 * i) < 20:
      num = count - (20 * i);
    if (num > 0):
      result += getCategoryListing(category, start, num);
      time.sleep(1);
      start += 20;
  
  # Write to file
  filename = output_dir + '/' + category.replace('/', '-') + '_' + str(count) + '.txt';
  print "Writing " + filename;
  f = open(filename, 'w');
  for i in range(len(result)):
    f.write((result[i] + '\n').encode("utf-8"));
  f.close();
  
  return result;

def getSubCategories(category, level, count):
  print "Getting sub-categories of " + category;
  if category == "Top/World" or category == "Top/Regional":
    return [];
  
  command = "php " + getCategoriesPhp + " " + category;
  p = subprocess.Popen(command, shell = True, stdout = subprocess.PIPE);
  temp = p.communicate()[0];
  
  data = json.loads(temp);
  categories= data['Response']["CategoryBrowseResult"]["Alexa"]["CategoryBrowse"]["Categories"];
  
  if 'Category' in categories:
    categories = categories['Category'];
  else:
    return [category]; 
  if type(categories) != list and categories != {}:
    categories = [categories];
  
  ret = []
  if (level == 1):
    for i in range(len(categories)):
      if categories[i] != {} and categories[i]['TotalListingCount'] !={} and (int(categories[i]['TotalListingCount']) >= minListings or count == 0):
        ret.append(categories[i]['Path']);
    return ret;
  else:
    for i in range(len(categories)):
      if categories[i] != {} and (categories[i]['TotalListingCount'] =={} or int(categories[i]['TotalListingCount']) >= minListings or count == 0) and int(categories[i]['SubCategoryCount'] > 0):
        ret += getSubCategories(categories[i]['Path'], level - 1, count);
      else:
        ret.append(categories[i]['Path']);
    return ret;

def main():
  checkArguments();
  
  base_category = sys.argv[1];
  level = int(sys.argv[2]);
  count = int(sys.argv[3]);
  output_dir = sys.argv[4];
  
  if level > 0:
    categories = getSubCategories(base_category, level, count);
    for i in range(len(categories)):
      getTopSitesInCategory(categories[i], count, output_dir);
  else:
    getTopSitesInCategory(base_category, count, output_dir);

if __name__ == "__main__":
  main();