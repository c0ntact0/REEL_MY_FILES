import PySimpleGUI as sg
from controller import Controller,ReelStatus,SourceTypes,HashAlgorithms,RenameHashGenerator
from pprint import pprint
from profiles import Profiles
from settings import Settings
import os
from textwrap import TextWrapper
import assets
import sys
import threading

#sg.main()
try:
    this_file = __file__
except NameError:
    this_file = sys.argv[0]
this_file = os.path.abspath(this_file)
if getattr(sys, 'frozen', False):
    APPDIR = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
else:
    APPDIR = os.path.dirname(this_file)

REEL_OPERATION_BUTTON_TEXT = "Reel My Files...Now!!!"
SELECTED_CAMS_TEXT_CHAR_LONG = 70
CONSOLE_MIN_SIZE = (60,15)
BUTTON_BG_IS_DARK = True
SYSTEM_EXPLORER = 'open'
#COPY_DIALOG_TEXT_SIZE = (180,10)
CANCEL_COPY_OP_BUTTON_TEXT="Cancel opereation"
COPY_OP_FONT_SIZE_DECREMENT = 6
FINAL_DESTINATION_TEXT = "Final destination: "

ctl = Controller()

settingsFolder = os.path.join(os.path.expanduser('~'),".ReelMyFiles")
settingsFile = os.path.join(settingsFolder,"settings.json")
profilesFile = os.path.join(settingsFolder,"profiles.json")
if not sg.user_settings_file_exists(settingsFile):
    sg.user_settings_save(settingsFile)

if not sg.user_settings_file_exists(profilesFile):
    sg.user_settings_save(profilesFile)
    
settings = Settings(filename=settingsFile)
theme = settings.get('listTheme',['DarkGrey9'])[0]
sg.set_global_icon(assets.ICON_APP)
sg.theme(settings.get('listTheme',['DarkGrey9'])[0])
BUTTON_BG_IS_DARK = int(sg.theme_button_color_background().replace('#','0x'),16) < assets.COLOR_MIDDLE_POINT

sg.set_options(pysimplegui_settings_path=settingsFolder)#,pysimplegui_settings_filename='global_settings.json')
# Values IDs that we don't need to save
profileSaveExclusions = ['menuID',
                  'cbProfileID',
                  'btBrowseSourceFolderID',
                  'btBrowseDestinationFolderID',
                  'listProjectsID',
                  'tabGroup',
                  'MacQuit',
                  'listExtensionsID',
                  'ckFilterProfile',
                  'txtSelectedCameras',
                  'listCamerasID',
                  'colWorkers',
                  'lbCopyDialog',
                  'progressBarCopy']
profileSaveExclusions += [num for num in range(100)] # add some "Tab" numbers
profiles = Profiles(filename=profilesFile,exclusions=profileSaveExclusions)
profile = profiles.getCurrentProfile()
currentTab = None
mainFont = ('Helvetica',settings.get('spFontSize',18))
textwrap = TextWrapper()

def createWorkerLayout(work_id:str):
    thisFont= (mainFont[0],mainFont[1]-COPY_OP_FONT_SIZE_DECREMENT)
    layout = [sg.pin(sg.Frame(work_id,[
            [sg.Text("Inicializing...",key=('lbCopyDialog',work_id),expand_y=True,expand_x=True,auto_size_text=True) ],
          [sg.Button(CANCEL_COPY_OP_BUTTON_TEXT,font=thisFont,key=('btCancelCopy',work_id)),
           sg.ProgressBar(max_value=100,orientation='h',size=(80,10),key=('progressBarCopy',work_id))]
          ],
                              key=('rowWorker',work_id),expand_x=True))]
         
    return layout

