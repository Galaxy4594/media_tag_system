import os
import platform
import sys
import argparse
import shutil
import subprocess
import json
from enum import Enum, auto
from urllib.request import Request, urlopen
from typing import List, Dict, BinaryIO

# -------------------------------------------------------------------------
# Script made to download thirdparty stuff quickly
# -------------------------------------------------------------------------

# Win32 Console Color Printing
_win32_legacy_con = False
_win32_handle = None

if os.name == "nt":
    if platform.release().startswith("10"):
        subprocess.call('', shell=True)
    else:
        import ctypes
        _win32_handle = ctypes.windll.kernel32.GetStdHandle(-11)
        _win32_legacy_con = True


class Color(Enum):
    if _win32_legacy_con:
        RED = "4"
        DGREEN = "2"
        GREEN = "10"
        YELLOW = "6"
        BLUE = "1"
        MAGENTA = "13"
        CYAN = "3"
        DEFAULT = "7"
    else:
        RED = "\033[0;31m"
        DGREEN = "\033[0;32m"
        GREEN = "\033[1;32m"
        YELLOW = "\033[0;33m"
        BLUE = "\033[0;34m"
        MAGENTA = "\033[1;35m"
        CYAN = "\033[0;36m"
        DEFAULT = "\033[0m"


class Severity(Enum):
    WARNING = Color.YELLOW
    ERROR = Color.RED


WARNING_COUNT = 0


def warning(*text):
    _print_severity(Severity.WARNING, "\n          ", *text)
    global WARNING_COUNT
    WARNING_COUNT += 1


def error(*text):
    _print_severity(Severity.ERROR, "\n        ", *text, "\n")
    quit(1)


def verbose(*text):
    print("".join(text))


def verbose_color(color: Color, *text):
    print_color(color, "".join(text))


def _print_severity(level: Severity, spacing: str, *text):
    print_color(level.value, f"[{level.name}] {spacing.join(text)}")


def win32_set_fore_color(color: int):
    ctypes.windll.kernel32.SetConsoleTextAttribute(_win32_handle, color)


def stdout_color(color: Color, *text):
    if _win32_legacy_con:
        win32_set_fore_color(int(color.value))
        sys.stdout.write("".join(text))
        win32_set_fore_color(int(Color.DEFAULT.value))
    else:
        sys.stdout.write(color.value + "".join(text) + Color.DEFAULT.value)


def print_color(color: Color, *text):
    stdout_color(color, *text, "\n")


def set_con_color(color: Color):
    if _win32_legacy_con:
        win32_set_fore_color(int(color.value))
    else:
        sys.stdout.write(color.value)


class OS(Enum):
    Any = auto(),
    Windows = auto(),
    Linux = auto(),


PUBLIC_DIR = "../public"
BUILD_DIR = "build"

if sys.platform in {"linux", "linux2"}:
    SYS_OS = OS.Linux
elif sys.platform == "win32":
    SYS_OS = OS.Windows
else:
    SYS_OS = None
    print("Error: unsupported/untested platform: " + sys.platform)
    quit(1)


if SYS_OS == OS.Windows:
    DLL_EXT = ".dll"
    EXE_EXT = ".exe"
    LIB_EXT = ".lib"
elif SYS_OS == OS.Linux:
    DLL_EXT = ".so"
    EXE_EXT = ""
    LIB_EXT = ".a"


VS_PATH = ""
VS_DEVENV = ""
VS_MSBUILD = ""
VS_MSVC = "v143"

ERROR_LIST = []
CUR_PROJECT = "PROJECT"
ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
DIR_STACK = []


def set_project(name: str):
    global CUR_PROJECT
    CUR_PROJECT = name
    print(f"\n"
          f"---------------------------------------------------------\n"
          f" Current Project: {name}\n"
          f"---------------------------------------------------------\n")


def push_dir(path: str):
    abs_dir = os.path.abspath(path)
    DIR_STACK.append(abs_dir)
    os.chdir(abs_dir)


def pop_dir():
    if len(DIR_STACK) == 0:
        print("ERROR: DIRECTORY STACK IS EMPTY!")
        return
    abs_dir = DIR_STACK.pop()
    os.chdir(abs_dir)


