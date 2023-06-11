from dataclasses import dataclass
import json
import unittest

from . import data_models as d
from . import actions


@dataclass
class MockArgs:
    action: str

    def add_params(self, params: dict):
        for k, v in params.items():
            setattr(self, k, v)


class TestPatchActions(unittest.TestCase):
    # TODO
    pass


class TestPatchListActions(unittest.TestCase):
    def setUp(self) -> None:
        with open("bulk_editor/test_data/test_1.bel", "r") as infile:
            self.backupfile = json.load(infile)

    def test_set_assign(self):
        params = {
            "assign_number": 4,
            "source": "MemM",
            "mode": "TGL",
            "target": "E.CTL: CTL2",
            "params": {},
        }
        args = MockArgs(action="set_assign")
        args.add_params(params)
        expected_patch = {
            # TODO
        }
        expected_default = {
            # TODO
        }
        patch_list = d.PatchList(self.backupfile["patch"])
        action_func = actions.VALID_ACTIONS["set_assign"]
        patches, default = action_func(patch_list, args)
        assign_set = set([patch.get_assign(4) for patch in patches])
        self.assertEqual(
            len(assign_set), 1
        )  # validate assign is the same for all patches
        self.assertEqual(
            expected_patch, patches[0]
        )  # validate that the first patch matches expected
        self.assertEqual(
            expected_default, default
        )  # validate that the default patch matches expected

    def test_set_default_patch(self):
        # TODO
        pass
