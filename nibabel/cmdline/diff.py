#!python
# emacs: -*- mode: python-mode; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the NiBabel package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
"""
Quick summary of the differences among a set of neuroimaging files
"""
from __future__ import division, print_function, absolute_import

import sys
from optparse import OptionParser, Option

import numpy as np

import nibabel as nib
import nibabel.cmdline.utils
import itertools
import hashlib


def get_opt_parser():
    # use module docstring for help output
    p = OptionParser(
        usage="%s [OPTIONS] [FILE ...]\n\n" % sys.argv[0] + __doc__,
        version="%prog " + nib.__version__)

    p.add_options([
        Option("-v", "--verbose", action="count",
               dest="verbose", default=0,
               help="Make more noise.  Could be specified multiple times"),

        Option("-H", "--header-fields",
               dest="header_fields", default='all',
               help="Header fields (comma separated) to be printed as well (if present)"),
    ])

    return p


def diff_values(compare1, compare2):
    """Generically compares two values, returns true if different"""
    if np.any(compare1 != compare2):
        return True
    elif type(compare1) != type(compare2):
        return True
    elif compare1 != compare2:
        return True
    else:
        return False


def diff_header_fields(key, inputs):
    """Iterates over a single header field of multiple files"""

    keyed_inputs = []

    for i in inputs:  # stores each file's respective header files
        field_value = i[key]

        try:  # filter numpy arrays
            if np.all(np.isnan(field_value)):
                continue
        except TypeError:
            pass

        for x in inputs[1:]:  # compare different values, print all as soon as diff is found
            data_diff = diff_values(str(x[key].dtype), str(field_value.dtype))

            if data_diff:
                break

        if data_diff:  # prints data types if they're different and not if they're not
            if field_value.ndim < 1:
                keyed_inputs.append("{}@{}".format(field_value, field_value.dtype))
            elif field_value.ndim == 1:
                keyed_inputs.append("{}@{}".format(list(field_value), field_value.dtype))
        else:
            if field_value.ndim < 1:
                keyed_inputs.append("{}".format(field_value))
            elif field_value.ndim == 1:
                keyed_inputs.append("{}".format(list(field_value)))

    if keyed_inputs:  # sometimes keyed_inputs is empty lol
        comparison_input = keyed_inputs[0]

        for i in keyed_inputs[1:]:
            if diff_values(comparison_input, i):
                return keyed_inputs


def get_headers_diff(files, opts):

    header_list = [nib.load(f).header for f in files]

    if opts.header_fields:
        # signals "all fields"
        if opts.header_fields == 'all':
            # TODO: header fields might vary across file types, thus prior sensing would be needed
            header_fields = header_list[0].keys()
        else:
            header_fields = opts.header_fields.split(',')

        output = {}

        for f in header_fields:
            val = diff_header_fields(f, header_list)

            if val:
                output[f] = val

        return output


def get_data_diff(files):

    data_list = [nib.load(f).get_data() for f in files]

    for a, b in itertools.combinations(data_list, 2):
        return diff_values(hashlib.md5(repr(a).encode('utf-8')).hexdigest(), hashlib.md5(
            repr(b).encode('utf-8')).hexdigest())


def main():
    """NO DAYS OFF"""

    parser = get_opt_parser()
    (opts, files) = parser.parse_args()

    nibabel.cmdline.utils.verbose_level = opts.verbose

    assert len(files) >= 2, "Please enter at least two files"

    if nibabel.cmdline.utils.verbose_level < 3:
        # suppress nibabel format-compliance warnings
        nib.imageglobals.logger.level = 50

    diff = get_headers_diff(files, opts)
    diff2 = get_data_diff(files)

    print("{:<11}".format('Field'), end="")

    for f in files:
        print("{:<45}".format(f), end="")
    print()

    for x in diff:
        print("{:<11}".format(x), end="")

        for e in diff[x]:
            print("{:<45}".format(e), end="")

        print()

    print("DATA: ", end="")

    if diff2:
        print("These files are different.")
    else:
        print("These files are identical!")

    raise SystemExit(1)
