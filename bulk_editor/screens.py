from dataclasses import asdict
from typing import Union, Dict, Any

from asciimatics.widgets import (
    Frame,
    Layout,
    Text,
    Button,
    Label,
    ListBox,
    Divider,
    Widget,
)
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import StopApplication, NextScene
from tinydb.table import Document
from typer import Context

from . import data_models as models


def _filter_data(data: Dict[str, Any], screen: str) -> Dict[str, Any]:
    """For a given data dict and screen:
        - find the associated data model
        - filter the data dict to remove keys not in the model
        - return the union of both dicts (to include any default fields from the model)
    """
    model = asdict(models.MODEL_MAP[screen]())
    filtered = {k: v for k, v in data.items() if k in model}
    return model | filtered


class UserPrefs(Frame):
    def __init__(self, screen: Screen, ctx):
        super().__init__(
            screen,
            screen.height,
            screen.width,
            can_scroll=False,
            title="Edit User Preferences",
            reduce_cpu=True,
        )
        self._list_options = {"_loop_prefs": 0, "_midi_prefs": 1}
        self._list_view = ListBox(
            Widget.FILL_FRAME,
            list(self._list_options.items()),
            name="preference_options",
            add_scroll_bar=True,
            on_change=self._on_pick,
            on_select=self._edit,
        )
        self.table = ctx.obj.db.table("user_prefs")
        self.prefs = ctx.obj.orm
        self.set_theme("bright")
        self._edit_button = Button("Edit", self._edit)
        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        layout.add_widget(self._list_view)
        layout.add_widget(Divider())
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(self._edit_button, 2)
        layout2.add_widget(Button("Done", self._done), 3)
        self.fix()
        self._on_pick()

    def _on_pick(self):
        self._edit_button.disabled = self._list_view.value is None

    def _edit(self):
        self.save()
        selected = {v: k for k, v in self._list_options.items()}[
            self.data["preference_options"]
        ]
        preference_option = getattr(self, selected)
        preference_option()


    @staticmethod
    def _loop_prefs():
        raise NextScene("loop_prefs")

    @staticmethod
    def _midi_prefs():
        raise NextScene("loop_prefs")

    @staticmethod
    def _done():
        raise StopApplication("User pressed quit")


class LoopPrefs(Frame):
    def __init__(self, screen: Screen, ctx):
        super().__init__(
            screen,
            screen.height,
            screen.width,
            can_scroll=False,
            title="Edit Loop Preferences",
            reduce_cpu=True,
        )
        self._table = ctx.obj.db.table("user_prefs")
        self._prefs = ctx.obj.orm
        self._curr_state = self._table.get(self._prefs.type == "loop_prefs")
        if self._curr_state is not None:
            self._doc_id = self._curr_state.doc_id
            self.data = self._curr_state

        fields = {
            "Loop 1": "loop_1",
            "Loop 2": "loop_2",
            "Loop 3": "loop_3",
            "Loop 4": "loop_4",
            "Loop 5": "loop_5",
            "Loop 6": "loop_6",
            "Loop 7": "loop_7",
            "Loop 8": "loop_8",
            "Volume Loop": "loop_v",
        }

        self.set_theme("bright")
        layout = Layout([1, 1], fill_frame=True)
        self.add_layout(layout)

        layout.add_widget(Label("Name your loops"), 0)
        help = Label("Press tab to navigate.", name="help")
        help.custom_colour = "disabled"
        layout.add_widget(help, 0)
        for label, name in fields.items():
            setattr(self, name, Text(label, name))
            layout.add_widget(getattr(self, name), 0)

        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("OK", self._ok), 0)
        layout2.add_widget(Button("Cancel", self._cancel), 3)
        self.fix()

    def reset(self):
        # Do standard reset to clear out form, then populate with new data.
        super().reset()
        last_state = self._table.get(self._prefs.type == "loop_prefs")
        self.data = last_state if last_state is not None else {}

        for key in self.data:
            if hasattr(self, key):
                getattr(self, key).value = self.data[key]

    def _ok(self):
        self.save()
        payload = _filter_data(self.data, "loop_prefs")
        if hasattr(self, "_doc_id"):
            self._table.upsert(Document(payload, doc_id=self._doc_id))
        else:
            self._table.upsert(payload, self._prefs.type == "loop_prefs")
        raise NextScene("user_prefs")

    @staticmethod
    def _cancel():
        raise NextScene("user_prefs")


def editor(
    screen,
    scene: Scene,
    ctx: Context,
    start_scene: Union[str, None],
):
    scenes = {
        "user_prefs": Scene([UserPrefs(screen, ctx)], -1, name="user_prefs"),
        "loop_prefs": Scene([LoopPrefs(screen, ctx)], -1, name="loop_prefs"),
    }
    if start_scene is not None:
        scene = scenes[start_scene]
    screen.play(
        list(scenes.values()), stop_on_resize=True, start_scene=scene, allow_int=True
    )
