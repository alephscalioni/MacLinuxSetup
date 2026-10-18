#!/usr/bin/env python3
from pathlib import Path
import os
import shlex
import subprocess

base=Path(__file__).resolve().parent
home=Path.home()
command=home/'.local/bin/maclinux-aplicar'
command.parent.mkdir(parents=True,exist_ok=True)
command.write_text('#!/usr/bin/env bash\nexec /usr/bin/python3 '+shlex.quote(str(base/'apply.py'))+' "$@"\n')
command.chmod(0o755)
exec_path=str(base/'apply.py').replace('\\','\\\\').replace('"','\\"')
entry='\n'.join(['[Desktop Entry]','Type=Application','Name=Aplicar ajustes macOS','Comment=Restaurar temas, painel, fontes, LEDs e botões do Chrome','Exec=/usr/bin/python3 "'+exec_path+'" --apply --gui','Icon=preferences-desktop-theme','Terminal=true','Categories=Settings;DesktopSettings;','StartupNotify=false',''])
menu=home/'.local/share/applications/maclinux-aplicar.desktop';menu.parent.mkdir(parents=True,exist_ok=True);menu.write_text(entry);menu.chmod(0o755)
try:
 desktop=Path(subprocess.check_output(['xdg-user-dir','DESKTOP'],text=True).strip())
 desktop.mkdir(parents=True,exist_ok=True);shortcut=desktop/'Aplicar ajustes macOS.desktop';shortcut.write_text(entry);shortcut.chmod(0o755)
 subprocess.run(['gio','set',str(shortcut),'metadata::trusted','true'],capture_output=True)
 print('Atalho:',shortcut)
except (OSError,subprocess.CalledProcessError):pass
subprocess.run(['update-desktop-database',str(menu.parent)],capture_output=True)
print('Comando instalado:',command)
