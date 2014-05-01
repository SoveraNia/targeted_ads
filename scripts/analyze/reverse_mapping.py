import sys;
import json;
import glob;

def checkArguments():
  if (len(sys.argv) < 2):
    print ("Usage:")
    print ("python reverse_mapping.py LOG_FILES");
    print "";
    print "Construct reverse mapping of trackers -> web pages."
    sys.exit(0);

country_code = ['ac','ad','ae','af','ag','ai','al','am','an','ao','aq','ar','as','at','au','aw','az','ba','bb','bd','be','bf','bg','bh','bi','bj','bm','bn','bo','br','bs','bt','bv','bw','by','by','bz','ca','cc','cd','cf','cg','ch','ci','ck','cl','cm','cn','co','cr','cs','cu','cv','cx','cy','cz','de','dj','dk','dm','do','dz','ec','ee','eg','eh','er','es','et','eu','fi','fj','fk','fm','fo','fr','ga','gd','ge','gf','gh','gi','gl','gm','gn','gp','gq','gr','gu','gt','gw','gy','hk','hm','hn','hr','ht','hu','id','ie','il','in','io','iq','ir','is','it','jm','jo','jp','ke','kg','kh','ki','km','kn','kp','kr','kw','ky','kz','la','lb','lc','li','lk','lr','ls','lt','lu','lv','ly','ma','mc','md','mg','mh','mk','ml','mm','mn','mo','mp','mq','mr','ms','mt','mu','mv','mw','mx','my','mz','na','nc','ne','nf','ng','ni','nl','no','np','nr','nt','nu','nz','om','pa','pe','pf','pg','ph','pk','pl','pm','pn','pr','ps','pt','pw','py','re','ro','ru','rw','sa','sb','sc','sd','se','sg','sh','si','sj','sl','sm','sn','so','sr','st','su','sv','sy','sz','tc','td','tf','tg','th','tj','tk','tm','tn','to','tp','tr','tt','tv','tw','tz','ua','ug','uk','um','us','uy','uz','va','vc','ve','vg','vi','vn','vu','ws','yu','za','zm','zr','zw'];

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

def main():
  checkArguments();
  
  mapping = {};
  
  log_files = glob.glob(sys.argv[1]);
  for i in range(len(log_files)):
    sys.stderr.write('Processing:\t' + log_files[i] + '\n')
    f = open(log_files[i]);
    lines = f.readlines();
    f.close();
    
    url = log_files[i].replace('-$$','://').replace("$",'/').replace(".txt",'');
    temp = url.split('_');
    url = temp[len(temp) - 1];
    category = log_files[i].split('_http')[0].split('Top-')[1].replace('-', '/');
    if not category in mapping:
      mapping[category] = {}
    for j in range(len(lines)):
      lines[j] = lines[j].replace('\n', '').split('\t');
      if len(lines[j]) >= 2 and lines[j][0] == '<TRACKER>':
        domain = url2Domain(lines[j][1]);
        if domain in mapping[category]:
          if not url in mapping[category][domain]: 
            mapping[category][domain].append(url);
        else:
          mapping[category][domain] = [url];
  # print num_distinct_trackers;
  # for key in sorted(mapping.iterkeys()):
  #   print key,'\t',mapping[key];
  print json.dumps(mapping);

if __name__ == "__main__":
  main();