def main_window(theme):
    global mainFont
    sg.theme(theme)
    
    menu_def = [['&Application', ['&Settings...','E&xit']],
                ['View',['Show/Hide &Console']],
                ['&Help', ['&About','&Manual']] ]
    
    # PROJECTS
    projectsLayout = [
                        [sg.Frame("",border_width=0,layout=[[sg.Listbox(values=settings.get('listProjectsID',[]),default_values=[settings.get('currentProject',"")],size=(None,5),select_mode=sg.LISTBOX_SELECT_MODE_EXTENDED,key='listProjectsID',enable_events=True)]]),
                        sg.Frame("",border_width=0,layout=[[sg.Button("Add",key='btAddProjectID'),sg.Button("Remove",key='btDeleteProjectID'),sg.Button("Rename",key='btRenameProjectID')],[sg.Button("Clone Selected",key='btCloneProjectID',tooltip="This will clone the selected project with all profiles")]])
                        ]
                    ]
    
    # PROFILES
    sourceTypesLayout = [
        [sg.Frame("Use Camera Folders (see Ingest Settings tab)",tooltip="Use when the media support contains more than one camera or recorder media type.\nE.g. SSD or HDD with backups of recordings from varius types of sources, like drones, Sony cameras, Canon cameras, etc...",layout=[[
            sg.Radio("Include in rename","radioGroupCameras",default=profile.get(SourceTypes.FOLDER_CAM_INCLUDE,True),enable_events=True, key=SourceTypes.FOLDER_CAM_INCLUDE),
            sg.Radio("Exclude from rename","radioGroupCameras",default=profile.get(SourceTypes.FOLDER_CAM_EXCLUDE,False),enable_events=True,key=SourceTypes.FOLDER_CAM_EXCLUDE)]])],[
        
        sg.Frame("Card from camera (SD,SxS,CF)",expand_x=True,tooltip="Use when the media contains only one camera or recorder type.\nAlso, can be used if the media support is a SSD or HDD but contains only one media type.",layout=[[
            sg.Radio("NOT rename media","radioGroupCameras",default=profile.get(SourceTypes.CARD_NOT_RENAME,False),enable_events=True,key=SourceTypes.CARD_NOT_RENAME),
            sg.Radio("Rename media","radioGroupCameras",default=profile.get(SourceTypes.CARD_RENAME,False),enable_events=True,key=SourceTypes.CARD_RENAME)]])
        ]]
    
    profileCamerasLayout = [[
        
        sg.Listbox(values=settings.get('listCamerasID',[]), default_values=profile.get('listProfileCamerasID',[]),enable_events=True,expand_x=True,expand_y=True,select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE,key='listProfileCamerasID')
    ]
    ]
    
    txtSourceFolderID = profile.get('txtSourceFolderID','')
    txtDestinationFolderID = profile.get('txtDestinationFolderID','')
    sourceBasename = os.path.basename(txtSourceFolderID)
    ckAddSourceBasename = profile.get('ckAddSourceBasename',True)
    
    profileLayout = [[sg.Button("Save Profile",key='btSaveProfileID'),
                    sg.Button("New Profile",key='btNewProfileID'),
                    sg.Button("Rename Profile",key='btRenameProfileID'),
                    sg.Button("Delete Profile",key='btDeleteProfileID'),
                    sg.Button("Change Project",key='btChangeProjectID')],
                    [sg.Checkbox("Filter by selected project",enable_events=True,key='ckFilterProfile',default=settings.get('ckFilterProfile',False))],
                    [sg.Combo(profiles.getProfilesKeys(),default_value=profiles.getCurrentProfileKey(),enable_events=True,readonly=True,key='cbProfileID')
                    ],
        [
        sg.Frame("",sourceTypesLayout,border_width=0),        
        sg.Frame("Profile Cameras",profileCamerasLayout,expand_x=True,expand_y=True)
        ],
        [sg.Text(createSelectedCamerasText(),auto_size_text=False,expand_x=True,size=(SELECTED_CAMS_TEXT_CHAR_LONG,None) ,key='txtSelectedCameras'),
         sg.Button("",key='btSelectAllProfileCameras',image_data=assets.ICON_SELECT_ALL_WHITE if BUTTON_BG_IS_DARK else assets.ICON_SELECT_ALL_BLACK,tooltip="Select all camera types",border_width=5),
         sg.Button("",key='btUnSelectAllProfileCameras',image_data=assets.ICON_UNSELECT_ALL_WHITE if BUTTON_BG_IS_DARK else assets.ICON_UNSELECT_ALL_BLACK,tooltip= "Unselect all camera types")],
        [
            sg.Text("Source Folder"),sg.Input(default_text = txtSourceFolderID, key='txtSourceFolderID',expand_x=True, tooltip="The folder with the media to rename. Normaly a SD Card or SxS Card"),
         sg.FolderBrowse(key='btBrowseSourceFolderID',initial_folder=txtSourceFolderID)],
        [sg.Text("Destination Folder"),sg.Input(default_text = txtDestinationFolderID, key='txtDestinationFolderID',expand_x=True,tooltip="The destination folder to save the renamed files."),
         sg.FolderBrowse(key='btBrowseDestinationFolderID',initial_folder=txtDestinationFolderID)],
        [sg.Checkbox("Add " + sourceBasename + " to destination folder.",default=ckAddSourceBasename,key='ckAddSourceBasename',enable_events=True)],
        [sg.Text(FINAL_DESTINATION_TEXT + ctl.createDestinationFolder(txtSourceFolderID,txtDestinationFolderID,ckAddSourceBasename),key='lbFinalDestination')]        
        ]
    
    generalTablayout = [
         [sg.Frame("Projects",projectsLayout,expand_x=True)],
        [sg.Frame("Profiles",profileLayout,expand_x=True)],
    ]
    
    # INGEST SETTINGS
    extensionsLayout = [
                        [sg.Frame("",border_width=0,expand_x=True,expand_y=True,layout=[[sg.Listbox(values=settings.get('listExtensionsID',[]),expand_x=True,expand_y=True,select_mode=sg.LISTBOX_SELECT_MODE_EXTENDED,key='listExtensionsID')]]),
                        sg.Frame("",border_width=0,layout=[[sg.Button("New",key='btAddExtensionID')],[sg.Button("Remove",key='btDeleteExtensionID')],])
                        ]
                    ]
    camerasFoldersLayout = [  
                            [sg.Frame("",border_width=0,expand_x=True, expand_y=True,layout=[[sg.Listbox(values=settings.get('listCamerasID',[]), expand_x=True,expand_y=True,select_mode=sg.LISTBOX_SELECT_MODE_EXTENDED,key='listCamerasID')]]),
                            sg.Frame("",border_width=0,layout=[[sg.Button("New",key='btAddCameraID')],[sg.Button("Remove",key='btDeleteCamerasID')]])
                            ]
                    ]
    ingestTabLayout = [
        [sg.Frame("Extensions",extensionsLayout,expand_x=True,expand_y=True),sg.Frame("Camera Folders",camerasFoldersLayout,expand_x=True,expand_y=True)],
        [sg.Button("Export Ingest Settings",key='btExportIngestSettings'),sg.Button("Import Ingest Settings",key='btImportIngestSettings')]
    ]
    
    workersTabLayout = [
        [sg.Col([],scrollable=True,size_subsample_width=1,expand_x=True,expand_y=True,key="colWorkers")]
    ]
    
    mainLayout = [[sg.MenubarCustom(menu_def, key='menuID', font='Courier 15', tearoff=True)],
                 
        [
            sg.TabGroup([[
                sg.Tab("General",generalTablayout,key='tabGeneral'),
                sg.Tab("Reel Operations Tasks List",workersTabLayout,key='tabWorkers'),
                sg.Tab("Ingest Settings",ingestTabLayout,key='tabIngest')
                
            ]],expand_x=True,key='tabGroup',enable_events=True)
        ],[
            #[sg.Text(key='txtStatus',font=('Helvetica',10))],
            #[sg.ProgressBar(max_value=1,orientation='h',key='pbReelOperation',size_px=(None,30),expand_x=True)],
            [sg.Exit(key='btExit'),sg.Button(REEL_OPERATION_BUTTON_TEXT,key='btReelMyFiles')],
        ]
    ]
    
    window = sg.Window(appName,
                       mainLayout,
                       finalize=True,
                       location=settings.get('location',(None,None)),
                       font=mainFont,
                       resizable=True,
                       icon="images/app-icon.png"
                       )
    window.set_min_size(window.size)
    mainFont = window.Font
    
    #window['txtStatus'].update(visible=False)
    #window['pbReelOperation'].update(visible=False)
    btSelectAllProfileCameras = window['btSelectAllProfileCameras']
    btSelectAllProfileCameras.bind('<Enter>','#Enter')
    btSelectAllProfileCameras.bind('<Leave>','#Leave')
    btUnSelectAllProfileCameras = window['btUnSelectAllProfileCameras']
    btUnSelectAllProfileCameras.bind('<Enter>','#Enter')
    btUnSelectAllProfileCameras.bind('<Leave>','#Leave')
    
    return window

