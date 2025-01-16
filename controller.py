import os
import hashlib
import xxhash
import datetime
from pprint import pprint
from enum import StrEnum,unique,auto
from settings import Settings
from profiles import Profiles
import shutil
import PySimpleGUI as sg
import time
import json
import statistics

INGEST_SETTINGS_FILENAME = "ingest_settings.json"

@unique
class ReelStatus(StrEnum):

    # Thread control
    KEY = "REEL_THREAD_KEY"
    STARTING = "REEL_THREAD_STARTING"
    COPYING = "REEL_THREAD_COPYING"
    COUNTING = "REEL_THREAD_COUNTING"
    COUNTING_FILES = "REEL_THREAD_COUNTING_FILES"
    FAILED = "REEL_THREAD_FAILED"
    SUCCESS = "REEL_THREAD_SUCCESS"
    CANCELED = "REEL_THREAD_CANCELED"
    EXIT = "REEL_THREAD_EXIT"
    # internal control
    COUTING_FILES_CANCELED = auto()
    RUNNING = auto()
    STOPED = auto()
    
@unique
class SourceTypes(StrEnum):
    FOLDER_CAM_INCLUDE = "radioIncludeCameras"
    FOLDER_CAM_EXCLUDE = "radioExcludeCameras"
    CARD_NOT_RENAME = "radioNotRenameCard"
    CARD_RENAME = "radioRenameCard"

@unique
class RenameHashGenerator(StrEnum):
    FILEPATH_PLUS_FILEMDATE = "radioFilepathHash"
    FILE_HASH = "radioFilehHash"

class HashAlgorithms:
    """
        This class avoids the need to have logic decisions to choose the algorithm to use.
        Joins the xxhash lib and the hashlib in one class. 
    """
    
    def __init__(self,algorithm:str = None) -> None:
        
               
        self._algorithm = algorithm
        self._algorithms = {
            "xxHash64" : xxhash.xxh64(),
            "MD5" : hashlib.md5()            
        }
        self._algorithmObj = self._algorithms.get(algorithm,None)
    
    @property
    def algorithms(self):
        return self._algorithms

    def algorithmsList(self):
        return list(self._algorithms.keys())
        
    @property
    def algorithm(self):
        return self._algorithm
    
    @algorithm.setter
    def algorithm(self,algorithm:str):
        self._algorithm=algorithm
        self._algorithmObj = self.algorithms.get(algorithm,None)
    
    def update(self,data):
        """
            Reimplementation (kind of) of algorithms update methods
        """
        if self._algorithmObj:
            return self._algorithmObj.update(data)
        
        return None
    
    def hexdigest(self):
        """
            Reimplementation (kind of) of algorithms hexdigest methods
        """        
        return self._algorithmObj.hexdigest()
    
    def createAlgorithmObj(self,algorithm:str):
        """
            Return a hash object of type "algorithm"
        """
        return self._algorithms[algorithm]
    
    def getHexDigest(self,data):
        """
            Calculates and return a hexdigest string
        """
        self._algorithmObj.update(data)
        return self._algorithmObj.hexdigest()
                
    
    
