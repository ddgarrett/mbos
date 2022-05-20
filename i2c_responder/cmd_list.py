
class CmdList:
    
    """
        Define a list of possible commands.
        
        Example:
        
            import cmd
            import cmd_list
            
            cmd_list = cmd_list.CmdList()
            
            cmd = cmd.Cmd("description",function,["c1","c2"]
            cmd_list.add(cmd)
            ... add more possible commands
            
            input_str = input("cmd >>")
            cmd_list.exec_cmd(input_str)
            
        
        Commands consisting of of a string with:
        
            [cmd] [[parm_1]...[parm_n]]
            
            cmd - Command identifier. Should be unique.
            parm_1 through
            parm_n - 0 to n parameters
            
    """
    
    def __init__(self,prompt="cmd: "):
        self.cmd_dict = {}  # dictionary of command id to index in cmd_func
        self.cmd_list = [] # list of commands
        self.prompt = prompt # prompt to use with input
        
    def add(self,cmd):
        self.cmd_list.append(cmd)
        # print(cmd.cmd_id_list)
        for cmd_id in cmd.cmd_id_list:
            # print(cmd_id)
            self.cmd_dict[cmd_id] = cmd
            
    # print help text for commands
    def help(self):
        for cmd in self.cmd_list:
            cmd.print_help()
            
    # excute a command
    def exec_cmd(self,cmd_str):
        parms = cmd_str.split(" ")
        
        if not (parms[0] in self.cmd_dict):
            print("uncrecognized command: " + parms[0])
            return parms
        
        cmd = self.cmd_dict[parms[0]]
        cmd.exec_cmd(parms)
        return parms
        
    def input_cmd(self):
        c = input(self.prompt)
        return self.exec_cmd(c)

        
        
        
        