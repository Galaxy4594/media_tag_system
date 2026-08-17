cmake_minimum_required( VERSION 3.18 FATAL_ERROR )

# use folders for visual studio
set_property( GLOBAL PROPERTY USE_FOLDERS ON )

set( CMAKE_CONFIGURATION_TYPES "Debug;Release;RelWithDebInfo" )

set( CMAKE_POSITION_INDEPENDENT_CODE ON )
set( CMAKE_SHARED_LIBRARY_PREFIX "" )

option( MIMALLOC "Use mimalloc" OFF )

project( media_tag_system )

include(FetchContent)

set(WITH_GTEST OFF CACHE BOOL "" FORCE)
set(ZLIB_COMPAT ON CACHE BOOL "" FORCE)

# --- zlib-ng Conditional Loading ---
find_package(PkgConfig QUIET)
if(PkgConfig_FOUND)
    pkg_check_modules(ZLIBNG QUIET zlib-ng)
endif()
if(NOT ZLIBNG_FOUND)
    find_package(ZLIB QUIET)
endif()

if(ZLIBNG_FOUND OR ZLIB_FOUND)
    message(STATUS "Found zlib/zlib-ng on system")
    # ZLIB_LIBRARIES is already set by find_package
elseif(EXISTS "${CMAKE_CURRENT_LIST_DIR}/thirdparty/zlib-ng/include/zlib.h")
    message(STATUS "Found zlib-ng in thirdparty folder")
    set(ZLIB_ROOT "${CMAKE_CURRENT_LIST_DIR}/thirdparty/zlib-ng")
    find_package(ZLIB REQUIRED)
else()
    message(STATUS "zlib/zlib-ng not found on system or thirdparty, using FetchContent")
    FetchContent_Declare(
        zlib-ng
        GIT_REPOSITORY https://github.com/zlib-ng/zlib-ng.git
        GIT_TAG 2.3.3
    )
    FetchContent_MakeAvailable(zlib-ng)
    set(ZLIB_LIBRARIES zlib)
endif()

set(WITH_TOOLS OFF CACHE BOOL "" FORCE)
set(WITH_TESTS OFF CACHE BOOL "" FORCE)
set(WITH_SYSTEM_SPNG ON CACHE BOOL "" FORCE)
set(WITH_SYSTEM_ZLIB ON CACHE BOOL "" FORCE)
set(PNG_SUPPORTED OFF CACHE BOOL "" FORCE)
FetchContent_Declare(
    libjpeg-turbo
    GIT_REPOSITORY https://github.com/libjpeg-turbo/libjpeg-turbo.git
    GIT_TAG 3.2.0
)

