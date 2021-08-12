from dataclasses import asdict

from . import data_models, defaults, errors, mappings


def set_global_assign_default(assign_number,
                              current_state,
                              global_defaults,
                              source,
                              mode,
                              target,
                              params,
                              initial=False,
                              force=False):
    """
        * Load currently used global defaults from global default file:
            * global_defaults = Patch(**global_defaults_file)
        * Apply changes to default (and validate that this doesn't overwrite existing defaults):
            call updated = global_defaults.update(changes)
        * Load patches from backup file + parse raw patches:
            * for each patch, call merged = updated.update(**patch)
        * save patches to new backup file
    """
    # Apply current global defaults
    current_global_defaults = data_models.Patch(**global_defaults)
    # Check if this assign already has a global default set
    current_assign_state = current_global_defaults.get_assign(assign_number)
    default_assign_state = data_models.DEFAULT_PATCH.get_assign(assign_number)
    if current_assign_state != default_assign_state and not force:
        raise errors.OverridesDefault(f"Assign {assign_number} already has a default set.")
    # update global defaults
    updated_defaults = current_global_defaults.update(build_assign_payload(assign_number, source, mode, target, params))
    # create masks from each patch in current state, using either the factory or global default as a base.
    mask_base = data_models.DEFAULT_PATCH if initial else current_global_defaults
    masks = [mask_base.mask(patch) for patch in current_state]
    new_base_patch = data_models.DEFAULT_PATCH.update(asdict(updated_defaults))
    # Apply patch data back on top of thew new udpdated_defaults for each patch, return updated_defaults
    return [new_base_patch.update(mask) for mask in masks], updated_defaults


def create_input_array(index, value, value_type, array_type):
    input_array = defaults.default_values(None, mappings.array_lengths_map[array_type])
    if value_type == "integer":
        input_array[index] = value
    else:
        input_array[index] = mappings.value_type_map[value_type].index(value)
    return input_array


def build_assign_payload(assign_number, source, mode, target, params):
    index = assign_number - 1
    non_assign_params = {}
    if source in mappings.ES8_FOOTSWITCHES:
        # if the assign is a footswitch of the ES-8, then disable the normal
        # functionality of the footswitch globally.
        non_assign_params["ID_PATCH_CTL_FUNC"] = create_input_array(
            mappings.ES8_FOOTSWITCHES.index(source), "OFF", "ctl_func", "ctl_func"
        )
    return dict(
        ID_PATCH_ASSIGN_SOURCE=create_input_array(index, source, "source", "assign"),
        ID_PATCH_ASSIGN_TARGET=create_input_array(index, target, "target", "assign"),
        ID_PATCH_ASSIGN_MODE=create_input_array(index, mode, "mode", "assign"),
        # NOTE: This assumes that _all_ params entries will _always_ be integers only!
        **{k: create_input_array(index, v, "integer", "assign") for (k, v) in params.items()},
        **non_assign_params
    )