def reset_dir():
    os.chdir(ROOT_DIR)


def syscmd_err(ret: int, string: str):
    global CUR_PROJECT
    err_str = f"{CUR_PROJECT}: {string}: return code {ret}\n"
    ERROR_LIST.append(err_str)
    sys.stderr.write(err_str)


def syscmd(cmd: str, string: str) -> bool:
    ret = os.system(cmd)
    if ret == 0:
        return True
    syscmd_err(ret, string)
    return False


def syscall(cmd: list, string: str) -> bool:
    ret = subprocess.call(cmd)
    if ret == 0:
        return True
    syscmd_err(ret, string)
    return False


def setup_vs_env():
    cmd = "vswhere.exe -latest"
    global VS_PATH
    global VS_DEVENV
    global VS_MSBUILD

    vswhere = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    for line in vswhere.stdout:
        if line.startswith("productPath"):
            VS_DEVENV = line[len("productPath: "):-1]
            print(f"Set VS_DEVENV to \"{VS_DEVENV}\"")
        elif line.startswith("installationPath"):
            VS_PATH = line[len("installationPath: "):-1]
            print(f"Set VS_PATH to \"{VS_PATH}\"")

    if VS_PATH == "" or VS_DEVENV == "":
        print("FATAL ERROR: Failed to find VS_DEVENV or VS_PATH?")
        quit(3)

    VS_MSBUILD = VS_PATH + "\\Msbuild\\Current\\Bin\\amd64\\msbuild.exe"


def parse_args() -> argparse.Namespace:
    args = argparse.ArgumentParser()
    args.add_argument("-nb", "--no-build", action="store_true", help="Don't build the libraries")
    args.add_argument("-t", "--target", nargs="+", help="Only download and build specific libraries")
    args.add_argument("-f", "--force", action="store_true", help="Force Run Everything")
    args.add_argument("-c", "--clean", action="store_true", help="Clean Everything in the thirdparty folder")
    return args.parse_args()


# =================================================================================================


def post_mozjpeg_extract():
    if ARGS.no_build:
        return
        
    set_project("MozJPEG")

    os.chdir("mozjpeg")

    build_options = "-DPNG_SUPPORTED=0 -DCMAKE_POLICY_VERSION_MINIMUM=3.5"

    if not syscmd(f"cmake -B build {build_options} .", "Failed to run cmake"):
        return

    print("Building MozJPEG - Release\n")
    if not syscmd(f"cmake --build ./build --config Release --parallel", "Failed to build in Release"):
        return

    print("Building MozJPEG - Debug\n")
    if not syscmd(f"cmake --build ./build --config Debug --parallel", "Failed to build in Debug"):
        return


# =================================================================================================

def post_zlib_extract():
	if ARGS.no_build:
		return

	set_project("zlib-ng")
	os.chdir("zlib-ng")

	build_options = "-DWITH_GTEST=OFF -DZLIB_COMPAT=ON"

	if not syscmd(f"cmake -B build {build_options} .", "Failed to run cmake"):
		return

	print("Building zlib-ng - Release\n")
	if not syscmd("cmake --build ./build --config Release --parallel", "Failed to build in Release"):
		return

# =================================================================================================

def find_file_in_tree(root_dir: str, target_filename: str) -> str:
    """Helper to dynamically find where an archive extracted a specific header or lib."""
    if not os.path.exists(root_dir):
        return ""
    for root, _, files in os.walk(root_dir):
        if target_filename in files:
            return os.path.join(root, target_filename)
        for f in files:
            if f.startswith(target_filename):
                return os.path.join(root, f)
    return ""


def post_freetype_extract():
    if ARGS.no_build:
        return

    set_project("Freetype")
    os.chdir("freetype")

    if SYS_OS == OS.Windows:
        for cfg in {"Debug Static", "Release Static"}:
            cmd = [VS_MSBUILD, "builds\\windows\\vc2010\\freetype.vcxproj", f"-property:Configuration={cfg}", "-property:Platform=x64"]
            subprocess.call(cmd)
    else:
        cmake_cmd = (
            "cmake -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF "
            "-DFT_DISABLE_ZLIB=TRUE -DFT_DISABLE_BZIP2=TRUE -DFT_DISABLE_PNG=TRUE "
            "-DFT_DISABLE_HARFBUZZ=TRUE -DFT_DISABLE_BROTLI=TRUE ."
        )
        if not syscmd(cmake_cmd, "Failed to run cmake"):
            return
            
        print("Building Freetype - Release\n")
        if not syscmd("cmake --build ./build --config Release --parallel", "Failed to build in Release"):
            return


