import sys;

f = open(sys.argv[1]);
lines_1 = f.readlines();
f.close();

f = open(sys.argv[2]);
lines_2 = f.readlines();
f.close();

for i in range(len(lines_1)):
  lines_1[i] = lines_1[i].replace('\n','');
for i in range(len(lines_2)):
  lines_2[i] = lines_2[i].replace('\n','');
  
for i in range(len(lines_1)):
  if lines_1[i] in lines_2:
    print lines_1[i];