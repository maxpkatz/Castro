#!/usr/bin/env python3

"""
This routine parses plain-text parameter files that list runtime
parameters for use in our codes.  The general format of a parameter
is:

max_step                            integer            1
small_dt                            real               1.d-10
xlo_boundary_type                   character          ""
octant                              logical            .false.

This specifies the parameter name, datatype, and default
value.

The optional 4th column indicates whether the parameter appears
in the fortin namelist ("y" or "Y").

If the parameter is an array, the optional 5th column indicates the size of
the array.  If the size is a variable from a module, then a tuple is provided
in the form (size, module-name)

This script takes a template file and replaces keywords in it
(delimited by @@...@@) with the Fortran code required to
initialize the parameters, setup a namelist, set the defaults, etc.

"""

import argparse
import re
import sys

header = """
! DO NOT EDIT THIS FILE!!!
!
! This file is automatically generated by write_probdata.py at
! compile-time.
!
! To add a runtime parameter, do so by editting the appropriate _prob_params
! file.

"""

class Parameter:
    # the simple container to hold the runtime parameters
    def __init__(self):
        self.var = ""
        self.dtype = ""
        self.value = ""
        self.module = None
        self.size = 1
        self.in_namelist = False

    def is_array(self):
        try:
            isize = int(self.size)
        except ValueError:
            return True
        else:
            if isize == 1:
                return False
            else:
                return True

    def __str__(self):
        return "{} : {}, {} elements".format(self.var, self.dtype, self.size)


def get_next_line(fin):
    # return the next, non-blank line, with comments stripped
    line = fin.readline()

    pos = line.find("#")

    while (pos == 0 or line.strip() == "") and line:
        line = fin.readline()
        pos = line.find("#")

    return line[:pos]


def parse_param_file(param_file):
    """read all the parameters in the parameter file and add valid
    parameters to the params list.  This returns the parameter list.
    """

    err = 0
    params_list = []

    try:
        f = open(param_file, "r")
    except IOError:
        sys.exit("write_probdata.py: ERROR: file {} does not exist".format(param_file))

    line = get_next_line(f)

    while line and not err:

        # this splits the line into separate fields.  A field is a
        # single word or a pair in parentheses like "(a, b)"
        fields = re.findall(r'[\w\"\+\.-]+|\([\w+\.-]+\s*,\s*[\w\+\.-]+\)', line)

        if len(fields) < 3:
            print("write_probin.py: ERROR: missing one or more fields in parameter definition.")
            err = 1
            continue

        current_param = Parameter()

        current_param.var = fields[0]
        current_param.dtype = fields[1]
        current_param.value = fields[2]

        # optional field: in namelist
        try:
            in_namelist = fields[3]
            if in_namelist in ["y", "Y"]:
                current_param.in_namelist = True
            else:
                current_param.in_namelist = False

        except:
            current_param.in_namelist = False


        # optional field: size -- this can have the form (var, module)
        # or just be a size
        try:
            size_info = fields[4]
            if size_info[0] == "(":
                size, module = re.findall(r"\w+", size_info)
            else:
                size = size_info
                module = None

        except:
            size = 1
            module = None

        current_param.size = size
        current_param.module = module

        print(current_param)

        if not err == 1:
            params_list.append(current_param)

        line = get_next_line(f)

    return err, params_list


def abort(outfile):
    """ abort exits when there is an error.  A dummy stub file is written
    out, which will cause a compilation failure """

    fout = open(outfile, "w")
    fout.write("There was an error parsing the parameter files")
    fout.close()
    sys.exit(1)


