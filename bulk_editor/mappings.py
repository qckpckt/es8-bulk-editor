"""Mappings for various components of patch file.
"""

CTL_FUNC_ORDER = [
    "OFF", "MemM", "Mute", "BnkD", "BnkU", "MemU", "MemD", "Num1",
    "Num2", "Num3", "Num4", "Num5", "Num6", "Num7", "Num8", "Ctl1",
    "Ctl2", "Ctl3", "Ctl4", "Ctl5", "Ctl6", "BPM"
]
EXP_FUNC_ORDER = ["OFF", "EXP1", "EXP2", "BPM"]
PATCH_ASSIGN_SOURCE_ORDER = [
    "CTL1", "CTL2", "CTL3", "CTL4", "MemM", "Mute", "BnkD", "BnkU",
    "Num1", "Num2", "Num3", "Num4", "Num5", "Num6", "Num7", "Num8",
    "CNum", "EXP1", "EXP2", "INT", "WAV", "CC"
]
ES8_FOOTSWITCHES = [
    "MemM", "Mute", "BnkD", "BnkU", "Num1", "Num2",
    "Num3", "Num4", "Num5", "Num6", "Num7", "Num8"
]
PATCH_ASSIGN_MODE_ORDER = ["MOM", "TGL"]
PATCH_ASSIGN_TARGET_ORDER = [
    "LOOP: L1", "LOOP: L2", "LOOP: L3", "LOOP: L4", "LOOP: L5", "LOOP: L6",
    "LOOP: L7", "LOOP: L8", "LOOP: LV", "E.CTL: CTL1", "E.CTL: CTL2",
    "E.CTL: CTL3", "E.CTL: CTL4", "E.CTL: CTL5", "E.CTL: CTL6", "E.CTL: EXP1",
    "E.CTL: EXP2", "InOut: IN", "InOut: OUT", "MODE: MemM", "MODE: Mute",
    "MODE: Bypass", "MIDI", "BPM: MstBPM", "BPM: Tap", "LED: BnkD", "LED: BnkU",
    "LED: Num1", "LED: Num2", "LED: Num3", "LED: Num4", "LED: Num5",
    "LED: Num6", "LED: Num7", "LED: Num8", "Pat.M: PMIDI1", "Pat.M: PMIDI2",
    "Pat.M: PMIDI3", "Pat.M: PMIDI4", "Pat.M: PMIDI5", "Pat.M: PMIDI6",
    "Pat.M: PMIDI7", "Pat.M: PMIDI8"
]
INT_PEDAL_CURVE_ORDER = ["LNR", "SLW", "FST"]
WAVE_PEDAL_RATE_ORDER = [
    "1/1", "1/2D", "1/1T", "1/2", "1/4D", "1/2T", "1/4",
    "1/8D", "1/4T", "1/8", "1/16D", "1/8T", "1/16"
] + [str(i) for i in range(100)]
WAVE_PEDAL_WAVEFORM_ORDER = ["SAW", "TRI", "SIN"]
# these fields should not trigger `OverridesDefault`
IGNORE = ["ID_PATCH_NAME"]
# map keywords to the length of arrays needed
array_lengths_map = {
    "assign": 12,
    "ctl_func": 16
}
# map keywords to arrays for indexing
value_type_map = {
    "source": PATCH_ASSIGN_SOURCE_ORDER,
    "target": PATCH_ASSIGN_TARGET_ORDER,
    "mode": PATCH_ASSIGN_MODE_ORDER,
    "ctl_func": CTL_FUNC_ORDER
}
