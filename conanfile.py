#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, CMake, tools
import os


class freeglutConan(ConanFile):
    name = "freeglut"
    version = "3.0.0"
    description = "Open-source alternative to the OpenGL Utility Toolkit (GLUT) library"
    url = "https://github.com/Croydon/conan-freeglut"
    homepage = "https://github.com/dcnieho/FreeGLUT"
    author = "Bincrafters <bincrafters@gmail.com>"
    license = "X11"
    exports = ["LICENSE.md"]
    exports_sources = ["CMakeLists.txt", "*.patch"]
    generators = "cmake"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "demos": [True, False],
        "gles": [True, False],
        "print_errors_at_runtime": [True, False],
        "print_warnings_at_runtime": [True, False],
        "replace_glut": [True, False],
        "install_pdb": [True, False]
    }
    default_options = (
        "shared=False",
        "fPIC=True",
        "demos=False",
        "gles=False",
        "print_errors_at_runtime=True",
        "print_warnings_at_runtime=True",
        "replace_glut=True",
        "install_pdb=False"
    )
    source_subfolder = "source_subfolder"
    build_subfolder = "build_subfolder"

    def config_options(self):
        if self.settings.os == 'Windows':
            self.options.remove("fPIC")
            self.options.replace_glut = True
        if self.settings.compiler != "Visual Studio":
            self.options.install_pdb = False

    def source(self):
        archive_url = "https://github.com/dcnieho/FreeGLUT/archive/FG_{}.tar.gz".format(self.version.replace(".", "_"))
        tools.get(archive_url, sha256="b0abf188cfbb572b9f9ef5c6adbeba8eedbd9a717897908ee9840018ab0b8eee")
        extracted_dir = "FreeGLUT-FG_" + self.version.replace(".", "_")
        os.rename(extracted_dir, self.source_subfolder)

        # Remove with > 3.0.0; https://github.com/dcnieho/FreeGLUT/issues/34
        # Windows build fails to install with FREEGLUT_BUILD_STATIC_LIBS and INSTALL_PDB enabled
        tools.patch(base_path=self.source_subfolder, patch_file="0001-removed-invalid-pdb-install.patch")

        # on macOS GLX can't be found https://github.com/dcnieho/FreeGLUT/issues/27
        tools.patch(base_path=self.source_subfolder, patch_file="0002-macOS-Fix-GLX-not-found.patch")

        # when build static the default lib name is freeglut_static what causes all kind of trouble to find/include this lib later
        tools.patch(base_path=self.source_subfolder, patch_file="0003-name-the-library-always-freeglut-not-static.patch")

    def system_requirements(self):
        if self.settings.os == "Macos":
            self.run("brew cask install xquartz")

        if self.settings.os == "Linux" and tools.os_info.is_linux:
            installer = tools.SystemPackageTool()
            if tools.os_info.with_apt:
                if self.settings.arch == "x86":
                    arch_suffix = ':i386'
                elif self.settings.arch == "x86_64":
                    arch_suffix = ':amd64'
                packages = ['libgl1-mesa-dev%s' % arch_suffix]
                packages.append('libglu1-mesa-dev%s' % arch_suffix)
                packages.append('libgl1-mesa-glx%s' % arch_suffix)
                packages.append('libx11-dev%s' % arch_suffix)
                packages.append('libxext-dev%s' % arch_suffix)
                packages.append('libxi-dev%s' % arch_suffix)

            if tools.os_info.with_yum:
                if self.settings.arch == "x86":
                    arch_suffix = '.i686'
                elif self.settings.arch == 'x86_64':
                    arch_suffix = '.x86_64'
                packages = ['mesa-libGL-devel%s' % arch_suffix]
                packages.append('mesa-libGLU-devel%s' % arch_suffix)
                packages.append('glx-utils%s' % arch_suffix)
                packages.append('libx11-devel%s' % arch_suffix)
                packages.append('libXext-devel%s' % arch_suffix)
                packages.append('libXi-devel%s' % arch_suffix)

            for package in packages:
                installer.install(package)

    def configure_env(self):
        env = dict()
        if self.settings.os == 'Linux':
            if self.settings.arch == 'x86':
                if tools.detected_architecture() == "x86_64":
                    env['PKG_CONFIG_PATH'] = '/usr/lib/i386-linux-gnu/pkgconfig'

        return env

    def configure_cmake(self):
        # See https://github.com/dcnieho/FreeGLUT/blob/44cf4b5b85cf6037349c1c8740b2531d7278207d/README.cmake
        cmake = CMake(self)

        env = self.configure_env()

        if self.settings.os == 'Linux':
            if self.settings.arch == 'x86':
                cmake.definitions['CMAKE_C_FLAGS'] = '-m32'
                cmake.definitions['CMAKE_CXX_FLAGS'] = '-m32'
            elif self.settings.arch == 'x86_64':
                cmake.definitions['CMAKE_C_FLAGS'] = '-m64'
                cmake.definitions['CMAKE_CXX_FLAGS'] = '-m64'

        cmake.definitions["FREEGLUT_BUILD_DEMOS"] = "ON" if self.options.demos else "OFF"
        cmake.definitions["FREEGLUT_BUILD_STATIC_LIBS"] = "OFF" if self.options.shared else "ON"
        cmake.definitions["FREEGLUT_BUILD_SHARED_LIBS"] = "ON" if self.options.shared else "OFF"
        cmake.definitions["FREEGLUT_GLES"] = "ON" if self.options.gles else "OFF"
        cmake.definitions["FREEGLUT_PRINT_ERRORS"] = "ON" if self.options.print_errors_at_runtime else "OFF"
        cmake.definitions["FREEGLUT_PRINT_WARNINGS"] = "ON" if self.options.print_warnings_at_runtime else "OFF"
        cmake.definitions["FREEGLUT_INSTALL_PDB"] = "ON" if self.options.install_pdb else "OFF"
        # cmake.definitions["FREEGLUT_WAYLAND"] = "ON" if self.options.wayland else "OFF" # nightly version only as of now

        with tools.environment_append(env):
            cmake.configure(build_folder=self.build_subfolder)
        return cmake

    def build(self):
        cmake = self.configure_cmake()
        env = self.configure_env()
        with tools.environment_append(env):
            cmake.build()

    def package(self):
        self.copy(pattern="COPYING", dst=".", src=self.source_subfolder)
        cmake = self.configure_cmake()
        env = self.configure_env()
        with tools.environment_append(env):
            cmake.install()

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        
        if self.settings.compiler == "Visual Studio":
            if not self.options.shared:
                self.cpp_info.libs.append("OpenGL32.lib")
        else:
            self.cpp_info.libs.append("opengl32")
            if self.settings.os == "Macos":
                self.cpp_info.exelinkflags.append("-framework OpenGL")
            elif not self.options.shared:
                self.cpp_info.libs.append("GL")

        for lib in self.cpp_info.libs:
            self.output.warn(lib)