def post_libspng_extract():
    if ARGS.no_build:
        return

    set_project("libspng")
    os.chdir("libspng")

    zlib_dir = os.path.abspath("../zlib-ng")
    
    # 1. Dynamically find where zlib.h landed inside ../zlib-ng
    zlib_header_path = find_file_in_tree(zlib_dir, "zlib.h")
    if not zlib_header_path:
        print_color(Color.RED, f"FATAL: Could not find zlib.h anywhere inside {zlib_dir}")
        return
    zlib_inc_dir = os.path.dirname(zlib_header_path)

    # 2. Dynamically find where the static/import library landed
    zlib_lib = ""
    if SYS_OS == OS.Windows:
        for lib_name in ("zlibstatic.lib", "zlib.lib", "zlib-ng.lib", "zlib-ng-static.lib"):
            zlib_lib = find_file_in_tree(zlib_dir, lib_name)
            if zlib_lib:
                break
    elif SYS_OS == OS.Linux:
        for lib_name in ("libz.so", "libz.a", "libzlib-ng.so", "libzlib-ng.a"):
            zlib_lib = find_file_in_tree(zlib_dir, lib_name)
            if zlib_lib:
                break

    if not zlib_lib:
        print_color(Color.RED, f"FATAL: Could not find compiled zlib library archive inside {zlib_dir}")
        return

    print_color(Color.CYAN, f"Auto-detected ZLIB include dir: {zlib_inc_dir}")
    print_color(Color.CYAN, f"Auto-detected ZLIB library: {zlib_lib}")

    build_options = f"-DBUILD_EXAMPLES=OFF -DSPNG_SHARED=ON -DZLIB_LIBRARY=\"{zlib_lib}\" -DZLIB_INCLUDE_DIR=\"{zlib_inc_dir}\""

    if not syscmd(f"cmake -B build {build_options} .", "Failed to run cmake"):
        return

    print("Building libspng - Release\n")
    if not syscmd("cmake --build ./build --config Release --parallel", "Failed to build in Release"):
        return


def compile_nativefiledialog():
    if ARGS.no_build:
        return
    set_project("Native File Dialog")
    os.chdir("nativefiledialog")

    if not syscmd("cmake -B build .", "Failed to run cmake"):
        return

    print("Building nativefiledialog - RelWithDebInfo\n")
    if not syscmd("cmake --build ./build --config RelWithDebInfo --parallel", "Failed to build in RelWithDebInfo"):
        return

    print("Building nativefiledialog - Release\n")
    if not syscmd("cmake --build ./build --config Release --parallel", "Failed to build in Release"):
        return

    print("Building nativefiledialog - Debug\n")
    if not syscmd("cmake --build ./build --config Debug --parallel", "Failed to build in Debug"):
        return


def compile_libfyaml():
    if ARGS.no_build:
        return
    set_project("libfyaml")
    os.chdir("libfyaml")

    if not syscmd("cmake -B build -DENABLE_NETWORK=OFF -DBUILD_TESTING=OFF .", "Failed to run cmake"):
        return

    print("Building libfyaml - RelWithDebInfo\n")
    if not syscmd("cmake --build ./build --config RelWithDebInfo --parallel", "Failed to build in RelWithDebInfo"):
        return

    print("Building libfyaml - Release\n")
    if not syscmd("cmake --build ./build --config Release --parallel", "Failed to build in Release"):
        return

    print("Building libfyaml - Debug\n")
    if not syscmd("cmake --build ./build --config Debug --parallel", "Failed to build in Debug"):
        return


