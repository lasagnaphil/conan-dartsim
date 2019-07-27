#!/usr/bin/env python
# -*- coding: utf-8 -*-
import copy

from cpt.packager import ConanMultiPackager

if __name__ == "__main__":
    builder = ConanMultiPackager()
    builder.add_common_builds()

    # add c++17 build configs
    new_builds = []
    for settings, options, env_vars, build_requires, reference in builder.items:
        new_settings = copy.copy(settings)
        new_settings["compiler.cppstd"] = "17"
        new_settings["compiler.libcxx"] = "libstdc++11"
        new_builds.append([settings, options, env_vars, build_requires])
        new_builds.append([new_settings, options, env_vars, build_requires])
    builder.builds = new_builds

    builder.run()
