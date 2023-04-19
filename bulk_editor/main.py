import json
from pathlib import Path
from sqlite3 import IntegrityError

import typer
from rich import print
from rich.prompt import Prompt, Confirm

# from asciimatics.screen import Screen
# from asciimatics.exceptions import ResizeScreenError


# from .screens import editor
from . import data_models as dm
from . import database as db

app = typer.Typer()


def get_model(backup_filepath: str):
    with open(backup_filepath, "r") as infile:
        backup = json.load(infile)
    return dm.PatchList(**backup["patch"])


@app.command()
def init(ctx: typer.Context):
    print(
        "[bold cyan1]:control_knobs:  Welcome to the BOSS ES-8 bulk editor! "
        ":control_knobs:[/]"
    )
    new_profile = {}
    script_path = Path(__file__).resolve()
    app_dir = script_path.parent
    default_patch_file = app_dir / "defaults" / "global_defaults.json"

    new_profile["name"] = Prompt.ask("Name your profile", default="default")
    while True:
        backup_filepath = Prompt.ask("Please specify the path to your backup file")
        path = Path(backup_filepath)
        if path.is_file():
            new_profile["patch_backup_filepath"] = backup_filepath
            break
        print("[prompt.invalid]File not found. Check for typos?")
    while True:
        defaults_filepath = Prompt.ask(
            "Provide the path to your default patch (if you have one)",
            default=str(default_patch_file),
        )
        path = Path(defaults_filepath)
        if path.is_file():
            new_profile["default_patch_filepath"] = defaults_filepath
            break
        print("[prompt.invalid]File not found. Check for typos?")
    metadata = ctx.obj
    try:
        profile_id = metadata.add(new_profile)
    except IntegrityError:
        replace = Confirm.ask(
            ":woozy_face: Oops. A profile already exists with name "
            f"{new_profile['name']}. Do you want to replace it?"
        )
        profile_id = metadata.get_metadata_by_name(new_profile["name"])["id"]
        if replace:
            metadata.update(profile_id, new_profile)
    print(f"profile id: {profile_id}")


# @app.command()
# def global_assign():
#     scene = None
#     start_scene = "assign"
#     context = "assign"
#     while True:
#         try:
#             Screen.wrapper(
#                 editor, catch_interrupt=True, arguments=[scene, context, start_scene]
#             )
#             break
#         except ResizeScreenError:
#             pass


# @app.command()
# def start_editor():
#     scene = None
#     start_scene = None
#     context = "assign"
#     while True:
#         try:
#             Screen.wrapper(
#                 editor, catch_interrupt=True, arguments=[scene, context, start_scene]
#             )
#             break
#         except ResizeScreenError:
#             pass


@app.callback()
def main(ctx: typer.Context):
    ctx.obj = db.Metadata()


if __name__ == "__main__":
    app()
