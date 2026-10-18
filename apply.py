#!/usr/bin/env python3
"""Restore the captured KDE adjustments with scoped backups and Chrome merging."""
from __future__ import annotations
import argparse
import configparser
import datetime
import filecmp
import hashlib
import json
import os
import platform
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time

BASE = Path(__file__).resolve().parent


def run(args, check=True):
    return subprocess.run([str(a) for a in args], check=check, capture_output=True, text=True)


def atomic_text(path, text, mode=0o600):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.' + path.name + '-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(text)
        os.chmod(name, mode)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def safe_path(home, relative):
    p = Path(relative)
    if p.is_absolute() or '..' in p.parts:
        raise ValueError('Invalid snapshot path: ' + relative)
    return home / p


class Backup:
    def __init__(self, home):
        self.home = home
        stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        self.path = home / '.local/state/maclinux-aplicador/backups' / stamp
        self.path.mkdir(parents=True, mode=0o700)
        self.data = {'version': 1, 'home': str(home), 'files': [], 'chrome': []}
        self.recorded = set()
        self.save()

    def save(self):
        atomic_text(self.path / 'backup.json', json.dumps(self.data, indent=2, ensure_ascii=False) + '\n')

    def record(self, relative):
        if relative in self.recorded:
            return
        dest = safe_path(self.home, relative)
        item = {'path': relative, 'exists': dest.exists() or dest.is_symlink()}
        if dest.is_symlink():
            item['link'] = os.readlink(dest)
        elif dest.is_file():
            copy = self.path / 'files' / relative
            copy.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dest, copy)
        elif item['exists']:
            raise RuntimeError('Expected a file, found a directory: ' + relative)
        self.data['files'].append(item)
        self.recorded.add(relative)
        self.save()

    def chrome(self, path, document):
        browser = document.get('browser', {})
        self.data['chrome'].append({'path': str(path.relative_to(self.home)),
                                   'present': 'custom_chrome_frame' in browser,
                                   'value': browser.get('custom_chrome_frame')})
        self.save()


def chrome_roots():
    result = []
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit():
            continue
        try:
            if entry.stat().st_uid != os.getuid() or (entry / 'comm').read_text().strip() != 'chrome':
                continue
            args = (entry / 'cmdline').read_bytes().split(b'\0')
            if not any(a.startswith(b'--type=') for a in args) and not any(a.startswith(b'--user-data-dir') for a in args):
                result.append(int(entry.name))
        except (OSError, ProcessLookupError):
            pass
    return result


def stop_chrome():
    pids = chrome_roots()
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    deadline = time.monotonic() + 20
    while chrome_roots() and time.monotonic() < deadline:
        time.sleep(0.2)
    if chrome_roots():
        raise RuntimeError('O Chrome não encerrou normalmente. Feche-o e execute novamente; o perfil não foi editado.')
    return bool(pids)


def reopen_chrome():
    executable = shutil.which('google-chrome') or shutil.which('google-chrome-stable')
    if executable:
        subprocess.Popen([executable, '--restore-last-session'], stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)


def change_chrome(home, backup, live):
    profiles = list((home / '.config/google-chrome').glob('*/Preferences'))
    changed = [p for p in profiles if json.loads(p.read_text()).get('browser', {}).get('custom_chrome_frame') is not False]
    if not changed:
        print('Chrome: decoração do sistema já configurada.', flush=True)
        return
    restarted = stop_chrome() if live else False
    try:
        for p in changed:
            # Re-read after graceful exit: Chrome may save its current preferences while exiting.
            doc = json.loads(p.read_text())
            backup.chrome(p, doc)
            doc.setdefault('browser', {})['custom_chrome_frame'] = False
            atomic_text(p, json.dumps(doc, ensure_ascii=False, separators=(',', ':')) + '\n', p.stat().st_mode & 0o777)
        print('Chrome: decoração do sistema ativada; contas e demais preferências preservadas.', flush=True)
    finally:
        if restarted:
            reopen_chrome()


def copy_payload(base, home, backup, source_home):
    source = base / 'payload/home'
    for src in sorted(source.rglob('*')):
        if src.is_dir() and not src.is_symlink():
            continue
        relative = str(src.relative_to(source))
        dest = safe_path(home, relative)
        if src.is_symlink():
            if dest.is_symlink() and os.readlink(src) == os.readlink(dest):
                continue
        elif dest.is_file() and not dest.is_symlink() and filecmp.cmp(src, dest, shallow=False):
            continue
        backup.record(relative)
        dest.parent.mkdir(parents=True, exist_ok=True)
        fd, temp = tempfile.mkstemp(prefix='.maclinux-', dir=dest.parent)
        os.close(fd)
        try:
            if src.is_symlink():
                os.unlink(temp)
                os.symlink(os.readlink(src), temp)
            else:
                shutil.copy2(src, temp)
            os.replace(temp, dest)
        finally:
            if os.path.lexists(temp):
                os.unlink(temp)
    print('Temas, painel, fontes e controle dos LEDs restaurados.', flush=True)


