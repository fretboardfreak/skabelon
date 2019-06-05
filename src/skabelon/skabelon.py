#!/usr/bin/env python3
"""
skabelon.py : A CLI Interface for the Jinja2 Templating Engine.

Skabelon is the Danish word for Template.
"""


import sys
import argparse
from importlib.util import spec_from_file_location
from importlib.util import module_from_spec
from pathlib import Path
from functools import partial

from jinja2 import Environment
from jinja2.loaders import FileSystemLoader


VERSION = "0.1"
VERBOSE = False
DEBUG = False


def main():
    """Main entrypoint for skabelon."""
    args = parse_cmd_line()
    dprint(args)

    env = Environment(loader=FileSystemLoader(str(args.templates)))

    spec = spec_from_file_location(args.dispatch.stem,
                                   args.dispatch.as_posix())
    dispatcher = module_from_spec(spec)
    spec.loader.exec_module(dispatcher)

    dispatch_args = {}
    for input_str in args.dispatch_opts:
        err_msg = ('--dispatch-args must be passed a key:value par '
                   'separated by a ":"')
        if ':' not in input_str:
            raise Exception(err_msg)
        parts = input_str.split(':')
        if len(parts) > 2:
            key = parts[0]
            value = ':'.join(parts[1:])
        elif len(parts) == 2:
            key, value = input_str.split(':')
        else:
            raise Exception(err_msg)
        dispatch_args[key] = value

    for tname, context, output_file in dispatcher.dispatch(**dispatch_args):
        template = env.get_template(tname)
        with open(output_file, 'w') as fout:
            fout.write(template.render(**context))

    return 0


def directory_path(error_message, input_string):
    """Ensure that the input string is an existing directory."""
    path = Path(input_string)
    if path.exists() and path.is_dir():
        return path
    else:
        raise argparse.ArgumentTypeError(error_message)


def dispatch_file(error_message, input_string):
    """Ensure that the input string is an existing dispatch module file."""
    path = Path(input_string)
    if path.exists() and '.py' in path.suffixes:
        return path
    else:
        raise argparse.ArgumentTypeError(error_message)


def parse_cmd_line():
    """Parse the command line arguments and return the results."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--version', help='Print the version and exit.', action='version',
        version='%(prog)s {}'.format(VERSION))
    DebugAction.add_parser_argument(parser)
    VerboseAction.add_parser_argument(parser)

    error_message = 'The given path is not a valid template directory.'
    parser.add_argument(
        '--templates', help='The directory to find the templates in.',
        default='.', type=partial(directory_path, error_message),
        required=True)

    error_message = 'The given path is not a valid dispatch script.'
    parser.add_argument(
        '--dispatch', help='The dispatch script for filling in the templates.',
        default='dispatch.py', type=partial(dispatch_file, error_message),
        required=True)

    error_message = ('A given dispatch-opt was not a colon '
                     'separated key value pair.')
    parser.add_argument(
        '--dispatch-opt', dest='dispatch_opts',
        help=('KEY:VALUE pairs to be passed into the dispatch method. '
              'Can be used more than once.'),
        action='append', default=[])

    return parser.parse_args()


def dprint(msg):
    """Conditionally print a debug message."""
    if DEBUG:
        print(msg)


def vprint(msg):
    """Conditionally print a verbose message."""
    if VERBOSE:
        print(msg)


class DebugAction(argparse.Action):
    """Enable the debugging output mechanism."""

    sflag = '-d'
    flag = '--debug'
    help = 'Enable debugging output.'

    @classmethod
    def add_parser_argument(cls, parser):
        """Add an argument to the given parser for this Action object."""
        parser.add_argument(cls.sflag, cls.flag, help=cls.help, action=cls)

    def __init__(self, option_strings, dest, **kwargs):
        """Initialize this Action object."""
        super(DebugAction, self).__init__(option_strings, dest, nargs=0,
                                          default=False, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        """Perform the Action when called from the ArgumentParser."""
        global DEBUG
        DEBUG = True
        setattr(namespace, self.dest, True)


class VerboseAction(DebugAction):
    """Enable the verbose output mechanism."""

    sflag = '-v'
    flag = '--verbose'
    help = 'Enable verbose output.'

    def __call__(self, parser, namespace, values, option_string=None):
        """Perform the Action when called from the ArgumentParser."""
        global VERBOSE
        VERBOSE = True
        setattr(namespace, self.dest, True)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except SystemExit:
        sys.exit(0)
    except KeyboardInterrupt:
        print('...interrupted by user, exiting.')
        sys.exit(1)
    except Exception as exc:
        import traceback
        traceback.print_exc()
        sys.exit(1)


DESIGN_NOTES = """
Design Notes
============

CLI Signature::

    ~> skabelon.py
                   --dispatch DISPATCH_SCRIPT
                   --dispatch-opt OPT_KEY:OPT_VAL
                   TEMPLATE


- dispatch: DISPATCH_SCRIPT is a python module containing a method named
  "dispatch" that yields objects that are incorporated into the Jinja2
  Environment object used in the render method as well as output file names for
  the results. For each yield call by the dispatch method a corresponding
  render call is made.

-  dispatch-opt: provide key/value option pairs to be passed into the dispatch
   method.

- TEMPLATE: the template file to use.


dispatch
========

The job of the dispatch phase is to allow customization of the render call in
order to provide flexability in how the sources are used to render the template
into one or more output files.

The "--dispatch" option expects a python module, "DISPATCH_SCRIPT", that
contains a method named "dispatch". The dispatch method can take in any number
of keyword arguments as passed in through the "--dispatch-opt" CLI option.

Skabelon expects the dispatch script to yield an update to the jinja
environment and an output filename. This provides a large amount of flexability
to customize what the outputs will look like.

"""
