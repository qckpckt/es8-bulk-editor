VALID_ACTIONS = {
    "set_assign": lambda patch_list, args: set_assign(patch_list, args),
    "set_default_patch": lambda patch_list, args: set_default_patch(patch_list, args),
}


def set_assign(patch_list, args):
    required_args = ["assign_number", "source", "mode", "target", "params"]
    payload = {k: getattr(args, k) for k in required_args}
    return patch_list.update_assign(**payload)


def set_default_patch(patch_list, args):
    bank, patch = [int(i) for i in getattr("coords", args).split(":")]
    patch_list.set_as_default(bank, patch)
    return patch_list.apply_default()