# ============= CONSOLE WINDOW ===============
def console_window(location,size):
    """
    Arguments:
        location: main window location tuple
        size: main window size tuple
    """
    consoleLocation = (location[0] + size[0],location[1])
    main_layout = [
        [sg.Text("Anything printed will display here!")],
                      [sg.Output(size=(60,15), font='Courier 12', expand_x=True, expand_y=True,
                                     echo_stdout_stderr=True,  key='mlConsola')]
                      # [sg.Output(size=(60,15), font='Courier 8', expand_x=True, expand_y=True)]
    ]
    
    window = sg.Window(appName + " Files Console",main_layout,finalize=True,location=settings.get('consoleLocation',consoleLocation),size=settings.get('consoleSize',CONSOLE_MIN_SIZE),resizable=True)
    window.set_min_size(CONSOLE_MIN_SIZE)
    return window

# ============= SETTINGS WINDOW ===============
def settings_window(hide=False):
    """
        Use hide=True if you need to save the current settings
    """
    
    consoleLayout = [[sg.Checkbox("Open Console at startup",key='ckConsole',default=settings.get('ckConsole',True)),
                    sg.Checkbox("Debug Events",key='ckDebug',default=settings.get('ckDebug',False)),
                    sg.Checkbox("Console follows the main window",key='ckConsoleFollows',default=settings.get('ckConsoleFollows',True))]
                   ]
    profilesLayout = [
                    [sg.Checkbox("Save on exit",key='ckSaveProfileExit',default=settings.get('ckSaveProfileExit',True),tooltip="Save the current profile on application exit"),
                    sg.Checkbox("Save on chage",key='ckSaveProfileOnChange',default=settings.get('ckSaveProfileOnChange',True),tooltip="Save the current profile when changing profile"),
                    sg.Checkbox("Make new current profile",key='ckMakeNewCurrentProfile',default=settings.get('ckMakeNewCurrentProfile',False),tooltip="When creating a new profile, make the new profile the current profile")]
                    ]
    operationLayout = [
            [sg.Checkbox("Use post-checksum (slower)",key='ckPostChecksum',default=settings.get('ckPostChecksum',True),tooltip="Perform a MD5 checksum in the source and destination files after the copy."),
            sg.Checkbox("Use pre-checksum (slower)",key='ckPreChecksum',default=settings.get('ckPreChecksum',True),tooltip="If the source file already exists in the destination, perform a MD5 checksum to confirm if the files are the same.")],
            [sg.Frame("Hash Algorithms",[[
                sg.Text("Rename files:"), sg.Combo(HashAlgorithms().algorithmsList(),default_value=settings.get('cbAlgorithmRename',HashAlgorithms().algorithmsList()[0]), key='cbAlgorithmRename'),
                sg.Text("Checksums: "),sg.Combo(HashAlgorithms().algorithmsList(),default_value=settings.get('cbAlgorithmChecksum',HashAlgorithms().algorithmsList()[0]), key='cbAlgorithmChecksum')
            ]])
                
            ],[sg.Frame("Rename hash generator",[[
                sg.Radio("From filepath+file modification date (faster)",'groupRenameHash',key=RenameHashGenerator.FILEPATH_PLUS_FILEMDATE,default=settings.get(RenameHashGenerator.FILEPATH_PLUS_FILEMDATE,False)),
                sg.Radio("From file (best but slower)",'groupRenameHash',key=RenameHashGenerator.FILE_HASH,default=settings.get(RenameHashGenerator.FILE_HASH,True)),
            ]])
                
            ]
            
    ]
    
    uiLayout = [
        [
            sg.Text("Font size") ,sg.Spin([sz for sz in range(6, 172)],initial_value=settings.get('spFontSize',mainFont[1]),change_submits=True,key='spFontSize'),sg.Text("Aa",size=(2,1),font=mainFont,key='lbFontSize'),
            sg.Frame("Theme (Need app restart to apply)",layout=[[sg.Listbox(values=sg.theme_list(), size=(None, 5),expand_x=True, key='listTheme', enable_events=True,default_values=[sg.theme()]),
                                                                  sg.Button("Show themes previews",key='btShowThemes')]])
            
            ]
        
        ]
    
    main_layout = [[sg.Frame("Console",consoleLayout,expand_x=True)],
                   [sg.Frame("Profiles",profilesLayout,expand_x=True)],
                   [sg.Frame("Operation",operationLayout,expand_x=True)],
                   [sg.Frame("UI",uiLayout,expand_x=True)],
                   [sg.Cancel(),sg.Exit("Exit & Save",key="Exit"),sg.Save(),sg.Button("Open Settings Folder",key='btSettingsFolder')]                  
                   ]
    window = sg.Window(appName + " Settings",main_layout,keep_on_top=False,finalize=True,modal=True,font=mainFont) # keep_on_top is False because of the tooltips. It's a tkinter/MacOS specific bug
    if hide:
        window.Hide()
    window.set_min_size(window.size)
    # save default settings
    saveSettings(window.ReturnValuesDictionary)
    return window

