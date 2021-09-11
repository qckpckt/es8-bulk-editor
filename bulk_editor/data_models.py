from dataclasses import dataclass, field, asdict
from datetime import datetime
from itertools import starmap
import json
import logging
import os
from typing import List

from . import defaults, mappings

GLOBAL_DEFAULTS_FILE = "global_defaults"


class BulkEditorError(Exception):
    pass


class NoDefaultSet(BulkEditorError):
    pass


@dataclass
class PatchCoords:

    bank: int
    patch: int


def get_global_defaults_from_file() -> dict:
    global_defaults = {}
    if os.path.isfile(GLOBAL_DEFAULTS_FILE):
        with open("{GLOBAL_DEFAULTS_FILE}.json", "r") as infile:
            global_defaults = json.load(infile)
    return global_defaults


@dataclass
class PatchList:
    """Class representing data structure of patch list element of backup file.

    Contains methods pertaining to the manipulation of the patch list.

    TODO - Currently, the data type of patches is in flux in this class. Generally they are stored as pure dictionaries,
           But some methods require manipulation that needs the patch to be an instatiated Patch() instance. A decision
           should be made on where and when patches should be dictionaries and Patch instances.
    """

    patch_list: List[dict]
    global_defaults_name: str = GLOBAL_DEFAULTS_FILE
    global_defaults_backup: str = "{GLOBAL_DEFAULTS_FILE}_{date}"
    default_patch: dict = field(default_factory=lambda: get_global_defaults_from_file())
    prev_default_patch: dict = field(default_factory=lambda: asdict(Patch()))

    @staticmethod
    def _convert_to_index(bank: int, patch: int):
        """The ES-8 has 800 patches arranged in 100 banks of 8.
        The banks go from 0-99, and each patch in a bank is numbered 1-8.
        The patch list is 0-indexed, so we must subtract 1 to get the correct index.
        EG Bank 32, patch 4 would be ((32 + 1) * 8 + 4) - 1 = 267.
        """
        return (((bank + 1) * 8) + patch) - 1

    def get_patch(self, bank: int, patch: int):
        """Return a patch specified by bank and integer."""
        return self.patch_list[self._convert_to_index(bank, patch)]

    def set_as_default(
        self, bank: int, patch: int, to_file: bool = True, as_dict: bool = False
    ):
        """Specify a patch as the default patch from which all others are based.

        NOTE - if this is not in fact the default patch, IE there are patches that are in fact the factory
               default instead, this method will produce unexpected results!

        :param bank: bank number for default patch
        :type bank: int
        :param patch: patch number for default patch
        :type patch: int
        :param to_file: boolean indicating whether to write out patch to file (default True)
        :type to_file: bool
        :param as_dict: boolean indicating whether to return patch as a dictionary or a Patch()
        :type as_dict: bool
        :return: Patch instance representing default patch or dictionary depending on as_dict state.
        :rtype: Patch() or dict
        """
        new_default_patch = self.get_patch(bank, patch)

        if self.default_patch:
            if new_default_patch == self.default_patch:
                logging.info(f"Patch {bank}:{patch} is already the default.")
                return self.default_patch
            else:
                logging.info(
                    f"Patch {bank}:{patch} is not the currently specified default patch. Updating state."
                )
                self._shuffle_defaults(new_default_patch)

        now = datetime.now()

        if to_file:
            # Update the current defaults plus save a backup copy of this new state.
            # TODO - also write out the previous default state? Not sure if this is necessary.
            backup_file = (
                f"{self.global_defaults_backup.format(date=now.toisoformat())}.json"
            )
            current_default_file = f"{self.global_defaults_name}.json"
            with open(backup_file, "w") as backupfile, open(
                current_default_file, "w"
            ) as defaultfile:
                json.dump(asdict(self.default_patch), defaultfile)
                json.dump(asdict(self.default_patch), backupfile)

        return Patch(**self.default_patch) if not as_dict else self.default_patch

    def _shuffle_defaults(self, new):
        if self.default_patch:
            # only overwrite prev_default_patch if default_patch actually has a value.
            self.prev_default_patch = self.default_patch
        self.default_patch = new

    def update_default(self, mask: dict):
        """Update the default patch using a supplied mask."""
        curr_default = Patch(**self.default_patch)
        new_default = curr_default.update(mask)
        self._shuffle_defaults(asdict(new_default))

    def apply_default(self, factory: bool = False, overwrite: bool = False):
        """Apply self.default_patch to all patches.

        Raise error if no default patch is set and factory is False (default).

        Assumes that self.default_patch is *not* the currently applied default patch.

        :param factory:   Set to True to apply the factory default to all patches.
        :type factory:    bool
        :param overwrite: Set to True to overwrite the current state of each patch with the default patch.
                          NOTE - destructive operation!
        :type overwrite:  bool
        """

        if not hasattr(self, "default_patch") and not factory:
            raise NoDefaultSet("No default_patch set.")

        if factory:
            # set whatever the current default patch is to the factory,
            # and store whatever it was to self.prev_default_patch (unless it was nothing)
            self._shuffle_defaults(asdict(Patch()))

        if overwrite:
            logging.warning("Destructive action! This will overwite data!")
            self.patch_list = [self.default_patch * 800]
            return

        self._apply(self.prev_default_patch, self.default_patch)

    def _apply(self, prev_state, new_state):
        """Apply new_state to patches, using prev_state as basis to create patch masks."""
        # create patch masks
        patch_masks = self.patch_list.map(lambda p: prev_state.mask(p))
        # Apply patch masks to new default state
        self.patch_list = patch_masks.map(lambda p: asdict(new_state.update(p)))


