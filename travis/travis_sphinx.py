#!/usr/bin/env python
# coding: utf-8

from __future__ import print_function
from __future__ import unicode_literals
import os
import sys
import sphinx
import subprocess
from test_server import get_addons_path, get_server_path, \
    get_addons_to_check
from travis_helpers import yellow_light


def main(argv=None):
    """
    Generate sphinx documentation from modules
    If not, export exits early.
    """
    if argv is None:
        argv = sys.argv

    travis_home = os.environ.get("HOME", "~/")
    travis_build_dir = os.environ.get("TRAVIS_BUILD_DIR", "../..")
    travis_repo_slug = os.environ.get("TRAVIS_REPO_SLUG")
    travis_repo_shortname = travis_repo_slug.split("/")[1]
    odoo_exclude = os.environ.get("EXCLUDE")
    odoo_include = os.environ.get("INCLUDE")
    odoo_version = os.environ.get("VERSION", "8.0")
    sphinx_builder = os.environ.get("SPHINX_BUILDER", "html")
    sphinx_dir = travis_build_dir + "/sphinx"
    sphinx_source_dir = sphinx_dir + "/source"

    if not odoo_version:
        # For backward compatibility, take version from parameter
        # if it's not globally set
        odoo_version = sys.argv[1]
        print(yellow_light("WARNING: no env variable set for VERSION. "
              "Using '%s'" % odoo_version))

    odoo_full = os.environ.get("ODOO_REPO", "odoo/odoo")
    server_path = get_server_path(odoo_full, odoo_version, travis_home)
    addons_path = get_addons_path(travis_home, travis_build_dir, server_path)
    addons_list = get_addons_to_check(travis_build_dir, odoo_include,
                                      odoo_exclude)
    addons = ','.join(addons_list)

    print("\nWorking in %s" % travis_build_dir)
    print("Using repo %s and addons path %s" % (odoo_full, addons_path))

    if not addons:
        print(yellow_light("WARNING! No module found- exiting early."))
        return 0

    print()
    print("\nModules used to generate documentation: %s" % addons)

    # Execute sphinx build
    print()
    if not os.path.exists(sphinx_source_dir):
        os.makedirs(sphinx_source_dir)
    with open(sphinx_dir + "/source/index.rst", "w+") as fil:
        fil.write("%s (%s)" % (travis_repo_shortname, odoo_version))
        for addon in addons_list:
            fil.write("""
    .. automodule:: openerp.addons.%s
       :members:
             """ % addon)
    sphinx_argv = [
        "sphinx-build",
        "-b", sphinx_builder,
        "-c", "%s/maintainer-quality-tools/travis/sphinxodoo" % travis_home,
        "%s/sphinx/source" % travis_build_dir,
        "%s/sphinx/html" % travis_build_dir,
    ]
    print("Running sphinx-build : %s" % ' '.join(sphinx_argv))
    sphinx.build_main(sphinx_argv)

    # Upload the documentation
    cmd = [
        "rsync",
        "-vaz",
        "-e", "ssh -o StrictHostKeyChecking=no -i %s/.travis/id_dsa" % travis_home,
        "--delete",
        "%s/sphinx/html" % travis_build_dir,
        "oca-doc@odoo-community.org:public_html/%s/%s" % (
            odoo_version, travis_repo_shortname),
    ]
    print()
    print('Uploading documentation')
    print(' '.join(cmd))
    subprocess.check_call(cmd)

    return 0


if __name__ == "__main__":
    exit(main())