class Controller:
    def __init__(self) -> None:
        self._fileMetadata = None

        self._reelFilesStatus = ReelStatus.STOPED
        self._humanReadbleDivider = 1024*1024 # MBytes
        self._humanReadbleName = "MBytes"
        self._mimesList =[]
        self._cameras = []
        self._renamedFiles = 0
        self._sourceType = SourceTypes.FOLDER_CAM_INCLUDE      
        self._filesHash = {}
        self._hashaAgorithmRename = ""
        self._hashAlgorithmChecksum = ""
        self._renameHashType = RenameHashGenerator.FILE_HASH
        
        self._work_id = ""

    @property
    def fileMetadata(self):
        return self._fileMetadata
    
    @fileMetadata.setter
    def fileMetadata(self,metadata):
        self._fileMetadata = metadata
    
    @property
    def reelFilesStatus(self):
        return self._reelFilesStatus    
    
    @reelFilesStatus.setter
    def reelFilesStatus(self,status):
        self._reelFilesStatus = status
    
    def getFileCreationDate(self,fieldSeparator = "_"):
        return self._fileMetadata.dateTime.date + fieldSeparator + self._fileMetadata.dateTime.time
    
    def createFileHash(self,filePath:str, addToDict=True,checksum=True):
        hexDigest = self._filesHash.get(filePath,None)
        if not hexDigest:
            hashObj = HashAlgorithms(self._hashAlgorithmChecksum if checksum else self._hashaAgorithmRename)
            
            with open(filePath, "rb") as f:
                for chunk in iter(lambda: f.read(1024*1024), b""): # 1MByte
                    hashObj.update(chunk)
            
            hexDigest = hashObj.hexdigest()
            if addToDict:
                self._filesHash[filePath] = hexDigest
             
        return hexDigest
    
    def ckeckSum(self,source:str,destination:str):
        
        hash_source = self.createFileHash(source)
        hash_destination = self.createFileHash(destination,False)
                
        return hash_source == hash_destination
    
    def getReelFilename(self,filename:str, # nome do ficheiro original (name)
                        sourceRoot:str, # pasta do ficheiro original (root)
                        destinationRoot:str, # pasta de destino
                        sourcePath:str # path de origem com filename

                        ):
        
        st = self._sourceType
        rht = self._renameHashType
        _,ext = os.path.splitext(filename)
        if ext.upper() in self._mimesList:
            cameraFolderExits = False
            if st != SourceTypes.CARD_NOT_RENAME: 
                if st != SourceTypes.CARD_RENAME:
                    for c in self._cameras:
                        rootArray = sourceRoot.split(os.path.sep) # garante igualdade na palavra e não em parte
                        if c in rootArray:
                            cameraFolderExits = True
                            break
                    
                if (cameraFolderExits and st == SourceTypes.FOLDER_CAM_INCLUDE) or \
                    (not cameraFolderExits and st == SourceTypes.FOLDER_CAM_EXCLUDE) or \
                    st == SourceTypes.CARD_RENAME:

                    self._renamedFiles+=1
                    if st == SourceTypes.CARD_RENAME or rht == RenameHashGenerator.FILE_HASH:
                        hashDigest = self.createFileHash(sourcePath,self._hashAlgorithmChecksum == self._hashaAgorithmRename,False)
                        
                    else:
                    
                        mtime = os.path.getmtime(sourcePath)
                        str2hash = sourcePath + str(mtime)
                        hashObject = HashAlgorithms(self._hashaAgorithmRename)
                        hashDigest = hashObject.getHexDigest(str2hash.encode())
                        
                    file,ext = os.path.splitext(filename)
                    reelFilename = file + "_" + hashDigest + ext
                    return os.path.join(destinationRoot,reelFilename)
        
        return os.path.join(destinationRoot,filename)
        
    
    def humanReadable(self,bytesNum,humanReadbleDivider=1024**2,humanReadbleName="MBytes"):
        return "{:.3f}".format(bytesNum/humanReadbleDivider) + " " + humanReadbleName
    
    def testFilePart(self,pathname,filename):
        """
            Texts if the original part of filename, without hash, exists in the pathname folder.
            
        """
        filenameSplitExt = os.path.splitext(filename)
        for root, dirs, files in os.walk(pathname):
             for name in files:
                 nameSplitExt = os.path.splitext(name)
                 if name.startswith(filenameSplitExt[0]) and nameSplitExt[1] == filenameSplitExt[1]:
                     return True
        return False
    
    
    
    
    def countSourceFiles(self,window,origem,destino=None,preChecksum=False):
        """
            Se destino=None não exclui ficheiros já existentes no destino da contagem
        """     
        totalFileNumber = 0
        for root, dirs, files in os.walk(origem):
            for name in files:
                if name.startswith("._"):
                    continue
                totalFileNumber+=1
                
        destRoot = os.path.join(destino, os.path.basename(origem)) if destino else None
        filesNumber = 0
        filesSize = 0
        progressFilesNumber = 0
        for root, dirs, files in os.walk(origem):
            thisDestRoot = root.replace(origem,destRoot) if destino else None
            for name in files:
                if destino and self._reelFilesStatus == ReelStatus.CANCELED:
                    self._reelFilesStatus = ReelStatus.COUTING_FILES_CANCELED
                    return (0,0)
                if name.startswith("._"):
                    continue
                progressFilesNumber+=1
                msg = "Comparing source and destination files...\n" + str(totalFileNumber-progressFilesNumber) + " files remaining."
                window.write_event_value((ReelStatus.KEY,ReelStatus.COUNTING),(progressFilesNumber,msg,totalFileNumber,self._work_id))
                origemPath = os.path.join(root,name)
                               
                if destino and self.testFilePart(thisDestRoot,name):
                    pathDest = self.getReelFilename(name,root,thisDestRoot,origemPath) if destino else None
                    if preChecksum and (os.path.exists(origemPath) and os.path.exists(pathDest)) and not self.ckeckSum(origemPath,pathDest):
                        os.remove(pathDest)
                    else:    
                        continue
                filesNumber+=1
                filesSize+=os.path.getsize(origemPath)
                
        return (filesNumber,filesSize)
    
    def setSourceType(self,profile):
        for st in SourceTypes:
            if profile[st]:
                self._sourceType = st
                break
        
    def setRenameHashType(self,settings):
        for rht in RenameHashGenerator:
            if settings[rht]:
                self._renameHashType = rht
                break
    
    def createDestinationFolder(self,source:str,destination:str,addSourceToDest:bool):
        
        return os.path.join(destination,os.path.basename(source)) if addSourceToDest else destination
    
    def reelFiles(self,origem:str,destino:str,settings:Settings,profile:Profiles,window:sg.Window,work_id:str):
        self._work_id = work_id
        self._filesHash.clear()
        self._hashaAgorithmRename = settings.get('cbAlgorithmRename')
        self._hashAlgorithmChecksum = settings.get('cbAlgorithmChecksum')
        postChecksum = settings.get('ckPostChecksum',True)
        preChecksum = settings.get('ckPreChecksum',True)
        
        self._cameras = profile.get('listProfileCamerasID',[])
        mimes = settings.get('listExtensionsID',[])
        self._mimesList=["." + x.upper() for x in mimes]
        
        self.setSourceType(profile)
        self.setRenameHashType(settings)
                
        msg = ""
        self._reelFilesStatus = ReelStatus.RUNNING

        if not os.path.exists(origem):
            msg = "Source path does not exist!"
            self._reelFilesStatus = ReelStatus.FAILED
        elif not os.path.exists(destino):
            msg = "Destination path does not exist!"    
            self._reelFilesStatus = ReelStatus.FAILED
                
        if self._reelFilesStatus == ReelStatus.FAILED:
            window.write_event_value((ReelStatus.KEY,ReelStatus.EXIT),self._work_id)
            window.write_event_value((ReelStatus.KEY,ReelStatus.FAILED),(msg,self._work_id))
            return
                
        destRoot = self.createDestinationFolder(origem,destino,profile.get('ckAddSourceBasename',True)) #os.path.join(destino, os.path.basename(origem))
        
        # get number of files to copy
        window.write_event_value((ReelStatus.KEY,ReelStatus.COUNTING),(0,"Counting source files...",1,self._work_id))

        totalFilesNumber, totalFilesSize = self.countSourceFiles(window,origem,destino,preChecksum)
            
        window.write_event_value((ReelStatus.KEY,ReelStatus.STARTING),(1 if totalFilesNumber == 0 else totalFilesNumber,totalFilesSize,self._work_id))
        filesCount=0
        filesSizeCount=0
        self._renamedFiles = 0
        meanBpsArray = []
        meanChecksumArray = []
        remainingMsg = "Speed: calculating\nTime remaining: calculating"
        convertedSeconds = "Calculating..."
        elapseTs = datetime.datetime.timestamp(datetime.datetime.now())
        elapseDt = 0
        elapseDtStr = ""
        for root, dirs, files in os.walk(origem):
            if self._reelFilesStatus in (ReelStatus.CANCELED, ReelStatus.COUTING_FILES_CANCELED):
                break
            # Create folders
            thisDestRoot = root.replace(origem,destRoot)
            if not os.path.exists(thisDestRoot):
                os.mkdir(thisDestRoot)
                
            for name in files:
                elapseDt = datetime.datetime.timestamp(datetime.datetime.now()) - elapseTs
                elapseDtStr = str(datetime.timedelta(seconds = int(elapseDt)))
                if self._reelFilesStatus in (ReelStatus.CANCELED, ReelStatus.COUTING_FILES_CANCELED):
                    break
                if name.startswith("._"):
                    continue
                
                pathOrigem = os.path.join(root,name)
                pathDest = self.getReelFilename(name,root,thisDestRoot,pathOrigem) # os.path.join(thisDestRoot,name)
                        
                #TODO: Remaining time

                if not os.path.exists(pathDest):
                    filesCount+=1
                    fileSize=os.path.getsize(os.path.join(root,name))
                    filesSizeCount+=fileSize
                    msg = "Post-checksum: " + ("ON" if postChecksum else "OFF") + "\tPre-checksum: " + ("ON" if preChecksum else "OFF") + "\n"
                    msg+= "Copy file " + str(filesCount) +" of " + str(totalFilesNumber) + "\n" + \
                        "Remaining: " + self.humanReadable(totalFilesSize-filesSizeCount)+ " of " + self.humanReadable(totalFilesSize)
                    msg+="\nSource->" + pathOrigem + "\nDestination->" + pathDest
                    msg+="\n" + remainingMsg
                    window.write_event_value((ReelStatus.KEY,ReelStatus.COPYING),(filesCount,msg,totalFilesNumber,self._work_id))
                    try:
                        timeRemaining = 0
                        ts = datetime.datetime.timestamp(datetime.datetime.now())
                        shutil.copyfile(pathOrigem,pathDest)
                        dt = datetime.datetime.timestamp(datetime.datetime.now()) - ts
                        bps = fileSize/dt
                        copySizeRemaining = totalFilesSize - filesSizeCount
                        meanBpsArray.append(bps)
                        meanBps = statistics.median(meanBpsArray)
                        timeRemaining = (copySizeRemaining/meanBps)
                        if postChecksum:
                            ts = datetime.datetime.timestamp(datetime.datetime.now())
                            if not self.ckeckSum(pathOrigem,pathDest):
                                msg="The file checksum failed!"
                                self._reelFilesStatus = ReelStatus.FAILED
                            dt = datetime.datetime.timestamp(datetime.datetime.now()) - ts
                            copyFilesRenaining = totalFilesNumber - filesCount
                            meanChecksumArray.append(dt)
                            meanFile=statistics.median(meanChecksumArray)
                            
                            timeRemaining+=copyFilesRenaining*meanFile
                        
                        #print(timeRemaining)
                        convertedSeconds = str(datetime.timedelta(seconds = int(timeRemaining)))
                        #convertedSeconds = str(timeRemaining)
                       
                        remainingMsg = "Speed: " + self.humanReadable(meanBps,humanReadbleName="MBytes/s") + \
                            "\nTime remaining: " + convertedSeconds + "\tTime elapsed: " + elapseDtStr
                            
                    except shutil.SameFileError:
                        msg="Source and destination represents the same file."
                        self._reelFilesStatus = ReelStatus.FAILED
                    except IsADirectoryError:
                        msg="Destination is a directory."
                        self._reelFilesStatus = ReelStatus.FAILED
                    except PermissionError:
                        msg="Permission denied."
                        self._reelFilesStatus = ReelStatus.FAILED 
                    except Exception as e:
                        msg="Error occurred while copying file.\n" + str(e)
                        self._reelFilesStatus = ReelStatus.FAILED
                        
                    if self._reelFilesStatus == ReelStatus.FAILED:
                        msg+="\nFile " + pathOrigem
                        window.write_event_value((ReelStatus.KEY,ReelStatus.EXIT),self._work_id)
                        window.write_event_value((ReelStatus.KEY,ReelStatus.FAILED),(msg,self._work_id))
                        return
                
                if filesCount == totalFilesNumber:
                    break

                time.sleep(0.01) # emulates copy time, remove in production
            
            if filesCount == totalFilesNumber:
                break 
            
        if not self._reelFilesStatus == ReelStatus.COUTING_FILES_CANCELED:
            window.write_event_value((ReelStatus.KEY,ReelStatus.COUNTING),(filesCount-1 if filesCount > 0 else 0,"Comparing souce with destination...",totalFilesNumber if totalFilesNumber > 0 else 1,self._work_id))

            totalFilesNumber,totalFilesSize = self.countSourceFiles(window,origem)
            destFilesNumber = 0
            destFilesSize = 0
            for root, dirs, files in os.walk(destRoot):
                for name in files:
                    if name.startswith("._"):
                        continue
                    destFilesNumber+=1
                    destFilesSize+=os.path.getsize(os.path.join(root,name))

            msg="Total source files: " + str(totalFilesNumber) + \
                "\nTotal destination files: " + str(destFilesNumber) + \
                "\nTotal source size (MBytes): " + self.humanReadable(totalFilesSize) + \
                "\nTotal destination size (MBytes): " + self.humanReadable(destFilesSize) + \
                "\nRenamed files: " + str(self._renamedFiles) + \
                "\nDuration: " + elapseDtStr
        
        if self._reelFilesStatus == ReelStatus.RUNNING:
            self._reelFilesStatus = ReelStatus.STOPED
            msg+="\n\nReel operation " + str(self._work_id) + " finished successfully."
            window.write_event_value((ReelStatus.KEY,ReelStatus.SUCCESS),(msg,self._work_id))
        elif self._reelFilesStatus in (ReelStatus.CANCELED, ReelStatus.COUTING_FILES_CANCELED):
            self._reelFilesStatus = ReelStatus.STOPED
            msg+= "\n\nThe reel operation " + str(self._work_id) + " was canceled by the user."
            window.write_event_value((ReelStatus.KEY,ReelStatus.CANCELED),(msg,self._work_id))
        window.write_event_value((ReelStatus.KEY,ReelStatus.EXIT),self._work_id)

    def exportIngestSettings(self,sg:sg, settings:dict,window:sg.Window):
        ingestSettings = dict()
        ingestSettings.update({'fileExtensions': settings.get('listExtensionsID',[])})
        ingestSettings.update({'cameras': settings.get('listCamerasID',[])})
        oldPath=settings.get('exportIngestSettingsFolder',os.path.expanduser("~"))
        if not oldPath:
            oldPath=os.path.expanduser("~")
        oldFile = os.path.join(oldPath,INGEST_SETTINGS_FILENAME)
        ingestSettingsFile = sg.popup_get_file("Choose the destination folder for ingest_settings.json file","Choose Folder",
                                     default_path=oldFile,
                                     initial_folder=oldPath,
                                     save_as=True,
                                     default_extension='json',
                                     file_types=(("JSON",".json")),
                                     font=window.Font
                                     )
       
        if ingestSettingsFile:
            settings.set('exportIngestSettingsFolder',os.path.dirname(ingestSettingsFile))
            with open(ingestSettingsFile, "w") as outfile:
                json.dump(ingestSettings, outfile)
        
            if os.path.exists(ingestSettingsFile):
                sg.popup_ok("Ingest Setings exported to " + ingestSettingsFile + ".",font=window.Font)
            else:
                sg.popup_error("Ingest Settings failed to export.",font=window.Font)
                
    def importIngestSettings(self,sg:sg,settings:Settings,window:sg.Window):
        
        oldPath=settings.get('exportIngestSettingsFolder',os.path.expanduser("~"))
        if not oldPath:
            oldPath=os.path.expanduser("~")
        oldFile = os.path.join(oldPath,INGEST_SETTINGS_FILENAME)
        ingestSettingsFile = sg.popup_get_file("Choose the file to import","Shoose File",
                                               default_path=oldFile,
                                               file_types=(("JSON",".json")),
                                               initial_folder=oldPath,
                                               font=window.Font)
        
        if ingestSettingsFile and os.path.exists(ingestSettingsFile):
            with open(ingestSettingsFile,'r') as openFile:
                ingestSettings = json.load(openFile)
                
            settings.set('listExtensionsID',ingestSettings.get('fileExtensions',[]))
            settings.set('listCamerasID',ingestSettings.get('cameras',[]))
            sg.popup_ok("Ingest Setings imported successfully.",font=window.Font)
        else:
            sg.popup_error("Ingest Settings failed to import.",font=window.Font)

        
    def testeThread(self,window,work_id):
        self._work_id = work_id
        
        