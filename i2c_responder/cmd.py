class Cmd:
    
    """            
        To define a possible command
        
            import cmd
            cmd = cmd.Cmd(cmd_list,descr,func,(cmd_id,...))
            
        where
            cmd_list = the CmdList object to add this command to
            descr  = a description of what the command does
            func   = the function to execute when the command is invoked
            cmd_id = a list of one or more strings which will invoked the command
            
        Commands are then added to a command list which will identify and invoke
        the command function based on the cmd_id.
        
        The command defined here will be passed a parsed list of strings which consist of:
        
            [cmd] [[parm_1]...[parm_n]]
            
        where
            cmd = the command id
            parm_1... parm_n  = zero or more parameter strings passed to the command
    """

    # define a command.
    # cmdv is one or more command identifiers.
    
    def __init__(self,cmd_list,descr,func,cmd_id_list):
        self.descr = descr
        self.func  = func
        
        self.cmd_id_list = cmd_id_list
        
        self.cmd_list = cmd_list
        cmd_list.add(self)
        
    def exec_cmd(self,parms):
        self.func(parms)
        
    

