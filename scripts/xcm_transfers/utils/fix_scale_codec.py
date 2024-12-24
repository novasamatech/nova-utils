from scalecodec import ScaleBytes, Tuple as ScaleTuple


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

def fix_scale_codec():
    ScaleTuple.process_encode = process_encode