@dataclass
class Patch:
    """Dataclass that represents all of the individual fields for a patch.

    **CORE CONCEPTS**

    Mask:   A mask in this context is a dictionary representation of a patch which only contains fields
            with values that are different from some base patch (either a global default or the factory default,
            which is represented by calling Patch() with no kwargs.) Most of the fields in a Patch are arrays.
            In this instance, the array will only contain values at indices that differ from the default. All
            other entries will be `None`. This methodology allows for layers of changes to be applied while
            preserving the unique aspects of each patch.

    **KEY METHODS**

    self.mask(patch):    Create a mask from a dictionary representation of a patch.

    self.update(mask):   Return a new Patch instance which contains the merged result of the supplied mask with
                         the state from the patch instance on which this method was called. Importantly, this method
                         can be used to apply masks to one another! If a mask is used to instantiate an instance of
                         Patch, then you can still call update with another mask, iteratively building up changes.
                         Before these changes are resolved to a new patch list though, it is necessary to apply them as
                         a mask to an instance of the Patch class which _does_ have values for every field, in order to
                         avoid errors when submitting to an ES-8 unit.

    self.get_assign(i):  Return all fields pertaining to the assign specified by an integer as a dictionary. Used to
                         validate that an action will not overwrite an existing custom set global default for assigns.
    """

    # list of 9 boolean integers, 1 for each loop + vol loop (9). 0: off, 1: on
    ID_PATCH_LOOP_SW_LOOP: list = field(default_factory=lambda: defaults.NINE_ZEROES)
    # list of 22 values:
    #   * idx[0-8]: the volume loop (0) and the 8 loops (1-8). Ordered by the loops
    #   * idx[9-21]: 9 then 10-12 listed twice and 13-15 listed twice. Use unknown.
    # TODO: figure out the 2nd half of this list.
    ID_PATCH_LOOP_POSITION: list = field(
        #                        <---------loops--------->  <--------------------unknown-------------------->
        default_factory=lambda: [
            8,
            7,
            6,
            5,
            4,
            3,
            2,
            1,
            0,
            9,
            10,
            11,
            12,
            10,
            11,
            12,
            13,
            14,
            15,
            13,
            14,
            15,
        ]
    )
    # 0: auto, 1: manual
    ID_PATCH_MIXER_MODE: int = 0
    # 0: -6db, 1: 0db
    ID_PATCH_MIXER_GAIN1: int = 0
    # 0: -6db, 1: 0db
    ID_PATCH_MIXER_GAIN2: int = 0
    # list of 9 boolean integers (1 if carryover enabled)
    ID_PATCH_CARRY_OVER_LOOP: list = field(default_factory=lambda: defaults.NINE_ZEROES)
    # 0: input 1, 1: input 2
    ID_PATCH_INPUT_SELECT: int = 0
    # 0: buffer off, 1: buffer on
    ID_PATCH_INPUT_BUFFER: int = 1
    # 0: output 1, 1: output 2, 2: output 1 & 2
    ID_PATCH_OUTPUT_SELECT: int = 0
    # 0: buffer off, 1: buffer on
    ID_PATCH_OUTPUT_BUFFER: int = 1
    # 0: 0db, 1: +2db, 2: +4db, 3: +6db
    ID_PATCH_OUTPUT_GAIN: int = 0
    # 0: off, 1: on
    ID_PATCH_CTL1: int = 1
    # 0: off, 1: on
    ID_PATCH_CTL2: int = 1
    # 0: off, 1: on
    ID_PATCH_CTL3: int = 1
    # 0: off, 1: on
    ID_PATCH_CTL4: int = 1
    # 0: off, 1: on
    ID_PATCH_CTL5: int = 1
    # 0: off, 1: on
    ID_PATCH_CTL6: int = 1
    # 0-127: some preset expression value, 128: exp1, 129: exp2
    ID_PATCH_EXP1: int = 128
    # 0-127: some preset expression value, 128: exp1, 129: exp2
    ID_PATCH_EXP2: int = 129
    # any integer between 20 and 500
    ID_PATCH_MASTER_BPM: int = 60
    # int list with length 16.
    ID_PATCH_NAME: list = field(default_factory=lambda: defaults.DEFAULT_PATCH_NAME)
    # 0: LED off, 1: LED on
    ID_PATCH_LED_NUM1: int = 0
    # 0: LED off, 1: LED on
    ID_PATCH_LED_NUM2: int = 0
    # 0: LED off, 1: LED on
    ID_PATCH_LED_NUM3: int = 0
    # 0: LED off, 1: LED on
    ID_PATCH_LED_NUM4: int = 0
    # 0: LED off, 1: LED on
    ID_PATCH_LED_NUM5: int = 0
    # 0: LED off, 1: LED on
    ID_PATCH_LED_NUM6: int = 0
    # 0: LED off, 1: LED on
    ID_PATCH_LED_NUM7: int = 0
    # 0: LED off, 1: LED on
    ID_PATCH_LED_NUM8: int = 0
    # 0: LED off, 1: LED on
    ID_PATCH_LED_BANK_D: int = 0
    # 0: LED off, 1: LED on
    ID_PATCH_LED_BANK_U: int = 0
    # list of 8 integers, 1 for each patch midi preset channel
    ID_PATCH_MIDI_TX_CH: list = field(default_factory=lambda: defaults.EIGHT_ZEROES)
    # list of 8 integers, 1 for each LSB setting for each patch midi preset
    ID_PATCH_MIDI_PC_BANK_LSB: list = field(
        default_factory=lambda: defaults.EIGHT_ZEROES
    )
    # list of 8 integers, 1 for each MSB setting for each patch midi preset
    ID_PATCH_MIDI_PC_BANK_MSB: list = field(
        default_factory=lambda: defaults.EIGHT_ZEROES
    )
    # list of 8 integers, 1 for each PC setting for each patch midi preset
    ID_PATCH_MIDI_PC: list = field(default_factory=lambda: defaults.EIGHT_ZEROES)
    # list of 8 integers, 1 for each CTL1 cc setting for each patch midi preset
    ID_PATCH_MIDI_CTL1_CC: list = field(default_factory=lambda: defaults.EIGHT_ZEROES)
    # list of 8 integers, 1 for each CTL1 cc value for each patch midi preset
    ID_PATCH_MIDI_CTL1_CC_VAL: list = field(
        default_factory=lambda: defaults.EIGHT_ZEROES
    )
    # list of 8 integers, 1 for each CTL1 cc setting for each patch midi preset
    ID_PATCH_MIDI_CTL2_CC: list = field(default_factory=lambda: defaults.EIGHT_ZEROES)
    # list of 8 integers, 1 for each CTL1 cc value for each patch midi preset
    ID_PATCH_MIDI_CTL2_CC_VAL: list = field(
        default_factory=lambda: defaults.EIGHT_ZEROES
    )
    # list of 16 integers, for each ctl func definition
    ID_PATCH_CTL_FUNC: list = field(
        default_factory=lambda: [
            1,
            2,
            3,
            4,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
        ]
    )
    # list of 16 integers, for each ctl min value (0 or 1)
    ID_PATCH_CTL_MIN: list = field(default_factory=lambda: defaults.SIXTEEN_ZEROES)
    # list of 16 integers, for each ctl max value (0 or 1)
    ID_PATCH_CTL_MAX: list = field(default_factory=lambda: defaults.SIXTEEN_ONES)
    # list of 16 integers, for each ctl mod value (0: momentary, 1: toggle)
    ID_PATCH_CTL_MOD: list = field(default_factory=lambda: defaults.SIXTEEN_ZEROES)
    # list of 2 integers, for each patch exp setting
    ID_PATCH_EXP_FUNC: list = field(default_factory=lambda: [1, 2])
    # list of 2 integers, for the patch exp min setting (for bpm) (default 20)
    ID_PATCH_EXP_MIN: list = field(default_factory=lambda: [20, 20])
    # list of 2 integers, for the patch exp max setting (for bpm) (default 127)
    ID_PATCH_EXP_MAX: list = field(default_factory=lambda: [127, 127])
    # list of 12 integers, for whether each assign is active.
    ID_PATCH_ASSIGN_SW: list = field(default_factory=lambda: defaults.TWELVE_ZEROES)
    # list of 12 integers, for the source of each assign.
    # TODO: find the actual default for this
    ID_PATCH_ASSIGN_SOURCE: list = field(default_factory=lambda: defaults.TWELVE_ZEROES)
    # list of 12 integers, for the mode of each assign. 1: toggle, 2: momentary
    # TODO: find the actual default for this
    ID_PATCH_ASSIGN_MODE: list = field(default_factory=lambda: defaults.TWELVE_ZEROES)
    # list of 12 integers, for the target of each assign.
    # TODO: find the actual default for this
    ID_PATCH_ASSIGN_TARGET: list = field(default_factory=lambda: defaults.TWELVE_ZEROES)
    # list of 12 integers, for the midi channel of each cc assign.
    # TODO: find the actual default for this
    ID_PATCH_ASSIGN_TARGET_CC_CH: list = field(
        default_factory=lambda: defaults.TWELVE_ZEROES
    )
    # list of 12 integers, for the midi message number of each cc assign.
    # TODO: find the actual default for this
    ID_PATCH_ASSIGN_TARGET_CC_NO: list = field(
        default_factory=lambda: defaults.TWELVE_ZEROES
    )
    # list of 12 integers, for the min value of each assign.
    # TODO: find the actual default for this
    ID_PATCH_ASSIGN_TARGET_MIN: list = field(
        default_factory=lambda: defaults.TWELVE_ZEROES
    )
    # list of 12 integers, for the max value of each assign.
    # TODO: find the actual default for this
    ID_PATCH_ASSIGN_TARGET_MAX: list = field(
        default_factory=lambda: defaults.TWELVE_ZEROES
    )
    # list of 12 integers, for act low range (this should always be 0)
    ID_PATCH_ASSIGN_ACT_RANGE_LO: list = field(
        default_factory=lambda: defaults.TWELVE_ZEROES
    )
    # list of 12 integers, for act low range (this should always be 127)
    ID_PATCH_ASSIGN_ACT_RANGE_HI: list = field(
        default_factory=lambda: defaults.TWELVE_127S
    )
    # list of 12 integers, for internal pedal trigger value
    ID_PATCH_ASSIGN_INT_PEDAL_TRIGGER: list = field(
        default_factory=lambda: defaults.TWELVE_ZEROES
    )
    # list of 12 integers, for internal pedal trigger cc value
    ID_PATCH_ASSIGN_INT_PEDAL_TRIGGER_CC: list = field(
        default_factory=lambda: defaults.TWELVE_80S
    )
    # list of 12 integers, for internal pedal time value
    ID_PATCH_ASSIGN_INT_PEDAL_TIME: list = field(
        default_factory=lambda: defaults.TWELVE_30S
    )
    # list of 12 integers, for internal pedal curve value
    ID_PATCH_ASSIGN_INT_PEDAL_CURVE: list = field(
        default_factory=lambda: defaults.TWELVE_ZEROES
    )
    # list of 12 integers, for internal wave pedal rate
    ID_PATCH_ASSIGN_WAVE_PEDAL_RATE: list = field(
        default_factory=lambda: defaults.TWELVE_SEVENS
    )
    # list of 12 integers, for internal wave pedal rate
    ID_PATCH_ASSIGN_WAVE_PEDAL_FORM: list = field(
        default_factory=lambda: defaults.TWELVE_TWOS
    )
    # 0: system, 1: off
    ID_PATCH_MIDI_CLOCK_OUT: int = 0
    # list of 8 integers: 0: auto, 1: manual
    ID_PATCH_MIDI_TRANSMIT: list = field(default_factory=lambda: defaults.EIGHT_ZEROES)

    def get_assign(self, number: int):
        index = number - 1  # assigns are 1-indexed, locations in backup 0-indexed.
        source = self.ID_PATCH_ASSIGN_SOURCE[index]
        params = self._get_params_for_assign_source(source)
        assign_map = {
            "is_enabled": self.ID_PATCH_ASSIGN_SW,
            "min": self.ID_PATCH_ASSIGN_TARGET_MIN,
            "max": self.ID_PATCH_ASSIGN_TARGET_MAX,
            **params,
        }
        return {
            "assign_number": number,
            "source": mappings.PATCH_ASSIGN_SOURCE_ORDER[
                self.ID_PATCH_ASSIGN_SOURCE[index]
            ],
            "target": mappings.PATCH_ASSIGN_TARGET_ORDER[
                self.ID_PATCH_ASSIGN_TARGET[index]
            ],
            "mode": mappings.PATCH_ASSIGN_MODE_ORDER[self.ID_PATCH_ASSIGN_MODE[index]],
            **{k: v[index] for (k, v) in assign_map.items()},
        }

    def _get_params_for_assign_source(self, source: int):
        global_params = {
            "ActL": self.ID_PATCH_ASSIGN_ACT_RANGE_LO,
            "ActH": self.ID_PATCH_ASSIGN_ACT_RANGE_HI,
        }
        params_map = {
            mappings.PATCH_ASSIGN_SOURCE_ORDER.index("INT"): {
                "trigger": self.ID_PATCH_ASSIGN_INT_PEDAL_TRIGGER,
                "time": self.ID_PATCH_ASSIGN_INT_PEDAL_TIME,
                "curve": self.ID_PATCH_ASSIGN_INT_PEDAL_CURVE,
            },
            mappings.PATCH_ASSIGN_SOURCE_ORDER.index("WAV"): {
                "rate": self.ID_PATCH_ASSIGN_WAVE_PEDAL_RATE,
                "form": self.ID_PATCH_ASSIGN_WAVE_PEDAL_FORM,
            },
            mappings.PATCH_ASSIGN_SOURCE_ORDER.index("CC"): {
                "cc#": self.ID_PATCH_ASSIGN_INT_PEDAL_TRIGGER_CC
            },
        }
        return {**global_params, **params_map.get(source, {})}

    @staticmethod
    def _pick(old, new):
        """Given two values, choose new if it is not None, else return old."""
        return new if new is not None else old

    @staticmethod
    def _mask(old, new):
        """Given two values, return None if old and new match else return new."""
        return None if old == new else new

    def _mutate(self, mode: str, dictionary: dict) -> dict:
        """Mutate the input dictionary based on the supplied mode."""
        output = {}
        action = getattr(self, mode)
        for k, v in dictionary.items():
            current = getattr(self, k)
            if current != v and isinstance(current, list):
                output[k] = list(starmap(action, zip(current, v)))
            elif current != v and isinstance(current, int):
                output[k] = action(current, v)
        return output

    def update(self, mask: dict):
        """Return a new Patch instance, with mask applied.

        The input mask dictionary will only contain keys/values that are different
        from either the factory default patch or the last state of the global_defaults.json.

        If the input mask value is a list, all Nones in this list are replaced with values from
        this Patch instance, and then the key/value pair are applied over the top of the field
        values from this Patch instance to create a new instance in an 'upsert' action.

        """
        return Patch(**{**asdict(self), **self._mutate("_pick", mask)})

    def mask(self, patch: dict) -> dict:
        """Return a 'mask' dictionary created by comparing the `patch` dictionary
        to this Patch instance.

        A 'mask' in this case means a dictionary where, for each key/value from `patch`:

        * if the value is a list:
            * if the value from `patch` is different to this Patch instance's
              version, for each index of the list, if the value matches the
              value at the same index in this Patch instance's version of key,
              the value is set to None. Then, save the resulting list to the
              output dict.
        * if the value is an int:
            * if the value is different from this Patch instance's version of
              key, pass that key on to the output dict.
        """
        return self._mutate("_mask", patch)


# Calling patch with no parameters instantiates the factory default.
DEFAULT_PATCH = Patch()
