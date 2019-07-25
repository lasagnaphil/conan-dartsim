from conans import ConanFile, CMake, tools
import os


class DartsimConan(ConanFile):
    name = "dart"
    version = "6.9.1"
    description = "Dynamic Animation and Robotics Toolkit"
    # topics can get used for searches, GitHub topics, Bintray tags
    # etc. Add here keywords about the library
    topics = ("physics", "simulation")
    url = "https://github.com/rhololkeolke/conan-dartsim.git"
    homepage = "https://dartsim.github.io"
    author = "Devin Schwab <dschwab@andrew.cmu.edu>"
    license = (
        'BSD 2-Clause "Simplified" License'
    )  # Indicates license type of the packaged library; please use
    # SPDX Identifiers https://spdx.org/licenses/
    exports = ["LICENSE.md"]  # Packages the license for the
    # conanfile.py Remove following lines if the target lib does not
    # use cmake.
    exports_sources = ["CMakeLists.txt"]
    generators = "cmake"

    # Options may need to change depending on the packaged library.
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}

    # Custom attributes for Bincrafters recipe conventions
    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    requires = (
        "eigen/3.3.7@conan/stable",
        "boost/1.69.0@conan/stable",
        "boost_regex/1.69.0@bincrafters/stable",
    )

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def source(self):
        source_url = "https://github.com/dartsim/dart"
        tools.get(
            "{0}/archive/v{1}.tar.gz".format(source_url, self.version),
            sha256="9e2954aaf2d4538a7e4aab5188f1061c3e216c8c0b72483c2d0b9e814525acd1",
        )
        extracted_dir = self.name + "-" + self.version

        # Rename to "source_subfolder" is a convention to simplify later steps
        os.rename(extracted_dir, self._source_subfolder)
        os.symlink(os.path.join(os.getcwd(), self._source_subfolder, "cmake"), "cmake")

    def system_package_architecture(self):
        if tools.os_info.with_apt:
            if self.settings.arch == "x86":
                return ":i386"
            elif self.settings.arch == "x86_64":
                return ":amd64"
            elif self.settings.arch == "armv6" or self.settings.arch == "armv7":
                return ":armel"
            elif self.settings.arch == "armv7hf":
                return ":armhf"
            elif self.settings.arch == "armv8":
                return ":arm64"

        if tools.os_info.with_yum:
            if self.settings.arch == "x86":
                return ".i686"
            elif self.settings.arch == "x86_64":
                return ".x86_64"
        return ""

    def system_requirements(self):
        packages = [
            "libassimp-dev",
            "libccd-dev",
            "libfcl-dev",
            "libtinyxml2-dev",
            "libode-dev",
        ]

        installer = tools.SystemPackageTool()
        arch_suffix = self.system_package_architecture()
        for package in packages:
            installer.install("{}{}".format(package, arch_suffix))

    def _configure_cmake(self):
        cmake = CMake(self)
        cmake.definitions["BUILD_TESTS"] = False  # example
        cmake.configure(
            build_folder=self._build_subfolder, source_folder=self._source_subfolder
        )
        return cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy(pattern="LICENSE", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()
        # If the CMakeLists.txt has a proper install method, the steps below may be redundant
        # If so, you can just remove the lines below
        include_folder = os.path.join(self._source_subfolder, "include")
        self.copy(pattern="*", dst="include", src=include_folder)
        self.copy(pattern="*.dll", dst="bin", keep_path=False)
        self.copy(pattern="*.lib", dst="lib", keep_path=False)
        self.copy(pattern="*.a", dst="lib", keep_path=False)
        self.copy(pattern="*.so*", dst="lib", keep_path=False)
        self.copy(pattern="*.dylib", dst="lib", keep_path=False)
        # copy all the external libraries
        external_lib_folders = [
            "dart/external/imgui",
            "dart/external/lodepng",
            "dart/external/odelcpsolver",
        ]
        for external_lib_folder in external_lib_folders:
            self.copy(
                pattern="*.dll", src=external_lib_folder, dst="bin", keep_path=False
            )
            self.copy(
                pattern="*.lib", src=external_lib_folder, dst="lib", keep_path=False
            )
            self.copy(
                pattern="*.a", src=external_lib_folder, dst="lib", keep_path=False
            )
            self.copy(
                pattern="*.so*", src=external_lib_folder, dst="lib", keep_path=False
            )
            self.copy(
                pattern="*.dylib", src=external_lib_folder, dst="lib", keep_path=False
            )

    def package_info(self):
        libs = tools.collect_libs(self)

        # make sure dart is the first library so that the linking
        # order is correct
        try:
            dart_index = libs.index("dart")
            if dart_index != 0:
                del libs[dart_index]
                libs.insert(0, "dart")
        except ValueError:
            pass

        # I don't know why sometimes it builds with dart and sometimes
        # with dartd
        try:
            dart_index = libs.index("dartd")
            if dart_index != 0:
                del libs[dart_index]
                libs.insert(0, "dartd")
        except ValueError:
            pass

        libs.append("fcl")
        libs.append("assimp")
        libs.append("ccd")
        libs.append("octomap")
        libs.append("octomath")
        libs.append("tinyxml2")
        # libs.append("ode")

        self.cpp_info.libs = libs
