from winreg import HKEY_LOCAL_MACHINE,HKEY_USERS,OpenKey,EnumKey,EnumValue,KEY_READ,HKEY_CURRENT_USER,KEY_WOW64_32KEY,KEY_WOW64_64KEY,QueryInfoKey,QueryValueEx,ConnectRegistry
from tabulate import tabulate
tabulate.PRESERVE_WHITESPACE = True
import operator
import os 

def to_tabulate(data,vertical=False):
        '''
        :data=[{"header1":"value1"}]
        '''
        data_list = []
        headers = []    
        if not isinstance(data,list):
            data = [data]
        for each in data:
            if vertical:
                headers = ["Key","Value"]            
                for k,v in each.items():                    
                    data_list.append([str(k),str(v)])

                data_list.append(["--------------------------------------------","--------------------------------------------"])
            else:        
                if not headers: # set headers on the first record
                    headers=each.keys()
                temp = []
                for col in headers:
                    e = each.get(col,"missing keys")
                    
                    value = str(e)                   
                    temp.append(value)
                if temp:
                    data_list.append(temp)         
        return tabulate(data_list,headers=headers)

def filter_op(data,filter=[],case_insen=True): 
    op_map = {
        "eq":operator.eq,
        "ne":operator.ne
    }  
    if not filter:
        return data
    if isinstance(data,dict):
        for filt in filter:
            k,op,v = filt
            if case_insen:
                k = k.lower()
                if isinstance(v,str):
                    v = v.lower()
            if not op_map[op](data[k],v):
                return None
        return data
                        
def filter_fields(data,filter=[],exc=[],inc=[],case_insen=True):
    inc = [x.lower() for x in inc if inc]
    exc = [x.lower() for x in exc if exc]
    dataset = []    
    if not isinstance(data,list):
        data = [data]
    for record in data:
        if filter_op(record,filter):
            temp_dict = {}
            for key,value in record.items():
                if case_insen:                
                    key = key.lower()
                    if isinstance(value,str):                        
                        value = value.lower()
                if key not in exc:                    
                    if not inc:
                        temp_dict[key] = value                        
                    elif key in inc:
                        temp_dict[key] = value
            dataset.append(temp_dict)
    return dataset
    
class Registry_Read():

    def __init__(self, const):
        HIVE = {
            "hklm":HKEY_LOCAL_MACHINE,
            "hkcu":HKEY_CURRENT_USER,
            "hku":HKEY_USERS
        }
        self.const = HIVE[const]

    def key_exist(self,keypath):
        try:
            ob = OpenKey(self.const, keypath, 0, KEY_READ)
            return True
        except:
            return None

    def list_contents(self,keypath):
        if self.key_exist(keypath):
            attrib = self.get_values(keypath)
            if not attrib:
                return "key",self.get_subkeys(keypath)
            return "value",attrib
        return None

    def get_subkeys(self, keypath):
        keys = None
        try:
            ob = OpenKey(self.const, keypath, 0, KEY_READ)
            keys = self.get_subattribs('key', ob)
        except Exception as e:
            print("Exception occured :- {}, key path :- {}".format(e, keypath))
        return keys

    def get_values(self, keypath):
        dict = {}
        try:
            with OpenKey(self.const, keypath, 0, KEY_READ) as subkey:
                v = self.get_subattribs('values',subkey)
                for each in v:
                    dict[each[0]] = each[1]
        except Exception as e:
            print("Exception occured :- {}, key path :- {}".format(e, keypath))
        return dict

    def get_subattribs(self, attrib_name, ob):
        count = 0
        attrib = []        
        while True:
            try:
                subattribs = EnumKey(ob, count) if attrib_name is 'key' else EnumValue(ob, count)
                attrib.append(subattribs)
                count+=1
            except WindowsError as e:
                break
        return attrib
        
    def get_all_values(self,keypath):
        full_list = []
        for keyname in self.get_subkeys(keypath):
            sub_values = self.get_values(os.path.join(keypath,keyname))
            temp = {}
            for attr,value in sub_values.items():
                temp[attr] = value
            if temp:
                temp["keyname"] = keyname
                full_list.append(temp)        
        return full_list
        
    def createRegistryParameter(self,keypath,argname,argvalue):
        newkey=win32api.RegOpenKeyEx(win32con.self.const, keypath,0,win32con.KEY_ALL_ACCESS)
        try:
            win32api.RegSetValueEx(newkey, argname, 0, win32con.REG_SZ, argvalue)
        finally:
            newkey.Close() 

def eformat(a, b):
    fmt = '%-40s %s\n' % (str(a), str(b)) 
    return fmt
  
def navigate_reg(cwd=None,hive="hklm"):
    obj = Registry_Read(hive)
    if cwd is None:
        cwd= r'System'

    while True:
        prompt = "cwd: R:\%s>" % (cwd)
        start = input("{}: ".format(prompt))
        input_by_user = start.split()
        if input_by_user:
            path,key = os.path.split(cwd)
            data = obj.get_subkeys(cwd)
            if input_by_user[0] in ("ls","dir"):
                if isinstance(data,list) and not data: # reached the end of a key
                    print("\n")
                    print("Displaying values of the key: %s" % (key))
                    print(to_tabulate(obj.get_values(cwd),vertical=True) )
                    print("\n")
                elif len(input_by_user) > 1: 
                    path = input_by_user[1]
                    if os.path.isabs(path):
                        drive,path = os.path.splitdrive(path)
                        ls = path.lstrip("\\")
                        print(ls)
                        contents = obj.list_contents(ls)
                        if contents:
                            k,v = contents
                            if k == "value":
                                v=filter_fields(v)
                                print(to_tabulate(v,vertical=True))
                            else:
                                print(contents)
                        else:
                            print("Registry path does not exist!")                          
                    
                else:
                    print(data)        
            elif input_by_user[0] == "cd":
                    if len(input_by_user) > 1:
                        path = input_by_user[1]
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
                                print("Changed registry path to: %s" % cwd)
                            else:
                                print("Registry path does not exist!")
            else:
                pass
        #elif input_by_user[0]
                                     
        
navigate_reg()    

#Manual Testing
#obj = Registry_Read("hklm")
#keypath = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
#data=obj.get_all_values(keypath)
#base,data = obj.list_contents(keypath)
