import argparse
import fileinput
import shutil
import os
from pathlib import Path
import subprocess
import urllib.request

parser = argparse.ArgumentParser(description="Install Ghidra light theme")
parser.add_argument("--path", dest="install_path", type=str, default=None,
                    help="The installation path for Ghidra")
args = parser.parse_args()

if os.name == "nt":
    find_ghidra = "WMIC path win32_process get Commandline"
    launch_sh = "launch.bat"
    install_dir = ";%INSTALL_DIR%"
    cpath = "set CPATH="
else:
    find_ghidra = "ps -ax"
    launch_sh = "launch.sh"
    install_dir = ":${INSTALL_DIR}/"
    cpath = "CPATH="

out = subprocess.check_output(find_ghidra.split())
if b"ghidrarun" in out.lower():
    print("Please close any running Ghidra instances")
    exit(-1)

install_path = args.install_path
if not install_path:
    # Attempt to find the installation directory based on `ghidraRun`
    ghidra_run_path = shutil.which("ghidraRun")
    if not ghidra_run_path:
        print("Could not find Ghidra installation, run with --path")
        exit(-1)
    else:
        install_path = Path(ghidra_run_path).parents[0]

print(f"Using Ghidra installation path: {install_path}")

# Get the version from the application.properties file
version = ""
properties_path = os.path.join(install_path, "Ghidra", "application.properties")
with open(properties_path, "r") as fp:
    for line in fp:
        if "application.version=" in line:
            version = line.split("=")[-1].strip()

print(f"Detected Ghidra v{version}")

flatlaf_path = os.path.join(install_path, "flatlaf-0.43.jar")
flatlaf_url = "https://bintray.com/jformdesigner/flatlaf/download_file?file_path=com/formdev/flatlaf/0.43/flatlaf-0.43.jar"

# Download the FlatLaf jar
if not os.path.exists(flatlaf_path):
    print("Downloading FlatLaf")
    response = urllib.request.urlopen(flatlaf_url)
    with open(flatlaf_path, "wb") as fp:
        fp.write(response.read())

launch_sh_path = os.path.join(install_path, "support", launch_sh)
launch_properties_path = os.path.join(install_path, "support", "launch.properties")

# Add FlatLaf to the list of jar files
with fileinput.FileInput(launch_sh_path, inplace=True, backup=".bak") as fp:
    for line in fp:
        if line.strip().startswith(cpath) and "flatlaf" not in line:
            if os.name == "nt":
                print(f"{line.rstrip()}{install_dir}flatlaf-0.43.jar")
            else:
                print(f"{line.rstrip()[:-1]}{install_dir}flatlaf-0.43.jar\"")
        else:
            print(line, end="")

# Check if FlatLaf is the system L&f
flatlaf_set = False
with open(launch_properties_path, "r") as fp:
    for line in fp:
        if "flatlaf" in line:
            flatlaf_set = True
            break

# Set FlatLaf as the system L&f
if not flatlaf_set:
    with open(launch_properties_path, "a") as fp:
        fp.write("\nVMARGS=-Dswing.systemlaf=com.formdev.flatlaf.FlatLightLaf")

# _PUBLIC was appended to the name after 9.0.4
# The "-" after .ghidra was changed to "_" after 9.0.4
if tuple(map(int, (version.split(".")))) > (9, 0, 4):
    version_path = f".ghidra_{version}_PUBLIC"
else:
    version_path = f".ghidra-{version}"

ghidra_home_path = os.path.join(Path.home(), ".ghidra", version_path)
preferences_path = os.path.join(ghidra_home_path, "preferences")
code_browser_path = os.path.join(ghidra_home_path, "tools", "_code_browser.tcd")
code_browser_bak_path = os.path.join(ghidra_home_path, "tools", "_code_browser.tcd.bak")

print(f"Using Ghidra home path: {ghidra_home_path}")

# Check if the current L&f is system
using_system = False
with open(preferences_path, "r") as fp:
    for line in fp:
        if "LastLookAndFeel=System" in line:
            using_system = True
            break

# Set the L&f to system
if not using_system:
    with open(preferences_path, "a") as fp:
        fp.write("LastLookAndFeel=System\n")
