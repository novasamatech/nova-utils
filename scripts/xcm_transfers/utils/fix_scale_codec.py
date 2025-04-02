from scalecodec import ScaleBytes, Tuple as ScaleTuple, GenericMetadataVersioned


def fix_substrate_interface():
    fix_tuple_encoding()
    fix_metadata_error_search()

def fix_tuple_encoding():
    ScaleTuple.process_encode = process_encode

# This is a modified implementation of Tuple.process_encode that fixes issue https://github.com/polkascan/py-scale-codec/issues/126
def process_encode(self: ScaleTuple, value):
    data = ScaleBytes(bytearray())
    self.value_object = ()

    # CHANGED: we additionally check for len(self.type_mapping) == 1 when wrapping the value
    if len(self.type_mapping) == 1 or type(value) not in (list, tuple):
        value = [value]

    if len(value) != len(self.type_mapping):
        raise ValueError('Element count of value ({}) doesn\'t match type_definition ({})'.format(
            len(value), len(self.type_mapping))
        )

    for idx, member_type in enumerate(self.type_mapping):
        element_obj = self.runtime_config.create_scale_object(
            member_type, metadata=self.metadata
        )
        data += element_obj.encode(value[idx])
        self.value_object += (element_obj,)

    return data

def fix_metadata_error_search():
    GenericMetadataVersioned.get_module_error = get_module_error

# This is a modified implementation of GenericMetadataVersioned.get_module_error that accounts for non-continuous error indices
def get_module_error(self, module_index, error_index):
    if self.portable_registry:
        for module in self.pallets:
            if module['index'] == module_index and module.errors:
                # CHANGED
                # return module.errors[error_index]
                for error in module.errors:
                    if error['index'] == error_index:
                        return error

                raise Exception(f"Error {error_index} was not found in module {module['name']}")
    else:
        return self.value_object[1].error_index.get(f'{module_index}-{error_index}')
