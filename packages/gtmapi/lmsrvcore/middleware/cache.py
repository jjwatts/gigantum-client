import time
import datetime
from typing import Any, Dict, Tuple, List

import redis
from gtmcore.logging import LMLogger
from gtmcore.inventory.inventory import InventoryManager
from gtmcore.labbook import LabBook
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


def _make_key(id_tuple: Tuple[str, str, str]) -> str:
    return '&'.join(['MODIFY_CACHE', *id_tuple])


def _extract_id(key_value: str) -> Tuple[str, str, str]:
    token, user, owner, name = key_value.rsplit('&', 3)
    assert token == 'MODIFY_CACHE'
    return user, owner, name


class RepoCacheEntry:
    # 24 Hours
    REFRESH_PERIOD_SEC = 60 * 60 * 24

    def __init__(self, redis_conn: redis.Redis, key: str):
        self.db = redis_conn
        self.key = key

    def _fetch_timestamps(self) -> Tuple[datetime.datetime, datetime.datetime]:
        logger.warning(f"Fetching {self.key} from disk.")
        lb = InventoryManager().load_labbook(*_extract_id(self.key))
        create_ts = lb.creation_date
        modify_ts = lb.modified_on
        self.db.hdel(self.key, 'creation_date', 'modified_on', 'last_cache_update')
        self.db.hset(self.key, 'creation_date', modify_ts.strftime("%Y-%m-%dT%H:%M:%S.%f"))
        self.db.hset(self.key, 'modified_on', modify_ts.strftime("%Y-%m-%dT%H:%M:%S.%f"))
        self.db.hset(self.key, 'last_cache_update', datetime.datetime.utcnow().isoformat())
        return create_ts, modify_ts

    @staticmethod
    def _date(bin_str: bytes):
        if bin_str is None:
            return None
        return datetime.datetime.strptime(bin_str.decode(), "%Y-%m-%dT%H:%M:%S.%f")

    def _fetch_property(self, hash_field: str) -> datetime.datetime:
        last_update = self._date(self.db.hget(self.key, 'last_cache_update'))
        if last_update is None:
            self._fetch_timestamps()
            last_update = self._date(self.db.hget(self.key, 'last_cache_update'))
        else:
            logger.warning(f"Using cached timestamp for {self.key}")
        delay_secs = (datetime.datetime.utcnow() - last_update).total_seconds()
        if delay_secs > self.REFRESH_PERIOD_SEC:
            logger.warning(f"Flushing cache for {self.key}")
            self._fetch_timestamps()
        return self._date(self.db.hget(self.key, hash_field))

    @property
    def modified_on(self) -> datetime.datetime:
        return self._fetch_property('modified_on')

    @property
    def created_time(self) -> datetime.datetime:
        return self._fetch_property('creation_date')


class RepoCacheController:
    def __init__(self):
        self.db = redis.Redis(db=7)

    def cached_modified_on(self, id_tuple: Tuple[str, str, str]) -> datetime.datetime:
        return RepoCacheEntry(self.db, _make_key(id_tuple)).modified_on

    def cached_created_time(self, id_tuple: Tuple[str, str, str]) -> datetime.datetime:
        return RepoCacheEntry(self.db, _make_key(id_tuple)).created_time
