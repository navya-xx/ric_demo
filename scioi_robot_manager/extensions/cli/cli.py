import dataclasses
import os
import re
import shlex
import signal
import sys
import threading
import time

import utils.colors as colors
import utils.string as string

from core.utils.callbacks import Callback
from utils.logging import Logger

from prompt_toolkit import prompt, HTML
from prompt_toolkit.history import InMemoryHistory

logger = Logger('CLI')
logger.setLevel("INFO")


@dataclasses.dataclass
class CommandArgument:
    name: str
    type: type
    array_size: int = 0
    short_name: str = None
    mapped_name: str = None
    description: str = None
    default: object = None
    is_flag: bool = False


# TODO: Add custom function inside command. This is executed first and then its outputs are given to the callback?
# TODO add a way to parse lists
#

class Command:
    description: str
    name: str
    arguments: dict[str, CommandArgument]
    callback: Callback

    def __init__(self, name, callback=None, description='', arguments: list[CommandArgument] = None):
        self.name = name
        self.description = description
        self.callback = callback
        self.arguments = {}

        if arguments is not None:
            for argument in arguments:
                self.arguments[argument.name] = argument

    # ------------------------------------------------------------------------------------------------------------------
    def function(self, *args, **kwargs):
        if self.callback is not None:
            self.callback(*args, **kwargs)

    # ------------------------------------------------------------------------------------------------------------------
    def run(self, string):
        # Parse the string
        arguments = self._parseString(string)

        if arguments is None:
            return

        positional_args = arguments[0]
        keyword_args = arguments[1]

        # For now there should not be any positional arguments:
        # if len(positional_args) > 0:
        #     logger.warning(f"Cannot parse positional arguments: {positional_args}")
        #     return

        # Check if all arguments are there
        for name, argument in self.arguments.items():
            if argument.default is not None:
                if argument.name not in keyword_args.keys():
                    keyword_args[argument.name] = argument.default
            elif argument.is_flag:
                if argument.name not in keyword_args.keys():
                    keyword_args[argument.name] = False
            else:
                if argument.name not in keyword_args.keys():
                    logger.error(f"Argument \"{argument.name}\" was not provided")
                    return
        # Run the function
        try:
            self.function(*positional_args, **keyword_args)
        except Exception as e:
            logger.error(f"Error executing command: {e}")

    # ------------------------------------------------------------------------------------------------------------------
    def _parseString(self, command_string):
        pattern = r'\[.*?\]|\'.*?\'|".*?"|\S+'
        tokens = re.findall(pattern, command_string)
        positional_args = []
        keyword_args = {}
        it = iter(tokens)

        for token in it:
            if token.startswith('--'):
                arg_name = token[2:]
                if arg_name not in self.arguments:
                    logger.error(f"Unknown argument: {arg_name}")
                    return None
                arg = self.arguments[arg_name]
                if arg.is_flag:
                    keyword_args[arg_name] = True
                else:
                    try:
                        value = next(it)
                        if arg.array_size > 0:
                            match = re.match(r'\[(.*)\]', value)
                            if not match:
                                logger.error(f"Argument {arg_name} expects a list enclosed in brackets.")
                                return None
                            values = [v.strip() for v in match.group(1).split(',')]
                            if len(values) != arg.array_size:
                                logger.error(f"Argument {arg_name} expects a list of {arg.array_size} values.")
                                return None
                            keyword_args[arg_name] = self._typecastArgument(self.arguments[arg_name], values)
                        else:
                            value = value.strip('"').strip("'")
                            keyword_args[arg_name] = self._typecastArgument(self.arguments[arg_name], value)
                    except StopIteration:
                        logger.error(f"Argument {arg_name} expects a value.")
                        return None
                    except Exception as e:
                        logger.error(f"Error parsing argument {arg_name}: {e}")
                        return None
            elif token.startswith('-'):
                arg_short_name = token[1:]
                arg = next((a for a in self.arguments.values() if a.short_name == arg_short_name), None)
                if not arg:
                    logger.error(f"Unknown argument: {arg_short_name}")
                    return None
                if arg.is_flag:
                    keyword_args[arg.name] = True
                else:
                    try:
                        value = next(it)
                        if arg.array_size > 0:
                            match = re.match(r'\[(.*)\]', value)
                            if not match:
                                logger.error(f"Argument {arg.name} expects a list enclosed in brackets.")
                                return None
                            values = [v.strip() for v in match.group(1).split(',')]
                            if len(values) != arg.array_size:
                                logger.error(f"Argument {arg.name} expects a list of {arg.array_size} values.")
                                return None
                            keyword_args[arg.name] = self._typecastArgument(self.arguments[arg.name], values)
                        else:
                            value = value.strip('"').strip("'")
                            keyword_args[arg.name] = self._typecastArgument(self.arguments[arg.name], value)
                    except StopIteration:
                        logger.error(f"Argument {arg.name} expects a value.")
                        return None
                    except Exception as e:
                        logger.error(f"Error parsing value \"{value}\" for argument \"{arg.name}\" of type {arg.type}")
                        return None
            else:
                positional_args.append(token.strip('"').strip("'"))

        return positional_args, keyword_args

    # ------------------------------------------------------------------------------------------------------------------
    def _typecastArgument(self, argument, value):
        try:
            if isinstance(value, list):
                return [argument.type(v) for v in value]
            return argument.type(value)
        except ValueError:
            # logger.error(f"Cannot convert value \"{value}\" for argument {argument.name} to {argument.type}")
            raise ValueError

    # ------------------------------------------------------------------------------------------------------------------

    def help(self):
        help_string = (f"{string.bold_text}Command:{string.text_reset} "
                       f"{string.escapeCode(text_color_rgb=colors.MEDIUM_CYAN)}"
                       f"{self.name}{string.text_reset}\n")

        help_string += f"{string.bold_text}Description:{string.text_reset} {self.description}\n"
        help_string += f"{string.bold_text}Arguments:{string.text_reset}"
        if len(self.arguments) > 0:
            help_string += f"\n"
            for argument in self.arguments.values():
                help_string += f"{string.escapeCode(text_color_rgb=colors.DARK_CYAN)}  --{argument.name}{string.text_reset}"
                if argument.short_name is not None:
                    help_string += f" (-{argument.short_name})"
                if argument.description:
                    help_string += f": {argument.description}"
                if argument.default is not None:
                    help_string += f" (Optional, default: {argument.default})"
                help_string += "\n"
        else:
            help_string += f" -\n"

        return help_string