def write_kwin(home, backup, manifest):
    relative = '.config/kwinrc'
    backup.record(relative)
    path = home / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    for section, values in manifest['kwin'].items():
        for key, value in values.items():
            run(['kwriteconfig6', '--file', path, '--group', section, '--key', key, value])


def desktop_entry(home):
    executable = str(home / '.local/bin/led-control').replace('\\', '\\\\').replace('"', '\\"')
    return '\n'.join(['[Desktop Entry]', 'Type=Application', 'Name=Cores dos LEDs',
                      'Comment=Ajustar a iluminação do computador pela barra superior',
                      f'Exec="{executable}"', 'Icon=preferences-desktop-color', 'Terminal=false',
                      'Categories=Settings;HardwareSettings;', 'StartupNotify=false', ''])


def write_desktops(home, backup, manifest):
    paths = ['.local/share/led-control/led-control.desktop', '.local/share/applications/led-control.desktop']
    if manifest['led_autostart']:
        paths.append('.config/autostart/led-control.desktop')
    for relative in paths:
        backup.record(relative)
        atomic_text(home / relative, desktop_entry(home), 0o644)


def plasma_script(manifest, home):
    def expand(value):
        if isinstance(value, str): return value.replace(manifest['source_home'], str(home))
        if isinstance(value, list): return [expand(v) for v in value]
        if isinstance(value, dict): return {k: expand(v) for k, v in value.items()}
        return value
    config = expand(manifest['plasma'])
    return '''var p=panels().filter(p=>p.location==='top')[0];
if(!p) throw new Error('Painel superior não encontrado. Instale a base XMacTahoe.');
var w=p.widgets().filter(w=>w.type==='Plasma.Flex.Hub')[0] || p.addWidget('Plasma.Flex.Hub');
w.currentConfigGroup=['General']; var cfg=CONFIG;
Object.keys(cfg).forEach(k=>w.writeConfig(k,cfg[k]));
var tray=p.widgets().filter(w=>w.type==='org.kde.plasma.systemtray')[0];
if(tray){tray.currentConfigGroup=['General'];var shown=tray.readConfig('shownItems',[]);
if(typeof shown==='string') shown=shown?shown.split(','):[];
if(shown.indexOf('Cores dos LEDs')<0) shown.push('Cores dos LEDs');tray.writeConfig('shownItems',shown);}
print('Painel restaurado');'''.replace('CONFIG', json.dumps(config, ensure_ascii=False))


def refresh_desktop(manifest, home):
    theme = manifest['kwin']['org.kde.kdecoration2']['theme']
    alternate = '__aurorae__svg__XMacTahoe' if 'Night' in theme else '__aurorae__svg__XMacTahoe-Night'
    run(['kwriteconfig6', '--file', 'kwinrc', '--group', 'org.kde.kdecoration2', '--key', 'theme', alternate])
    run(['qdbus', 'org.kde.KWin', '/KWin', 'org.kde.KWin.reconfigure'])
    time.sleep(0.25)
    run(['kwriteconfig6', '--file', 'kwinrc', '--group', 'org.kde.kdecoration2', '--key', 'theme', theme])
    run(['qdbus', 'org.kde.KWin', '/KWin', 'org.kde.KWin.reconfigure'])
    run(['qdbus', 'org.kde.KWin', '/Effects', 'org.kde.kwin.Effects.unloadEffect', 'kwin4_effect_shapecorners'], check=False)
    run(['qdbus', 'org.kde.KWin', '/Effects', 'org.kde.kwin.Effects.loadEffect', 'kwin4_effect_shapecorners'])
    run(['systemctl', '--user', 'restart', 'plasma-plasmashell.service'])
    # Wait until the existing top panel has been re-created before updating widgets.
    for _ in range(60):
        probe = run(['qdbus', 'org.kde.plasmashell', '/PlasmaShell', 'org.kde.PlasmaShell.evaluateScript',
                     "print(panels().filter(p=>p.location==='top').length);"], check=False)
        if probe.returncode == 0 and probe.stdout.strip() not in ('', '0'):
            break
        time.sleep(0.25)
    else:
        raise RuntimeError('O painel não ficou disponível após o recarregamento.')
    run(['qdbus', 'org.kde.plasmashell', '/PlasmaShell', 'org.kde.PlasmaShell.evaluateScript', plasma_script(manifest, home)])
    run(['fc-cache', '-f', home / '.local/share/fonts/SF-Pro'], check=False)
    run(['update-desktop-database', home / '.local/share/applications'], check=False)
    run(['systemctl', '--user', 'stop', 'led-control.service'], check=False)
    run(['pkill', '-u', str(os.getuid()), '-x', 'led-control'], check=False)
    started = run(['systemd-run', '--user', '--unit=led-control', '--collect', home / '.local/bin/led-control'], check=False)
    if started.returncode:
        subprocess.Popen([str(home / '.local/bin/led-control')], stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)


