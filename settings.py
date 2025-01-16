from PySimpleGUI import UserSettings
from pprint import pprint

class Settings(UserSettings):
    def __init__(self, filename=None, path=None, silent_on_error=False, autosave=True, use_config_file=None, convert_bools_and_none=True):
        super().__init__(filename, path, silent_on_error, autosave, use_config_file, convert_bools_and_none)
        
       
    def addListItem(self,item:str,listId:str):
        if not self[listId]:
            self[listId] = []
        
        self[listId].append(item)
        self[listId].sort()
        self.save()
        
    def deleteListItem(self,items:list,listId:str):

        for item in items:
            self[listId].remove(item)
        
        self.save()
        
    def listItemExists(self,item: str,listId:str):
        if not self.get(listId,False):
            return False
        for v in self[listId]:
            if v.upper() == item.upper():
                return True
        
        return False
    
    
    def countList(self,listId:str):
        
        return len(self[listId])
    
    def isEmptyList(self,listId:str):
        
        return self.countList(listId) == 0 
        