class CommandSet:
    commands: dict[str, Command]

    def __init__(self, name):
        self.commands = {}
        self.name = name
        self.parent_set = None
        self.child_sets = {}

        self.addCommand(Command(name='help',
                                description='Prints all available commands',
                                arguments=[CommandArgument(
                                    name='detail',
                                    type=bool,
                                    short_name='d',
                                    is_flag=True,
                                    default=False
                                )],
                                callback=self.help))

    # ------------------------------------------------------------------------------------------------------------------
    def addCommand(self, command: Command):
        if isinstance(command, dict):
            for key, value in command.items():
                self.commands[value.name] = value
        elif isinstance(command, Command):
            self.commands[command.name] = command

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def commandSetPath(self):
        if self.parent_set is None:
            return self.name
        else:
            return f"{self.parent_set.commandSetPath}/{self.name}"

    # ------------------------------------------------------------------------------------------------------------------
    def run(self, command_string):
        # Parse the command string
        command, args, params, remaining_string = self._parse(command_string)
        logger.debug(f"Command: {command}, Positional arguments: {args}, Keyword arguments: {params}")

        # Process the command
        ret = self.processCommand(command, args, params, remaining_string)

        return ret

    # ------------------------------------------------------------------------------------------------------------------
    def processCommand(self, command, args, params, command_string):

        # Check if the user wants to exit the command set
        if command == 'exit' and len(args) == 0 and len(params) == 0:
            if self.parent_set is not None:
                return self.parent_set
        elif command == 'EXIT' and len(args) == 0 and len(params) == 0:
            if self.parent_set is not None:
                ret = self.parent_set.run("EXIT")
                return ret
            else:
                return self

        elif command in self.child_sets.keys():
            if len(args) == 0:
                return self.child_sets[command]
            else:
                ret = self.child_sets[command].run(command_string)
                return ret

        elif command in self.commands.keys():
            self.commands[command].run(command_string)
        else:
            logger.warning(f"Command {command} not found")

        return None

    # ------------------------------------------------------------------------------------------------------------------
    # def process_command(self, command, args, params):
    #     self.commands[command].execute(*args, **params)

    # def parseCommand(self, command_string):
    #     command, args, params = parse_command(command_string)
    #     ret = self.handle_command(command, args, params)
    #     return ret
    # ------------------------------------------------------------------------------------------------------------------
    # def handle_command(self, command, args, params):
    #     if command == 'exit' and len(args) == 0 and len(params) == 0:
    #         if self.parent_set is not None:
    #             return self.parent_set
    #         print("EXIT")
    #
    #     elif command in self.commands.keys():
    #         self.process_command(command, args, params)
    #
    #     elif command in self.child_sets.keys():
    #         if len(args) == 0:
    #             return self.child_sets[command]
    #         else:
    #             self.child_sets[command].handle_command(command=args[0], args=args[1:], params=params)
    #     else:
    #         logger.warning(f"Command {command} not found")

    # ------------------------------------------------------------------------------------------------------------------
    def printCommand(self, command, args, params):
        print(f'{self.name.capitalize()} - Command: {command}')
        print(f'Arguments: {args}')
        print('Parameters:')
        for key, value in params.items():
            print(f'  {key}: {value}')

    # ------------------------------------------------------------------------------------------------------------------
    def addChild(self, child_cli):
        self.child_sets[child_cli.name] = child_cli
        child_cli.parent_set = self

    # ------------------------------------------------------------------------------------------------------------------
    def removeChild(self, child_cli):
        self.child_sets.pop(child_cli.name)

    # ------------------------------------------------------------------------------------------------------------------
    def help(self, *args, detail=False, **kwargs):
        # Check if we only want to print the help to a specific command or for the whole set
        if len(args) == 1:
            command = args[0]
            if command in self.commands.keys():
                print("-----------------------------------------")
                print(self.commands[command].help())
                print("-----------------------------------------")
            elif command in self.child_sets.keys():
                print("-----------------------------------------")
                print(self.child_sets[command].shortHelp())
                print("-----------------------------------------")
            else:
                logger.warning(f"Command {command} not found")

        elif len(args) == 0:
            print(
                f"Help for command set {string.escapeCode(text_color_rgb=colors.MEDIUM_MAGENTA, bold=True)}{self.commandSetPath}{string.text_reset}\nuse \"help --detail\" for more details")
            print("-----------------------------------------")
            # Print subsets:
            command_sets_overview_string = f"{string.escapeCode(colors.MEDIUM_MAGENTA, bold=True)}Command Sets: {string.text_reset}"
            if len(self.child_sets.keys()) > 0:
                for subset in self.child_sets.values():
                    command_sets_overview_string += f"{string.escapeCode(colors.MEDIUM_MAGENTA)}{subset.name}{string.text_reset}  "
            else:
                command_sets_overview_string += "-"
            print(command_sets_overview_string)

            if detail:
                print("-----------------------------------------")
                print(f"Enter command set name to enter. "
                      f"Type \"exit\" to exit to parent set, type \"EXIT\" to jump to root set.")
                print("-----------------------------------------")
                for child in self.child_sets.values():
                    print(child.shortHelp())

            # Print commands
            print("-----------------------------------------")
            commands_overview_string = f"{string.escapeCode(colors.MEDIUM_CYAN, bold=True)}Commands: {string.text_reset}"
            if len(self.commands) > 1:
                for command in self.commands.values():
                    commands_overview_string += f"{string.escapeCode(colors.MEDIUM_CYAN)}{command.name}{string.text_reset} "
            else:
                commands_overview_string += "-"

            print(commands_overview_string)
            print("-----------------------------------------")
            if detail:

                print(f"Enter command and add keyword aguments by --name (-shortname). Arrays are denoted by [].")
                print("-----------------------------------------")
                if len(self.commands) > 1:
                    for command in self.commands.values():
                        if command.name != "help":
                            print(command.help())
                            print("-----------------------------------------")

    # ------------------------------------------------------------------------------------------------------------------
    def shortHelp(self):
        helpstring = ''
        helpstring += f"{string.bold_text}Command Set: {string.text_reset}{string.escapeCode(colors.MEDIUM_MAGENTA)}{self.name}{string.text_reset}\n"
        helpstring += f"{string.bold_text}Description: {string.text_reset} \n"
        helpstring += f"{string.bold_text}Commands:{string.text_reset}  "
        for subset in self.child_sets.values():
            helpstring += f"{string.escapeCode(colors.MEDIUM_MAGENTA)}{subset.name}{string.text_reset}   "
        for command in self.commands.values():
            helpstring += f"{string.escapeCode(colors.MEDIUM_CYAN)}{command.name}{string.text_reset}   "
        return helpstring

    # ------------------------------------------------------------------------------------------------------------------
    def _parse(self, command_string):
        # Use shlex.split to correctly handle quoted strings
        tokens = shlex.split(command_string)

        # The first token is the command
        command = tokens[0]

        # Initialize an empty dictionary to hold parameters
        params = {}
        # Initialize a list to hold positional arguments
        args = []

        # Iterate over the tokens to find parameters and their values
        i = 1
        while i < len(tokens):
            if tokens[i].startswith('-'):
                if tokens[i].startswith('--'):
                    # The current token is a long option
                    key = tokens[i][2:]  # Strip the leading "--"
                else:
                    # The current token is a short option
                    key = tokens[i][1:]  # Strip the leading "-"

                if i + 1 < len(tokens) and not tokens[i + 1].startswith('-'):
                    # The next token is the parameter value
                    value = tokens[i + 1]
                    i += 1  # Skip the value token in the next iteration
                else:
                    # No value provided for the parameter
                    value = None
                params[key] = value
            else:
                # If the token does not start with "-", it is a positional argument
                args.append(tokens[i])
            i += 1

        # Reconstruct the command string without the first command
        remaining_command_string = ' '.join(tokens[1:])

        return command, args, params, remaining_command_string


