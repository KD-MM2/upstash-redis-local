import os
import shutil
from glob import glob

from Cython.Build import cythonize
from setuptools import find_packages, setup

# Set build directory for Cython-generated files
# Prepare build directory
build = "build"
src = "src"
package_name = "upstash_redis_local"

if os.path.exists(build):
    shutil.rmtree(build)
os.makedirs(build)

build_src = os.path.join(build, package_name)
os.makedirs(build_src)

# Copy Python source files to build directory
# Keep original extension for __init__.py and __main__.py, rename others to .pyx
src_dir = os.path.join("src", package_name)
for p in glob(os.path.join(src_dir, "*.py")):
    filename = os.path.basename(p)
    if filename in ("__init__.py", "__main__.py"):
        shutil.copy(p, os.path.join(build_src, filename))
    else:
        new_filename = filename.replace(".py", ".pyx")
        shutil.copy(p, os.path.join(build_src, new_filename))

# Get .pyx files for Cython compilation
pyx_files = glob(os.path.join(build_src, "*.pyx"))

# Configure Cython build options
ext_modules = cythonize(
    pyx_files,
    compiler_directives={
        "language_level": "3",
        "embedsignature": True,
    },
    build_dir=build,
)

setup(
    name="upstash-redis-local",
    version="0.1.0",
    packages=[package_name],
    package_dir={package_name: build_src},
    ext_modules=ext_modules,
    include_package_data=False,
    zip_safe=False,
)
