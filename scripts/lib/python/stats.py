###################################
# Statistics
###################################
class Stats:
  def __init__(self, title = 'Statistics'):
    self.title = title;
    self.stats = {};
  def setTitle(self, title):
    self.title = title;
  def increment(self, key, value):
    if key in self.stats:
      self.stats[key] += value;
    else:
      self.stats[key] = value;
  def output(self):
    print '===== ' + self.title + ' ====='
    for key in self.stats:
      print key,'\t',self.stats[key];