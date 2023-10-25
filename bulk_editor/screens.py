# from dataclasses import asdict
from typing import (
    Dict,
    Tuple,
    Union,
    # Any,
    # Optional
)

from asciimatics.widgets import (
    Frame,
    Layout,
    Text,
    Button,
    Label,
    ListBox,
    Divider,
    Widget,
    DropdownList,
)
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import StopApplication, NextScene

# from tinydb.table import Document
from typer import Context

from . import mappings
from .context import AppContext

USER_PREFERENCES = {
    "Loop Preferences": "loop_prefs",
    "Midi Preferences": "midi_prefs",
}
BASE_LISTVIEW_TEMPLATE = "{option} {idx} [{detail}]"


def _next_scene(scene_name: str):
    raise NextScene(scene_name)


class ListView(Frame):
    parent_scene = None
    child_scene = None
    option_name = None

    def __init__(
        self,
        screen: Screen,
        ctx: AppContext,
        title: str,
        view: ListBox,
        *args,
        **kwargs,
    ):
        super().__init__(
            screen,
            screen.height * 2 // 3,
            screen.width * 2 // 3,
            hover_focus=True,
            title=title,
            reduce_cpu=True,
            *args,
            **kwargs,
        )
        self._list_view = view
        self.set_theme("bright")
        self.base_layout = Layout([100], fill_frame=True)
        self.add_layout(self.base_layout)
        self.base_layout.add_widget(self._list_view)
        self.base_layout.add_widget(Divider())
        self.button_layout = Layout([1, 1, 1, 1])
        self.add_layout(self.button_layout)
        self._edit_button = Button("Edit", self._edit)
        self._done_button = Button("Done", self._done)
        self.button_layout.add_widget(self._edit_button, 1)
        self.button_layout.add_widget(self._done_button, 3)
        # self._pref_template = "{option} {idx} [{detail}]"
        # self._sort_key = "type"  # noop unless overridden
        # self._pref_sort_fn = lambda x: x[self._sort_key]
        self.fix()
        self._on_pick()

    def _fetch_prefs(self, sort_fn: callable):
        pref_list = []
        for pref in sorted(
            self._table.search(screen=self.child_scene),
            key=sort_fn,
        ):
            pref_list.append((self._build_pref_title(pref), pref.doc_id))
        return pref_list

    def _build_pref_title(self, pref: dict):
        raise NotImplementedError

    def _on_pick(self):
        raise NotImplementedError

    def _edit(self):
        raise NotImplementedError

    def _done(self):
        if self.parent_scene is None:
            raise StopApplication("User pressed quit")
        else:
            _next_scene(self.parent_scene)


class UserPrefs(ListView):
    option_name = "user_prefs"

    def __init__(
        self,
        screen: Screen,
        ctx: AppContext,
    ):
        view = ListBox(
            Widget.FILL_FRAME,
            self._fetch_prefs(),
            name="pref_choice",
            add_scroll_bar=True,
            on_change=self._on_pick,
            on_select=self._edit,
        )
        super().__init__(
            screen,
            ctx,
            title="Edit User Preferences",
            view=view,
            can_scroll=False,
        )
        self.pref_options = list(USER_PREFERENCES.keys())

    def _fetch_prefs(self):
        return [(b, a) for (a, b) in enumerate(USER_PREFERENCES)]

    def _on_pick(self):
        self._edit_button.disabled = self._list_view.value is None

    def _edit(self):
        self.save()
        choice = self.pref_options[self.data["pref_choice"]]
        selected = USER_PREFERENCES[choice]
        _next_scene(selected)

    @staticmethod
    def _done():
        raise StopApplication("User pressed quit")


