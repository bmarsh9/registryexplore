def navigate_registry(self,cmd="pwd",cwd=r'System',hive="hklm"):
    obj = Registry_Read(hive)
    input = cmd.split()
    if input:
        output = ""            
        if input[0] in ("ls","dir"):
            path = cwd
            if len(input) > 1:
                path = " ".join(input[1:])
                if os.path.isabs(path):
                    drive,path = os.path.splitdrive(path)
                    path = path.lstrip("\\")
                else:
                    path = os.path.join(cwd,path)                                                                        
            contents = obj.list_contents(path)
            if contents:
                key,val = contents
                if key == "value":
                    val=filter_fields(val)
                    output+= "\n"
                    output+= str(to_tabulate(val,vertical=True))
                    output+= "\n"
                else:
                    output+= str(contents)
            else:
                output+= "Registry path does not exist!"                                            
        elif input[0] == "cd":
                if len(input) > 1:
                    path = " ".join(input[1:]).strip("\\")                    
                    if path == "..":
                        base = os.path.dirname(cwd)
                        cwd = base
                    else: #move into key                    
                        path = os.path.join(cwd,path)                                                                        
                        if os.path.isabs(path):
                            drive,path = os.path.splitdrive(path)
                            path = path.lstrip("\\")
                        if obj.key_exist(path): 
                            cwd = path                        
                            output+= "Changed registry path to: %s" % cwd
                        else:
                            output+= "Registry path does not exist!"
        return cwd,output 
            
cwd= r''
cmd="ls"
hive="hklm"
cwd,output = navigate_registry(cmd=cmd,cwd=cwd,hive=hive)            
while True:
    cmd = raw_input("Enter cmd: ")
    if cmd:
        cwd,output = navigate_registry(cmd=cmd,cwd=cwd,hive=hive)
        print output