def libjxl_run():
    set_project("jxl")

    # Stable version of libjxl to use
    branch = "v0.12.x"

    # TODO: implement a global basic version check system for tasks
    # check version
    redownload = False
    if os.path.isdir("libjxl"):
        if os.path.isfile("libjxl/IMAGE_VIEW_VERSION"):
            version = ""
            with open("libjxl/IMAGE_VIEW_VERSION", "r") as version_io:
                version = version_io.read()

            if version != branch:
                print_color(Color.YELLOW, f"JXL: Version mismatch: got version {version}, expected {branch}")
                redownload = True
        else:
            print_color(Color.YELLOW, "JXL: Version file not found, redownloading!")
            redownload = True

    if redownload:
        shutil.rmtree("libjxl")

    if not os.path.isdir("libjxl"):
        if not syscmd(f"git clone --depth 1 https://github.com/libjxl/libjxl.git -b {branch} --recursive --shallow-submodules", "Failed to clone libjxl with git"):
            return

        with open("libjxl/IMAGE_VIEW_VERSION", "w") as version_io:
            version_io.write(branch)

        # add spacing
        print()

    os.chdir("libjxl")

    defines = "-DBUILD_SHARED_LIBS=ON -DJPEGXL_ENABLE_FUZZERS=OFF -DCXX_FUZZERS_SUPPORTED=OFF -DJPEGXL_ENABLE_DOXYGEN=OFF -DJPEGXL_ENABLE_MANPAGES=OFF -DJPEGXL_ENABLE_EXAMPLES=OFF -DJPEGXL_ENABLE_JNI=OFF -DJPEGXL_ENABLE_OPENEXR=OFF -DJPEGXL_ENABLE_SJPEG=OFF -DJPEGXL_ENABLE_BENCHMARK=OFF -DBUILD_TESTING=OFF -DJPEGXL_ENABLE_TOOLS=OFF"

    if not syscmd(f"cmake -B build -DCMAKE_BUILD_TYPE=Release {defines}", "Failed to run cmake"):
        return

    print("Building jxl - Release\n")
    if not syscmd("cmake --build ./build --config Release --parallel", "Failed to build in Release"):
        return
        
    print("Building jxl - Debug\n")
    if not syscmd("cmake --build ./build --config Debug --parallel", "Failed to build in Debug"):
        return


def compile_sdl3():
    set_project("SDL3")
    os.chdir("SDL3")

    if not syscmd("cmake -B build -DCMAKE_BUILD_TYPE=Release -DSDL_STATIC=OFF -DSDL_SHARED=ON .", "Failed to run cmake"):
        return

    print("Building SDL3 - Release\n")
    if not syscmd("cmake --build ./build --config Release --parallel", "Failed to build in Release"):
        return


# =================================================================================================

def get_latest_mpv_release():
    api_url = "https://api.github.com/repos/shinchiro/mpv-winbuild-cmake/releases/latest"
    req = Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        response = urlopen(req, timeout=30)
        data = json.loads(response.read().decode('utf-8'))
        for asset in data.get('assets', []):
            name = asset.get('name', '')
            if name.startswith('mpv-dev-x86_64-v3-'):
                return asset.get('browser_download_url'), name
    except Exception as e:
        print(f"Error fetching latest mpv release from GitHub API: {e}")
    return None, None

mpv_url, mpv_file = get_latest_mpv_release()

# =================================================================================================

