import copy
import collections

# Both of these are copied from the adversarial policies codebase


def update(d, u):
    """Recursive dictionary update."""
    for k, v in u.items():
        if isinstance(v, collections.Mapping):
            d[k] = update(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def sacred_copy(o):
    """Perform a deep copy on nested dictionaries and lists.

    If `d` is an instance of dict or list, copies `d` to a dict or list
    where the values are recursively copied using `sacred_copy`. Otherwise, `d`
    is copied using `copy.deepcopy`. Note this intentionally loses subclasses.
    This is useful if e.g. `d` is a Sacred read-only dict. However, it can be
    undesirable if e.g. `d` is an OrderedDict.

    :param o: (object) if dict, copy recursively; otherwise, use `copy.deepcopy`.
    :return A deep copy of d."""
    if isinstance(o, dict):
        return {k: sacred_copy(v) for k, v in o.items()}
    elif isinstance(o, list):
        return [sacred_copy(v) for v in o]
    else:
        return copy.deepcopy(o)