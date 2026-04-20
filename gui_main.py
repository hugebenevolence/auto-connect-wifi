import tkinter as tk
from tkinter import ttk, filedialog
import time
import os

# Import functions from main.py (netsh wrappers)
from main import (
     list_profiles,
     show_profile_details,
     export_all_profiles,
     import_profile_from_xml,
     create_and_add_profile,
     connect_profile,
     list_profiles_from_folder,
     find_xml_for_profile,
     delete_profile,
 )


class WifiGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Auto Wi‑Fi Helper (GUI)')
        self.geometry('800x520')
        self.create_widgets()
        self.refresh_profiles()

    def create_widgets(self):
        left_frame = ttk.Frame(self)
        left_frame.pack(side='left', fill='y', padx=10, pady=10)

        ttk.Label(left_frame, text='Saved Profiles').pack()
        self.profile_list = tk.Listbox(left_frame, width=60, height=18)
        self.profile_list.pack()
        ttk.Button(left_frame, text='Refresh', command=self.refresh_profiles).pack(fill='x')
        ttk.Button(left_frame, text='Show Details', command=self.show_details).pack(fill='x')
        ttk.Button(left_frame, text='Connect', command=self.connect_selected).pack(fill='x')
        ttk.Button(left_frame, text='Delete', command=self.delete_selected).pack(fill='x')

        right_frame = ttk.Frame(self)
        right_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)

        ttk.Label(right_frame, text='Actions').pack()
        export_frame = ttk.Frame(right_frame)
        export_frame.pack(fill='x')
        self.export_folder = tk.StringVar(value='profiles')
        ttk.Button(export_frame, text='Export All', command=self.export_all).pack(side='left')
        ttk.Button(export_frame, text='Load Known WiFi', command=self.load_known_wifi).pack(side='left')
        ttk.Entry(export_frame, textvariable=self.export_folder).pack(side='left', fill='x', expand=True)

        import_frame = ttk.Frame(right_frame)
        import_frame.pack(fill='x', pady=(6,0))
        self.import_path = tk.StringVar()
        ttk.Button(import_frame, text='Browse XML to Import', command=self.browse_xml).pack(side='left')
        ttk.Button(import_frame, text='Import', command=self.import_xml).pack(side='left')

        ttk.Separator(right_frame, orient='horizontal').pack(fill='x', pady=6)

        ttk.Label(right_frame, text='Add Profile (SSID + Password)').pack()
        add_frame = ttk.Frame(right_frame)
        add_frame.pack(fill='x')
        self.new_ssid = tk.StringVar()
        self.new_pwd = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.new_ssid).pack(side='left', fill='x', expand=True)
        ttk.Entry(add_frame, textvariable=self.new_pwd, show='*').pack(side='left', fill='x', expand=True)
        ttk.Button(right_frame, text='Add & Connect', command=self.add_and_connect).pack(pady=(6,0))

        ttk.Label(self, text='Status / Output').pack(pady=(6,0))
        self.output = tk.Text(self, wrap='word', height=12)
        self.output.pack(fill='both', padx=10, pady=(0,10), expand=True)

        ttk.Button(self, text='Exit', command=self.quit).pack(pady=(0,10))

    def write(self, msg):
        self.output.insert('end', msg + '\n')
        self.output.see('end')

    def refresh_profiles(self):
        try:
            # load both Windows saved profiles and local XML-saved profiles
            windows = list_profiles()
            local_map = list_profiles_from_folder('profiles')
            # Build combined list: local first (from ./profiles), then windows-only
            local_names = sorted(local_map.keys())
            windows_only = [n for n in windows if n not in local_map]
            profiles = []
            for n in local_names:
                profiles.append(n)
            for n in windows_only:
                profiles.append(n)
        except Exception as e:
            profiles = []
            self.write(f'Error listing profiles: {e}')
        self.profile_list.delete(0, 'end')
        for p in profiles:
            self.profile_list.insert('end', p)
        self.write('Profiles refreshed.')

    def _parse_selected(self):
        """Return (name, is_local, is_windows) for current selection or (None,False,False)."""
        sel = self.profile_list.curselection()
        if not sel:
            return None, False, False
        name = self.profile_list.get(sel[0])
        # determine source by checking local folder and Windows profiles
        try:
            local_map = list_profiles_from_folder('profiles')
        except Exception:
            local_map = {}
        try:
            windows = list_profiles()
        except Exception:
            windows = []
        is_local = name in local_map
        is_windows = name in windows
        return name, is_local, is_windows

    def show_details(self):
        name, is_local, is_windows = self._parse_selected()
        if not name:
            self.write('Select a profile first.')
            return
        # Try Windows netsh first
        out, pwd = show_profile_details(name)
        if out:
            self.write(out)
        if pwd:
            self.write(f'Recovered password: {pwd}')
            return
        # If password not available via netsh, try local XML
        xml = find_xml_for_profile(name, 'profiles') if is_local else find_xml_for_profile(name, 'profiles')
        if xml:
            try:
                with open(xml, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.write(f'Local XML ({xml}):')
                self.write(content)
                # try to extract keyMaterial quickly
                import re
                m = re.search(r'<keyMaterial>(.+?)</keyMaterial>', content, re.DOTALL)
                if m:
                    self.write(f'Recovered password (from XML): {m.group(1).strip()}')
            except Exception as e:
                self.write(f'Failed to read local xml: {e}')

    def export_all(self):
        folder = self.export_folder.get() or 'profiles'
        out = export_all_profiles(folder)
        self.write(out)
        self.write(f'Exported XMLs to {os.path.abspath(folder)}')

    def load_known_wifi(self):
        """Export all known Windows Wi‑Fi profiles into the local 'profiles' folder and refresh list."""
        folder = 'profiles'
        self.write('Loading known WiFi profiles into local profiles folder...')
        out = export_all_profiles(folder)
        self.write(out)
        # Ensure any exported files are present and refresh mapping
        self.write(f'Known profiles exported to {os.path.abspath(folder)}')
        # short delay to ensure files are written
        time.sleep(0.5)
        self.refresh_profiles()

    def delete_selected(self):
        name, is_local, is_windows = self._parse_selected()
        if not name:
            self.write('Select a profile to delete.')
            return
        # Show custom dialog with clear defaults: default is delete local only
        dlg = tk.Toplevel(self)
        dlg.title('Delete profile')
        dlg.transient(self)
        dlg.grab_set()
        ttk.Label(dlg, text=f"Delete profile '{name}'?").pack(padx=12, pady=8)
        ttk.Label(dlg, text="Choose action: (default is Local only)").pack(padx=12, pady=(0,8))

        result = {'action': None}

        def do_local():
            result['action'] = 'local'
            dlg.destroy()

        def do_both():
            result['action'] = 'both'
            dlg.destroy()

        def do_cancel():
            result['action'] = 'cancel'
            dlg.destroy()

        btn_frame = ttk.Frame(dlg)
        btn_frame.pack(padx=12, pady=8)
        ttk.Button(btn_frame, text='Delete Local Only', command=do_local).pack(side='left', padx=4)
        ttk.Button(btn_frame, text='Delete Local + Forget Windows', command=do_both).pack(side='left', padx=4)
        ttk.Button(btn_frame, text='Cancel', command=do_cancel).pack(side='left', padx=4)

        self.wait_window(dlg)

        if result['action'] == 'cancel' or result['action'] is None:
            self.write('Delete aborted.')
            return
        remove_local = True
        remove_windows = (result['action'] == 'both')
        out = delete_profile(name, remove_local=remove_local, remove_windows=remove_windows, folder='profiles')
        self.write(out)
        # refresh list
        self.refresh_profiles()

    def browse_xml(self):
        path = filedialog.askopenfilename(filetypes=[('XML files','*.xml')])
        if path:
            # copy the selected XML into ./profiles (overwrite if exists)
            try:
                import shutil
                dest_folder = os.path.abspath('profiles')
                os.makedirs(dest_folder, exist_ok=True)
                dest_path = os.path.join(dest_folder, os.path.basename(path))
                shutil.copy2(path, dest_path)
                self.import_path.set(dest_path)
                self.write(f'Copied XML into profiles folder: {dest_path}')
            except Exception as e:
                self.write(f'Failed to copy XML into profiles folder: {e}')
                # still set original path so user can import directly
                self.import_path.set(path)
                self.write(f'Selected for import: {path}')

    def import_xml(self):
        path = self.import_path.get()
        if not path:
            self.write('No file selected for import.')
            return
        out = import_profile_from_xml(path)
        self.write(out)
        # after import ensure UI shows local copy
        self.refresh_profiles()

    def add_and_connect(self):
        ssid = self.new_ssid.get().strip()
        pwd = self.new_pwd.get().strip()
        if not ssid or not pwd:
            self.write('SSID and password required to add profile.')
            return
        out, path = create_and_add_profile(ssid, pwd)
        self.write(out)
        self.write(f'Temporary XML used: {path}')
        # After adding, ensure the local profiles folder contains the new XML and refresh list
        self.refresh_profiles()
        self.write(connect_profile(ssid))

    def connect_selected(self):
        name, is_local, is_windows = self._parse_selected()
        if not name:
            self.write('Select a profile to connect.')
            return
        windows = list_profiles()
        if name in windows:
            self.write(connect_profile(name))
            return
        xml = find_xml_for_profile(name, 'profiles')
        if xml:
            self.write(self.import_and_connect(xml, name))
        else:
            self.write(f'No local xml found to import for {name}; cannot connect.')

    def import_and_connect(self, xml_path, name=None):
        # import_profile_from_xml copies xml into profiles folder as well
        out = import_profile_from_xml(xml_path)
        # small delay to ensure Windows registers profile
        time.sleep(1)
        connect_out = connect_profile(name if name else os.path.splitext(os.path.basename(xml_path))[0])
        return out + '\n' + connect_out


def main():
    app = WifiGUI()
    app.mainloop()


if __name__ == '__main__':
    main()