TASK_LIST = {
    # Windows Only
    OS.Windows: [
        {
            "name": "mozjpeg",
            "url":  "https://github.com/mozilla/mozjpeg/archive/refs/tags/v4.1.1.zip",
            "file": "mozjpeg-4.1.1.zip",
            "func": post_mozjpeg_extract,
        },
        {
            "name": "zlib-ng",
            "url":  "https://github.com/zlib-ng/zlib-ng/releases/download/2.2.5/zlib-ng-win-x86-64-compat.zip",
            "file": "zlib-ng-win-x86-64-compat.zip",
            "extract_folder": "zlib-ng",  # Added so it extracts into its own folder!
        },
        {
            "name": "libspng",
            "url":  "https://github.com/randy408/libspng/archive/v0.7.4.zip",
            "file": "libspng-0.7.4.zip",
            "func": post_libspng_extract,
        },
        {
            "name": "nativefiledialog",
            "url":  "https://github.com/btzy/nativefiledialog-extended/archive/refs/tags/v1.2.1.zip",
            "file": "nativefiledialog-extended-1.2.1.zip",
            "func": compile_nativefiledialog,
        },
        {
            "name": "libfyaml",
            "url":  "https://github.com/pantoniou/libfyaml/releases/download/v0.9.5/libfyaml-0.9.5.tar.gz",
            "file": "libfyaml-0.9.5.tar.gz",
            "func": compile_libfyaml,
        },
        {
            "name": "vswhere",
            "url":  "https://github.com/microsoft/vswhere/releases/download/2.8.4/vswhere.exe",
            "file": "vswhere.exe",
            "func": setup_vs_env,
        },
        {
            "name": "freetype",
            "url":  "https://github.com/ubawurinna/freetype-windows-binaries/archive/refs/tags/v2.14.2.zip",
            "file": "freetype-v2.14.2-windows.zip",
            "extracted_folder": "freetype-windows-binaries-2.14.2",
        },
        {
            "name": "jxl",
            "url":  "https://github.com/libjxl/libjxl/releases/download/v0.12.0/jxl-x64-windows.7z",
            "file": "jxl-x64-windows.7z",
            "extracted_folder": "x64-windows",
        },
        {
            "name": "SDL3",
            "url":  "https://github.com/libsdl-org/SDL/releases/download/release-3.2.24/SDL3-devel-3.2.24-VC.zip",
            "file": "SDL3-3.2.24.zip",
        },
        {
            "name": "FreeImageRe",
            "url":  "https://github.com/agruzdev/FreeImageRe/releases/download/v4.2.0/FreeImageRe-v4.2.0-win64.zip",
            "extract_folder": "FreeImageRe",
            "file": "FreeImageRe-v4.2.0-win64.zip",
        },
        {
            "name": "mpv",
            "url":  mpv_url,
            "file": mpv_file,
            "extract_folder": "mpv",
            "user_extract": False,
        },
    ],

    # Linux Only
    OS.Linux: [
        {
            "name": "mozjpeg",
            "url":  "https://github.com/mozilla/mozjpeg/archive/refs/tags/v4.1.1.zip",
            "file": "mozjpeg-4.1.1.zip",
            "func": post_mozjpeg_extract,
        },
        {
            "name": "zlib-ng",
            "url":  "https://github.com/zlib-ng/zlib-ng/archive/refs/tags/2.2.5.zip",
            "file": "zlib-ng-2.2.5.zip",
            "func": post_zlib_extract,
        },
        {
            "name": "libspng",
            "url":  "https://github.com/randy408/libspng/archive/v0.7.4.zip",
            "file": "libspng-0.7.4.zip",
            "func": post_libspng_extract,
        },
        {
            "name": "nativefiledialog",
            "url":  "https://github.com/btzy/nativefiledialog-extended/archive/refs/tags/v1.2.1.zip",
            "file": "nativefiledialog-extended-1.2.1.zip",
            "func": compile_nativefiledialog,
        },
        {
            "name": "libfyaml",
            "url":  "https://github.com/pantoniou/libfyaml/releases/download/v0.9.5/libfyaml-0.9.5.tar.gz",
            "file": "libfyaml-0.9.5.tar.gz",
            "func": compile_libfyaml,
        },
        {
            "name": "FreeImageRe",
            "url":  "https://github.com/agruzdev/FreeImageRe/releases/download/v4.1.1/FreeImageRe-v4.1.1-linux64.zip",
            "extract_folder": "FreeImageRe",
            "file": "FreeImageRe-v4.1.1-linux64.zip",
        },
        {
            "name": "freetype",
            "url":  "https://nongnu.askapache.com/freetype/freetype-2.14.1.tar.xz",
            "file": "freetype-2.14.1.tar.xz",
            "func": post_freetype_extract,
        },
        {
            "name": "jxl",
            "func": libjxl_run,
        },
        {
            "name": "SDL3",
            "url":  "https://github.com/libsdl-org/SDL/archive/refs/tags/release-3.2.24.tar.gz",
            "file": "SDL3-release-3.2.24.tar.gz",
            "extracted_folder": "SDL-release-3.2.24",
            "func": compile_sdl3,
        },
    ],
}


# =================================================================================================
# 7-ZIP DOWNLOADER & EXTRACTION ENGINE
# =================================================================================================

