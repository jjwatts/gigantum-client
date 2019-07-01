import time
from typing import Dict, Tuple

import redis
from gtmcore.logging import LMLogger
from lmsrvcore.auth.user import get_logged_in_username

logger = LMLogger.get_logger()


class RepositoryCacheMiddleware:
    def resolve(self, next, root, info, **args):
        if hasattr(info.context, "repo_cache_middleware_complete"):
            # Ensure that this is called ONLY once per request.
            return next(root, info, **args)

        if info.operation.operation == 'mutation':
            try:
                username, owner, name = parse_mutation(info.operation, info.variable_values)
                logger.warning((username, owner, name))
            except UnknownRepo as e:
                pass
            finally:
                info.context.repo_cache_middleware_complete = True

        return_value = next(root, info, **args)
        return return_value


# TODO/Question - Can we directly import these mutations
# OR can we add some optional metadata to the mutation definitions
# themselves in order to let-them self-identify as mutations to skip
skip_mutations = [
    'LabbookContainerStatusMutation',
    'LabbookLookupMutation'
]


class UnknownRepo(Exception):
    pass


def parse_mutation(operation_obj, variable_values: Dict) -> Tuple[str, str, str]:
    input_vals = variable_values.get('input')
    if input_vals is None:
        raise UnknownRepo("No input vals")

    if operation_obj.name.value in skip_mutations:
        raise UnknownRepo(f"Skip mutation {operation_obj.name}")

    owner = input_vals.get('owner')
    if owner is None:
        raise UnknownRepo("No owner")

    repo_name = input_vals.get('labbook_name')
    if not repo_name:
        repo_name = input_vals.get('name')

    if repo_name is None:
        raise UnknownRepo("No repo name")

    return get_logged_in_username(), owner, repo_name


class RepoCacheEntry:
    def __init__(self, x):
        pass


class RepoCacheController:
    def __init__(self):
        self.db = redis.Redis(db=7)

    @staticmethod
    def _make_key(id_tuple: Tuple[str, str, str]) -> str:
        return '&'.join(['MODIFY_CACHE', *id_tuple])

    @staticmethod
    def _extract_id(key_value: str) -> Tuple[str, str, str]:
        token, user, owner, name = key_value.rsplit('&', 3)
        assert token == 'MODIFY_CACHE'

    def set_repo_modified(self, id_tuple: Tuple[str, str, str]):
        logger.warning(f"Set {id_tuple} modified at {time.time()}")

    def query_repo_modified(self, id_tuple: Tuple[str, str, str]):
        logger.warning(f"Querying for {id_tuple} modified")
