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
    license = "X11"
    exports = ["LICENSE.md", "CMakeLists.txt"]
    exports_sources = ["CMakeLists.txt"]
    generators = "cmake"

    # Custom attributes for Bincrafters recipe conventions
    source_subfolder = "source_subfolder"
    build_subfolder = "build_subfolder"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "demos": [True, False],
        "gles": [True, False],
        "print_errors_at_runtime": [True, False],
        "print_warnings_at_runtime": [True, False],
        "replace_gut": [True, False],
        "install_pdb": [True, False]
    }

    default_options = (
        "shared=False",
        "fPIC=True",
        "demos=False",
        "gles=False",
        "print_errors_at_runtime=True",
        "print_warnings_at_runtime=False",
        "replace_gut=True",
        "install_pdb=False"
    )

    # FIXME: What are the recommended default values for print_errors and print_warnings?

    def config_options(self):
        if self.settings.os == 'Windows':
            self.options.fPIC = False
            self.options.replace_gut = False
        if self.settings.compiler != "Visual Studio":
            self.options.install_pdb = False

    def source(self):
        source_url = "https://github.com/dcnieho/FreeGLUT"
        tools.get("{0}/archive/FG_{1}.tar.gz".format(source_url, self.version.replace(".", "_")))
        # tools.get("file:FG_{}.tar.gz".format(self.version.replace(".", "_")))
        extracted_dir = "FreeGLUT-FG_" + self.version.replace(".", "_")

        # Rename to "source_subfolder" is a convention to simplify later steps
        os.rename(extracted_dir, self.source_subfolder)

    def configure_cmake(self):
        # See https://github.com/dcnieho/FreeGLUT/blob/44cf4b5b85cf6037349c1c8740b2531d7278207d/README.cmake
        cmake = CMake(self)
        cmake.definitions["FREEGLUT_BUILD_DEMOS"] = "ON" if self.options.demos else "OFF"
        cmake.definitions["FREEGLUT_BUILD_STATIC_LIBS"] = "OFF" if self.options.shared else "ON"
        cmake.definitions["FREEGLUT_BUILD_SHARED_LIBS"] = "ON" if self.options.shared else "OFF"
        cmake.definitions["FREEGLUT_GLES"] = "ON" if self.options.gles else "OFF"
        cmake.definitions["FREEGLUT_PRINT_ERRORS"] = "ON" if self.options.print_errors_at_runtime else "OFF"
        cmake.definitions["FREEGLUT_PRINT_WARNINGS"] = "ON" if self.options.print_warnings_at_runtime else "OFF"
        cmake.definitions["FREEGLUT_INSTALL_PDB"] = "ON" if self.options.install_pdb else "OFF"
        # cmake.definitions["FREEGLUT_WAYLAND"] = "ON" if self.options.wayland else "OFF" # nightly version only as of now

        if self.settings.os != 'Windows':
            cmake.definitions['CMAKE_POSITION_INDEPENDENT_CODE'] = self.options.fPIC
        cmake.configure(build_folder=self.build_subfolder, source_folder=self.source_subfolder) # , source_folder=self.source_folder
        return cmake

    def build(self):
        cmake = self.configure_cmake()
        cmake.build()

    def package(self):
        self.copy(pattern="COPYING", dst=".", src=self.source_subfolder)
        cmake = self.configure_cmake()
        cmake.install()
        # If the CMakeLists.txt has a proper install method, the steps below may be redundant
        # If so, you can just remove the lines below
        include_folder = os.path.join(self.source_subfolder, "include")
        self.copy(pattern="*", dst="include", src=include_folder)
        self.copy(pattern="*.dll", dst="bin", keep_path=False)
        self.copy(pattern="*.lib", dst="lib", keep_path=False)
        self.copy(pattern="*.a", dst="lib", keep_path=False)
        self.copy(pattern="*.so*", dst="lib", keep_path=False)
        self.copy(pattern="*.dylib", dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
