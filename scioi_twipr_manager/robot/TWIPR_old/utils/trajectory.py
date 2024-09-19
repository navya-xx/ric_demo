def transform_input_2d_3d(input):
    new_input = []
    for u in input:
        new_input.append([u / 2, u / 2])
    return new_input


def _get_nested(data, *args):
    if args and data:
        element = args[0]
        if element:
            value = data.get(element)
            return value if len(args) == 1 else _get_nested(value, *args[1:])


def getSignal(sample_dict: dict, *args):
    out = [_get_nested(sample, *args) for sample in sample_dict]
    return out
