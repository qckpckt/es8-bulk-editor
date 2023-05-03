from dataclasses import asdict
from functools import wraps, partial
import json
from pathlib import Path
from sqlite3 import IntegrityError
import time
from typing import Dict

from tinydb import Query
import typer
from rich import print, pretty
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, BarColumn, TaskProgressColumn, TextColumn

# from asciimatics.screen import Screen
# from asciimatics.exceptions import R esizeScreenError


# from .screens import editor
from . import data_models as dm
from . import database as db
from . import mappings
from .context import DotDict

app = typer.Typer()
console = Console()


class ProfileError(IntegrityError):
    def __init__(self, message: str, payload: Dict[str, str], ctx: typer.Context):
        super().__init__(message)
        self.payload = payload
        self.ctx = ctx


def handle_profile_error(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ProfileError as e:
            if e.payload["name"] == "default":
                print(
                    ":prohibited:Changing the default profile values is prohibited "
                    "outside of the patch backup location. To do this run "
                    "[bold cyan1]`es8 init --update`[/]"
                )
            modify = Confirm.ask(
                ":woozy_face: Oops. A profile already exists with name "
                f"{e.payload['name']}. Do you want to modify this entry?"
            )
            if modify:
                profile_id = e.ctx.obj.metadata.get_metadata_by_name(e.payload["name"])[
                    "id"
                ]
                e.ctx.metadata.update(profile_id, e.payload)

    return wrapper


def get_model(backup_filepath: str) -> dm.PatchList:
    with open(backup_filepath, "r") as infile:
        backup = json.load(infile)
    return dm.PatchList(backup["patch"])


def default_local_storage() -> str:
    home_dir = Path.home()
    local_storage = home_dir / ".es8"
    local_storage.mkdir(parents=True, exist_ok=True)
    return str(local_storage)


def default_patch_filepath() -> str:
    script_path = Path(__file__).resolve()
    app_dir = script_path.parent
    return str(app_dir / "templates" / "global_defaults.json")


def start_editor(screen: str, ctx: typer.Context):
    """Start editor in screen `screen`. Pass context object to screen."""
    pass


@app.command()
def init(
    ctx: typer.Context,
    update: bool = typer.Option(False, help="update the global patch backup filepath"),
):
    """Initialize ES8 editor with the default profile."""

    payload = {
        "type": "metadata",
        "name": "default",
        "default_patch_filepath": default_patch_filepath(),
        "patch_backup_filepath": None,
        "is_ingested": False,
    }

    conf_table = ctx.obj.db.table("conf")
    patch_table = ctx.obj.db.table("patch")
    conf = ctx.obj.orm

    db_method = conf_table.insert

    if metadata := conf_table.get(conf.type == "metadata"):
        if not update:
            print(
                "\n\n[bold]Editor already intialized with default profile:[/]\n\n",
            )
            print(str(pretty.pretty_repr(metadata)))
            print(
                "\n\nTo update the patch backup filepath, pass the "
                "[bold cyan1]--update[/] option.\n\n"
            )
            raise typer.Exit()

        else:
            if metadata["is_ingested"]:
                proceed = Confirm.ask(
                    "[bold red]Supplying a new backup path means the patch table will "
                    "be nuked. Proceed?[/]"
                )
                if not proceed:
                    raise typer.Exit()
                print(":bomb: [bold orange]Erasing patch table![/] :bomb:")
                ctx.obj.db.drop_table("patch")
            db_method = partial(conf_table.update, doc_ids=[metadata.doc_id])

    print(
        "\n\n[bold cyan1]:control_knobs:  Welcome to the BOSS ES-8 bulk editor! "
        ":control_knobs:[/]\n\n"
    )

    while True:
        backup_filepath = Prompt.ask("Please specify the path to your backup file")
        path = Path(backup_filepath)
        if path.is_file():
            payload["patch_backup_filepath"] = backup_filepath
            break
        print("[prompt.invalid]File not found. Check for typos?")

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        expand=True,
        transient=True,
    ) as progress:
        add_default = progress.add_task("[red]Creating Default Entry...[/]", total=15)

        db_method(payload)

        for i in range(15):
            if i == 14:
                progress.update(
                    add_default,
                    advance=1,
                    description="[red]Creating Default Entry...[/][green] Done![/]",
                )
            progress.update(add_default, advance=1)
            time.sleep(0.05)

        load_patches = progress.add_task(
            "[blue]Loading patches from default file...", total=800
        )
        ctx.obj.patch_list = get_model(payload["patch_backup_filepath"])

        for i, p in enumerate(ctx.obj.patch_list.patches):
            bank, patch = mappings.index_to_patch(i)
            p_id = patch_table.insert(asdict(p))
            progress.update(
                load_patches,
                advance=1,
                description=(
                    f"[blue]inserted [bold green_yellow]{bank}[/]:"
                    f"[spring_green1]{patch}[/] - "
                    f"[light_cyan1]'{p.patch_name}[/]' "
                    f"with id [sping_green1 bold]{p_id}...[/]"
                ),
            )

        metadata_doc_id = conf_table.get(conf.type == "metadata").doc_id
        conf_table.update({"is_ingested": True}, doc_ids=[metadata_doc_id])

    print(
        "\n\n:sparkles: [bold]Default profile set with patch backup path "
        f"[green]{backup_filepath}[/] :sparkles:\n\n"
    )

    if Confirm.ask("Configure ES-8 preferences?"):
        start_editor("prefs", ctx)


@app.command()
def add_template(
    ctx: typer.Context,
    name: str = typer.Option("", help="Name of new profile"),
    default_patch_location: str = typer.Option(
        "", help="Location of patch in the form bank:patch, eg 0:1"
    ),
    default_patch_filepath: str = typer.Option(
        "",
        help=(
            "filepath of json file representing default patch, "
            "as generated by the patch editor."
        ),
    ),
    targets: str = typer.Option("", help="Patches that this default applies to."),
    is_global: bool = typer.Option("", help="Use this flag for global default patch"),
):
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
    metadata = ctx.obj.metadata
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
    path = default_local_storage()

    ctx.obj = DotDict()
    ctx.obj.db = db.init_db(path)
    ctx.obj.orm = Query()


if __name__ == "__main__":
    app()
