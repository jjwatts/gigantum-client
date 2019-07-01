from typing import Dict
from gtmcore.logging import LMLogger

logger = LMLogger.get_logger()


class RepositoryCacheMiddleware(object):
    def resolve(self, next, root, info, **args):
        if hasattr(info.context, "repo_cache_middleware_complete"):
            # Ensure that this is called ONLY once per request.
            return next(root, info, **args)

        if info.operation.operation == 'mutation':
            try:
                owner, name = parse_mutation(info.operation, info.variable_values)
                logger.warning((owner, name))
            except UnknownRepo as e:
                pass
            finally:
                info.context.repo_cache_middleware_complete = True

        return_value = next(root, info, **args)
        return return_value


skip_mutations = [
    'LabbookContainerStatusMutation',
    'LabbookLookupMutation'
]


class UnknownRepo(Exception):
    pass


def parse_mutation(operation_obj, variable_values: Dict):
    input_vals = variable_values.get('input')
    if input_vals is None:
        raise UnknownRepo("No input vals")

    #logger.warning((operation_obj.name, skip_mutations))
    if operation_obj.name.value in skip_mutations:
        raise UnknownRepo(f"Skip mutation {operation_obj.name}")

    owner = input_vals.get('owner')
    if owner is None:
        raise UnknownRepo("No owner")

    # First, try labbook_name
    repo_name = input_vals.get('labbook_name')
    if not repo_name:
        repo_name = input_vals.get('name')

    if repo_name is None:
        raise UnknownRepo("No repo name")

    logger.warning(('xxx', operation_obj.name.value))
    return owner, repo_name
