# This file is part of classifier
#
#    classifier is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    classifier is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with classifier.  If not, see <http://www.gnu.org/licenses/>.
"""
Tools for microbial sequence analysis and classification.

Assembles subcommands and provides top-level script.
"""

import argparse
import importlib
import logging
import os
import pkg_resources
import pkgutil
import re
import subprocess
import sys

from classifier import utils

log = logging.getLogger(__name__)

_data = os.path.join(os.path.dirname(__file__), 'data')


def main(argv=sys.argv[1:]):
    # add_help after logging is setup or parse_known_args will exit on -h
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)

    # setup main arguments
    parser = parse_args(parser)

    # get logging namespace
    namespace, argv = parser.parse_known_args(argv)

    setup_logging(namespace)

    # parse version after logging has been configured
    parse_version(parser)

    # add_help=True
    parser.add_argument('-h', '--help', action='help')

    # setup actions and actions' arguments
    from classifier import subcommands
    parser, actions = parse_subcommands(parser, subcommands, argv)

    # finish building namespace
    namespace = parser.parse_args(args=argv, namespace=namespace)

    # Determine which subcommand (action) is in play
    action = namespace.subparser_name

    # execute subcommand (action)
    if action == 'help':
        # convert help <action> to <action> -h and loop back
        return main([str(namespace.action[0]), '-h'])
    else:
        # global action, see subcommands/__init__.py
        namespace = subcommands.action(namespace)
        return actions[action](namespace)


def setup_logging(namespace):
    """
    setup global logging
    """

    loglevel = {
        0: logging.ERROR,
        1: logging.WARNING,
        2: logging.INFO,
        3: logging.DEBUG,
    }.get(namespace.verbosity, logging.DEBUG)

    if namespace.verbosity > 1:
        logformat = '%(levelname)s classifier %(lineno)s %(message)s'
    else:
        logformat = 'classifier %(message)s'

    logging.basicConfig(stream=namespace.log, format=logformat, level=loglevel)


def parse_version(parser):
    parser.add_argument('-V', '--version',
                        action='version',
                        version=version(),
                        help='Print the version number and exit')


def parse_args(parser):
    parser.add_argument('-l', '--log',
                        metavar='FILE',
                        default=sys.stdout,
                        type=utils.opener('a'),  # append
                        help='Send logging to a file')

    parser.add_argument('-v', '--verbose',
                        action='count',
                        dest='verbosity',
                        default=0,
                        help='Increase verbosity of screen output '
                             '(eg, -v is verbose, -vv more so)')

    parser.add_argument('-q', '--quiet',
                        action='store_const',
                        dest='verbosity',
                        const=0,
                        help='Suppress output')

    return parser


def parse_subcommands(parser, subcommands, argv):
    """
    Setup all sub-commands
    """

    subparsers = parser.add_subparsers(dest='subparser_name')

    # add help sub-command
    parser_help = subparsers.add_parser(
        'help', help='Detailed help for actions using `help <action>`')
    parser_help.add_argument('action', nargs=1)

    # add all other subcommands
    modules = [
        name for _, name, _ in pkgutil.iter_modules(subcommands.__path__)]
    commands = [m for m in modules if m in argv]

    actions = {}

    # `commands` will contain the module corresponding to a single
    # subcommand if provided; otherwise, generate top-level help
    # message from all submodules in `modules`.
    for name in commands or modules:
        # set up subcommand help text. The first line of the dosctring
        # in the module is displayed as the help text in the
        # script-level help message (`script -h`). The entire
        # docstring is displayed in the help message for the
        # individual subcommand ((`script action -h`))
        # if no individual subcommand is specified (run_action[False]),
        # a full list of docstrings is displayed
        try:
            imp = '{}.{}'.format(subcommands.__name__, name)
            mod = importlib.import_module(imp)
        except Exception as e:
            log.error(e)
            continue

        subparser = subparsers.add_parser(
            name,
            help=mod.__doc__.lstrip().split('\n', 1)[0],
            description=mod.__doc__,
            formatter_class=argparse.RawDescriptionHelpFormatter)

        mod.build_parser(subparser)

        # see global subcommands/__init__.py
        subcommands.build_parser(subparser)

        actions[name] = mod.action

    return parser, actions


def version():
    """
    Depending on if git exists and at what version we can try these commands
    to get the git version from the git tags.  Second, if the package has been
    installed return the installed version.  Finally, if nothing else,
    return 0.0.0
    """

    version = None

    install_dir = os.path.dirname(__file__)
    git_cmds = (['git', '-C', install_dir, 'describe', '--tags'],  # >= 1.8.5
                ['git', 'describe', '--tags'])  # < 1.8.5
    devnull = open(os.devnull, 'w')

    """
    try the two git commands above ^
    git versions are organized as
    [tag]-[number of commits over tag]-[commit id]
    ex - v0.1.2-38-g6a8e5e3
    """
    for cmd in git_cmds:
        logging.debug(' '.join(cmd))
        git_re = 'v(?P<tag>[\d.]*)-?(?P<commit>[\d.]*)-?.*'
        try:
            git_ver = subprocess.check_output(cmd, stderr=devnull)
            git_search = re.search(git_re, git_ver)
            if git_search.group('commit') == '':
                version = git_search.group('tag')
            else:
                version = '{tag}.dev{commit}'.format(**git_search.groupdict())
            break
        except Exception as e:
            log.debug(e)

    if version is None:
        try:
            """
            return version that was installed if available
            """
            version = pkg_resources.require("classifier")[0].version
        except pkg_resources.DistributionNotFound as e:
            logging.warn(e)

    return version or '0.0.0'
