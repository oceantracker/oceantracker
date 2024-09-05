from os import  path
from glob import glob, iglob

all_lines=[]
def_lines=[]
def_file=[]
for filename in iglob('../**/*.py',   recursive = True):
    #print(filename)
    with open(filename, 'r', encoding="utf8") as f:
            lines = f.readlines()

    for l in lines:
        if 'def ' in l:
            def_lines.append(l.strip())
            def_file.append(filename)
        else:
            if l !='\n': # remove blank lines
                all_lines.append(l.strip())
no_refs=[]
for n, dl in enumerate(def_lines):
    s=dl.split(' ')[1].split('(')[0] +'('
    e=[]
    for l in all_lines:
        if s in l:
            e.append(l)
    if len(e) ==0:
        no_refs.append(n)

for n in no_refs:
    l = def_lines[n]
    fn =def_file[n]
    if 'def demo' in l or 'def is_' in l or 'dev_' in l or 'dev_' in fn: continue
    print(l,2*'\t',fn)

pass




