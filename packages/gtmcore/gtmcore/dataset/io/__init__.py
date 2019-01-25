from typing import NamedTuple, List

# Named tuple for objects that need to be pushed
PushObject = NamedTuple('PushObject', [('object_path', str), ('revision', str), ('dataset_path', str)])

# Named tuple for the result of a Push operation
PushResult = NamedTuple('PushResult', [('success', List[PushObject]), ('failure', List[PushObject]), ('message', str)])

# Named tuple for objects that need to be pulled
PullObject = NamedTuple('PullObject', [('object_path', str), ('revision', str), ('dataset_path', str)])

# Named tuple for the result of a Pull operation
PullResult = NamedTuple('PullResult', [('success', List[PullObject]), ('failure', List[PullObject]), ('message', str)])
