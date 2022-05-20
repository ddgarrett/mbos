import cmd
import cmd_list
import sys

cl = cmd_list.CmdList()

def cmd_quit(l):
    sys.exit()
    
def cmd_nop(l):
    print(l)
    
cmd.Cmd(cl,"quit",cmd_quit,("q","quit"))
cmd.Cmd(cl,"noop",cmd_nop,("n","nop"))

# cl.add(c)

while True:
    cl.input_cmd()
    
    