set(BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(SPNG_SHARED ON CACHE BOOL "" FORCE)
FetchContent_Declare(
    libspng
    GIT_REPOSITORY https://github.com/randy408/libspng.git
    GIT_TAG v0.7.4
)

FetchContent_Declare(
    freetype
    URL https://nongnu.askapache.com/freetype/freetype-2.14.1.tar.xz
)

FetchContent_Declare(
    nativefiledialog
    GIT_REPOSITORY https://github.com/btzy/nativefiledialog-extended.git
    GIT_TAG v1.2.1
)

set(ENABLE_NETWORK OFF CACHE BOOL "" FORCE)
set(BUILD_TESTING OFF CACHE BOOL "" FORCE)
FetchContent_Declare(
    libfyaml
    GIT_REPOSITORY https://github.com/pantoniou/libfyaml.git
    GIT_TAG v1.0.0-alpha8
)

FetchContent_MakeAvailable(libspng freetype nativefiledialog libfyaml)

# --- libjxl Conditional Loading ---
find_package(PkgConfig QUIET)
if(PkgConfig_FOUND)
    pkg_check_modules(JXL QUIET libjxl)
endif()

if(JXL_FOUND)
    message(STATUS "Found libjxl via pkg-config")
    include_directories(${JXL_INCLUDE_DIRS})
    link_directories(${JXL_LIBRARY_DIRS})
    set(JXL_LIBS ${JXL_LIBRARIES})
elseif(EXISTS "${CMAKE_CURRENT_LIST_DIR}/thirdparty/libjxl/x64-windows/include")
    message(STATUS "Found libjxl in thirdparty folder")
    include_directories("${CMAKE_CURRENT_LIST_DIR}/thirdparty/libjxl/x64-windows/include")
    if ( WIN32 )
        link_directories("${CMAKE_CURRENT_LIST_DIR}/thirdparty/libjxl/x64-windows/lib")
    endif()
    set(JXL_LIBS jxl jxl_cms jxl_threads hwy brotlidec brotlienc brotlicommon)
else()
    message(STATUS "libjxl not found on system or thirdparty, using FetchContent")
    set(BUILD_SHARED_LIBS ON CACHE BOOL "" FORCE)
    set(JPEGXL_ENABLE_FUZZERS OFF CACHE BOOL "" FORCE)
    set(CXX_FUZZERS_SUPPORTED OFF CACHE BOOL "" FORCE)
    set(JPEGXL_ENABLE_DOXYGEN OFF CACHE BOOL "" FORCE)
    set(JPEGXL_ENABLE_MANPAGES OFF CACHE BOOL "" FORCE)
    set(JPEGXL_ENABLE_EXAMPLES OFF CACHE BOOL "" FORCE)
    set(JPEGXL_ENABLE_JNI OFF CACHE BOOL "" FORCE)
    set(JPEGXL_ENABLE_OPENEXR OFF CACHE BOOL "" FORCE)
    set(JPEGXL_ENABLE_SJPEG OFF CACHE BOOL "" FORCE)
    set(JPEGXL_ENABLE_BENCHMARK OFF CACHE BOOL "" FORCE)
    set(JPEGXL_ENABLE_TOOLS OFF CACHE BOOL "" FORCE)
    FetchContent_Declare(
        libjxl
        GIT_REPOSITORY https://github.com/libjxl/libjxl.git
        GIT_TAG v0.12.x
        GIT_SHALLOW ON
    )
    FetchContent_MakeAvailable(libjxl)
    set(JXL_LIBS jxl jxl_cms jxl_threads)
    
    # libjxl sets CMAKE_INSTALL_MANDIR to "" when manpages are disabled, which breaks libjpeg-turbo later
    set(CMAKE_INSTALL_MANDIR "share/man" CACHE PATH "" FORCE)
endif()

FetchContent_GetProperties(libjpeg-turbo)
if(NOT libjpeg-turbo_POPULATED)
    FetchContent_Populate(libjpeg-turbo)
    file(READ "${libjpeg-turbo_SOURCE_DIR}/CMakeLists.txt" JPEG_CMAKE)
    string(REPLACE "if(NOT CMAKE_SOURCE_DIR STREQUAL CMAKE_CURRENT_SOURCE_DIR)" "if(FALSE)" JPEG_CMAKE "${JPEG_CMAKE}")
    string(REPLACE "add_custom_target(uninstall" "add_custom_target(uninstall_jpeg" JPEG_CMAKE "${JPEG_CMAKE}")
    string(REPLACE "pkg_check_modules(spng REQUIRED spng IMPORTED_TARGET)" "add_library(PkgConfig::spng ALIAS spng)" JPEG_CMAKE "${JPEG_CMAKE}")
    string(REPLACE "find_package(ZLIB REQUIRED)" "set(ZLIB_FOUND 1)\nset(ZLIB_LIBRARIES ${ZLIB_LIBRARIES})" JPEG_CMAKE "${JPEG_CMAKE}")
    file(WRITE "${libjpeg-turbo_SOURCE_DIR}/CMakeLists.txt" "${JPEG_CMAKE}")
    
    # Globally replace CMAKE_SOURCE_DIR and CMAKE_BINARY_DIR across all libjpeg-turbo CMakeLists.txt files
    # to prevent them from looking in our project root instead of their own.
    file(GLOB_RECURSE JPEG_CMAKELISTS "${libjpeg-turbo_SOURCE_DIR}/CMakeLists.txt")
    foreach(F IN LISTS JPEG_CMAKELISTS)
        file(READ "${F}" CONTENT)
        string(REPLACE "CMAKE_SOURCE_DIR" "PROJECT_SOURCE_DIR" CONTENT "${CONTENT}")
        string(REPLACE "CMAKE_BINARY_DIR" "PROJECT_BINARY_DIR" CONTENT "${CONTENT}")
        file(WRITE "${F}" "${CONTENT}")
    endforeach()
    set(CMAKE_INSTALL_DOCDIR "doc" CACHE PATH "" FORCE)
    add_subdirectory(${libjpeg-turbo_SOURCE_DIR} ${libjpeg-turbo_BINARY_DIR} EXCLUDE_FROM_ALL)
endif()



set( PROJ_OBJ "obj" )
set( PROJ_OUT "${CMAKE_CURRENT_LIST_DIR}/out" )
set( THIRDPARTY_DIR "${CMAKE_CURRENT_LIST_DIR}/thirdparty" )

set( CMAKE_RUNTIME_OUTPUT_DIRECTORY ${PROJ_OUT} )
set( CMAKE_LIBRARY_OUTPUT_DIRECTORY ${PROJ_OUT} )
set( CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${PROJ_OUT} )

foreach( OUTPUTCONFIG ${CMAKE_CONFIGURATION_TYPES} )
    string( TOUPPER ${OUTPUTCONFIG} OUTPUTCONFIG )
    set( CMAKE_RUNTIME_OUTPUT_DIRECTORY_${OUTPUTCONFIG} ${PROJ_OUT} )
    set( CMAKE_LIBRARY_OUTPUT_DIRECTORY_${OUTPUTCONFIG} ${PROJ_OUT} )
    set( CMAKE_ARCHIVE_OUTPUT_DIRECTORY_${OUTPUTCONFIG} ${PROJ_OUT} )
endforeach( OUTPUTCONFIG ${CMAKE_CONFIGURATION_TYPES} )

set_property( GLOBAL PROPERTY PREFIX "" )
set_property( GLOBAL PROPERTY USE_FOLDERS ON )

set( CMAKE_CXX_STANDARD 23 )
set( CMAKE_EXPORT_COMPILE_COMMANDS ON )

# Compiler/Platform specifc options
if ( MSVC )
	add_compile_definitions(
		_AMD64_ __x86_64 __amd64
		NOMINMAX
		_CRT_SECURE_NO_WARNINGS
		
		# TODO: ideally i only want this in debug, but i may still need it in release
		# https://stackoverflow.com/questions/28702665/warning-lnk4098-defaultlib-libcmt-conflicts-with-use-of-other-libs-use-node
		_ALLOW_RUNTIME_LIBRARY_MISMATCH _ALLOW_ITERATOR_DEBUG_LEVEL_MISMATCH _ALLOW_MSC_VER_MISMATCH
		
		_UNICODE=1
		UNICODE=1
	)
	
	# Use these runtime libraries for both so it doesn't crash smh my head
	# actually this is useless right now because of core.dll, god dammit
	# set_property( GLOBAL PROPERTY MSVC_RUNTIME_LIBRARY "MultiThreadedDLL" )
	
	# set( CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>DLL" )
	# set_property( GLOBAL PROPERTY MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>DLL" )

	# set( MSVC_VERSION 1939 )

	add_compile_options(
		"/WX"               # treat warnings as errors
		# "/Wall"             # Show ALL Warnings
		"/W4"               # Warning Level 4
		"/MP"               # multi-threaded compilation
		"/permissive-"      # make MSVC very compliant
		"/Zc:__cplusplus"   # set the __cplusplus macro to be the correct version
		# "/fp:fast"          # fast floating point model
		"/GF"               # string pooling: allows compiler to create a single copy of identical strings in the program image and in memory during execution
		
		# disable stupid warnings
		"/wd4100"  # 'X' unreferenced formal paramter
		"/wd4189"  # local variable is initialized but not referenced
		"/wd4996"  # The POSIX name for this item is deprecated.

		# there's a lot of number type conversions, don't feel like dealing with that currently
		"/wd4244"  # conversion from 'X' to 'Y', possible loss of data
		"/wd4267"  # conversion from 'X' to 'Y', possible loss of data (yes there's 2 idk why)
		
	#	"/wd4305"  # truncation from 'double' to 'float'
	#	"/wd4464"  # relative include path contains ".."
	#	"/wd4668"  # 'X' is not defined as a preprocessor macro, replacing '0' for '#if/#elif' (floods with win32 stuff)
	#	"/wd4514"  # 'X' unreferenced inline function has been removed
	#	"/wd4505"  # 'X' unreferenced function with internal linkage has been removed
	#	"/wd4201"  # nonstandard extension used: nameless struct/union (used in glm)
	#	"/wd5045"  # Compiler will insert Spectre mitigation for memory load if /Qspectre switch specified
    #
	#	"/wd4706"  # assignment within conditional expression
	#	
	#	# probably temporary
	#	"/wd4365"  # signed/unsigned mismatch
	#	"/wd4061"  # enumerator 'X' in switch of enum 'Y' is not explicitly handled by a case label
	#	
	#	# padding stuff
	#	"/wd4324"  # 'X' structure was padded due to alignment specifier
	#	"/wd4820"  # 'X' bytes padding added after data member 'Y'
    #
	#	# Treat these warnings as errors
    #
	#	# MSVC doesn't care about this one, but this errors on gcc and can help catch a mistake i made unknowingly
	#	"/we4002"  # Too many arguments for function-like macro invocation
	
		# I accidently get this a lot with printing std::string, so I want this to error so I know i made a mistake
		"/we4840"  # non-portable use of class 'type' as an argument to a variadic function
		
	#	# This is self-explanitory
	#	"/we4129"  # 'X' unrecognized character escape sequence
	)

	set( COMPILE_OPTIONS_DEBUG
		"/Od"        # no optimizations
		"/ZI"        # edit and continue
		"/fp:except" # raise floating point exceptions
		# "/fsanitize=address" # use address sanitizing in Debug (incompatible with /INCREMENTAL and /ZI)
	)
	
	set( COMPILE_OPTIONS_RELEASE
		"/fp:fast"
	)
	
	add_compile_options(
		"$<$<CONFIG:Debug>:${COMPILE_OPTIONS_DEBUG}>"
		"$<$<CONFIG:Release>:${COMPILE_OPTIONS_RELEASE}>"
		"$<$<CONFIG:RelWithDebInfo>:${COMPILE_OPTIONS_RELEASE}>"
	)
	
	set( LINK_OPTIONS_DEBUG
		"/INCREMENTAL"
	)
	
	set( LINK_OPTIONS_RELEASE
		""
	)
	
	add_link_options(
		"$<$<CONFIG:Debug>:${LINK_OPTIONS_DEBUG}>"
		"$<$<CONFIG:Release>:${LINK_OPTIONS_RELEASE}>"
		"$<$<CONFIG:RelWithDebInfo>:${LINK_OPTIONS_RELEASE}>"
	)
	
	add_link_options(
		"/SUBSYSTEM:WINDOWS"
		"/ENTRY:mainCRTStartup"
		# "/INCREMENTAL"
	)

	link_libraries( Dwmapi ntdll )
	
	# TODO: move all these copying of files to the thirdparty.py script, and have a check to make sure it was run before cmake was run
	# do a version compare, store a version number here and in thirdparty, if out of sync, fail until they build it
	# or build it in here?
	message( "Copying SDL3" )
	configure_file( "thirdparty/SDL3/lib/x64/SDL3.dll" "${PROJ_OUT}/SDL3.dll" COPYONLY )
	
	message( "Copying MPV" )
	configure_file( "thirdparty/mpv/libmpv-2.dll" "${PROJ_OUT}/libmpv-2.dll" COPYONLY )
	
	message( "Copying FreeImage" )
	configure_file( "thirdparty/FreeImageRe/bin/FreeImage.dll" "${PROJ_OUT}/FreeImage.dll" COPYONLY )
	configure_file( "thirdparty/FreeImageRe/bin/heif.dll" "${PROJ_OUT}/heif.dll" COPYONLY )
	
	message( "Copying libjxl" )
	configure_file( "thirdparty/libjxl/x64-windows/bin/jxl.dll" "${PROJ_OUT}/jxl.dll" COPYONLY )
	configure_file( "thirdparty/libjxl/x64-windows/bin/jxl_cms.dll" "${PROJ_OUT}/jxl_cms.dll" COPYONLY )
	configure_file( "thirdparty/libjxl/x64-windows/bin/jxl_threads.dll" "${PROJ_OUT}/jxl_threads.dll" COPYONLY )
	configure_file( "thirdparty/libjxl/x64-windows/bin/brotlicommon.dll" "${PROJ_OUT}/brotlicommon.dll" COPYONLY )
	configure_file( "thirdparty/libjxl/x64-windows/bin/brotlidec.dll" "${PROJ_OUT}/brotlidec.dll" COPYONLY )
	configure_file( "thirdparty/libjxl/x64-windows/bin/brotlienc.dll" "${PROJ_OUT}/brotlienc.dll" COPYONLY )

	message( "Copying ZLIB" )
	configure_file( "thirdparty/zlib-ng/bin/zlib1.dll" "${PROJ_OUT}/zlib1.dll" COPYONLY )

else()  # linux
	link_libraries( GL )
	
	add_compile_definitions(
		_FILE_OFFSET_BITS=64
		_TIME_BITS=64
	)
	
	if(EXISTS "${CMAKE_CURRENT_LIST_DIR}/thirdparty/FreeImageRe/lib/libFreeImage.so")
		message( "Copying FreeImage" )
		configure_file( "thirdparty/FreeImageRe/lib/libFreeImage.so" "${PROJ_OUT}/libFreeImage.so" COPYONLY )
		configure_file( "thirdparty/FreeImageRe/lib/libheif.so" "${PROJ_OUT}/libheif.so" COPYONLY )
	endif()
endif()


# ========================================================================================================

set(
    SRC_FILES
    src/main.cpp
    src/main.h
    src/thumbnail_loader.cpp
    src/thumbnail_jxl.cpp
    src/mpv_interface.cpp
    src/mpv_interface.h
    src/image_loader.cpp
    src/memory.cpp
    src/config.cpp
    src/folder_scan.cpp
    src/job_system.cpp
    src/gl_render.cpp
    
	src/ui_main.cpp
	src/ui_directory_tree.cpp
	src/ui_settings_menu.cpp
    src/ui_view_gallery.cpp
    src/ui_view_gallery_sidebar.cpp
    src/ui_view_gallery_content.cpp
    src/ui_view_media.cpp
	
    src/util.h
    src/util.cpp
    src/util_filesystem.cpp
    src/array.hpp

    src/args.cpp
    src/args.h
    src/handles.h

    src/codecs/loader_jpeg.cpp
    src/codecs/loader_png.cpp
    # src/codecs/format_gif.cpp
    src/codecs/loader_freeimage.cpp
    src/codecs/loader_jpegxl.cpp

    src/system/system.h

    src/imgui/imconfig.h
    src/imgui/imgui.cpp
    src/imgui/imgui_demo.cpp
    src/imgui/imgui_draw.cpp
    src/imgui/imgui_impl_opengl3.cpp
    src/imgui/imgui_impl_sdl3.cpp
    src/imgui/imgui_tables.cpp
    src/imgui/imgui_widgets.cpp

    src/imgui/imgui_demez.cpp

	src/glad/glad.c
	src/glad/glad.h
	src/glad/khrplatform.h
)


if ( MSVC )
	set(
		SYSTEM_FILES
		src/system/win32/media_tag_system.manifest
		src/system/win32/sys_win32.h
		src/system/win32/sys_win32.cpp
		src/system/win32/sys_win32_filesystem.cpp
		src/system/win32/sys_win32_internal.cpp
		src/system/win32/sys_win32_dragdrop.cpp
		src/system/win32/sys_win32_folder_monitor.cpp
	)
else()
	set(
		SYSTEM_FILES
		src/system/linux/sys_linux.cpp
	)
endif()

set( FREETYPE_DIR "thirdparty/freetype" )

set(
	FREETYPE_IMGUI_SRC
	src/imgui/imgui_freetype.cpp
	src/imgui/imgui_freetype.h
)

include_directories( "${FREETYPE_DIR}/include" )
add_compile_definitions( IMGUI_ENABLE_FREETYPE=1 )

file(
	GLOB_RECURSE THIRDPARTY_FILES CONFIGURE_DEPENDS
	thirdparty/*.h
	thirdparty/*.hpp
)

include_directories(
	"src/"
	"src/imgui"
	"src/glad"
	"thirdparty"
	"thirdparty/SDL3/include"
	"thirdparty/mpv/include"
	"thirdparty/gif_load"
	"thirdparty/FreeImageRe/include"
	"thirdparty/stb"
	${libjpeg-turbo_SOURCE_DIR}
	${libjpeg-turbo_SOURCE_DIR}/src
	${libjpeg-turbo_BINARY_DIR}
	
	${nativefiledialog_SOURCE_DIR}/src/include
	${libspng_SOURCE_DIR}/spng
	${libfyaml_SOURCE_DIR}/include
)

set(SDL3_LINK_TARGET "SDL3")

if( LINUX )
    find_package(PkgConfig QUIET)
    if(PkgConfig_FOUND)
        pkg_check_modules(SDL3_PKG QUIET sdl3)
        if(SDL3_PKG_FOUND)
            include_directories(${SDL3_PKG_INCLUDE_DIRS})
            link_directories(${SDL3_PKG_LIBRARY_DIRS})
            message(STATUS "Found SDL3 via pkg-config")
        endif()
    endif()
    
    if(NOT SDL3_PKG_FOUND AND NOT EXISTS "${CMAKE_CURRENT_LIST_DIR}/thirdparty/SDL3/include")
        message(STATUS "SDL3 not found on system or thirdparty, using FetchContent")
        FetchContent_Declare(
            SDL3
            GIT_REPOSITORY https://github.com/libsdl-org/SDL.git
            GIT_TAG release-3.2.4
            GIT_SHALLOW ON
        )
        set(SDL_SHARED ON CACHE BOOL "" FORCE)
        set(SDL_STATIC OFF CACHE BOOL "" FORCE)
        set(SDL_TEST_LIBRARY OFF CACHE BOOL "" FORCE)
        set(SDL_TESTS OFF CACHE BOOL "" FORCE)
        FetchContent_MakeAvailable(SDL3)
        include_directories("${sdl3_SOURCE_DIR}/include")
        set(SDL3_LINK_TARGET "SDL3-shared")
    endif()
endif()

if ( MIMALLOC )
	add_compile_definitions( USE_MIMALLOC=1 )
	include_directories( "thirdparty/mimalloc/include" )
else()
	add_compile_definitions( USE_MIMALLOC=0 )
endif()

link_libraries(
	freetype
	nfd
	${SDL3_LINK_TARGET}
	spng
	fyaml
	${JXL_LIBS}

	# must be below jxl, or my program will link the jxl functions to freeimage instead
	FreeImage
)

if ( MIMALLOC )
	link_libraries( mimalloc )
	link_directories( "thirdparty/mimalloc/out/msvc-x64/Release" )
endif()

set( LINK_DIR_DEBUG
	"${THIRDPARTY_DIR}/nativefiledialog/build/src/Debug"
	"${THIRDPARTY_DIR}/libjpeg-turbo/build/Debug"
)

set( LINK_DIR_RELEASE
	"${THIRDPARTY_DIR}/nativefiledialog/build/src/Release"
	"${THIRDPARTY_DIR}/libjpeg-turbo/build/Release"
)

set( LINK_DIR_RELEASE_DEBUG_INFO
	"${THIRDPARTY_DIR}/nativefiledialog/build/src/RelWithDebInfo"
	"${THIRDPARTY_DIR}/libjpeg-turbo/build/Release"
)

link_directories(
	
	# i don't want to use static, but for some reason, it can't find the lib when using the dll version?
	
	"$<$<CONFIG:Debug>:${LINK_DIR_DEBUG}>"
	"$<$<CONFIG:Release>:${LINK_DIR_RELEASE}>"
	"$<$<CONFIG:RelWithDebInfo>:${LINK_DIR_RELEASE_DEBUG_INFO}>"
	
	"thirdparty/FreeImageRe/lib"
	
	# "thirdparty/nativefiledialog/build/src/${CMAKE_CFG_INTDIR}"
)

if ( WIN32 )
	link_directories(
		"thirdparty/SDL3/lib/x64"
	)
	link_libraries(
		turbojpeg
	)
elseif( LINUX )
	link_directories(
	)
	link_libraries(
		turbojpeg
		stdc++exp
	)
endif()

foreach( OUTPUT_CONFIG ${CMAKE_CONFIGURATION_TYPES} )
	link_directories(
	#	"${FREETYPE_DIR}/objs/x64/${OUTPUT_CONFIG} Static"
	#	"thirdparty/nativefiledialog/build/src/${OUTPUT_CONFIG}"
	#	"thirdparty/libjpeg-turbo/build/${OUTPUT_CONFIG}"
		# "thirdparty/libfyaml/build/${OUTPUT_CONFIG}"
		# "thirdparty/libspng/build/${OUTPUT_CONFIG}"
	)
endforeach( OUTPUT_CONFIG ${CMAKE_CONFIGURATION_TYPES} )

add_executable( media_tag_system ${SRC_FILES} ${SYSTEM_FILES} ${FREETYPE_IMGUI_SRC} ${THIRDPARTY_FILES} )

if ( WIN32 )
	add_executable( media_tag_system_con ${SRC_FILES} ${SYSTEM_FILES} ${FREETYPE_IMGUI_SRC} ${THIRDPARTY_FILES} )

	target_link_options(
		media_tag_system_con PRIVATE
		"/SUBSYSTEM:CONSOLE"
	)

	set_target_properties(
		media_tag_system_con PROPERTIES
		SUFFIX ".com"
		RUNTIME_OUTPUT_NAME "media_tag_system"
		PDB_NAME "media_tag_system_con"
	)
endif()

# Automatically copy DLLs/SOs to the output directory after compilation
add_custom_command(TARGET media_tag_system POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different $<TARGET_FILE:spng> "${PROJ_OUT}"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different $<TARGET_FILE:turbojpeg> "${PROJ_OUT}"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different $<TARGET_FILE:fyaml> "${PROJ_OUT}"
    COMMENT "Copying FetchContent shared libraries to output directory"
)

if(TARGET SDL3-shared)
    add_custom_command(TARGET media_tag_system POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_if_different $<TARGET_FILE:SDL3-shared> "${PROJ_OUT}"
    )
endif()

if ( WIN32 )
    add_custom_command(TARGET media_tag_system_con POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_if_different $<TARGET_FILE:spng> "${PROJ_OUT}"
        COMMAND ${CMAKE_COMMAND} -E copy_if_different $<TARGET_FILE:turbojpeg> "${PROJ_OUT}"
        COMMAND ${CMAKE_COMMAND} -E copy_if_different $<TARGET_FILE:fyaml> "${PROJ_OUT}"
    )
    if(TARGET SDL3-shared)
        add_custom_command(TARGET media_tag_system_con POST_BUILD
            COMMAND ${CMAKE_COMMAND} -E copy_if_different $<TARGET_FILE:SDL3-shared> "${PROJ_OUT}"
        )
    endif()
endif()

source_group(
	TREE ${CMAKE_CURRENT_LIST_DIR}/src
	PREFIX "Source Files"
	FILES ${SRC_FILES} ${SYSTEM_FILES} ${FREETYPE_IMGUI_SRC}
)

source_group(
	TREE ${CMAKE_CURRENT_LIST_DIR}/thirdparty
	PREFIX "Thirdparty Files"
	FILES ${THIRDPARTY_FILES}
)

