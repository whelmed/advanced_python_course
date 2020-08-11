
def use_ipdb():
    import os
    os.environ['PYTHONBREAKPOINT'] = 'ipdb.set_trace'


def ipython_shell():
    from IPython.terminal.embed import InteractiveShellEmbed
    from traitlets.config.loader import Config
    config = Config()
    config.InteractiveShell.colors = 'Linux'
    embed = InteractiveShellEmbed(config=config)
    embed('Welcome! Type Ctl+D to detach from this IPython Shell')
