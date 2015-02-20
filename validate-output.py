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


class File(object):

    """An object that stores relevant information about a file, including
    validation results."""
    
    def __init__(self, pipeline_dir, fname):
        self.fname = fname
        self.fpath = os.path.join(pipeline_dir, self.fname)
        self.fh = codecs.open(self.fpath, encoding='utf8')
        self.is_error = False
        self.is_json = False
        self.is_lif = False
        self.json_data = None
        self.messages = []

    def validate(self):
        self.check_filetype()
        self.check_lif_schema()
        self.check_lif_principles()

    def check_filetype(self):
        try:
            self.json_data = json.load(self.fh)
            self.is_json = True
        except ValueError:
            self.is_json = False
            self.json_data = None
        self.is_error = True if has_error(self.fh) else False

    def check_lif_schema(self):
        if not self.is_json:
            return
        cmd = validator_command(self.fpath)
        p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output = read_validator_output(p)
        if output is None:
            self.is_lif = True
        else:
            self.is_lif = False
            self.messages = ["lif-error - %s" % obj['message'] for obj in output]

    def check_lif_principles(self):
        if not self.is_lif:
            return
        lif = Lif(self.json_data)
        lif.analyze()
        self.messages += lif.messages

    def print_results(self):
        print "      %sERROR %sJSON %sLIF" % ('+' if self.is_error else '-',
                                              '+' if self.is_json else '-',
                                              '+' if self.is_lif else '-')
        for m in self.messages:
            print "      %s" % m



class Lif(object):

    def __init__(self, json_data):
        self.json = json_data
        self.messages = []

    def analyze(self):
        steps = self.json['views']
        self.declared = self.get_declared_annotations(steps)
        self.actual = self.get_actual_annotations(steps)
        self.messages.append("lif-note - declared annotations: [%s]" % ', '.join(self.declared))
        self.messages.append("lif-note - actual annotations: [%s]" % ', '.join(self.actual))

    def get_declared_annotations(self, steps):
        annotations = {}
        for step in steps:
            #print step['metadata']
            for anno in step['metadata']['contains'].keys():
                annotations[anno] = True
        return sorted(annotations.keys())

    def get_actual_annotations(self, steps):
        annotations = {}
        for step in steps:
            for anno in step['annotations']:
                tp = anno['@type']
                annotations[tp] = annotations.get(tp, 0) + 1
        # return annotations
        return sorted(annotations.keys())


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
        if fname[-1] == '~': continue
        print "\n  ", fname
        f = File(pipeline_dir, fname)
        f.validate()
        f.print_results()
    print


def has_error(fh):
    # TODO: this is very brittle and needs to be changed
    fh.seek(0)
    line = fh.readline()
    if line.startswith('Unable to execute'):
        return True
    return False

def read_validator_output(process):
    for line in process.stdout:
        if line.startswith('[') and line.endswith(']'):
            return eval(line)
    return None
    

    
if __name__ == '__main__':

    pipeline_p = False

    opts, args = getopt.getopt(sys.argv[1:], 'p:', ['pipeline='])

    for opt, val in opts:
        if opt in ('-p', '--pipeline'):
            pipeline_p = True
            pipeline_dir = val
            
    if pipeline_p:
        validate_pipeline(pipeline_dir)
