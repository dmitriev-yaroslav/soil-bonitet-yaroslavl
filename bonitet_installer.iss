[Setup]
AppName=Bonitet
AppVersion=1.0
AppPublisher=Ярослав Дмитриев
DefaultDirName={commonpf}\Bonitet
DefaultGroupName=Bonitet
UninstallDisplayIcon={app}\Bonitet.ico
OutputDir=installer_output
OutputBaseFilename=BonitetInstaller
Compression=lzma2/ultra
SolidCompression=yes
CreateAppDir=yes
DisableWelcomePage=no
WizardStyle=modern
Uninstallable=yes

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Files]
Source: "app\*"; DestDir: "{app}\app"; Flags: recursesubdirs createallsubdirs
Source: "src\*"; DestDir: "{app}\src"; Flags: recursesubdirs createallsubdirs
Source: "data\sample\*"; DestDir: "{app}\data\sample"; Flags: recursesubdirs createallsubdirs
Source: ".streamlit\*"; DestDir: "{app}\.streamlit"; Flags: recursesubdirs createallsubdirs
Source: "requirements.txt"; DestDir: "{app}"
Source: "run-app.bat"; DestDir: "{app}"
Source: "Bonitet.ico"; DestDir: "{app}"

[Icons]
Name: "{group}\Запуск Bonitet"; Filename: "{app}\run-app.bat"; WorkingDir: "{app}"; IconFilename: "{app}\Bonitet.ico"
Name: "{commondesktop}\Bonitet"; Filename: "{app}\run-app.bat"; WorkingDir: "{app}"; IconFilename: "{app}\Bonitet.ico"
Name: "{group}\Удалить Bonitet"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\run-app.bat"; Description: "Запустить приложение после установки"; Flags: postinstall nowait skipifsilent