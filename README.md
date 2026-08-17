# Media Tag System

## Usage
- Copy config_default.yaml to config.yaml, change anything if needed
- Bookmarks are stored in config.yaml, the program does not write and added bookmarks or config changes, you need to add it yourself for now
- Enter toggles between gallery view and media/fullscreen view when selected on an image or video
- Files or folders can be dragged in to enter them or look at the file

## Build Requirements

- CMake 3.20+
- Python 3
- Visual Studio 2022+ (Windows only)

The build system will automatically download and configure most dependencies via a combination of a Python script and CMake's `FetchContent`. 

### System Dependencies

If you prefer to install dependencies globally via a package manager rather than letting CMake fetch and build them from source, the full list of libraries used is:
- `libmpv` (Must be installed globally on Linux)
- `SDL3`
- `libjpeg-turbo`
- `libjxl`
- `libfyaml`
- `freetype` (freetype2)
- `libspng`
- `nativefiledialog` (nfd)
- `FreeImage`
- `libheif`

## Building

### Linux
Open a terminal and run:
```bash
cd thirdparty
./thirdparty.sh
cd ..
cmake -B build . && cmake --build build --config Release --parallel
```

### Windows
Open the **x64 Native Tools Command Prompt for VS** and run:
```cmd
cd thirdparty
thirdparty.cmd
cd ..
cmake_run.cmd
```
Or just `cmake -B build .` and open media_tag_system.sln and build from there

The compiled binaries will be placed in the `out/` folder, ready to run.
