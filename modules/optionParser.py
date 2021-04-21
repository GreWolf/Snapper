import os
import json
from typing import Dict


def parseOptions(filepath: str) -> Dict:
    options = {}

    dirpath = os.path.join(os.path.dirname(filepath), "options")

    if os.path.exists(dirpath):
        for file in os.listdir(os.path.join(os.path.dirname(filepath), "options")):
            filename, extension = os.path.splitext(file)
            if extension == ".json":
                with open(os.path.join(os.path.dirname(filepath), "options", file), encoding="utf-8-sig") as jfile:
                    options.update({filename: json.load(jfile)})

    return options