def write_probin(probin_template, param_file, out_file):

    """ write_probin will read through the list of parameter files and
    output the new out_file """

    # read the parameters defined in the parameter files

    err, params = parse_param_file(param_file)
    if err:
        abort(out_file)

    # open up the template
    try:
        ftemplate = open(probin_template, "r")
    except IOError:
        sys.exit("write_probin.py: ERROR: file {} does not exist".format(probin_template))

    template_lines = [line for line in ftemplate]

    ftemplate.close()

    # output the template, inserting the parameter info in between the @@...@@
    fout = open(out_file, "w")

    fout.write(header)

    for line in template_lines:

        index = line.find("@@")

        if index >= 0:
            index2 = line.rfind("@@")

            keyword = line[index+len("@@"):index2]
            indent = index*" "

            if keyword == "usestatements":
                # figure out the modules we need and then the unique
                # set of variables for those modules
                modules = set([q.module for q in params])
                for m in modules:
                    if m is None:
                        continue
                    mvars = ",".join(set([q.size for q in params if q.module == m]))

                    fout.write("{}use {}, only : {}\n".format(indent, m, mvars))

            elif keyword == "declarations":

                # declaraction statements
                for p in params:

                    print(p.dtype)
                    if p.dtype == "real":
                        if p.is_array():
                            decl_string = "{}real (kind=rt), allocatable, public :: {}(:)\n"
                        else:
                            decl_string = "{}real (kind=rt), allocatable, public :: {}\n"

                    elif p.dtype == "character":
                        if p.is_array():
                            print("error, cannot have character arrays")
                            abort(out_file)
                        else:
                            decl_string = "{}character (len=256), public :: {}\n"

                    elif p.dtype == "integer":
                        if p.is_array():
                            decl_string = "{}integer, allocatable, public :: {}(:)\n"
                        else:
                            decl_string = "{}integer, allocatable, public :: {}\n"

                    elif p.dtype == "logical":
                        if p.is_array():
                            print("error, cannot have logical arrays")
                            abort(out_file)
                        else:
                            decl_string = "{}logical, allocatable, public :: {}\n"

                    else:
                        print("write_probin.py: invalid datatype for variable {}".format(p.var))

                    fout.write(decl_string.format(indent, p.var))


            elif keyword == "cudaattributes":
                for p in params:
                    if p.dtype != "character":
                        fout.write("{}attributes(managed) :: {}\n".format(indent, p.var))


            elif keyword == "namelist":
                for p in params:
                    if p.in_namelist:
                        fout.write("{}namelist /fortin/ {}\n".format(indent, p.var))


            elif keyword == "allocations":
                for p in params:
                    if p.dtype != "character":
                        if p.is_array():
                            fout.write("{}allocate({}({}))\n".format(indent, p.var, p.size))
                        else:
                            fout.write("{}allocate({})\n".format(indent, p.var))


            elif keyword == "defaults":
                for p in params:
                    if p.is_array():
                        fout.write("{}{}(:) = {}\n".format(indent, p.var, p.value))
                    else:
                        fout.write("{}{} = {}\n".format(indent, p.var, p.value))


            elif keyword == "deallocations":
                for p in params:
                    if p.dtype != "character":
                        fout.write("{}deallocate({})\n".format(indent, p.var))


            elif keyword == "printing":

                fout.write("100 format (1x, a3, 2x, a32, 1x, \"=\", 1x, a)\n")
                fout.write("101 format (1x, a3, 2x, a32, 1x, \"=\", 1x, i10)\n")
                fout.write("102 format (1x, a3, 2x, a32, 1x, \"=\", 1x, g20.10)\n")
                fout.write("103 format (1x, a3, 2x, a32, 1x, \"=\", 1x, l)\n")

                for p in params:
                    if not p.in_namelist:
                        continue

                    if p.dtype == "logical":
                        ltest = "\n{}ltest = {} .eqv. {}\n".format(indent, p.var, p.value)
                    else:
                        ltest = "\n{}ltest = {} == {}\n".format(indent, p.var, p.value)

                    fout.write(ltest)

                    cmd = "merge(\"   \", \"[*]\", ltest)"

                    if p.dtype == "real":
                        fout.write("{}write (unit,102) {}, &\n \"{}\", {}\n".format(
                            indent, cmd, p.var, p.var))

                    elif p.dtype == "character":
                        fout.write("{}write (unit,100) {}, &\n \"{}\", trim({})\n".format(
                            indent, cmd, p.var, p.var))

                    elif p.dtype == "integer":
                        fout.write("{}write (unit,101) {}, &\n \"{}\", {}\n".format(
                            indent, cmd, p.var, p.var))

                    elif p.dtype == "logical":
                        fout.write("{}write (unit,103) {}, &\n \"{}\", {}\n".format(
                            indent, cmd, p.var, p.var))

                    else:
                        print("write_probin.py: invalid datatype for variable {}".format(p.var))

        else:
            fout.write(line)

    print(" ")
    fout.close()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-t', type=str, help='probin_template')
    parser.add_argument('-o', type=str, help='out_file')
    parser.add_argument('-p', type=str, help='parameter file name')

    args = parser.parse_args()

    probin_template = args.t
    out_file = args.o
    params = args.p

    if probin_template == "" or out_file == "":
        sys.exit("write_probin.py: ERROR: invalid calling sequence")

    write_probin(probin_template, params, out_file)