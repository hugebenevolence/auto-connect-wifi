# Auto_login_wifi — User Guide

Auto_login_wifi is a small Windows helper that uses `netsh` to manage Wi‑Fi profiles.

Features
- List Wi‑Fi profiles saved on the machine.
- Export and import profile XML files into the local `./profiles` folder.
- Show profile details and attempt to reveal password when Windows returns `key=clear`, or read `<keyMaterial>` from an XML file when available.
- Add a profile from SSID + password (creates a temporary XML and imports it).
- Connect to a saved profile.

Project files
- `main.py` — netsh helper functions and a simple CLI.
- `gui_main.py` — Tkinter GUI for interactive use.
- `profiles/` — local storage for exported/imported profile XML files.

Notes and prerequisites
- This tool only runs on Windows because it relies on the `netsh` command.
- Some operations (export/import/delete) may require Administrator privileges; if you see permission errors, run the program as Administrator.

Running the GUI (recommended)
1. Open PowerShell in the project folder.
2. Run:

```powershell
python gui_main.py
```

GUI quick guide
- `Refresh`: reload the list from both `netsh` and the `./profiles` folder.
- `Load Known WiFi`: export all Windows-known profiles into `./profiles` (this will overwrite files with the same name).
- `Browse XML to Import`: pick an XML file — it will be copied into `./profiles` (overwrites if same name). Then press `Import` to add it to Windows.
- `Show Details`: show profile details and any discovered password (tries `netsh` first, then `<keyMaterial>` in XML).
- `Add & Connect`: create a new profile by SSID + password, import it to Windows, and connect.
- `Connect`: if an XML exists in `./profiles` but Windows doesn't have that profile, the GUI imports it and then connects.
- `Delete`: remove the local XML file; you can also choose to forget the Windows profile (option in the dialog).

Using the CLI
- List profiles:

```powershell
python main.py --list
```

- Show profile details:

```powershell
python main.py --show "ProfileName"
```

- Export all profiles into the `profiles` folder:

```powershell
python main.py --export-all profiles
```

- Import a single XML and exit:

```powershell
python main.py --import path\to\profile.xml
```

Security and privacy
- Exported XML files in `./profiles` may include plaintext passwords inside `<keyMaterial>` when exported with `key=clear`. Treat the `profiles` folder as sensitive and avoid committing these files to version control.

.gitignore
- The project includes `.gitignore` that excludes `profiles/*.xml` and common build artifacts to avoid accidentally committing sensitive files.

Removed build artifacts
- Build artifacts (if previously present) such as `build/`, `dist/`, `*.spec`, temporary exes, and `.venv_build` were removed to keep the repo clean.

What next?
- Build a single-file GUI executable using PyInstaller (I can run this here if you want).
- Add an optional backup step when overwriting profiles in `./profiles`.
- Add management operations (rename/unhide) for XML files in `./profiles`.

If you'd like, I can run a build now or demo exporting/importing profiles — tell me which.
