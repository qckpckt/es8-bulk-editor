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
        * Load currently used global defaults mask from global default file
        * Apply changes to default mask (and validate that this doesn't overwrite existing defaults)
        * Load patches from backup file + parse raw patches to create masks,
          either from the factory default or base patch.
        * Apply the updated default mask to the factory default patch, to create a complete patch
        * Apply each patch mask to this complete patch in order to add back any individual patch customizations
        * Return list of updated patches, and the newly updated global default mask.
    """
    # Apply current global defaults to base patch to create the default mask
    current_global_defaults_mask = data_models.Patch(**global_defaults)
    # Check if this assign already has a global default set
    current_assign_state = current_global_defaults_mask.get_assign(assign_number)
    default_assign_state = data_models.DEFAULT_PATCH.get_assign(assign_number)
    if current_assign_state != default_assign_state and not force:
        raise errors.OverridesDefault(f"Assign {assign_number} already has a default set.")
    # update global defaults
    updated_defaults = current_global_defaults_mask.update(
        build_assign_mask(assign_number, source, mode, target, params)
    )
    # Create masks from each patch in current state, using either the factory or global default as a base.
    # The key here is that it is necessary to start from a known state. Using the global defaults mask will
    # produce unexpected results if it does not actually represent the base of every patch.
    mask_base = data_models.DEFAULT_PATCH if initial else current_global_defaults_mask
    masks = [mask_base.mask(patch) for patch in current_state]
    # Apply the newly updated global default mask to the default patch in order to fill in any Nones
    # with the factory default values.
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


def build_assign_mask(assign_number, source, mode, target, params):
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
        ID_PATCH_ASSIGN_SW=create_input_array(index, 1, "integer", "assign"),  # turn on patch assign
        # NOTE: This assumes that _all_ params entries will _always_ be integers only!
        **{k: create_input_array(index, v, "integer", "assign") for (k, v) in params.items()},
        **non_assign_params
    )
