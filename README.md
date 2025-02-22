<img title="ReelMyFiles" alt="Logo" src="images/app-icon.png">
<br>

<div align="justify">
ReelMyFiles is a utility to rename files adding a UID at the end of the filename using hashing. Was developed to be used in video post production.<br><br>
The purpose of the application is to copy media files from one location to another, renaming files that do not have unique names so that they have a name that can uniquely identify them. Most cameras do not have mechanisms to give files unique names, so ReelMyFiles will create that unique name, thus creating a “Reel Name” or “Tape Name”, which can be safely used to create proxies and future relink of the proxy media to the original media.  
<br><br>
As the application can use file checksums to guarantee the reliability of the copy, its use as a copy tool, even without using its renaming function, is recommended to guarantee error-free copies. On the other hand, using checksums makes copying slower.
<br><br>
Rui Loureiro (2025)
<br><br>
This application is developed using PySimpleGUI. To use it you must comply with the PySimpleGUI license agreement.

https://pysimplegui.com/eula

# Install and Run
* Install PySimpleGUI
* Clone or download this repository
* In a terminal window or command shell change to the ReelMyFiles directory
* Run:
```
python ReelMyFiles.py
```
# User manual

Read the user manual in the [Wiki](https://github.com/c0ntact0/REEL_MY_FILES/wiki).


# Versions
2025.0.1
- Help->About linked to Github
- User Manual moved to Github Wiki (English)
- Portuguese manual still available [here](https://github.com/c0ntact0/REEL_MY_FILES/blob/main/manual/ReelMyFilesManual_pt.pdf)

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


</div>