SEVEN_ZIP_EXE = None

def get_7z() -> str:
    """Finds 7z.exe in PATH, Program Files, or downloads standalone 7zr.exe locally."""
    global SEVEN_ZIP_EXE
    if SEVEN_ZIP_EXE and os.path.exists(SEVEN_ZIP_EXE):
        return SEVEN_ZIP_EXE

    # 1. Check System PATH
    for name in ("7z", "7za", "7zr"):
        found = shutil.which(name)
        if found:
            SEVEN_ZIP_EXE = found
            return SEVEN_ZIP_EXE

    # 2. Check Standard Windows Install Locations
    if SYS_OS == OS.Windows:
        for path in (
            r"C:\Program Files\7-Zip\7z.exe",
            r"C:\Program Files (x86)\7-Zip\7z.exe",
        ):
            if os.path.isfile(path):
                SEVEN_ZIP_EXE = path
                return SEVEN_ZIP_EXE

    # 3. Check Local Fallback in Script Directory
    local_7z = os.path.join(ROOT_DIR, "7zr.exe" if SYS_OS == OS.Windows else "7zr")
    if os.path.isfile(local_7z):
        SEVEN_ZIP_EXE = local_7z
        return SEVEN_ZIP_EXE

    # 4. Download Standalone 7zr.exe if on Windows and missing
    if SYS_OS == OS.Windows:
        print_color(Color.GREEN, "7-Zip not found. Downloading standalone 7zr.exe...")
        file_data = download_file("https://www.7-zip.org/a/7zr.exe")
        if file_data and write_file(local_7z, file_data):
            SEVEN_ZIP_EXE = local_7z
            return SEVEN_ZIP_EXE

    return ""


def download_file(url: str) -> bytes:
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        response = urlopen(req, timeout=120)
        file_data: bytes = response.read()
    except Exception as F:
        error("Error opening url: ", url, "\n", str(F), "\n")
        return b""
    return file_data


def write_file(file: str, file_data: bytes) -> bool:
    try:
        with open(file, mode="wb") as file_io:
            file_io.write(file_data)
    except Exception as E:
        print(f"Failed to write \"{file}\", {E}")
        return False
    return True


def extract_file_user(file: str, folder: str) -> bool:
    print("\007")  # Play bell/error sound
    print(f"Please extract the file \"{file}\" into a folder named \"{folder}\" yourself, extraction failed.")
    input("Press Enter when finished")

    if not os.path.exists(folder):
        print("Extracted folder does not exist? Skipping")
        return False
    return True


def extract_file(tmp_file: str, file_ext: str, tmp_folder: str, folder: str, user_extract: bool) -> bool:
    if not os.path.isdir(folder):
        os.makedirs(folder)

    if user_extract:
        return extract_file_user(tmp_file, tmp_folder)

    if file_ext == "exe":
        if os.path.exists(tmp_file):
            os.remove(tmp_file)
        return True

    seven_zip = get_7z()
    return_value = False

    # 1. Try 7-Zip first (Handles .7z, .xz, and .zip if full 7z.exe is installed)
    if seven_zip:
        print_color(Color.CYAN, f"Extracting {tmp_file} using 7-Zip...")
        cmd = [seven_zip, "x", tmp_file, f"-o{folder}", "-y"]
        res = subprocess.call(cmd)
        if res == 0:
            return_value = True
            # Check if 7z decompressed an outer archive (e.g. .tar.xz) leaving an un-extracted .tar file
            if os.path.isdir(folder):
                for item in os.listdir(folder):
                    if item.endswith(".tar"):
                        tar_path = os.path.join(folder, item)
                        try:
                            shutil.unpack_archive(tar_path, extract_dir=folder)
                            os.remove(tar_path)
                        except Exception:
                            pass
        else:
            print_color(Color.YELLOW, f"7z extraction returned exit code {res}. Attempting OS/Python fallback...")

    # 2. Try native OS tar (Handles Deflate64 ZIPs and tarballs when 7zr standalone fails)
    if not return_value and shutil.which("tar"):
        try:
            res = subprocess.call(["tar", "-xf", tmp_file, "-C", folder])
            if res == 0:
                return_value = True
        except Exception:
            pass

    # 3. Fallback to Python standard library
    if not return_value:
        try:
            shutil.unpack_archive(tmp_file, extract_dir=folder)
            return_value = True
        except Exception as e:
            print_color(Color.RED, f"All extraction methods failed: {e}")
            return_value = extract_file_user(tmp_file, tmp_folder)

    if os.path.exists(tmp_file):
        os.remove(tmp_file)
    return return_value


