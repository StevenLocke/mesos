# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This is the main executable of the mesos-cli.
"""

import sys

import config
import mesos

from mesos.docopt import docopt
from mesos.exceptions import CLIException


VERSION = "Mesos " + config.VERSION + " CLI"

SHORT_HELP = "Perform operations on a running mesos cluster."

USAGE = \
"""Mesos CLI

Usage:
  mesos (-h | --help)
  mesos --version
  mesos <command> [<args>...]

Options:
  -h --help  Show this screen.
  --version  Show version info.

Commands:
{commands}
See 'mesos help <command>' for more information on a specific command.
"""


def autocomplete(cmds, plugins, current_word, argv):
    """
    Perform autocomplete for the given input arguments. If not
    completing a top level command (or "help"), this function passes
    the arguments down to the appropriate plugins for per-plugin
    autocompletion.
    """

    option = "default"

    if len(argv) > 0 and argv[0] == "help":
        argv = argv[1:]

    comp_words = list(cmds.keys()) + ["help"]
    comp_words = mesos.util.completions(comp_words, current_word, argv)
    if comp_words != None:
        return (option, comp_words)

    plugin = mesos.util.get_module(plugins, argv[0])
    plugin_class = getattr(plugin, plugin.PLUGIN_CLASS)

    return plugin_class(config).__autocomplete_base__(current_word, argv[1:])


def main(argv):
    """
    This is the main function for the mesos-cli.
    """

    # Initialize the various plugins
    plugins = mesos.util.import_modules(config.PLUGINS, "plugins")

    cmds = {
        mesos.util.get_module(plugins, a).PLUGIN_NAME:
        mesos.util.get_module(plugins, a).SHORT_HELP
        for a in plugins.keys()
    }

    # Parse all incoming arguments using docopt.
    command_strings = ""
    if cmds != {}:
        command_strings = mesos.util.format_commands_help(cmds)
    usage = USAGE.format(commands=command_strings)

    arguments = docopt(usage, argv=argv, version=VERSION, options_first=True)

    cmd = arguments["<command>"]
    argv = arguments["<args>"]

    # Use the meta-command `__autocomplete__` to perform
    # autocompletion on the remaining arguments.
    if cmd == "__autocomplete__":
        current_word = argv[0]
        argv = argv[1:]

        option = "default"
        comp_words = []

        # If there is an error performing the autocomplete, treat it
        # as if we were just unable to complete any words. This avoids
        # passing the erroring stack trace back as the list of words
        # to complete on.
        try:
            option, comp_words = autocomplete(cmds, plugins, current_word, argv)
        except Exception:
            pass

        print option
        print " ".join(comp_words)

    # Use the meta-command "help" to print help information for the
    # supplied command and its subcommands.
    elif cmd == "help":
        if len(argv) > 0 and argv[0] in cmds:
            plugin = mesos.util.get_module(plugins, argv[0])
            plugin_class = getattr(plugin, plugin.PLUGIN_CLASS)
            plugin_class(config).main(argv[1:] + ["--help"])
        else:
            main(["--help"])

    # Run the command through its plugin.
    elif cmd in cmds.keys():
        plugin = mesos.util.get_module(plugins, cmd)
        plugin_class = getattr(plugin, plugin.PLUGIN_CLASS)
        plugin_class(config).main(argv)

    # Print help information if no commands match.
    else:
        main(["--help"])


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except CLIException as exception:
        sys.exit("Error: {error}.".format(error=str(exception)))
    except KeyboardInterrupt:
        pass