from dataclasses import asdict
from functools import partial
import json
from pathlib import Path
import time

from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError
from rich import print, pretty
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, BarColumn, TaskProgressColumn, TextColumn

from tinydb import Query
import typer

from . import defaults
from .screens import editor
from . import data_models as dm
from . import database as db
from . import mappings
from .context import AppContext

app = typer.Typer()
console = Console()


def get_model(backup_filepath: str) -> dm.PatchList:
    with open(backup_filepath, "r") as infile:
        backup = json.load(infile)
    return dm.PatchList(backup["patch"])


@app.command()
def init(
    ctx: typer.Context,
    update: bool = typer.Option(False, help="update the global patch backup filepath"),
):
    """Initialize ES8 editor with the default profile."""

    payload = {
        "type": "metadata",
        "name": "default",
        "default_patch_filepath": defaults.patch_filepath(),
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


@app.command()
def configure(ctx: typer.Context):
    scene = None
    start_scene = "user_prefs"
    while True:
        try:
            Screen.wrapper(
                editor, catch_interrupt=True, arguments=[scene, ctx.obj, start_scene]
            )
            break
        except ResizeScreenError:
            pass


@app.callback()
def main(ctx: typer.Context):
    path = defaults.local_storage()
    app_context = AppContext(
        user_prefs=db.Es8Table(
            db=db.init_db(path), orm=Query(), table_name="user_prefs"
        )
    )
    ctx.obj = app_context


if __name__ == "__main__":
    app()