class CLI:
    active_set: CommandSet

    def __init__(self):

        self.active_set = None
        self.thread = None
        self.running = False
        self.history = InMemoryHistory()

    def start(self, commandSet):
        self.active_set = commandSet
        self.running = True
        self.thread = threading.Thread(target=self.listen_for_commands)
        self.thread.start()

    def clear_terminal(self):
        # Check the operating system and execute the appropriate command
        if os.name == 'nt':  # For Windows
            os.system('cls')
        else:  # For MacOS and Linux
            os.system('clear')

    def listen_for_commands(self):
        while self.running:
            try:
                # prompt = f"\033[1;36mCommand ({self.active_set.commandSetPath})\033[0m: "
                if os.isatty(sys.stdin.fileno()):
                    prompt_message = HTML('<ansicyan>Command ({})</ansicyan>: '.format(self.active_set.commandSetPath))
                    user_input = prompt(prompt_message, history=self.history)
                else:
                    prompt_message = f"\033[1;36mCommand ({self.active_set.commandSetPath})\033[0m: "
                    user_input = input(prompt_message)
                if user_input == '':
                    continue
                if user_input == 'clear':
                    self.clear_terminal()
                    continue
                try:
                    ret = self.active_set.run(user_input)
                    if isinstance(ret, CommandSet):
                        self.active_set = ret
                except Exception as e:
                    logger.error(f"Error while executing command")

                time.sleep(0.1)
            except KeyboardInterrupt:
                self.stop()

    def stop(self):
        self.running = False
