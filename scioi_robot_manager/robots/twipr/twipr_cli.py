from robots.twipr.twipr_manager import TWIPR_Manager
from robots.twipr.twipr import TWIPR
from extensions.cli.cli import *


# TWIPR Command Set
# General Commands:
# info --detail
# stop
# controlmode -m
# controlconfig --config
# statefeedback --gain
# input -l -r
# speed -f -t
# sensors --detail
# state --detail
# stream --values
# led --front --back --all --color
# restart


class TWIPR_CommandSet(CommandSet):
    robot: TWIPR

    def __init__(self, robot: TWIPR):
        super().__init__(name=robot.id)
        self.robot = robot


# TWIPR Manager Command Set

# stop
# info
# list --detail
# controlmode -a -m --all
# stream

#
# name: str
# type: type
# array_size: int = 0
# short_name: str = None
# mapped_name: str = None
# description: str = None
# default: object = None
# is_flag: bool = False

class TWIPR_Manager_CommandSet(CommandSet):
    name = 'manager'

    def __init__(self, manager: TWIPR_Manager):
        super().__init__(name=self.name)
        ...


class TWIPR_Manager_Command_List(Command):
    description = 'Lists all connected TWIPR ric_robots'
    name = 'list'
    manager: TWIPR_Manager
    arguments = {
        'detail': CommandArgument(
            name='detail',
            type=bool,
            short_name='d',
            description='Shows detailed information for each robot',
            is_flag=True,
            default=False
        )
    }

    # arguments: dict[str, CommandArgument]

    def __init__(self, manager: TWIPR_Manager):
        super().__init__(name=self.name, callback=None, description=self.description, arguments=None)
        self.manager = manager

    def function(self, *args, **kwargs):
        print("Listing connected TWIPR ric_robots...")