def handle_item(item: dict):
    url = item.get("url", "")
    file = item.get("file", "")
    name = item.get("name", "")
    func = item.get("func", None)
    extracted_folder = item.get("extracted_folder", None)
    extract_folder = item.get("extract_folder", ".")
    user_extract = item.get("user_extract", False)

    if ARGS.target is not None:
        if name not in ARGS.target:
            return

    if file:
        folder, file_ext = file.rsplit(".", 1)
        is_zip = file_ext in ("zip", "7z", "xz", "gz")

        if not url:
            err_str = f"Project \"{name}\" Has a download file specified, but no url to download it!"
            ERROR_LIST.append(err_str)
            sys.stderr.write(err_str)
            return

        if folder.endswith(".tar"):
            folder = folder.rsplit(".", 1)[0]

        if extracted_folder:
            folder = extracted_folder

        if not os.path.isdir(name) or ARGS.force or not is_zip:
            print_color(Color.CYAN, f"Downloading \"{name}\"")

            file_data: bytes = download_file(url)
            if file_data == b"":
                return

            tmp_file = file if (user_extract or not is_zip) else ("tmp." + file)

            if not write_file(tmp_file, file_data):
                return False

            if is_zip:
                if not extract_file(tmp_file, file_ext, folder, extract_folder, user_extract):
                    return

                if folder != name and extract_folder == "." and os.path.exists(folder):
                    if os.path.exists(name):
                        shutil.rmtree(name)
                    os.rename(folder, name)
        else:
            print_color(Color.CYAN, f"Already Downloaded: {name}")

    if func:
        print_color(Color.CYAN, f"Running Task Function: \"{name}\"")
        try:
            func()
        except Exception as e:
            print(f"Task Function Crashed with error: {e}")
        finally:
            reset_dir()


def check_linux_dependencies():
    import time
    missing_packages = []
    
    try:
        subprocess.run(["pkg-config", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except FileNotFoundError:
        print_color(Color.YELLOW, "Warning: pkg-config not found! Cannot verify if system dependencies are installed.\n")
        return
    except subprocess.CalledProcessError:
        pass

    def check_pkg(pkg_name, desc):
        result = subprocess.run(["pkg-config", "--exists", pkg_name])
        if result.returncode != 0:
            missing_packages.append(desc)

    check_pkg("mpv", "MPV (e.g. libmpv-dev or mpv-devel)")
    check_pkg("gtk+-3.0", "GTK3 (e.g. libgtk-3-dev or gtk3-devel)")

    if missing_packages:
        print_color(Color.RED, f"\nWARNING: You are missing required system development libraries!")
        print_color(Color.RED, f"Please use your distribution's package manager to install the development headers for:")
        for pkg in missing_packages:
            print_color(Color.RED, f"  - {pkg}")
        print_color(Color.RED, "")
        time.sleep(3)


def main():
    if SYS_OS == OS.Linux:
        check_linux_dependencies()
    if ARGS.clean:
        print("NOT IMPLEMENTED YET!!!")
        return

    for item in TASK_LIST[SYS_OS]:
        handle_item(item)
        reset_dir()

    print("\n---------------------------------------------------------\n")



    errors_str = "Error" if len(ERROR_LIST) == 1 else "Errors"
    if len(ERROR_LIST) > 0:
        print("\n---------------------------------------------------------")
        sys.stderr.write(f"\n{len(ERROR_LIST)} {errors_str}:\n")
        for err in ERROR_LIST:
            sys.stderr.write(err)

    print(f"\n"
          f"---------------------------------------------------------\n"
          f" Finished - {len(ERROR_LIST)} {errors_str}\n"
          f"---------------------------------------------------------\n")

    if len(ERROR_LIST) > 0:
        exit(-1)


if __name__ == "__main__":
    ARGS = parse_args()
    main()