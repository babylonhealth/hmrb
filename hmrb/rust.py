# -*- coding: utf-8 -*-
import os.path
import os
import sys
from cffi import FFI

# See https://github.com/SimonSapin/hello-pyrust


if sys.platform == "win32":
    DYNAMIC_LIB_FORMAT = "%s.dll"
elif sys.platform == "darwin":
    DYNAMIC_LIB_FORMAT = "lib%s.dylib"
elif "linux" in sys.platform:
    DYNAMIC_LIB_FORMAT = "lib%s.so"
else:
    raise NotImplementedError(
        'No implementation for "{}".'
        " Supported platforms are "
        '"win32", "darwin", and "linux"'
        "".format(sys.platform)
    )
ffi = FFI()
(file_path, _) = os.path.split(__file__)
cwd = os.getcwd()

h_path = os.path.join(file_path, "rust", "src", "hmrb.h",)
h_rel_path = os.path.join(os.curdir, os.path.relpath(h_path, cwd))

dlib_path = os.path.join(
    file_path, "rust", "target", "release", DYNAMIC_LIB_FORMAT % "hmrb"
)
dlib_rel_path = os.path.join(os.curdir, os.path.relpath(dlib_path, cwd))

with open(h_rel_path) as h:
    ffi.cdef(h.read())

rust_lib = ffi.dlopen(dlib_rel_path)


def main():
    assert rust_lib.is_prime(13) == 1
    assert rust_lib.is_prime(12) == 0


if __name__ == "__main__":
    main()
