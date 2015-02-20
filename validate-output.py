"""

Think of doing this in groovy, where you would import

import groovy.json.JsonSlurper;


"""


import os, sys, codecs, shlex, getopt, json
from subprocess import Popen, PIPE

# the schema are currently not needed because the validator has them hard-wired,
# but this may change at some point
VALIDATOR = 'http://grid.anc.org:9080/json-validator/lif'
SCHEMA = 'http://vocab.lappsgrid.org/schema/lif-schema.json'


class FileValidation(object):

    """Just a simple object to store valiation results in."""
    
    def __init__(self, fname):
        self.fname = fname
        self.is_json = False
        self.json_data = None
        self.is_lif = False
        self.lif_messages = []

    def print_results(self):
        print "      %sJSON %sLIF" % ('+' if self.is_json else '-',
                                      '+' if self.is_lif else '-')
        for m in self.lif_messages:
            print "      lif-error: %s" % m


def validator_command(fname):
    """Return the curl command needed to call the validator, the command is a list
    of arguments as needed by Popen."""
    cmd = "curl -i -X POST " + \
          "-H Content-Type:application/json " + \
          "-H Accept:application/json " + \
          "--data-binary @%s " % fname + \
          VALIDATOR
    return shlex.split(cmd)


def validate_pipeline(pipeline_dir):
    print "\nValidating %s" % pipeline_dir
    fnames = os.listdir(pipeline_dir)
    for fname in fnames:
        print "\n  ", fname
        fv = FileValidation(fname)
        validate_file(pipeline_dir, fname, fv)
        fv.print_results()
    print


def validate_file(pipeline_dir, fname, fv):
    fpath = os.path.join(pipeline_dir, fname)
    fh = codecs.open(fpath, encoding='utf8')
    check_filetype(fh, fv)
    check_lif_schema(fpath, fv)
    check_lif_principles(fv)


def check_filetype(fh, fv):
    try:
        json_data = json.load(fh)
        #print json_data
        fv.is_json = True
        fv.jason_data = json_data
    except ValueError:
        fv.is_json = False


def check_lif_schema(fpath, fv):
    if not fv.is_json:
        return
    cmd = validator_command(fpath)
    p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    output = read_validator_output(p)
    if output is None:
        fv.is_lif = True
    else:
        fv.is_lif = False
        fv.lif_messages = []
        for obj in output:
            fv.lif_messages.append(obj['message'])


def read_validator_output(process):
    for line in process.stdout:
        if line.startswith('[') and line.endswith(']'):
            return eval(line)
    return None

    
def check_lif_principles(fv):
    if not fv.is_lif:
        return
    # TODO: this shows up empty
    print fv.json_data
    

    
if __name__ == '__main__':

    pipeline_p = False

    opts, args = getopt.getopt(sys.argv[1:], 'p:', ['pipeline='])

    for opt, val in opts:
        if opt in ('-p', '--pipeline'):
            pipeline_p = True
            pipeline_dir = val
            
    if pipeline_p:
        validate_pipeline(pipeline_dir)