def apply(base, home, live=True):
    manifest = json.loads((base / 'manifest.json').read_text())
    if live:
        if platform.machine() != 'x86_64' or 'KDE' not in os.environ.get('XDG_CURRENT_DESKTOP', '').upper():
            raise RuntimeError('Este snapshot requer KDE Plasma em Linux x86_64.')
        if 'VERSION_ID=44' not in Path('/etc/os-release').read_text().replace('"', ''):
            raise RuntimeError('Este snapshot foi preparado para Fedora 44. Confira os requisitos antes de adaptar.')
    for executable in ['kwriteconfig6'] + (['qdbus', 'systemctl', 'fc-cache'] if live else []):
        if not shutil.which(executable):
            raise RuntimeError('Dependência ausente: ' + executable)
    backup = Backup(home)
    print('Backup: ' + str(backup.path), flush=True)
    # The panel's existing full file is backed up for exact rollback, but only selected keys are changed.
    backup.record('.config/plasma-org.kde.plasma.desktop-appletsrc')
    copy_payload(base, home, backup, manifest['source_home'])
    write_kwin(home, backup, manifest)
    write_desktops(home, backup, manifest)
    change_chrome(home, backup, live)
    if live:
        desired_rules = base / 'payload/system/etc/udev/rules.d'
        needs_rules = any(not (Path('/etc/udev/rules.d') / p.name).is_file() or not filecmp.cmp(p, Path('/etc/udev/rules.d') / p.name, shallow=False)
                          for p in desired_rules.glob('*.rules'))
        if needs_rules:
            run(['pkexec', '/bin/bash', base / 'install-rules.sh'])
        refresh_desktop(manifest, home)
    backup.data['completed'] = True
    backup.save()
    return backup.path


def restore(path, home, live=True):
    metadata = json.loads((path / 'backup.json').read_text())
    if metadata['home'] != str(home):
        raise RuntimeError('Esse backup pertence a outra pasta pessoal.')
    restart = stop_chrome() if live and metadata.get('chrome') else False
    try:
        for item in reversed(metadata['files']):
            dest = safe_path(home, item['path'])
            if item['exists']:
                dest.parent.mkdir(parents=True, exist_ok=True)
                if dest.is_symlink(): dest.unlink()
                if 'link' in item:
                    if dest.exists(): dest.unlink()
                    dest.symlink_to(item['link'])
                else:
                    shutil.copy2(path / 'files' / item['path'], dest)
            elif dest.is_file() or dest.is_symlink():
                dest.unlink()
        for item in metadata.get('chrome', []):
            dest = safe_path(home, item['path'])
            if not dest.is_file(): continue
            doc = json.loads(dest.read_text()); browser = doc.setdefault('browser', {})
            if item['present']: browser['custom_chrome_frame'] = item['value']
            else: browser.pop('custom_chrome_frame', None)
            atomic_text(dest, json.dumps(doc, ensure_ascii=False, separators=(',', ':')) + '\n', dest.stat().st_mode & 0o777)
    finally:
        if restart: reopen_chrome()
    if live:
        run(['qdbus', 'org.kde.KWin', '/KWin', 'org.kde.KWin.reconfigure'])
        run(['systemctl', '--user', 'restart', 'plasma-plasmashell.service'])
    print('Backup restaurado: ' + str(path), flush=True)


def main():
    parser = argparse.ArgumentParser(description='Reaplicar os ajustes macOS deste computador em um comando.')
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--gui', action='store_true', help='Mostrar erros em uma janela ao executar pelo atalho.')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--restore-latest', action='store_true')
    parser.add_argument('--restore', type=Path)
    parser.add_argument('--target-home', type=Path, help='Destino isolado para testes; não controla a sessão desktop.')
    args = parser.parse_args()
    home = args.target_home.resolve() if args.target_home else Path.home()
    live = home == Path.home()
    if args.dry_run:
        print('Snapshot: ' + str(BASE)); print('Destino: ' + str(home))
        print('Aplicaria temas, painel, fontes, LEDs, inicialização e decoração do Chrome. Nenhuma alteração feita.')
        return
    if args.restore or args.restore_latest:
        path = args.restore or sorted((home / '.local/state/maclinux-aplicador/backups').glob('*/backup.json'))[-1].parent
        restore(path, home, live)
    else:
        backup = apply(BASE, home, live)
        print('Concluído. Para desfazer: maclinux-aplicar --restore ' + str(backup), flush=True)
    if live and shutil.which('notify-send'):
        run(['notify-send', 'MacLinux Setup', 'Ajustes aplicados. Backup salvo para desfazer.'], check=False)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('ERRO: ' + str(exc), file=sys.stderr, flush=True)
        if '--gui' in sys.argv and shutil.which('kdialog'):
            run(['kdialog', '--error', 'Não foi possível concluir os ajustes.\n' + str(exc)], check=False)
        sys.exit(1)
