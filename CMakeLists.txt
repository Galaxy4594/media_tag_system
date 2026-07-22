cmake_minimum_required( VERSION 3.18 FATAL_ERROR )

# ========================================================================================================
# GLOBAL CONFIGURATION
# ========================================================================================================

set_property( GLOBAL PROPERTY USE_FOLDERS ON )
set_property( GLOBAL PROPERTY PREFIX "" )

set( CMAKE_CONFIGURATION_TYPES "Debug;Release;RelWithDebInfo" )
set( CMAKE_POSITION_INDEPENDENT_CODE ON )
set( CMAKE_SHARED_LIBRARY_PREFIX "" )
set( CMAKE_CXX_STANDARD 23 )
set( CMAKE_EXPORT_COMPILE_COMMANDS ON )

option( MIMALLOC "Use mimalloc" OFF )

project( media_tag_system )

set( PROJ_OBJ "obj" )
set( PROJ_OUT "${CMAKE_CURRENT_LIST_DIR}/out" )

set( CMAKE_RUNTIME_OUTPUT_DIRECTORY ${PROJ_OUT} )
set( CMAKE_LIBRARY_OUTPUT_DIRECTORY ${PROJ_OUT} )
set( CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${PROJ_OUT} )

foreach( OUTPUTCONFIG ${CMAKE_CONFIGURATION_TYPES} )
    string( TOUPPER ${OUTPUTCONFIG} OUTPUTCONFIG )
    set( CMAKE_RUNTIME_OUTPUT_DIRECTORY_${OUTPUTCONFIG} ${PROJ_OUT} )
    set( CMAKE_LIBRARY_OUTPUT_DIRECTORY_${OUTPUTCONFIG} ${PROJ_OUT} )
    set( CMAKE_ARCHIVE_OUTPUT_DIRECTORY_${OUTPUTCONFIG} ${PROJ_OUT} )
endforeach()


# ========================================================================================================
# SOURCE FILES
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

    src/view_gallery.cpp
    src/view_gallery_sidebar.cpp

    src/view_media.cpp
	
    src/util.h
    src/util.cpp
    src/util_filesystem.cpp

    src/args.cpp
    src/args.h
    src/handles.h

    src/codecs/loader_jpeg.cpp
    src/codecs/loader_png.cpp
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

	src/glad/glad.c
	src/glad/glad.h
	src/glad/khrplatform.h
)

