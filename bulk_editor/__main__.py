import argparse
from dataclasses import asdict
import json

from .data_models import PatchList
from .loggers import init_logging
from . import mappings, actions

init_logging(log_file="bulk_editor.log")

BACKUP_FILE = "test_1.bel"
OUTPUT_FILE = "test_output.bel"
DEFAULTS_FILE = "global_defaults.json"

parser = argparse.ArgumentParser()

parser.add_argument("action", type=str, choices=actions.VALID_ACTIONS.keys())

parser.add_argument(
    "-a",
    "--assign_number",
    type=int,
    choices=range(1, 13),
)
parser.add_argument(
    "-s", "--source", type=str, choices=mappings.PATCH_ASSIGN_SOURCE_ORDER
)
parser.add_argument(
    "-m", "--mode", type=str, choices=mappings.PATCH_ASSIGN_MODE_ORDER, default="TGL"
)
parser.add_argument(
    "-t", "--target", type=str, choices=mappings.PATCH_ASSIGN_TARGET_ORDER
)
parser.add_argument("-p", "--params", type=str, default="noop")
parser.add_argument("-c", "--coords", type=str)
parser.add_argument("-f", "--force", action="store_true", default=False)

args = parser.parse_args()

if args.params != "noop":
    with open(args.params, "r") as paramfile:
        args.params = json.load(paramfile)
else:
    args.params = {}

with open(BACKUP_FILE, "r") as infile:
    backup_file = json.load(infile)

patch_list = PatchList(patches=backup_file["patch"])

updated_patches, new_global_defaults = actions.VALID_ACTIONS[args.action](
    patch_list, args
)

backup_file["patch"] = [asdict(patch) for patch in updated_patches]

with open(OUTPUT_FILE, "w") as outfile, open(DEFAULTS_FILE, "w") as defaultsfile:
    json.dump(backup_file, outfile)
    # TODO - probably want to save the new defaults file as a new file rather than overwriting.
    json.dump(asdict(new_global_defaults), defaultsfile)