class UserPrefsOption(Frame):
    option_name = None
    parent_scene = None
    fields: Dict[str, Tuple[str, Widget]] = {}

    def __init__(
        self,
        screen: Screen,
        ctx: AppContext,
        can_scroll: bool,
        title: str,
        widget_label: str,
    ):
        super().__init__(
            screen,
            screen.height,
            screen.width,
            can_scroll=can_scroll,
            title=title,
            reduce_cpu=True,
        )

        self.set_theme("bright")
        self.base_layout = Layout([1, 1], fill_frame=True)
        self.add_layout(self.base_layout)
        self.button_layout = Layout([1, 1, 1, 1])
        self.add_layout(self.button_layout)
        self.base_layout.add_widget(Label(widget_label), 0)
        help = Label("Press tab to navigate.", name="help")
        help.custom_colour = "disabled"
        self.base_layout.add_widget(help, 0)
        self._set_fields()
        self.button_layout.add_widget(Button("OK", self._ok), 0)
        self.button_layout.add_widget(Button("Cancel", self._cancel), 3)

    @staticmethod
    def _cancel():
        raise NextScene("user_prefs")

    def _set_fields(self):
        for label, (name, field_type) in self.fields.items():
            setattr(self, name, field_type(label, name))
            self.base_layout.add_widget(getattr(self, name), 0)


class LoopPrefs(UserPrefsOption):
    option_name = "loop_prefs"
    parent_scene = "user_prefs"
    fields = {
        "Loop 1": ("loop_1", Text),
        "Loop 2": ("loop_2", Text),
        "Loop 3": ("loop_3", Text),
        "Loop 4": ("loop_4", Text),
        "Loop 5": ("loop_5", Text),
        "Loop 6": ("loop_6", Text),
        "Loop 7": ("loop_7", Text),
        "Loop 8": ("loop_8", Text),
        "Volume Loop": ("loop_v", Text),
        "Other": ("other", Text),
    }

    def __init__(self, screen: Screen, ctx: AppContext):
        super().__init__(
            screen,
            ctx=ctx,
            can_scroll=False,
            title="Edit Loop Preferences",
            widget_label="Name your loops",
        )
        self._table = ctx.user_prefs
        self.fix()

    def _ok(self):
        self.save()
        self._table.upsert(payload=self.data, screen=self.option_name)
        _next_scene(self.parent_scene)

    def reset(self):
        # Do standard reset to clear out form, then populate with new data.
        super().reset()
        if last_state := self._table.get(screen=self.option_name):
            self.data = last_state
            self._table.current_entry[self.option_name] = last_state.doc_id

        for key in self.data:
            if hasattr(self, key):
                getattr(self, key).value = self.data[key]


class MidiPrefs(ListView):
    option_name = "midi_prefs"
    parent_scene = "user_prefs"
    child_scene = "midi_pref"

    def __init__(self, screen: Screen, ctx: AppContext):
        self._table = ctx.user_prefs
        self._sort_fn = lambda x: int(x["midi_ch"])

        view = ListBox(
            Widget.FILL_FRAME,
            self._fetch_prefs(sort_fn=self._sort_fn),
            name="midi_choice",
            add_scroll_bar=True,
            on_change=self._on_pick,
            on_select=self._edit,
        )
        super().__init__(
            screen,
            ctx=ctx,
            view=view,
            on_load=self._reload_list,
            can_scroll=False,
            title="Edit Midi Preferences",
        )
        self._add_button = Button("Add", self._add)
        self._delete_button = Button("Delete", self._delete)
        self._delete_button.disabled = self._table.current_entry is None
        self.button_layout.add_widget(self._add_button, 0)
        self.button_layout.add_widget(self._delete_button, 2)

        self.fix()
        self._on_pick()

    def _build_pref_title(self, pref: dict):
        return BASE_LISTVIEW_TEMPLATE.format(
            option="Channel",
            idx=" " + pref["midi_ch"] if len(pref["midi_ch"]) < 2 else pref["midi_ch"],
            detail=pref["loop_num"],
        )

    # def _fetch_midi_prefs(self):
    #     return [
    #         (
    #             f"Channel {' ' + pref['midi_ch'] if len(pref['midi_ch']) < 2 else pref['midi_ch']} [{pref['loop_num']}]",
    #             pref.doc_id,
    #         )
    #         for pref in sorted(
    #             self._table.search(screen=self.child_scene),
    #             key=lambda x: int(x["midi_ch"]),
    #         )
    #     ]

    def _reload_list(self, new_value=None):
        self._list_view.options = self._fetch_prefs(sort_fn=self._sort_fn)
        self._list_view.value = new_value

    def _on_pick(self):
        self._edit_button.disabled = self._list_view.value is None

    def _add(self):
        self._table.current_entry[self.child_scene] = None
        _next_scene(self.child_scene)

    def _edit(self):
        self.save()
        self._table.current_entry[self.child_scene] = self.data["midi_choice"]
        _next_scene(self.child_scene)

    def _delete(self):
        self.save()
        self._table.delete(screen=self.child_scene)
        self._reload_list()


