import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

spec=importlib.util.spec_from_file_location('applicator',Path(__file__).with_name('apply.py'))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class ApplicatorTests(unittest.TestCase):
    def test_scoped_apply_and_rollback_preserve_unrelated_chrome_preferences(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);base=root/'bundle';home=root/'target';base.mkdir();home.mkdir()
            (base/'manifest.json').write_text(json.dumps({'source_home':'/old/home','kwin':{'Round-Corners':{'OutlineThickness':'0'}},'plasma':{},'led_autostart':True}))
            source=base/'payload/home/.local/share/fixture';source.parent.mkdir(parents=True);source.write_text('after')
            dest=home/'.local/share/fixture';dest.parent.mkdir(parents=True);dest.write_text('before')
            link=source.with_name('fixture-link');link.symlink_to('fixture')
            profile=home/'.config/google-chrome/Default/Preferences';profile.parent.mkdir(parents=True)
            original={'browser':{'custom_chrome_frame':True,'keep_me':123},'account_info':[{'synthetic_test_fixture':True}],'session':{'restore_on_startup':7}}
            profile.write_text(json.dumps(original))
            backup=module.apply(base,home,live=False)
            current=json.loads(profile.read_text())
            self.assertIs(current['browser']['custom_chrome_frame'],False)
            self.assertEqual(current['browser']['keep_me'],123)
            self.assertEqual(current['account_info'],original['account_info'])
            self.assertEqual(current['session'],original['session'])
            self.assertEqual(dest.read_text(),'after')
            self.assertTrue((dest.parent/'fixture-link').is_symlink())
            self.assertIn(str(home), (home/'.local/share/applications/led-control.desktop').read_text())
            journal=json.loads((backup/'backup.json').read_text())
            self.assertNotIn('account_info',json.dumps(journal))
            module.restore(backup,home,live=False)
            self.assertEqual(dest.read_text(),'before')
            self.assertEqual(json.loads(profile.read_text()),original)
            self.assertFalse((dest.parent/'fixture-link').exists())
            self.assertFalse((home/'.config/autostart/led-control.desktop').exists())

    def test_profile_with_absent_flag_is_restored_without_adding_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp);p=home/'.config/google-chrome/Default/Preferences';p.parent.mkdir(parents=True);p.write_text('{"browser":{"unrelated":true}}')
            backup=module.Backup(home);module.change_chrome(home,backup,False)
            module.restore(backup.path,home,False)
            self.assertNotIn('custom_chrome_frame',json.loads(p.read_text())['browser'])

    def test_configuration_lists_and_home_are_translated_without_shell_expansion(self):
        manifest={'source_home':'/old/home','plasma':{'commands':['/old/home/.local/bin/tool literal'],'enabled':False}}
        script=module.plasma_script(manifest,Path('/new home'))
        self.assertIn('/new home/.local/bin/tool literal',script)
        self.assertIn('"enabled": false',script)
        self.assertNotIn('/old/home',script)

    def test_already_configured_chrome_is_not_stopped(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp);p=home/'.config/google-chrome/Default/Preferences';p.parent.mkdir(parents=True);p.write_text('{"browser":{"custom_chrome_frame":false}}')
            backup=module.Backup(home)
            with mock.patch.object(module,'stop_chrome',side_effect=AssertionError('must not stop')):
                module.change_chrome(home,backup,True)
            self.assertEqual(backup.data['chrome'],[])

    def test_backup_rejects_paths_outside_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):module.safe_path(Path(tmp),'../outside')
            with self.assertRaises(ValueError):module.safe_path(Path(tmp),'/etc/passwd')

if __name__=='__main__':unittest.main()
