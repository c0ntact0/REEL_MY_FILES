ReelMyFiles is a utility to rename files adding a UID at the end of the filename.

Rui Loureiro (2023)

This application is developed using PySimpleGUI. To use it you must comply with the PySimpleGUI license agreement.

# Install
* Clone or download the repository
* In a terminal window or command shell change to the ReelMyFiles directory
* Run:
```
python ReelMyFiles.py
```

https://pysimplegui.com/eula

# Versions
2023.1.1
- Hash algorithm choice added.
- xxHash64 algorithm added.
- Add checkbox to decide when the last folder of the source path must be create at the destination path or not.
- New "Clone Project" button
- New "Rename" (Project) button
- Must important! New App Icon :-)

2023.1.0
- Multithread reel operations
- New "Reel Operations Tasks List" tab
- Copy speed and time remaining information
- Progress bar while comparing source and destination files.

2023.0.3
- Card rename use file md5 instead of path + modification date
- Manual pdf file included in the APP Bundle and accessible in the menu (Help->Manual) 
- Bug solved: current profile global variable value does not change when changing the currente profile in the GUI
- This pretty About with the README.txt included in the APP Bundle

2023.0.2
- Pre-Checksum (for files already in the destination)
- Post-Checksum (after copy the file)

2023.0.1:
- Initial version

