#!/usr/bin/python3
# =========================================================================================================
# Script: casewalker.py
# Execution: $ ./casewalker.py -f ./facts.json
# Author: Roy Maassen (Deltiq)
# Company: Deltiq
# =========================================================================================================
# MIT License
# Copyright (c) 2020 Roy Maassen (Deltiq)
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# =========================================================================================================

import getopt
import sys
import glob
import json
import os.path
import re
from datetime import datetime
from datetime import date

# handy constants
cdivider = "*" * 70
cnewline = "\n"

# elements that are used in the script below, these must be present in the json data:
ctitle = "title"
cmodel = "model"
ctags = "tags"
cdata = "data"
ctemplate = "template"

# Text will be inserted into factsentences where there is no corresponding data element found.
cmissing = "###MISSING###"

# Prepended text before datetimestamp.
cgenon = "Generated on"

# separator for tags
ccomma = ", "

# default filename when no model element is found
cdeffilename = "generated_by_the_casewalker.exp"

# default slash (windows uses other)
cslash = "/"

# Switch to different slash for windows:
if sys.platform == 'win32':
    cslash = "\\"

casterisk = "*"

# default output location for generated files
coutputdirectory = f".{cslash}output{cslash}{date.today()}"

# define the access rights
access_rights = 0o755

# default file extension:
cfileext = ".exp"

def usage():
    # =========================================================================================================
    # Standard output when script is executed without argument.
    # =========================================================================================================
    print("./casewalker.py -f <json-bestand>")


def remove_files():
    # =========================================================================================================
    # Remove the generated files, otherwise facttypes will be appended to the files..
    # =========================================================================================================
    try:
        if os.path.exists(coutputdirectory):
            # remove present files
            files = glob.glob(f"{coutputdirectory}{cslash}{casterisk}")
            for f in files:
                os.remove(f)
    except OSError:
        print(f"Removal of the files inside {coutputdirectory} failed.")

def generate_files(facttype_string='', model_string=''):
    # =========================================================================================================
    # The various facttypes will be written to their own files based on the model tag.
    # The filename will be a lowercased, underscored version of the model name, with the .exp extension
    # When there is no model element, output will be written to 'generated_by_the_casewalker.exp'
    # =========================================================================================================

    # Generate the filename for writing of the facttype, otherwise use default filename..
    if model_string == '':
        output_file = f"{coutputdirectory}{cslash}{cdeffilename}"
    else:
        file_name = model_string.replace(' ', '_')
        file_name = file_name.lower()
        output_file = f"{coutputdirectory}{cslash}{file_name}{cfileext}"

    # Test if the file already exists, if so, overwrite it's contents (it's generated each time.. remember?)
    print(f"Writing fact-type to {output_file}.")

    # Try to create the output directory:
    try:
        if not os.path.exists(coutputdirectory):
            os.mkdir(coutputdirectory, access_rights)
    except OSError:
        print(f"Creation of the directory {coutputdirectory} failed")

    # Upon file creation
    if not os.path.exists(output_file):
        with open(output_file, 'w+') as f:
            f.write(f"[EXPFILE]{cnewline}")

    # Write away the fact-type in the correct file:
    with open(output_file, 'a+') as f:
        f.write(facttype_string)


def generate_sentence(sentence='', values=[]):
    # =========================================================================================================
    # For each row in the data element, the fact sentence gets generated.
    # =========================================================================================================

    for i, value in enumerate(values, 1):
        sentence = sentence.replace(f"<val{i}>", value)

    # Add double quotes to the generated sentence:
    sentence = f'"{sentence}"'

    # Add #MISSING# string for missing data elements in the source json file:
    sentence = re.sub(r'<val\d+>', cmissing, sentence)
    sentence += f"{cnewline}"
    return sentence


def generate_facttype(data=''):
    # =========================================================================================================
    # The entire facttype block gets generated in this function, and it's output will be saved to the
    # corresponding filename.
    # =========================================================================================================

    # This variable will hold the filename and the strings with facttypes
    files_dict = {}

    # Sort the json data alphabetically on title.
    newlist = sorted(data, key=lambda k: k['title'])

    # Iterate over all the sentences:
    for elem in newlist:
        # Iterate over the dictionary that contains the sentences
        facttype_string = ''
        model_string = ''

        for key, value in elem.items():

            # Print the title part
            if key in [ctitle]:
                facttype_string += f"; {cdivider}{cnewline}"
                facttype_string += f"; FACT-TYPE: {value.upper()}{cnewline}"
                facttype_string += f"; {cdivider}{cnewline}"
                facttype_string += f"; {cgenon:20}: {datetime.now()}{cnewline}"

            # Print the metadata parts (exclude those parts that are processed elsewhere).
            if key not in [ctitle, ctags, ctemplate, cdata]:
                facttype_string += f"; {key.capitalize():20}: {value}{cnewline}"

            # Setup the tags part:
            if key in [ctags]:
                tag_string = f"; {key.capitalize():20}: "
                for i in range(len(value)):
                    tag_string += f"#{value[i].upper()}"
                    if i < len(value)-1:
                        tag_string += ccomma
                facttype_string += f"{tag_string}{cnewline}"

            # Generate the sentence for each row of example data:
            if key in [cdata]:
                for j in value:
                    facttype_string += generate_sentence(elem[ctemplate], j)

            # If the model element exists in the structure, pass it to the model_string (for file generation).
            # Else, keep it empty and use the default file for file generation (see generate_files function).
            if key in [cmodel]:
                model_string = elem[cmodel]

        # Append an extra newline for nice layout
        facttype_string += cnewline

        # If the element cmodel doesn't exist, pass an empty string.
        generate_files(facttype_string, model_string)


def main():
    file = ''

    # Inlezen van de commandline variabelen
    try:
        opts, args = getopt.getopt(sys.argv[1:], "f:")
    except getopt.GetoptError as err:
        usage()
        sys.exit(2)

    # Is het bestand meegegeven in de aanroep van het script?
    for arg, val in opts:
        if arg in ("-f", "--file"):
            file = val
        else:
            usage()
            sys.exit(0)

    # Is het een bestaand bestand en niet leeg?
    if os.path.exists(file) and os.path.getsize(file) > 0:

        # Is het een valide json bestand?
        try:
            with open(file) as f:
                return json.load(f)
        except ValueError as e:
            print('De JSON syntax was niet in orde: %s' % e)
            sys.exit(1)


if __name__ == "__main__":
    # Inlezen van de bestandsnaam:
    data = main()

    # Delete generated files if present in output folder:
    remove_files()

    # Generate facttypes and write them into separated files:
    generate_facttype(data)