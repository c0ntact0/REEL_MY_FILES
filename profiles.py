from PySimpleGUI import UserSettings
from pprint import pprint

class Profiles(UserSettings):
    
    def __init__(self,filename,exclusions) -> None:
        super().__init__(filename)
        if not self['profiles']:
            self['profiles'] = {
                'default': {'name':'default'}
            }
            
            #self.set('profiles',profilesList)
            self.set('currentProfile','default')
        
        # keys to be excluded from save
        self._exclusions =  exclusions

    def dummyProfile(self):
        
        dummy = {
            "name":"",
            "project": "",
            "txtSourceFolderID": "",
            "txtDestinationFolderID": "",
            "ckFilterProfile": False,
            "listExtensionsID": [],
            "listCamerasID": []
        }
        
        return dummy
    
    def createProfileKey(self,name,project):
        return project + " - " + name
    
    def filterProject(self,project):
        keys = []
        profiles = self['profiles']
        for key in profiles.keys():
            if profiles[key]['project'] == project:
                keys.append(key)
        
        return keys
        
    def getProfilesKeys(self,project=None):
        
        keys=[]
        if project:
            keys = self.filterProject(project)
        else:
            keys = list(self['profiles'].keys())
    
        if keys:
            keys.sort()
            
        return keys
    
    
    def getCurrentProfileKey(self):
        return self.get('currentProfile','default')
    
    def setCurrentProfileKey(self,name):
        self.set('currentProfile',name)
    
    def getCurrentProfile(self):

        name = self.getCurrentProfileKey()
        if name:
            return self['profiles'][name]
        else:
            return self.dummyProfile()
    
    def saveProfile(self,values):
        currentProfile = self.getCurrentProfile()
        for key in values:
            if key in self._exclusions:
                continue
            currentProfile[key] = values[key]
        self.save()
        
    def addProfile(self,name,project,values):
        newProfile = {}
        newProfile['name'] = name
        newProfile['project'] = project
        for key in values:
            if key in self._exclusions:
                continue

            newProfile[key] = values[key]
        
        projectKey = self.createProfileKey(name,project) 
        self['profiles'][projectKey] = newProfile
        self.save()
    
    def deleteProfile(self):
        currentProfileName = self.getCurrentProfileKey()
        if self.count() > 1: 
            profiles = self['profiles']
            profiles.pop(currentProfileName)
            self['profiles'] = profiles
            self['currentProfile'] = self.getFirstProfileKey()
            self.save()
            return True
        
        return False
    
    def deleteProjectProfiles(self,project:str):
        profiles2delete = self.getProfilesKeys(project)
        profiles = self['profiles']
        for key in profiles2delete:
            print("Removing",key)
            profiles.pop(key)
        
        self['profiles'] = profiles
        self['currentProfile'] = self.getFirstProfileKey()
        self.save()
    
    def renameProfile(self,name):
        currentProfile = self.getCurrentProfile()
        currentProfileKey = self.getCurrentProfileKey()
        currentProfile['name'] = name
        self.save()
        profileKey = self.createProfileKey(name,currentProfile['project'])
        self['currentProfile'] = profileKey
        self['profiles'][profileKey] = self['profiles'].pop(currentProfileKey)
        self.save()
    
    def changeProfileProject(self,project):
        currentProfile = self.getCurrentProfile()
        currentProfileKey = self.getCurrentProfileKey()
        currentProfile['project'] = project
        self.save()
        profileKey = self.createProfileKey(currentProfile['name'],project)
        self['currentProfile'] = profileKey
        self['profiles'][profileKey] = self['profiles'].pop(currentProfileKey)
        self.save()
    
    def renameProject(self,projectToRename, newProjectName):
        profiles2Rename = self.getProfilesKeys(projectToRename)
        profiles = self['profiles']
        for key in profiles2Rename:
            thisProfile = self['profiles'][key].copy()
            profiles.pop(key)
            profileKey = self.createProfileKey(thisProfile['name'],newProjectName)
            thisProfile['project'] = newProjectName
            profiles[profileKey] = thisProfile
        
        self.save()
                
    def cloneProfiles(self,projectToClone,newProject):
        profiles2Clone = self.getProfilesKeys(projectToClone)
        profiles = self['profiles']
        for key in profiles2Clone:
            thisProfile = self['profiles'][key].copy()
            profileKey = self.createProfileKey(thisProfile['name'],newProject)
            thisProfile['project'] = newProject
            profiles[profileKey] = thisProfile
            
        self.save()
            
            
            
        
    def profileExists(self,key: str):
        if not self['profiles']:
            return False
        for k in self['profiles']:
            if (k.upper() == key.upper()):
                return True
            
        return False
    
    def getProfileName(self):
        """
        Returns the profile name values, not the profile key
        """
        currentProfile = self.getCurrentProfile()
        return currentProfile['name']
    
    def getProfileProject(self, profile:str = None):
        currentProfile = self['profiles'][profile] if profile else self.getCurrentProfile()
        return currentProfile['project']
    
    def count(self):
        return len(list(self['profiles'].keys()))
    
    def getFirstProfileKey(self):
        return list(self['profiles'].keys())[0]
    
    def haveSamePaths(self,otherProfileKey:str):
        """
            Compares the paths of the current profile with the paths of other profile
            
            Arguments:
                otherProfileKey: the key of the orther profile
        """
        currentProfile = self.getCurrentProfile()
        otherProfile = self['profiles'][otherProfileKey]
        if not (currentProfile or otherProfile):
            return False
        if currentProfile.get('txtSourceFolderID') == otherProfile.get('txtSourceFolderID') \
            and currentProfile.get('txtDestinationFolderID') == otherProfile.get('txtDestinationFolderID'):
                return True
            
        return False
        