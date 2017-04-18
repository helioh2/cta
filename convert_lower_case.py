


f = open("simulator.py","r")
fw = open("simulator2.py","w")

import re

def convert(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

code = f.read()
code2 = convert(code)

fw.write(code2)

f.close()
fw.close()