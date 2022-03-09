import gc
import os

# disk free space
def df():
  s = os.statvfs('//')
  blk_size = s[0]
  total_mb = (s[2] * blk_size) / 1048576
  free_mb  = (s[3] * blk_size) / 1048576
  pct = free_mb/total_mb*100
  # return ('Disk Total: {0:.2f} MB Free: {1:.2f} ({2:.2f}%)'.format(total_mb, free_mb, pct))
  return ('DFr {0:.2f}MB {1:.0f}%'.format(free_mb, pct))

def free(full=False):
  F = gc.mem_free()
  A = gc.mem_alloc()
  T = F+A
  P = '{0:.0f}%'.format(F/T*100)
  if not full: return P
  else : return ('MFr {0:,} {1}'.format(F,P))
  
def print_stats():
    print(df())
    print(len(df()))
    print(free(full=True))
    print(len(free(full=True)))

print_stats()