cmake_minimum_required(VERSION 2.8.12)
project(test_package)

set(CMAKE_VERBOSE_MAKEFILE TRUE)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} ${CONAN_LIBS})

# only run if conanfile for test_package deems necessary
add_custom_target(test_python_bindings
  ${CMAKE_COMMAND} -E env PYTHONPATH="${CONAN_DART_ROOT}/python" python3.7 ${CMAKE_CURRENT_SOURCE_DIR}/test_python_bindings.py)
set_target_properties(test_python_bindings PROPERTIES EXCLUDE_FROM_ALL ON)
