
def use_ipdb():
    import os
    os.environ['PYTHONBREAKPOINT'] = 'ipdb.set_trace'