class MidiPref(UserPrefsOption):
    option_name = "midi_pref"
    parent_scene = "midi_prefs"
    fields = {
        "Patch Midi #:": ("pmidi_num", Text),
        "Midi Channel:": ("midi_ch", Text),
    }

    def __init__(self, screen: Screen, ctx: Context):
        super().__init__(
            screen,
            ctx=ctx,
            can_scroll=False,
            title="Edit Midi Preference",
            widget_label="Provide midi config details",
        )
        self._table = ctx.user_prefs
        self._pedal_options = self._fetch_pedal_options()
        self._loop_num = DropdownList(
            options=[(option, i) for (i, option) in enumerate(self._pedal_options)],
            label="Loop",
            name="_loop_num",
        )
        self.base_layout.add_widget(self._loop_num)
        self.fix()

    def _fetch_pedal_options(self):
        loop_prefs = self._table.get(screen="loop_prefs")
        pedal_options = []
        for loop, p in loop_prefs.items():
            if "loop" in loop:
                title = loop.replace("_", " ").capitalize()
                if ">>" in p:
                    pedal_options.extend(
                        [": ".join([title, i]) for i in p.split(" >> ")]
                    )
                else:
                    pedal_options.append(": ".join([title, p]))
            if loop == "other" and loop_prefs[loop]:
                title = loop.capitalize()
                pedal_options.extend([": ".join([title, i]) for i in p.split(", ")])
        return pedal_options

    def reset(self):
        super().reset()
        if self._table.current_entry[self.option_name] is not None:
            self.data = self._table.get(screen=self.option_name)
            try:
                self.data["_loop_num"] = mappings.name_to_index(
                    self.data["loop_num"], self._pedal_options
                )
            except ValueError:
                parts = self.data["loop_num"].split(": ")
                title = parts[0]
                converted = ": ".join([title.replace("_", " ").capitalize(), parts[1]])
                self.data["_loop_num"] = mappings.name_to_index(
                    converted, self._pedal_options
                )

        for key in self.data:
            if hasattr(self, key):
                getattr(self, key).value = self.data[key]

    def _ok(self):
        self.save()
        self.data["loop_num"] = mappings.index_to_name(
            self.data["_loop_num"], self._pedal_options
        )

        if self._table.current_entry[self.option_name] is not None:
            self._table.upsert(payload=self.data, screen=self.option_name)
        else:
            self._table.insert(payload=self.data, screen=self.option_name)
        _next_scene(self.parent_scene)


