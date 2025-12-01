import os
import subprocess
import tempfile
import argparse
import re
from pathlib import Path


def run_netsh(args):
    """Run a netsh command and return its output as text."""
    try:
        # capture bytes and decode trying utf-8 first, then platform encoding (mbcs)
        res = subprocess.run(["netsh"] + args, capture_output=True)
        out_bytes = (res.stdout or b'') + (res.stderr or b'')
        # try utf-8, then mbcs (Windows ANSI), then fallback with replace
        try:
            text = out_bytes.decode('utf-8')
        except Exception:
            try:
                text = out_bytes.decode('mbcs')
            except Exception:
                text = out_bytes.decode('utf-8', errors='replace')
        return text
    except Exception as e:
        return str(e)


def list_profiles():
    """Return list of saved Wi‑Fi profile names."""
    out = run_netsh(["wlan", "show", "profiles"])
    # Try to extract profile names robustly (handles different locales)
    profiles = []
    for line in out.splitlines():
        # common English entry: "    All User Profile     : MyWifi"
        if ':' not in line:
            continue
        left, right = line.split(':', 1)
        name = right.strip()
        left_norm = left.strip().lower()
        # skip headings like 'User profiles', 'Group policy profiles', or separators
        if not name:
            continue
        if any(h in left_norm for h in ['profile', 'user profiles', 'group policy', 'giao diện', 'user profiles', 'user profile']):
            # If left contains 'profile' it's likely an actual profile entry (e.g., 'All User Profile')
            # But skip when left is a header like 'User profiles' exactly
            if left_norm.startswith('user profiles') or left_norm.startswith('group policy'):
                continue
        # accept the name
        profiles.append(name)
    # Deduplicate while preserving order
    seen = set()
    filtered = []
    for p in profiles:
        if p not in seen:
            seen.add(p)
            filtered.append(p)
    return filtered


def show_profile_details(name):
    """Show details for a profile, including the cleartext key if available."""
    out = run_netsh(["wlan", "show", "profile", f'name="{name}"', "key=clear"]) 
    # Try to find the line containing the password (Key Content)
    pwd = None
    for line in out.splitlines():
        m = re.search(r"Key Content\s*[:\t]+(.+)$", line)
        if m:
            pwd = m.group(1).strip()
            break
        # localized fallback: look for 'Mật khẩu' or 'Key' generic
        m2 = re.search(r"Key\s*:\s*(.+)$", line)
        if m2:
            pwd = m2.group(1).strip()
    return out, pwd


def export_all_profiles(folder="profiles"):
    """Export all profiles as XML files into `folder` (requires permission)."""
    Path(folder).mkdir(parents=True, exist_ok=True)
    out = run_netsh(["wlan", "export", "profile", f'folder="{os.path.abspath(folder)}"', "key=clear"]) 
    return out


def import_profile_from_xml(xml_path):
    xml_path = os.path.abspath(xml_path)
    if not os.path.exists(xml_path):
        return f"File not found: {xml_path}"
    out = run_netsh(["wlan", "add", "profile", f'filename="{xml_path}"', "user=current"]) 
    # Also copy the xml into the local profiles folder for future use
    try:
        dest_folder = os.path.join(os.getcwd(), 'profiles')
        os.makedirs(dest_folder, exist_ok=True)
        import shutil
        dest_path = os.path.join(dest_folder, os.path.basename(xml_path))
        # If source and destination are the same, skip copy
        if os.path.abspath(xml_path) != os.path.abspath(dest_path):
            shutil.copy2(xml_path, dest_path)
        # copied into profiles folder
    except Exception as e:
        out += f"\nWarning: failed to copy XML to profiles folder: {e}"
    return out


def list_profiles_from_folder(folder='profiles'):
    """Return mapping of profile name -> xml file path for XML files in folder."""
    import xml.etree.ElementTree as ET
    res = {}
    folder_path = os.path.abspath(folder)
    if not os.path.isdir(folder_path):
        return res
    for fn in os.listdir(folder_path):
        if not fn.lower().endswith('.xml'):
            continue
        fp = os.path.join(folder_path, fn)
        try:
            tree = ET.parse(fp)
            root = tree.getroot()
            # find 'name' element (namespace-aware)
            name_elem = None
            # Try simple search for tag ending with 'name'
            for el in root.iter():
                if el.tag.lower().endswith('name'):
                    name_elem = el
                    break
            if name_elem is not None and name_elem.text:
                res[name_elem.text.strip()] = fp
        except Exception:
            # skip malformed files
            continue
    return res


def find_xml_for_profile(name, folder='profiles'):
    mapping = list_profiles_from_folder(folder)
    return mapping.get(name)



