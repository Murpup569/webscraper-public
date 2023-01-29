"""Imports/Loads data from files"""
import json
import os
import sys


def file_check(file_name):
    """Verifies that file exists. (input: filename)"""

    exists1 = os.path.isfile(file_name)
    if not exists1:
        print(f"{file_name} not found")
        sys.exit()


def env_check(env_var):
    """Check if environment variable was found"""
    if env_var is None:
        print("Error: Environment variables not set correctly")
        sys.exit()


def load_json(file_name):
    """Loads a json file. (input: filename)"""

    with open(file_name, "r", encoding="UTF-8") as file_handler:
        output = json.load(file_handler)
    return output

