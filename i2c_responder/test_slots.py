"""
    test slots in micropython
"""

import mem_use

class Obj(object):
  __slots__ = ('i', 'l')
  def __init__(self, i):
    self.i = i
    self.l = []
    
print("before: " + mem_use.free())

all = {}
for i in range(1000):
  all[i] = Obj(i)
  

print("after: " + mem_use.free())