def delete_profile(name, remove_local=True, remove_windows=False, folder='profiles'):
    """Delete profile: optionally remove local XML and/or remove Windows profile."""
    out_msgs = []
    if remove_windows:
        out = run_netsh(["wlan", "delete", "profile", f'name="{name}"'])
        out_msgs.append(out)
    if remove_local:
        xml = find_xml_for_profile(name, folder)
        if xml and os.path.exists(xml):
            try:
                os.remove(xml)
                out_msgs.append(f"Deleted local file: {xml}")
            except Exception as e:
                out_msgs.append(f"Failed to delete local file {xml}: {e}")
        else:
            out_msgs.append(f"No local xml found for {name} in {folder}")
    # No hidden-list behavior: deleting local removes the XML file; forgetting Windows is performed if requested.
    return '\n'.join(out_msgs)


def create_and_add_profile(ssid, password, authentication="WPA2PSK", encryption="AES"):
    """Create a minimal profile XML with provided SSID/password and add it to Windows.

    Returns netsh output and the temp file path used.
    """
    xml_template = f'''<?xml version="1.0"?>
<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
  <name>{ssid}</name>
  <SSIDConfig>
    <SSID>
      <name>{ssid}</name>
    </SSID>
  </SSIDConfig>
  <connectionType>ESS</connectionType>
  <connectionMode>auto</connectionMode>
  <MSM>
    <security>
      <authEncryption>
        <authentication>{authentication}</authentication>
        <encryption>{encryption}</encryption>
        <useOneX>false</useOneX>
      </authEncryption>
      <sharedKey>
        <keyType>passPhrase</keyType>
        <protected>false</protected>
        <keyMaterial>{password}</keyMaterial>
      </sharedKey>
    </security>
  </MSM>
</WLANProfile>
'''
    fd, path = tempfile.mkstemp(suffix=".xml", prefix=f"wifi_{ssid}_")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(xml_template)
    out = import_profile_from_xml(path)
    return out, path


def connect_profile(name):
    """Connect to a profile by name (profile must exist)."""
    out = run_netsh(["wlan", "connect", f'name="{name}"'])
    return out


def interactive_menu():
    while True:
        print("\n=== Wi‑Fi Helper Menu ===")
        print("1) List saved profiles")
        print("2) Show profile details (incl. password, if available)")
        print("3) Export all profiles to XML")
        print("4) Import XML profile and connect")
        print("5) Add profile (enter SSID/password) and connect")
        print("6) Connect to an existing profile")
        print("0) Exit")
        choice = input("Choose an option: ").strip()
        if choice == "1":
            profiles = list_profiles()
            print("Saved profiles:")
            for p in profiles:
                print(" -", p)
        elif choice == "2":
            name = input("Profile name: ").strip()
            out, pwd = show_profile_details(name)
            print(out)
            if pwd:
                print(f"Recovered password: {pwd}")
            else:
                print("Password not found or not available.")
        elif choice == "3":
            folder = input("Export folder (default 'profiles'): ").strip() or "profiles"
            print(export_all_profiles(folder))
            print(f"Exported XMLs to {os.path.abspath(folder)} if permitted.")
        elif choice == "4":
            path = input("Path to profile XML: ").strip()
            print(import_profile_from_xml(path))
            name = input("Connect to profile name (press Enter to skip): ").strip()
            if name:
                print(connect_profile(name))
        elif choice == "5":
            ssid = input("SSID: ").strip()
            pwd = input("Password: ").strip()
            out, path = create_and_add_profile(ssid, pwd)
            print(out)
            print(f"Temporary XML used: {path}")
            print(connect_profile(ssid))
        elif choice == "6":
            name = input("Profile name to connect: ").strip()
            print(connect_profile(name))
        elif choice == "0":
            break
        else:
            print("Unknown option")


def main():
    parser = argparse.ArgumentParser(description="Simple Wi‑Fi helper for Windows (netsh wrapper)")
    parser.add_argument("--list", action="store_true", help="List saved Wi‑Fi profiles and exit")
    parser.add_argument("--show", metavar="NAME", help="Show profile details for NAME and exit")
    parser.add_argument("--export-all", metavar="FOLDER", nargs='?', const='profiles', help="Export all profiles to FOLDER and exit")
    parser.add_argument("--import", dest="import_file", metavar="FILE", help="Import profile XML FILE and exit")
    parser.add_argument("--connect", metavar="NAME", help="Connect to existing profile NAME and exit")
    args = parser.parse_args()

    if args.list:
        profiles = list_profiles()
        print("Saved profiles:")
        for p in profiles:
            print(" -", p)
        return
    if args.show:
        out, pwd = show_profile_details(args.show)
        print(out)
        if pwd:
            print(f"Recovered password: {pwd}")
        return
    if args.export_all is not None:
        out = export_all_profiles(args.export_all)
        print(out)
        return
    if args.import_file:
        print(import_profile_from_xml(args.import_file))
        return
    if args.connect:
        print(connect_profile(args.connect))
        return

    # No CLI flags → interactive mode
    interactive_menu()


if __name__ == "__main__":
    main()
