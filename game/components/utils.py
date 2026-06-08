import os
import importlib
import random as r

FACES = list(range(1,7))

def import_player_classes_from_dir(directory):
    player_objects = []

    # List all .py files in the directory
    for filename in os.listdir(directory):
        if filename.endswith(".py"):
            module_name = filename[:-3]  # Remove .py extension
            module_path = os.path.join(directory, filename)

            # Dynamically import the module
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Instantiate the Player class from the module (if it exists)
            if hasattr(module, 'Player'):
                player_class = getattr(module, 'Player')
                player_instance = player_class()  # Assuming no arguments in the constructor
                player_objects.append(player_instance)

    return player_objects


def roll_dice(hands: list):
    for h in hands:
        h['hand'] = r.choices(FACES, k=h['n_dice'])
    return hands