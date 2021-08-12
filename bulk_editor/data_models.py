from dataclasses import dataclass, field, asdict
from itertools import starmap

from . import defaults, mappings


@dataclass()
class Patch:

    # list of 9 boolean integers, 1 for each loop + vol loop (9). 0: off, 1: on
    ID_PATCH_LOOP_SW_LOOP: list = field(default_factory=lambda: defaults.NINE_ZEROES)
    # list of 22 values:
    #   * idx[0-8]: the volume loop (0) and the 8 loops (1-8). Ordered by the loops
    #   * idx[9-21]: 9 then 10-12 listed twice and 13-15 listed twice. Use unknown.
    # TODO: figure out the 2nd half of this list.
    ID_PATCH_LOOP_POSITION: list = field(
        #                        <---------loops--------->  <--------------------unknown-------------------->
        default_factory=lambda: [8, 7, 6, 5, 4, 3, 2, 1, 0, 9, 10, 11, 12, 10, 11, 12, 13, 14, 15, 13, 14, 15]
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
    ID_PATCH_MIDI_PC_BANK_LSB: list = field(default_factory=lambda: defaults.EIGHT_ZEROES)
    # list of 8 integers, 1 for each MSB setting for each patch midi preset
    ID_PATCH_MIDI_PC_BANK_MSB: list = field(default_factory=lambda: defaults.EIGHT_ZEROES)
    # list of 8 integers, 1 for each PC setting for each patch midi preset
    ID_PATCH_MIDI_PC: list = field(default_factory=lambda: defaults.EIGHT_ZEROES)
    # list of 8 integers, 1 for each CTL1 cc setting for each patch midi preset
    ID_PATCH_MIDI_CTL1_CC: list = field(default_factory=lambda: defaults.EIGHT_ZEROES)
    # list of 8 integers, 1 for each CTL1 cc value for each patch midi preset
    ID_PATCH_MIDI_CTL1_CC_VAL: list = field(default_factory=lambda: defaults.EIGHT_ZEROES)
    # list of 8 integers, 1 for each CTL1 cc setting for each patch midi preset
    ID_PATCH_MIDI_CTL2_CC: list = field(default_factory=lambda: defaults.EIGHT_ZEROES)
    # list of 8 integers, 1 for each CTL1 cc value for each patch midi preset
    ID_PATCH_MIDI_CTL2_CC_VAL: list = field(default_factory=lambda: defaults.EIGHT_ZEROES)
    # list of 16 integers, for each ctl func definition
    ID_PATCH_CTL_FUNC: list = field(
        default_factory=lambda: [
            0, 0, 0, 0, 7, 8, 9, 10, 11, 12, 13, 0, 15, 16, 17, 18
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
    ID_PATCH_ASSIGN_TARGET_CC_CH: list = field(default_factory=lambda: defaults.TWELVE_ZEROES)
    # list of 12 integers, for the midi message number of each cc assign.
    # TODO: find the actual default for this
    ID_PATCH_ASSIGN_TARGET_CC_NO: list = field(default_factory=lambda: defaults.TWELVE_ZEROES)
    # list of 12 integers, for the min value of each assign.
    # TODO: find the actual default for this
    ID_PATCH_ASSIGN_TARGET_MIN: list = field(default_factory=lambda: defaults.TWELVE_ZEROES)
    # list of 12 integers, for the max value of each assign.
    # TODO: find the actual default for this
    ID_PATCH_ASSIGN_TARGET_MAX: list = field(default_factory=lambda: defaults.TWELVE_ZEROES)
    # list of 12 integers, for act low range (this should always be 0)
    ID_PATCH_ASSIGN_ACT_RANGE_LO: list = field(default_factory=lambda: defaults.TWELVE_ZEROES)
    # list of 12 integers, for act low range (this should always be 127)
    ID_PATCH_ASSIGN_ACT_RANGE_HI: list = field(default_factory=lambda: defaults.TWELVE_127S)
    # list of 12 integers, for internal pedal trigger value
    ID_PATCH_ASSIGN_INT_PEDAL_TRIGGER: list = field(default_factory=lambda: defaults.TWELVE_ZEROES)
    # list of 12 integers, for internal pedal trigger cc value
    ID_PATCH_ASSIGN_INT_PEDAL_TRIGGER_CC: list = field(default_factory=lambda: defaults.TWELVE_80S)
    # list of 12 integers, for internal pedal time value
    ID_PATCH_ASSIGN_INT_PEDAL_TIME: list = field(default_factory=lambda: defaults.TWELVE_30S)
    # list of 12 integers, for internal pedal curve value
    ID_PATCH_ASSIGN_INT_PEDAL_CURVE: list = field(default_factory=lambda: defaults.TWELVE_ZEROES)
    # list of 12 integers, for internal wave pedal rate
    ID_PATCH_ASSIGN_WAVE_PEDAL_RATE: list = field(default_factory=lambda: defaults.TWELVE_SEVENS)
    # list of 12 integers, for internal wave pedal rate
    ID_PATCH_ASSIGN_WAVE_PEDAL_FORM: list = field(default_factory=lambda: defaults.TWELVE_TWOS)
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
            **params
        }
        return {
            "assign_number": number,
            "source": mappings.PATCH_ASSIGN_SOURCE_ORDER[self.ID_PATCH_ASSIGN_SOURCE[index]],
            "target": mappings.PATCH_ASSIGN_TARGET_ORDER[self.ID_PATCH_ASSIGN_TARGET[index]],
            "mode": mappings.PATCH_ASSIGN_MODE_ORDER[self.ID_PATCH_ASSIGN_MODE[index]],
            **{k: v[index] for (k, v) in assign_map.items()}
        }

    def _get_params_for_assign_source(self, source: int):
        global_params = {
            "ActL": self.ID_PATCH_ASSIGN_ACT_RANGE_LO,
            "ActH": self.ID_PATCH_ASSIGN_ACT_RANGE_HI
        }
        params_map = {
            mappings.PATCH_ASSIGN_SOURCE_ORDER.index("INT"): {
                "trigger": self.ID_PATCH_ASSIGN_INT_PEDAL_TRIGGER,
                "time": self.ID_PATCH_ASSIGN_INT_PEDAL_TIME,
                "curve": self.ID_PATCH_ASSIGN_INT_PEDAL_CURVE
            },
            mappings.PATCH_ASSIGN_SOURCE_ORDER.index("WAV"): {
                "rate": self.ID_PATCH_ASSIGN_WAVE_PEDAL_RATE,
                "form": self.ID_PATCH_ASSIGN_WAVE_PEDAL_FORM
            },
            mappings.PATCH_ASSIGN_SOURCE_ORDER.index("CC"): {
                "cc#": self.ID_PATCH_ASSIGN_INT_PEDAL_TRIGGER_CC
            }
        }
        return {
            **global_params, **params_map.get(source, {})
        }

    @staticmethod
    def pick(old, new):
        """Given two values, choose new if it is not None."""
        return new if new is not None else old

    def update(self, params: dict):
        """Return a new Patch instance with updated parameters.
        """
        for k, v in params.items():
            assert hasattr(self, k)
            current = getattr(self, k)
            # if the values of current and v are different and current is a list,
            # v will be a list of Nones interspersed with one or more ints.
            # update v[i] to be current[i] where v[i] is None.
            if current != v and isinstance(current, list):
                params[k] = list(starmap(self.pick, zip(current, v)))
        return Patch(**{**asdict(self), **params})


DEFAULT_PATCH = Patch()