class Templates(ListView):
    option_name = "templates"
    # parent_scene = "user_prefs"
    child_scene = "template_pref"

    def __init__(self, screen: Screen, ctx: AppContext):
        self._table = ctx.templates
        self._sort_fn = lambda x: x["name"]

        view = ListBox(
            Widget.FILL_FRAME,
            self._fetch_prefs(sort_fn=self._sort_fn),
            name="template_choice",
            add_scroll_bar=True,
            on_change=self._on_pick,
            on_select=self._edit,
        )
        super().__init__(
            screen,
            ctx=ctx,
            view=view,
            on_load=self._reload_list,
            can_scroll=False,
            title="Edit Patch Templates",
        )
        self._add_button = Button("Add", self._add)
        self._delete_button = Button("Delete", self._delete)
        self._delete_button.disabled = self._table.current_entry is None
        self.button_layout.add_widget(self._add_button, 0)
        self.button_layout.add_widget(self._delete_button, 2)
        self.fix()
        self._on_pick()

    def _build_pref_title(self, pref: dict):
        """Function used to create title for self._fetch_prefs"""
        return BASE_LISTVIEW_TEMPLATE.format(
            option="Template", idx=pref["name"], detail=pref["applies_to"]
        )

    def _reload_list(self, new_value=None):
        self._list_view.options = self._fetch_prefs(sort_fn=self._sort_fn)
        self._list_view.value = new_value

    def _on_pick(self):
        self._edit_button.disabled = self._list_view.value is None

    def _add(self):
        self._table.current_entry[self.child_scene] = None
        _next_scene(self.child_scene)

    def _edit(self):
        self.save()
        self._table.current_entry[self.child_scene] = self.data["template_choice"]
        _next_scene(self.child_scene)

    def _delete(self):
        self.save()
        self._table.delete(screen=self.child_scene)
        self._reload_list()


class TemplatePrefOption(UserPrefsOption):
    option_name = "template_pref"
    parent_scene = "templates"
    fields = {
        "Template Name": ("name", Text),
        "Source Bank": ("source_bank", Text),
        "Source Patch": ("source_patch", Text),
        "Targets": ("_applies_to", Text),
        "Version": ("version", Text),
    }

    def __init__(self, screen: Screen, ctx: Context):
        super().__init__(
            screen,
            ctx=ctx,
            can_scroll=False,
            title="Edit Midi Preference",
            widget_label="Provide midi config details",
        )
        self._table = ctx.templates
        self.fix()

    def reset(self):
        super().reset()
        if self._table.current_entry[self.option_name] is not None:
            self.data = self._table.get(screen=self.option_name)

        for key in self.data:
            if hasattr(self, key):
                if key == "source_patch_coords":
                    getattr(self, "source_bank").value = key["bank"]
                    getattr(self, "source_patch").value = key["patch"]
                if key == "applies_to":
                    getattr(self, "_applies_to").value = ", ".join(
                        self.data["applies_to"]
                    )
                getattr(self, key).value = self.data[key]

    def _ok(self):
        self.save()
        self.data["source_patch_coords"] = {
            "bank": int(self.data["source_bank"]),
            "patch": int(self.data["source_patch"]),
        }
        applies_to = self.data["_applies_to"].split(", ")
        self.data["applies_to"] = (
            applies_to if applies_to == ["all"] else [int(i) for i in applies_to]
        )
        self.data["version"] = int(self.data["version"])
        if self._table.current_entry[self.option_name] is not None:
            self._table.upsert(payload=self.data, screen=self.option_name)
        else:
            self._table.insert(payload=self.data, screen=self.option_name)
        _next_scene(self.parent_scene)


def editor(
    screen,
    scene: Scene,
    ctx: AppContext,
    start_scene: Union[str, None],
):
    scenes = {
        "user_prefs": Scene([UserPrefs(screen, ctx)], -1, name="user_prefs"),
        "loop_prefs": Scene([LoopPrefs(screen, ctx)], -1, name="loop_prefs"),
        "midi_prefs": Scene([MidiPrefs(screen, ctx)], -1, name="midi_prefs"),
        "midi_pref": Scene([MidiPref(screen, ctx)], -1, name="midi_pref"),
        "templates": Scene([Templates(screen, ctx)], -1, name="templates"),
        "template_pref": Scene(
            [TemplatePrefOption(screen, ctx)], -1, name="template_pref"
        ),
    }
    if start_scene is not None:
        scene = scenes[start_scene]
    screen.play(
        list(scenes.values()), stop_on_resize=True, start_scene=scene, allow_int=True
    )