set( FREETYPE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/freetype" )
set(
	FREETYPE_IMGUI_SRC
	src/imgui/imgui_freetype.cpp
	src/imgui/imgui_freetype.h
)

file(
	GLOB_RECURSE THIRDPARTY_FILES CONFIGURE_DEPENDS
	thirdparty/*.h
	thirdparty/*.hpp
)

if ( WIN32 )
	set(
		SYSTEM_FILES
		src/system/win32/media_tag_system.manifest
		src/system/win32/sys_win32.h
		src/system/win32/sys_win32.cpp
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


# ========================================================================================================
# GLOBAL INCLUDES & LINKS
# ========================================================================================================

add_compile_definitions( IMGUI_ENABLE_FREETYPE=1 )

if ( MIMALLOC )
	add_compile_definitions( USE_MIMALLOC=1 )
	include_directories( "${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/mimalloc/include" )
else()
	add_compile_definitions( USE_MIMALLOC=0 )
endif()

include_directories(
	"${CMAKE_CURRENT_SOURCE_DIR}/src"
	"${CMAKE_CURRENT_SOURCE_DIR}/src/imgui"
	"${CMAKE_CURRENT_SOURCE_DIR}/src/glad"
	"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty"
	"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/nativefiledialog/src/include"
	"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/SDL3/include"
	"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/mozjpeg"
	"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/libspng/spng"
	"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/mpv/include"
	"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/gif_load"
	"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/FreeImageRe/include"
	"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/stb"
	"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/libfyaml/include"
	"${FREETYPE_DIR}/include"
)

link_directories(
	"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/nativefiledialog/build/src"
	"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/mozjpeg/build"
	"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/libspng/build"
	"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/FreeImageRe/lib"
	"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/libfyaml/build"
)

link_libraries(
	freetype
	nfd
	SDL3
	spng
	fyaml
	jxl
	jxl_cms
	jxl_threads
	FreeImage
)

foreach( OUTPUT_CONFIG ${CMAKE_CONFIGURATION_TYPES} )
	link_directories(
		"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/nativefiledialog/build/src/${OUTPUT_CONFIG}"
		"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/mozjpeg/build/${OUTPUT_CONFIG}"
	)
endforeach()


# ========================================================================================================
# PLATFORM SPECIFIC (WINDOWS)
# ========================================================================================================

if ( WIN32 )
	add_compile_definitions(
		_AMD64_ __x86_64 __amd64
		NOMINMAX
		_CRT_SECURE_NO_WARNINGS
		_ALLOW_RUNTIME_LIBRARY_MISMATCH _ALLOW_ITERATOR_DEBUG_LEVEL_MISMATCH _ALLOW_MSC_VER_MISMATCH
		_UNICODE=1
		UNICODE=1
	)

	add_compile_options(
		"/W4"               
		"/MP"               
		"/permissive-"      
		"/Zc:__cplusplus"   
		"/GF"               
		"/wd4100"           
		"/we4840"           
	)

	set( COMPILE_OPTIONS_DEBUG "/Od" "/ZI" "/fp:except" )
	set( COMPILE_OPTIONS_RELEASE "/fp:fast" )
	
	add_compile_options(
		"$<$<CONFIG:Debug>:${COMPILE_OPTIONS_DEBUG}>"
		"$<$<CONFIG:Release>:${COMPILE_OPTIONS_RELEASE}>"
		"$<$<CONFIG:RelWithDebInfo>:${COMPILE_OPTIONS_RELEASE}>"
	)
	
	set( LINK_OPTIONS_DEBUG "/INCREMENTAL" )
	set( LINK_OPTIONS_RELEASE "" )
	
	add_link_options(
		"$<$<CONFIG:Debug>:${LINK_OPTIONS_DEBUG}>"
		"$<$<CONFIG:Release>:${LINK_OPTIONS_RELEASE}>"
		"$<$<CONFIG:RelWithDebInfo>:${LINK_OPTIONS_RELEASE}>"
		"/SUBSYSTEM:WINDOWS"
		"/ENTRY:mainCRTStartup"
	)

	include_directories(
		"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/jxl/include"
	)

	if ( USE_SHARED_LIBS )
		set( FREETYPE_LIB_DIR "${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/freetype/release dll/x64" )
	else()
		set( FREETYPE_LIB_DIR "${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/freetype/release static/vs2026/x64" )
	endif()

	link_directories(
		"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/libspng/build/Release"
		"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/libfyaml/build/Release"
		"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/jxl/lib"
		"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/SDL3/lib/x64"
		"${FREETYPE_LIB_DIR}"
	)

	link_libraries(
		Dwmapi
		turbojpeg-static
	)

	# Consolidate Windows DLL copying
	configure_file( "${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/SDL3/lib/x64/SDL3.dll" "${PROJ_OUT}/SDL3.dll" COPYONLY )
	configure_file( "${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/mpv/libmpv-2.dll" "${PROJ_OUT}/libmpv-2.dll" COPYONLY )
	configure_file( "${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/libspng/build/Release/spng.dll" "${PROJ_OUT}/spng.dll" COPYONLY )
	configure_file( "${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/FreeImageRe/bin/FreeImage.dll" "${PROJ_OUT}/FreeImage.dll" COPYONLY )
	configure_file( "${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/FreeImageRe/bin/heif.dll" "${PROJ_OUT}/heif.dll" COPYONLY )
	configure_file( "${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/libfyaml/build/Release/fyaml.dll" "${PROJ_OUT}/fyaml.dll" COPYONLY )
	configure_file( "${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/jxl/bin/jxl.dll" "${PROJ_OUT}/jxl.dll" COPYONLY )
	configure_file( "${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/jxl/bin/jxl_cms.dll" "${PROJ_OUT}/jxl_cms.dll" COPYONLY )
	configure_file( "${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/jxl/bin/jxl_threads.dll" "${PROJ_OUT}/jxl_threads.dll" COPYONLY )
	configure_file( "${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/jxl/bin/brotlicommon.dll" "${PROJ_OUT}/brotlicommon.dll" COPYONLY )
	configure_file( "${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/jxl/bin/brotlidec.dll" "${PROJ_OUT}/brotlidec.dll" COPYONLY )
	configure_file( "${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/jxl/bin/brotlienc.dll" "${PROJ_OUT}/brotlienc.dll" COPYONLY )


# ========================================================================================================
# PLATFORM SPECIFIC (LINUX)
# ========================================================================================================

elseif( LINUX )
	add_compile_definitions(
		_FILE_OFFSET_BITS=64
		_TIME_BITS=64
	)

	include_directories(
		"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/libjxl/build/lib/include"
	)

	link_directories(
		"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/SDL3/build"
		"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/SDL3/build/lib"
		"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/libjxl/build/lib"
		"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/libjxl/build/third_party/brotli"
		"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/freetype/build"
	)

	link_libraries(
		GL
		turbojpeg
		stdc++exp
	)

	# Consolidate Linux SO copying using GLOB to handle versions and symlinks gracefully
	file( GLOB LINUX_SO_FILES 
		"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/libspng/build/libspng.so*"
		"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/libspng/build/spng.so*"
		"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/FreeImageRe/lib/libFreeImage.so*"
		"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/FreeImageRe/lib/libheif.so*"
		"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/libfyaml/build/libfyaml.so*"
		"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/SDL3/build/libSDL3.so*"
		"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/SDL3/build/lib/libSDL3.so*"
		"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/libjxl/build/lib/libjxl.so*"
		"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/libjxl/build/lib/libjxl_cms.so*"
		"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/libjxl/build/lib/libjxl_threads.so*"
		"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/libjxl/build/third_party/brotli/libbrotlicommon.so*"
		"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/libjxl/build/third_party/brotli/libbrotlidec.so*"
		"${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/libjxl/build/third_party/brotli/libbrotlienc.so*"
	)
	file( COPY ${LINUX_SO_FILES} DESTINATION "${PROJ_OUT}" )
endif()

# ========================================================================================================
# EXECUTABLES
# ========================================================================================================

add_executable( media_tag_system ${SRC_FILES} ${SYSTEM_FILES} ${FREETYPE_IMGUI_SRC} ${THIRDPARTY_FILES} )

if ( WIN32 )
	add_executable( media_tag_system_con ${SRC_FILES} ${SYSTEM_FILES} ${FREETYPE_IMGUI_SRC} ${THIRDPARTY_FILES} )
	target_link_options( media_tag_system_con PRIVATE "/SUBSYSTEM:CONSOLE" )
	set_target_properties( media_tag_system_con PROPERTIES SUFFIX ".com" RUNTIME_OUTPUT_NAME "media_tag_system" PDB_NAME "media_tag_system_con" )
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
