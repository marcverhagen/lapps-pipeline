"""check_pipeline_output.py

This takes all results in data/out-hybrid-* (created by test-pipelines.lsd) and
runs some tests on it, searching for errors and unexpected output.

TODO: deal with types in the metadata:contains section in a smarter way.

"""


import os, glob, json



def get_service_name(fname):
    return os.path.basename(fname).split('-')[1][:-4]

def print_pipeline(files):
    for fname in files:
        print '  ', get_service_name(fname)

def timeout_occurred(files):
    timeout_occurred = False
    for fname in files:
        fh = open(files[-1])
        text = fh.read()
        fh.close()
        if text.startswith('(408)Request Timeout'):
            timeout_occurred = True
            #print  "ERROR: Request Timeout in", get_service_name(fname)
    return timeout_occurred


def analyze(json_object):
    
    steps = json_object['steps']
    contains = get_declared_annotations(steps)
    contains_string = ' '.join(contains)
    if contains_string != "Location Lookup Person Sentence Token pos":
    #if contains_string != "NamedEntity Sentence Token posX":
        print "WARNING: unexpected declared types"
        print "         %s" % contains_string

    annotations = get_actual_annotations(steps)
    print "ANNOTATIONS:",
    for tp in sorted(annotations.keys()):
        print "%s:%d" % (tp, annotations[tp]), 
    print
    
    
def get_declared_annotations(steps):
    annotations = {}
    for step in steps:
        for anno in step['metadata']['contains'].keys():
            annotations[anno] = True
    return sorted(annotations.keys())


def get_actual_annotations(steps):
    annotations = {}
    for step in steps:
        for anno in step['annotations']:
            tp = anno['@type']
            annotations[tp] = annotations.get(tp, 0) + 1
    return annotations



if __name__ == '__main__':

    pipeline_dirs = glob.glob("data/out-hybrid-*")
    
    for pipeline_dir in pipeline_dirs:

        print "\nPIPELINE:", os.path.basename(pipeline_dir)
        
        files = sorted(glob.glob("%s/*.txt" % pipeline_dir))

        print_pipeline(files)
        
        if timeout_occurred(files):
            print  "ERROR: Request Timeout"
            continue
            
        fh = open(files[-1])
        text = fh.read()
        try:
            json_object = json.loads(text)
            print "OUTFILE:", files[-1]
            analyze(json_object)
        except ValueError, e:
            print "ERROR:", e