def copyProgressDialog(work_id,maxVal):
    layout = [[sg.Text(key='lbCopyDialog',expand_y=True) ],
              [sg.ProgressBar(max_value=maxVal,orientation='h',size=(80,30),key='progressBarCopy')],
              [sg.Button("Cancel",key='btCancelCopy#' + work_id)]]
    copyDialog = sg.Window("Running " + work_id,layout,keep_on_top=False,finalize=True,
                           modal=False,font=(mainFont[0],mainFont[1]-4),auto_size_text=False)
    return copyDialog

def disableWindow(window:sg.Window,state,currentTab):
    for elem in window.element_list():
        try:
            if type(elem) ==sg.Tab:
                #print(type(elem))
                continue 
            elem.update(disabled=state)
        except:
            pass
    
    window[currentTab].Select()

def createSelectedCamerasText(camList = None):
    selectedCams = camList if camList else profile.get('listProfileCamerasID',[])
    out = "None" if len(selectedCams) == 0 else ""
    for i in range(len(selectedCams)):
        out+=selectedCams[i] + (", " if i < len(selectedCams) - 1 else "")
    textwrap.width = SELECTED_CAMS_TEXT_CHAR_LONG
    return "Selected cameras:\n" + textwrap.fill(out)
    
    
def updateMainWindow(window: sg.Window,values):
    global profile
    comboWidth = max([len(width) for width in profiles.getProfilesKeys()])
    projectsList = settings.get('listProjectsID',[])
    listProjectsID = window['listProjectsID']
    listProjectsID.update(values=projectsList)
    listProjectsID.set_value([settings.get('currentProject',"")])
    if len(listProjectsID.get_indexes()) > 0:
        listProjectsID.update(scroll_to_index=listProjectsID.get_indexes()[0])
    project = settings.get('currentProject',"") if values['ckFilterProfile'] else None
    lista = profiles.getProfilesKeys(project)
    currentProfile = profiles.getCurrentProfileKey()
    if not currentProfile in lista:
        if len(lista) == 0:
            currentProfile = ""
        else:
            currentProfile = lista[0]
    profiles.setCurrentProfileKey(currentProfile)
    profile = profiles.getCurrentProfile()
    window['cbProfileID'].update(value = currentProfile,values=lista,size=(comboWidth,None))
    txtSourceFolderID = profile.get('txtSourceFolderID','')
    txtDestinationFolderID = profile.get('txtDestinationFolderID','')
    window['btBrowseSourceFolderID'].InitialFolder = txtSourceFolderID
    window['txtSourceFolderID'].update(value = txtSourceFolderID)
    window['btBrowseDestinationFolderID'].InitialFolder = txtDestinationFolderID
    window['txtDestinationFolderID'].update(value = txtDestinationFolderID)
    ckAddSourceBasename = profile.get('ckAddSourceBasename',True)
    window['ckAddSourceBasename'].update(value=ckAddSourceBasename)
    window['lbFinalDestination'].update(value=FINAL_DESTINATION_TEXT + \
                        ctl.createDestinationFolder(txtSourceFolderID,txtDestinationFolderID,ckAddSourceBasename))
    window[SourceTypes.FOLDER_CAM_INCLUDE].update(value=profile.get(SourceTypes.FOLDER_CAM_INCLUDE,True))
    window[SourceTypes.FOLDER_CAM_EXCLUDE].update(value=profile.get(SourceTypes.FOLDER_CAM_EXCLUDE,False))
    window[SourceTypes.CARD_NOT_RENAME].update(value=profile.get(SourceTypes.CARD_NOT_RENAME,False))
    window[SourceTypes.CARD_RENAME].update(value=profile.get(SourceTypes.CARD_RENAME,False))
    
    
    window['listCamerasID'].update(values=settings.get('listCamerasID',[]))
    camProfileList = profile.get('listProfileCamerasID' ,[])
    window['listProfileCamerasID'].update(values=settings.get('listCamerasID',[]))
    window['listProfileCamerasID'].set_value(camProfileList)
    window['txtSelectedCameras'].update(value=createSelectedCamerasText(camProfileList))
    window['listExtensionsID'].update(values=settings.get('listExtensionsID',[]))
    #window['btBrowseSourceFolderID'].update(initial_folder = profile.get('txtSourceFolderID',''))

