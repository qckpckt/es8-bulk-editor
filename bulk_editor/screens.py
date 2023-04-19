from typing import Union

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


def set_assign(assign_number: int, target: str, action: str):
    print(f"Assign number: {assign_number}")
    print(f"Target: {target}")
    print(f"Action: {action}")


# class model(object):
#     """stub class representing the underlying data model"""

#     def delete(self, *args, **kwargs):
#         pass

#     def get_current_val(self, context, *args, **kwargs):
#         val_map = {"assign": {"assign_number": "", "target": "", "action": ""}}
#         return val_map.get(context, {})

#     def get_summary(self):
#         return get_summary_for_context("assign")


class EditorView(Frame):
    def __init__(self, screen, model):
        super().__init__(
            screen,
            screen.height * 2 // 3,
            screen.width * 2 // 3,
            on_load=self._reload_list,
            hover_focus=True,
            can_scroll=False,
            title="ES8 Editor",
        )
        self._model = model
        self._list_view = self._get_list_items()
        self._edit_button = Button("Edit", self._edit)
        self._delete_button = Button("Delete", self._delete)
        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        layout.add_widget(self._list_view)
        layout.add_widget(Divider())
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("Add", self._add), 0)
        layout2.add_widget(self._edit_button, 1)
        layout2.add_widget(self._delete_button, 2)
        layout2.add_widget(Button("Quit", self._quit), 3)
        self.fix()
        self._on_pick()

    def _on_pick(self):
        self._edit_button.disabled = self._list_view.value is None
        self._delete_button.disabled = self._list_view.value is None

    def _reload_list(self, new_value=None):
        self._list_view.options = self._model.get_summary()
        self._list_view.value = new_value

    def _add(self):
        self._model.current_id = None
        raise NextScene(self._ctx)

    def _edit(self):
        self.save()
        self._model.current_id = self.data[self._ctx]
        raise NextScene(self._ctx)

    def _delete(self):
        self.save()
        self._model.delete(self.data[self._ctx])
        self._reload_list()

    @staticmethod
    def _quit():
        raise StopApplication("User pressed quit")

    def _get_list_items(self) -> ListBox:
        return ListBox(
            Widget.FILL_FRAME,
            self._model.get_summary(),
            name="Edit Options",
            add_scroll_bar=True,
            on_change=self._on_pick,
            on_select=self._edit,
        )


class AssignForm(Frame):
    def __init__(
        self,
        screen: Screen,
        model,
    ):
        super().__init__(
            screen,
            screen.height,
            screen.width,
            can_scroll=False,
            title="Edit Assign",
            reduce_cpu=True,
        )
        self._model = model
        self.set_theme("bright")
        layout = Layout([1, 1], fill_frame=True)
        self.add_layout(layout)

        self.assign_number = Text("Assign Number:", "assign_number")
        self.target = Text("Target:", "target")
        self.action = Text("Action:", "action")

        layout.add_widget(Label("Set Assign"), 0)
        help = Label("Press tab to navigate.", name="help")
        help.custom_colour = "disabled"
        layout.add_widget(help, 0)
        layout.add_widget(self.assign_number, 0)
        layout.add_widget(self.target, 0)
        layout.add_widget(self.action, 0)

        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("OK", self._ok), 0)
        layout2.add_widget(Button("Cancel", self._cancel), 3)
        self.fix()

    def reset(self):
        # Do standard reset to clear out form, then populate with new data.
        super().reset()
        self.data = self._model.get_current_val("assign")

    def _ok(self):
        self.save()
        self._model.update_current_contact(self.data)
        raise NextScene("main")

    @staticmethod
    def _cancel():
        raise NextScene("main")


def editor(
    screen,
    scene: Scene,
    context: str,
    model,
    start_scene: Union[str, None],
):
    scenes = {
        "main": Scene([EditorView(screen, model, context)], -1, name="main"),
        "assign": Scene([AssignForm(screen, model)], -1, name="assign"),
    }
    if start_scene is not None:
        scene = scenes[start_scene]
    screen.play(
        list(scenes.values()), stop_on_resize=True, start_scene=scene, allow_int=True
    )
