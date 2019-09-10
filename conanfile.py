import os

from conans import CMake, ConanFile, tools
from conans.errors import ConanInvalidConfiguration


class DartsimConan(ConanFile):
    name = "dart"
    version = "6.9.2"
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
    exports = [
        "LICENSE.md",
        "dartpy_find_python.patch",
        "find-assimp-using-conan.patch",
    ]
    generators = "cmake"

    # Options may need to change depending on the packaged library.
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "build_dartpy": [True, False],
        "python_version": "ANY",
        "shared_python": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "bullet3:double_precision": True,
        "build_dartpy": False,
        "python_version": "UNSET",
        "shared_python": False,
    }

    # Custom attributes for Bincrafters recipe conventions
    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    requires = (
        "assimp/5.0.0.rc2@rhololkeolke/stable",
        "eigen/3.3.5@conan/stable",
        "boost/1.69.0@conan/stable",
        "boost_regex/1.69.0@bincrafters/stable",
        "libccd/2.1@rhololkeolke/stable",
        "fcl/0.6.0RC@rhololkeolke/stable",
        "octomap/1.9.0@rhololkeolke/stable",
        "nlopt/2.6.1@rhololkeolke/stable",
        "pagmo/2.10@rhololkeolke/stable",
        "bullet3/2.88@bincrafters/stable",
    )

    def configure(self):
        if self.options.build_dartpy and self.options.python_version == "UNSET":
            raise ConanInvalidConfiguration(
                "If you enable the build_dartpy option, you must specify a python version"
            )

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def requirements(self):
        if self.options.build_dartpy:
            self.requires("pybind11/2.3.0@conan/stable")

    def source(self):
        source_url = "https://github.com/dartsim/dart"
        tools.get(
            "{0}/archive/v{1}.tar.gz".format(source_url, self.version),
            sha256="7d46d23c04d74d3b78331f9fa7deb5ab32fd4b0c03b93548cd84a2d67771d816",
        )
        extracted_dir = self.name + "-" + self.version

        # Rename to "source_subfolder" is a convention to simplify later steps
        os.rename(extracted_dir, self._source_subfolder)

        tools.replace_in_file(
            os.path.join(self._source_subfolder, "CMakeLists.txt"),
            "project(dart)",
            """project(dart)
include(${CMAKE_CURRENT_BINARY_DIR}/../conanbuildinfo.cmake)
conan_basic_setup()""",
        )

        tools.patch(
            base_path=self._source_subfolder, patch_file="dartpy_find_python.patch"
        )
        tools.patch(
            base_path=self._source_subfolder, patch_file="find-assimp-using-conan.patch"
        )

        # hack to get dartpy to link against assimp correctly
        assimp_libs = [f"-l{lib}" for lib in self.deps_cpp_info["assimp"].libs]
        tools.replace_in_file(
            os.path.join(self._source_subfolder, "python", "dartpy", "CMakeLists.txt"),
            "target_include_directories(dartpy PUBLIC ${CONAN_INCLUDE_DIRS_ASSIMP})",
            (
                "target_include_directories(dartpy PUBLIC ${CONAN_INCLUDE_DIRS_ASSIMP})\n"
                f"target_link_libraries(dartpy PUBLIC {' '.join(assimp_libs)})\n"
            ),
        )

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
            "coinor-libipopt-dev",
            "libtinyxml2-dev",
            "libode-dev",
            "libflann-dev",
            "liburdfdom-dev",
            "libgl1-mesa-dev",
            "freeglut3-dev",
            "libopenscenegraph-dev",
            "libopenthreads-dev",
            "liblz4-dev",
        ]

        installer = tools.SystemPackageTool()
        arch_suffix = self.system_package_architecture()
        for package in packages:
            installer.install("{}{}".format(package, arch_suffix))

    def _configure_cmake(self, with_py=False):
        cmake = CMake(self)
        cmake.definitions["BUILD_TESTS"] = False  # example

        # DART tries to detect if the packaged assimp version has the
        # constructor/destructor defined. However, this check seems to
        # fail when using the conan package (which does have these
        # symbols). This likely has something to do with the
        # check_cxx_compiles not getting the right flags from
        # conan. When the final linking happens, there are multiple
        # definitions of the constructors/destructors which breaks the
        # build. Manually defining these preprocessor macros to
        # prevent this issue.
        cmake.definitions["ASSIMP_AISCENE_CTOR_DTOR_DEFINED"] = 1
        cmake.definitions["ASSIMP_AIMATERIAL_CTOR_DTOR_DEFINED"] = 1
        if with_py:
            cmake.definitions["DART_BUILD_DARTPY"] = self.options.build_dartpy
            if self.options.build_dartpy:
                cmake.definitions[
                    "PYBIND11_PYTHON_VERSION"
                ] = self.options.python_version
                cmake.definitions["DARTPY_PYTHON_VERSION"] = self.options.python_version
                cmake.definitions[
                    "Python_USE_STATIC_LIBS"
                ] = not self.options.shared_python
                if "Python_ROOT_DIR" in os.environ:
                    cmake.definitions["Python_ROOT_DIR"] = os.environ["Python_ROOT_DIR"]
        else:
            cmake.definitions["DART_BUILD_DARTPY"] = False
        if self.options.build_dartpy:
            cmake.definitions["CMAKE_CXX_FLAGS"] = "-fsized-deallocation"
        cmake.configure(
            build_folder=self._build_subfolder, source_folder=self._source_subfolder
        )
        return cmake

    def build(self):
        cmake = self._configure_cmake(with_py=True)
        cmake.build()

    def package(self):
        self.copy(pattern="LICENSE", dst="licenses", src=self._source_subfolder)
        # before installing, we need to configure without python
        # because DART disables the install targets when python
        # bindings are built
        cmake = self._configure_cmake(with_py=False)
        cmake.install()
        # If the CMakeLists.txt has a proper install method, the steps below may be redundant
        # If so, you can just remove the lines below
        include_folder = os.path.join(self._source_subfolder, "include")
        self.copy(pattern="*", dst="include", src=include_folder)
        self.copy(pattern="*.dll", dst="bin", keep_path=False)
        self.copy(pattern="*.lib", dst="lib", keep_path=False)
        self.copy(pattern="*.a", dst="lib", keep_path=False)
        self.copy(pattern="*.so*", dst="lib", keep_path=False, excludes="*dartpy.so*")
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
        # copy the python library to separate folder
        if self.options.build_dartpy:
            self.copy(pattern="*dartpy.so*", dst="python", keep_path=False)

    def package_info(self):
        libs = tools.collect_libs(self)
        if self.options.build_dartpy:
            # Make sure dartpy.so didn't sneak into the libs list
            #
            # Although the copy rules in the package method should
            # prevent this.
            try:
                del libs[libs.index("dartpy")]
            except ValueError:
                pass

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

        libs.append("tinyxml2")
        libs.append("ode")

        self.cpp_info.libs = libs

        # set pythonpath if python bindings are built
        if self.options.build_dartpy:
            self.env_info.PYTHONPATH.append(os.path.join(self.package_folder, "python"))