def saveSettings(values):
    for key in values:
        settings.set(key,values[key])

def mac_quit(window):
    window.write_event_value('MacQuit', None)
 
 
def reverseButtonImage(lightImage:str,darkImage:str, event:str,button:sg.Button):
    action = event.split('#')[1]
    if action == 'Enter':
        button.update(image_data=darkImage if BUTTON_BG_IS_DARK else lightImage)
    elif action == 'Leave':
        button.update(image_data=lightImage if BUTTON_BG_IS_DARK else darkImage)

        
def main():
    global currentTab, profile
    threadsList = {}
    #ctlList = {}
    #copyProgressDialogList = {}
    mainWindow = main_window(sg.theme())
    settingsWindow = settings_window(True)
    settingsWindow.close()
    settingsWindow = None
    oldlocation = mainWindow.CurrentLocation()
    oldMainWindowSize = mainWindow.size
    consoleWindow = console_window(oldlocation,oldMainWindowSize)
    if not settings.get('ckConsole',False):
        consoleWindow.close()
    else:
        consoleWindow.sise = settings.get('consoleSize',CONSOLE_MIN_SIZE)
    # atualiza janela. preciso para filtrar profiles
    _,values = mainWindow.read(timeout=0)
    updateMainWindow(mainWindow,values)
    print()
    sg.Window.hidden_master_root.createcommand("tk::mac::Quit" , lambda win=mainWindow:mac_quit(win))
    # This is an Event Loop 
    while True:
        location = mainWindow.CurrentLocation()
        mainWindowSize = mainWindow.size
        if not consoleWindow.was_closed() and settings.get('ckConsoleFollows',True):
            if location != oldlocation or mainWindowSize != oldMainWindowSize:
                oldlocation = location
                oldMainWindowSize = mainWindowSize
                consoleWindow.Move(oldlocation[0] + oldMainWindowSize[0],oldlocation[1])
        
        window,event, values = sg.read_all_windows(timeout=100)
        
        if event not in (sg.TIMEOUT_EVENT, sg.WIN_CLOSED):
            if settings.get('ckDebug',False):
                print('============ Event = ', event, ' ==============')
                print('============ Window = ', window, ' ==============')
                print('-------- Values Dictionary (key=value) --------')
                for key in values:
                    print(key, ' = ',values[key])

        # ******** MAINWINDOW WINDOW **********
        if window == mainWindow:
            currentTab = values['tabGroup'] if values['tabGroup'] else currentTab
            if event in (sg.WIN_CLOSED,'Exit','btExit','MacQuit'):
                if settingsWindow or len(threadsList) > 0:
                    continue
                # save profile
                if settings.get('ckSaveProfileExit',True):
                    profiles.saveProfile(values)
                print("Exiting ReelMyFiles...")
                break
            
            # ======== REEL THREAD ===========
            elif event == 'btReelMyFiles':

                currentProfile = profiles.getCurrentProfileKey()
                if currentProfile in threadsList.keys():
                    sg.popup_error("The profile " + currentProfile + " already have a thread running." \
                        " Please choose another profile to run.",title="Error!",font=mainFont,non_blocking=True)
                    continue
                
                samePaths = False
                for key in threadsList.keys():
                    if profiles.haveSamePaths(key):
                        sg.popup_error("The profile " + currentProfile + " have the same paths as the profile " + key + \
                        ". Please choose another profile to run.",title="Error!",font=mainFont,non_blocking=True)
                        samePaths = True
                        break
                
                if samePaths:
                    continue
                                 
                thisCtl = Controller()
                thread_id = threading.Thread(
                    target=thisCtl.reelFiles,
                    args=(
                    values['txtSourceFolderID'],
                    values['txtDestinationFolderID'],
                    settings,
                    profile,window,currentProfile),
                    daemon=True
                )
                if ('rowWorker',currentProfile) in window.AllKeysDict:
                    window['lbCopyDialog',currentProfile].update(value="Inicializing...")
                    window[('btCancelCopy', currentProfile)].update(text=CANCEL_COPY_OP_BUTTON_TEXT)
                    window['progressBarCopy',currentProfile].update(visible=True)
                    window[('rowWorker',currentProfile)].update(visible=True)
                else:
                    window.extend_layout(window['colWorkers'], [createWorkerLayout(currentProfile)])
                thisFont= (mainFont[0],mainFont[1]-COPY_OP_FONT_SIZE_DECREMENT)
                window['lbCopyDialog',currentProfile].update(font=thisFont)
                window['colWorkers'].contents_changed()

                threadsList[currentProfile] = (thread_id,thisCtl)
                thread_id.start()
                #window['btReelMyFiles'].update(text="Starting Reel Operation...",disabled=True)
                #window['txtStatus'].update(value="Preparing to copy...",visible=True)
                window['btExit'].update(disabled=True)
                print("Starting reel operation...")
                window['tabWorkers'].select()

                    
            elif event[0] == ReelStatus.KEY:
                if event[1] == ReelStatus.CANCELED or event[1] == ReelStatus.SUCCESS:
                    thisWork_id = values[event][1]
                    window['lbCopyDialog',thisWork_id].update(value=values[event][0])
                elif event[1] == ReelStatus.STARTING:
                    print("Files to copy:",values[event][0])
                    print("Total size to copy:",values[event][1])
                
                elif event[1] in (ReelStatus.COPYING,ReelStatus.COUNTING):
                    
                    currentValue = values[event][0]
                    maxValue = values[event][2]
                    thisWork_id = values[event][3]
                    thisCopyProgress = window['progressBarCopy',thisWork_id]
                    thisLbCopyDialog = window['lbCopyDialog',thisWork_id]
                    msg = values[event][1]
                    thisCopyProgress.update(current_count=currentValue,max=maxValue)
                    lbSize = thisLbCopyDialog.get_size()
                    thisLbCopyDialog.update(value=msg)
                    window.refresh()
                    if thisLbCopyDialog.get_size()[0] < lbSize[0]:
                       thisLbCopyDialog.set_size((lbSize[0],None)) 
                   
                    window['colWorkers'].contents_changed()
                    print(values[event][1])
                elif event[1] == ReelStatus.FAILED:
                    print(values[event])
                    thisWork_id = values[event][1]
                    thisLbCopyDialog = window['lbCopyDialog',thisWork_id]
                    thisLbCopyDialog.update(value=values[event][0])
                    window[('btCancelCopy', thisWork_id)].update(text="Close")
                elif event[1] == ReelStatus.EXIT:
                    thisWork_id = values[event]
                    window[('btCancelCopy', thisWork_id)].update(text="Close",disabled=False)
                    window['progressBarCopy',thisWork_id].update(visible=False)
                    window['colWorkers'].contents_changed()
                    if not threadsList.pop(thisWork_id, False):
                        print("Can't remove copy operation thread",thisWork_id,"from the cue.")

                    if len(threadsList) == 0:
                        window['btExit'].update(disabled=False)

            elif event[0] == 'btCancelCopy':
                    thisWork_id = event[1]
                    thisTreath = threadsList.get(thisWork_id,False) 
                    thisCtl = False if not thisTreath else threadsList.get(thisWork_id)[1]
                    if thisCtl:
                        thisCtl.reelFilesStatus = ReelStatus.CANCELED
                        window[('btCancelCopy', thisWork_id)].update(text="Stopping...",disabled=True)
                    else:
                        row = window[('rowWorker', thisWork_id)]
                        row.update(visible=False)            
            
            elif event == 'tabGroup':
                window[values[event]].SetFocus(True)
            
            # ========= BUTTONS ENTER/LEAVE =========
            elif event.startswith('btSelectAllProfileCameras#'):
                reverseButtonImage(assets.ICON_SELECT_ALL_WHITE,
                                   assets.ICON_SELECT_ALL_BLACK,
                                   event,
                                   window['btSelectAllProfileCameras'])
            elif event.startswith('btUnSelectAllProfileCameras#'):
                reverseButtonImage(assets.ICON_UNSELECT_ALL_WHITE,
                                   assets.ICON_UNSELECT_ALL_BLACK,
                                   event,
                                   window['btUnSelectAllProfileCameras'])

            # ========= MENU =========
            elif event == 'Settings...':
                if not settingsWindow:
                    disableWindow(mainWindow,True,currentTab)
                    settingsWindow = settings_window()
                    #settingsWindow.bring_to_front()
                    settingsWindow.normal()
            elif event == 'Show/Hide Console':
                if consoleWindow.was_closed():
                    consoleWindow = console_window(oldlocation,oldMainWindowSize)
                else:
                    settings.set('consoleSize',consoleWindow.size)
                    consoleWindow.close()
            elif event == 'About':
                with open(os.path.join(APPDIR,'README.md'),'r') as of:
                    
                    sg.popup_scrolled(of.read(),title="About",font=('Helvetica',14),size=(70,20),image=bytes(assets.ICON_APP,encoding='utf-8'))
            
            elif event == 'Manual':
                print(os.listdir(APPDIR))
                sg.execute_command_subprocess(SYSTEM_EXPLORER,os.path.join(APPDIR,'manual/ReelMyFilesManual.pdf'))
            
            
            # ========= PROJECTS ========
            elif event == 'btAddProjectID':
                projectName = sg.popup_get_text("Enter the project name","New Project",font=mainFont)
                if projectName:
                    listId = 'listProjectsID'
                    if not settings.listItemExists(projectName,listId):
                        settings.addListItem(projectName,listId)
                        settings.set('currentProject',projectName)
                        updateMainWindow(window,values)

                    else:
                        sg.popup_error("A project named \"" + projectName + "\" already exist!",title="Error!!!",font=mainFont)
            elif event == 'btDeleteProjectID':
                listId = 'listProjectsID'
                if sg.popup_yes_no("Are you sure? This will delete this project profiles also!!!","Delete project",font=mainFont) == 'Yes':
                    profiles.deleteProjectProfiles(values[listId][0])
                    settings.deleteListItem(values[listId],listId)
                    if settings.isEmptyList(listId):
                        currentProject = ""
                    else:
                        currentProject = settings.get('listProjectsID')[0]
                    settings.set('currentProject',currentProject)
                    updateMainWindow(window,values)
            elif event == 'btRenameProjectID':
                listId = 'listProjectsID'
                selectedProject = values[listId][0]
                projectName = sg.popup_get_text("Enter the project new name","Rename Project",font=mainFont,default_text=selectedProject)
                if projectName:
                    if not settings.listItemExists(projectName,listId):
                        profiles.renameProject(selectedProject,projectName)
                        settings.deleteListItem([selectedProject],listId)
                        settings.addListItem(projectName,listId)
                        settings.set('currentProject',projectName)
                        updateMainWindow(window,values)

                    else:
                        sg.popup_error("A project named \"" + projectName + "\" already exist!",title="Error!!!",font=mainFont) 
            elif event == 'btCloneProjectID':
                projectName = sg.popup_get_text("Enter the project name","Clone Project",font=mainFont)
                if projectName:
                    listId = 'listProjectsID'
                    selectedProject = values[listId][0]
                    if not settings.listItemExists(projectName,listId):
                        profiles.cloneProfiles(selectedProject,projectName)
                        settings.addListItem(projectName,listId)
                        settings.set('currentProject',projectName)
                        
                        updateMainWindow(window,values)

                    else:
                        sg.popup_error("A project named \"" + projectName + "\" already exist!",title="Error!!!",font=mainFont) 
            elif event == 'listProjectsID':
                settings.set('currentProject',values['listProjectsID'][0])
                updateMainWindow(window,values)

            # ========= PROFILES ========
            # SAVE
            elif event in ['btSaveProfileID','listProfileCamerasID',SourceTypes,'ckAddSourceBasename']:
                profiles.saveProfile(values)
                
                if event == 'listProfileCamerasID':
                    window['txtSelectedCameras'].update(value=createSelectedCamerasText(values['listProfileCamerasID']))
                
                else:
                    updateMainWindow(window,values)
                """
                elif event == 'ckAddSourceBasename':
                    txtSourceFolderID = profile.get('txtSourceFolderID','')
                    txtDestinationFolderID = profile.get('txtDestinationFolderID','')
                    ckAddSourceBasename = profile.get('ckAddSourceBasename',True)
                    window['lbFinalDestination'].update(value=FINAL_DESTINATION_TEXT + \
                        ctl.createDestinationFolder(txtSourceFolderID,txtDestinationFolderID,ckAddSourceBasename))
                """
                
                
            # ADD
            elif event == 'btNewProfileID':
                if len(values['listProjectsID']) != 1:
                    sg.popup_error("Please, select only one project from the list.",title="Error!",font=mainFont)
                    continue
                project = values['listProjectsID'][0]
                profileName = sg.popup_get_text("Enter de profile name for the project \"" + project + "\"","New Profile",font=mainFont)
                if profileName:
                    
                    profileKey = profiles.createProfileKey(profileName,project)
                    if not profiles.profileExists(profileKey):
                        profiles.addProfile(profileName,project,values)
                        if settings.get('ckMakeNewCurrentProfile',False):
                            profiles.setCurrentProfileKey(profileKey)
                            updateMainWindow(window,values)
                        else:
                            mainWindow['cbProfileID'].update(values = profiles.getProfilesKeys(),value = profiles.getCurrentProfileKey())
                    else:
                        sg.popup_error("A profile named \"" + profileName + "\" already exist for the project \"" + project + "\"!",title="Error!!!",font=mainFont)
            # DELETE
            elif event == 'btDeleteProfileID':
                if sg.popup_yes_no("Are you sure?",title="Delete profile",font=mainFont) == 'Yes':
                    if profiles.deleteProfile():
                        updateMainWindow(window,values)
                    else:
                        sg.popup_error("You can not delete the last profile.","Error!!!")
                    
            # RENAME
            elif event == 'btRenameProfileID':
                project = profiles.getProfileProject()
                profileName = sg.popup_get_text("Enter de profile name","Rename Profile",font=mainFont, default_text=profiles.getProfileName())
                if profileName:
                    profileKey = profiles.createProfileKey(profileName,project)
                    if not profiles.profileExists(profileKey):
                        profiles.renameProfile(profileName)
                        updateMainWindow(window,values)
                    else:
                        sg.popup_error("A profile named \"" + profileName + "\" already exist for the project \"" + project + "\"!",title="Error!!!",font=mainFont)
            # CHANGE PROFILE PROJECT
            elif event == 'btChangeProjectID':
                if len(values['listProjectsID']) != 1:
                    sg.popup_error("Please, select only one project from the list.",title="Error!",font=mainFont)
                    continue
                project = values['listProjectsID'][0]
                profileName = profiles.getProfileName()
                profileKey = profiles.createProfileKey(profileName,project)
                if not profiles.profileExists(profileKey):
                    profiles.changeProfileProject(project)
                    updateMainWindow(window,values)
                else:
                    sg.popup_error("A profile named \"" + profileName + "\" already exist for the project \"" + project + "\"!",title="Error!!!",font=mainFont)
                
            #CHANGE CURRENT PROFILE    
            elif event == 'cbProfileID':
                if settings.get('ckSaveProfileOnChange',True):
                    profiles.saveProfile(values)
                profiles.setCurrentProfileKey(values['cbProfileID'])
                updateMainWindow(window,values)
                
                
            # FILTER BY PROJECT
            elif event == 'ckFilterProfile':
                settings.set('ckFilterProfile',values['ckFilterProfile'])
                updateMainWindow(window,values)
            
            # SELECT/UNSELECT ALL CAMERAS
            elif event in ('btSelectAllProfileCameras','btUnSelectAllProfileCameras') :
                value = settings.get('listCamerasID',[]) if event == 'btSelectAllProfileCameras' else []
                window['listProfileCamerasID'].set_value(value)
                profiles.saveProfile(values)
                profile = profiles.getCurrentProfile()
                window['txtSelectedCameras'].update(value=createSelectedCamerasText(value))
                            
            # ========= EXTENSIONS ========
            elif event == 'btAddExtensionID':
                extName = sg.popup_get_text("Enter the extension name","New Extension",font=mainFont)
                if extName:
                    extName = extName.lower()
                    listId = 'listExtensionsID'
                    if not settings.listItemExists(extName,listId):
                        settings.addListItem(extName,listId)
                        updateMainWindow(window,values)
                    else:
                        sg.popup_error("A extention named \"" + extName + "\" already exist!",title="Error!!!",font=mainFont)
            elif event == 'btDeleteExtensionID':
                if sg.popup_yes_no("Are you sure?","Delete extension(s)",font=mainFont) == 'Yes':
                    listId = 'listExtensionsID'
                    settings.deleteListItem(values[listId],listId)
                    updateMainWindow(window,values)
            
            # ========= CAMERAS ========        
            elif event == 'btAddCameraID':
                camName = sg.popup_get_text("Enter the camera folder name","New Camera Folder",font=mainFont)
                if camName:
                    camName = camName.upper()
                    listId = 'listCamerasID'
                    if not settings.listItemExists(camName,listId):
                        settings.addListItem(camName,listId)
                        updateMainWindow(window,values)
                    else:
                        sg.popup_error("A camera folder named \"" + camName + "\" already exist!",title="Error!!!",font=mainFont)
            
            elif event == 'btDeleteCamerasID':
                if sg.popup_yes_no("Are you sure?","Delete camera folders(s)",font=mainFont) == 'Yes':
                    listId = 'listCamerasID'
                    settings.deleteListItem(values[listId],listId)
                    updateMainWindow(window,values)
                
            # ========= IMPORT/EXPORT INGEST SETTINGS =========
            elif event == 'btExportIngestSettings':
                ctl.exportIngestSettings(sg,settings,window)
            elif event == 'btImportIngestSettings':
                ctl.importIngestSettings(sg,settings,window)
                updateMainWindow(window,values)

        
        # ******** SETTINGS WINDOW **********
        elif window == settingsWindow:
            if event == 'Exit':
                saveSettings(values)
                disableWindow(mainWindow,False,currentTab)
                settingsWindow.close()
                settingsWindow = None
            elif event == 'Save':
                saveSettings(values)
            elif event == 'Cancel':
                disableWindow(mainWindow,False,currentTab)
                settingsWindow.close()
                settingsWindow = None
            elif event == 'btSettingsFolder':
                sg.execute_command_subprocess(SYSTEM_EXPLORER,settingsFolder)
            elif event == 'spFontSize':
                window['lbFontSize'].Update(font=(mainFont[0],values['spFontSize']))
            elif event == 'listTheme':
                theme = sg.theme()
                sg.theme(values[event][0])
                settingsWindow.Close()
                settingsWindow = settings_window()
                listTheme = settingsWindow[event]
                listTheme.set_value(values[event])
                idx = listTheme.get_indexes()[0]
                settingsWindow[event].update(scroll_to_index=idx)
                sg.theme(theme)
            elif event == 'btShowThemes':
                sg.theme_previewer()
        # elif window in [x[2] for x in threadsList.values()]:
        #     if event.startswith('btCancelCopy#'):
        #         thisWork_id = event.split('#')[1]
        #         thisCtl = threadsList.get(thisWork_id)[1]
        #         if thisCtl:
        #             thisCtl.reelFilesStatus = ReelStatus.CANCELED
            
            
    # save settings
    if not consoleWindow.was_closed():
        settings.set('consoleSize',consoleWindow.size)
        settings.set('consoleLocation',consoleWindow.CurrentLocation())
    settings.set('location',location)
    mainWindow.close()
    
if __name__ == '__main__':
    #ctl.readSettings()
    appName = "ReelMyFiles"
    
    main()