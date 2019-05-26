# -*- coding: utf-8 -*-

from conans import ConanFile, CMake, tools
import os


class freeglutConan(ConanFile):
    name = "freeglut"
    version = "3.0.0"
    description = "Open-source alternative to the OpenGL Utility Toolkit (GLUT) library"
    topics = ("conan", "freeglut", "opengl", "gl", "glut", "utility", "toolkit", "graphics")
    url = "https://github.com/bincrafters/conan-freeglut"
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
        "gles": [True, False],
        "print_errors_at_runtime": [True, False],
        "print_warnings_at_runtime": [True, False],
        "replace_glut": [True, False],
        "install_pdb": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "gles": False,
        "print_errors_at_runtime": True,
        "print_warnings_at_runtime": True,
        "replace_glut": True,
        "install_pdb": False
    }

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    @property
    def _build_subfolder(self):
        return "build_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
            self.options.replace_glut = False
        if self.settings.compiler != "Visual Studio":
            self.options.install_pdb = False

    def configure(self):
        del self.settings.compiler.libcxx

    def source(self):
        archive_url = "{}/archive/FG_{}.tar.gz".format(self.homepage, self.version.replace(".", "_"))
        tools.get(archive_url, sha256="b0abf188cfbb572b9f9ef5c6adbeba8eedbd9a717897908ee9840018ab0b8eee")
        extracted_dir = "FreeGLUT-FG_" + self.version.replace(".", "_")
        os.rename(extracted_dir, self._source_subfolder)

        # Remove with > 3.0.0; https://github.com/dcnieho/FreeGLUT/issues/34
        # Windows build fails to install with FREEGLUT_BUILD_STATIC_LIBS and INSTALL_PDB enabled
        tools.patch(base_path=self._source_subfolder, patch_file="0001-removed-invalid-pdb-install.patch")

        # on macOS GLX can't be found https://github.com/dcnieho/FreeGLUT/issues/27
        tools.patch(base_path=self._source_subfolder, patch_file="0002-macOS-Fix-GLX-not-found.patch")

        # when build static the default lib name is freeglut_static what causes all kind of trouble to find/include this lib later
        tools.patch(base_path=self._source_subfolder, patch_file="0003-name-the-library-always-freeglut-not-static.patch")

    def system_requirements(self):
        if self.settings.os == "Macos":
            self.run("brew cask install xquartz")

        if self.settings.os == "Linux" and tools.os_info.is_linux:
            installer = tools.SystemPackageTool()
            arch_suffix = ""
            if tools.os_info.with_apt:
                if self.settings.arch == "x86" and tools.cross_building(self.settings):
                    arch_suffix = ':i386'
                elif self.settings.arch == "x86_64":
                    arch_suffix = ':amd64'
                packages = ['libgl1-mesa-dev%s' % arch_suffix]
                packages.append('libglu1-mesa-dev%s' % arch_suffix)
                packages.append('libgl1-mesa-glx%s' % arch_suffix)
                packages.append('libx11-dev%s' % arch_suffix)
                packages.append('libxext-dev%s' % arch_suffix)
                packages.append('libxi-dev%s' % arch_suffix)
                packages.append('libxrandr-dev%s' % arch_suffix)

            elif tools.os_info.with_yum:
                if self.settings.arch == "x86" and tools.cross_building(self.settings):
                    arch_suffix = '.i686'
                elif self.settings.arch == 'x86_64':
                    arch_suffix = '.x86_64'
                packages = ['mesa-libGL-devel%s' % arch_suffix]
                packages.append('mesa-libGLU-devel%s' % arch_suffix)
                packages.append('glx-utils%s' % arch_suffix)
                packages.append('libX11-devel%s' % arch_suffix)
                packages.append('libXext-devel%s' % arch_suffix)
                packages.append('libXi-devel%s' % arch_suffix)

            elif tools.os_info.with_pacman:
                if self.settings.arch == "x86" and tools.cross_building(self.settings):
                    arch_suffix = 'lib32-'
                packages = ['%smesa' % arch_suffix]
                packages.append('%sglu' % arch_suffix)
                packages.append('%slibx11' % arch_suffix)
                packages.append('%slibxext' % arch_suffix)
                packages.append('%slibxi' % arch_suffix)

            installer.install(" ".join(packages))

    def _configure_cmake(self):
        # See https://github.com/dcnieho/FreeGLUT/blob/44cf4b5b85cf6037349c1c8740b2531d7278207d/README.cmake
        cmake = CMake(self, set_cmake_flags=True)

        cmake.definitions["FREEGLUT_BUILD_DEMOS"] = "OFF"
        cmake.definitions["FREEGLUT_BUILD_STATIC_LIBS"] = "OFF" if self.options.shared else "ON"
        cmake.definitions["FREEGLUT_BUILD_SHARED_LIBS"] = "ON" if self.options.shared else "OFF"
        cmake.definitions["FREEGLUT_GLES"] = "ON" if self.options.gles else "OFF"
        cmake.definitions["FREEGLUT_PRINT_ERRORS"] = "ON" if self.options.print_errors_at_runtime else "OFF"
        cmake.definitions["FREEGLUT_PRINT_WARNINGS"] = "ON" if self.options.print_warnings_at_runtime else "OFF"
        cmake.definitions["FREEGLUT_INSTALL_PDB"] = "ON" if self.options.install_pdb else "OFF"
        cmake.definitions["INSTALL_PDB"] = False
        # cmake.definitions["FREEGLUT_WAYLAND"] = "ON" if self.options.wayland else "OFF" # nightly version only as of now

        cmake.configure(build_folder=self._build_subfolder)
        return cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy(pattern="COPYING", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()
        tools.rmdir(os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.libdirs = ["lib", "lib64"]

        self.cpp_info.libs = []

        if self.options.replace_glut:
            if self.options.shared:
                self.cpp_info.libs.append("libglut.so")
            else:
                self.cpp_info.libs.append("libglut.a")
        else:
            if self.settings.compiler == "Visual Studio" and self.settings.build_type == "Debug":
                self.cpp_info.libs.append("freeglutd")
            else:
                self.cpp_info.libs.append("freeglut")

        if self.settings.os == "Windows":
            if not self.options.shared:
                self.cpp_info.defines.append("FREEGLUT_STATIC=1")
            self.cpp_info.defines.append("FREEGLUT_LIB_PRAGMAS=0")
            self.cpp_info.libs.append("glu32")
            self.cpp_info.libs.append("opengl32")
            self.cpp_info.libs.append("gdi32")
            self.cpp_info.libs.append("winmm")
            self.cpp_info.libs.append("user32")

        if self.settings.os == "Macos":
            self.cpp_info.exelinkflags.append("-framework OpenGL")

        if self.settings.os == "Linux":
            self.cpp_info.libs.append("GL")
            self.cpp_info.libs.append("GLU")
            self.cpp_info.libs.append("Xxf86vm")
            self.cpp_info.libs.append("Xrandr")
            self.cpp_info.libs.append("Xi")
            self.cpp_info.libs.append("GLX")
            self.cpp_info.libs.append("GLdispatch")
            self.cpp_info.libs.append("xcb")
            self.cpp_info.libs.append("Xext")
            self.cpp_info.libs.append("Xrender")
            self.cpp_info.libs.append("X11")
            self.cpp_info.libs.append("pthread")
            self.cpp_info.libs.append("m")
            self.cpp_info.libs.append("dl")
            self.cpp_info.libs.append("rt")

        self.output.info(self.cpp_info.libs)
