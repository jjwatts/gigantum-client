import json
from contextlib import contextmanager
from enum import Enum
from typing import (Any, List, Tuple, Optional, Dict)
import base64
import blosc
import copy
import operator
import datetime

from gtmcore.activity.serializers import Serializer
from gtmcore.exceptions import GigantumException
from gtmcore.logging import LMLogger

logger = LMLogger.get_logger()

class ActivityType(Enum):
    """Enumeration representing the type of Activity Record"""
    # User generated Notes
    NOTE = 0
    # For any changes to the environment config
    ENVIRONMENT = 1
    # Anything related to files in the code directory or execution
    CODE = 2
    # Anything related to files in the input directory
    INPUT_DATA = 3
    # Anything related to files in the output directory
    OUTPUT_DATA = 4
    # A milestone record
    MILESTONE = 5
    # A branch record
    BRANCH = 6
    # A record for any high-level labbook ops
    LABBOOK = 7
    # A record for any high-level dataset ops
    DATASET = 8


class ActivityDetailType(Enum):
    """Enumeration representing the type of Activity Detail Record"""
    # Any dataset level changes (e.g. create, rename)
    DATASET = 8
    # User generated Notes
    NOTE = 7
    # Any labbook level changes (e.g. create, rename)
    LABBOOK = 6
    # Anything related to files in the input directory
    INPUT_DATA = 5
    # Anything related to files in the code directory
    CODE = 4
    # For storing the executed block of code
    CODE_EXECUTED = 3
    # For storing results from running code
    RESULT = 2
    # Anything related to files in the input directory
    OUTPUT_DATA = 1
    # For any changes to the environment config
    ENVIRONMENT = 0


class ActivityAction(Enum):
    """Enumeration representing the modifiers on Activity Detail Records"""
    NOACTION = 0
    CREATE = 1
    EDIT = 2
    DELETE = 3
    EXECUTE = 4


class ActivityDetailRecordEncoder(json.JSONEncoder):
    """Custom JSON encoder to encoded binary data as base64 when serializing to json"""
    def default(self, obj):
        if isinstance(obj, bytes):
            return base64.b64encode(obj).decode("UTF-8")

        return json.JSONEncoder.default(self, obj)


class ActivityDetailRecord(object):
    """A class to represent an activity detail entry that can be stored in an activity entry"""

    def __init__(self, detail_type: ActivityDetailType, key: Optional[str] = None, show: bool = True,
                 importance: int = 0, action: ActivityAction = ActivityAction.NOACTION) -> None:
        """Constructor

        Args:
            key(str): Key used to access and identify the object
        """
        # Key used to load detail record from the embedded detail DB
        self.key = key

        # Flag indicating if this record object has been populated with data (used primarily during lazy loading)
        self.is_loaded = False

        # Storage for detail record data, organized by MIME type to support proper rendering
        self.data: dict = dict()

        # Type indicating the category of detail
        self.type = detail_type

        # Action for this detail record
        self.action = action

        # Boolean indicating if this item should be "shown" or "hidden"
        self.show = show

        # A score indicating the importance, currently expected to range from 0-255
        self.importance = importance

        # A list of tags for the record
        self.tags: Optional[List[str]] = []

    @property
    def log_str(self) -> str:
        """Method to create the identifying string stored in the git log

        Returns:
            str
        """
        if not self.key:
            raise ValueError("Detail Object key must be set before accessing the log str.")

        return "{},{},{},{},{}".format(self.type.value, int(self.show), self.importance, self.key, self.action.value)

    @staticmethod
    def from_log_str(log_str: str) -> 'ActivityDetailRecord':
        """Static method to create a ActivityDetailRecord instance from the identifying string stored in the git log

        Args:
            log_str(str): the identifying string stored in the git lo

        Returns:
            ActivityDetailRecord
        """
        try:
            type_int, show_int, importance, key, action_int = log_str.split(',')
        except ValueError:
            # Legacy record with no Action modifier available
            type_int, show_int, importance, key = log_str.split(',')
            action_int = "0"  # No action

        return ActivityDetailRecord(ActivityDetailType(int(type_int)), show=bool(int(show_int)),
                                    importance=int(importance), key=key, action=ActivityAction(int(action_int)))

    def add_value(self, mime_type: str, value: Any) -> None:
        """Method to add data to this record by MIME type

        Args:
            mime_type(str): The MIME type of the representation of the object
            value(Any): The value for this record

        Returns:
            None
        """
        if mime_type in self.data:
            raise ValueError("Attempting to duplicate a MIME type while adding detail data")

        # Store value
        self.data[mime_type] = value

        # Since you added data, it can be accessed now
        self.is_loaded = True

    @property
    def data_size(self) -> int:
        """A property to get the uncompressed byte count for detail objects

        Returns:
            int
        """
        obj_size = 0
        for mime_type in self.data:
            obj_size += len(self.data[mime_type])

        return obj_size

    def to_dict(self, compact=False) -> dict:
        """Method to convert to a dictionary

        Args:
            compact(bool): Flag indicating if compact values should be used (default when storing to log)

        Returns:
            dict
        """
        if compact:
            # Compact representation and do deep copy so binary conversions don't stick around in the object
            return {"t": self.type.value,
                    "i": self.importance,
                    "s": int(self.show),
                    "d": copy.deepcopy(self.data),
                    "a": self.tags,
                    "n": self.action.value
                    }
        else:
            return {"type": self.type.value,
                    "importance": self.importance,
                    "show": self.show,
                    "data": self.data,
                    "tags": self.tags,
                    "action": self.action.value
                    }

    def to_bytes(self, compress: bool=True) -> bytes:
        """Method to serialize to bytes for storage in the activity detail db

        Returns:
            bytes
        """
        dict_data = self.to_dict(compact=True)

        # Serialize data items
        serializer_obj = Serializer()
        for mime_type in dict_data['d']:
            dict_data['d'][mime_type] = serializer_obj.serialize(mime_type, dict_data['d'][mime_type])

            # Compress object data
            if compress:
                if type(dict_data['d'][mime_type]) != bytes:
                    raise ValueError("Data must be serialized to bytes before compression")

                dict_data['d'][mime_type] = blosc.compress(dict_data['d'][mime_type], typesize=8,
                                                           cname='blosclz',
                                                           shuffle=blosc.SHUFFLE)

        # Base64 encode binary data while dumping to json string
        return json.dumps(dict_data, cls=ActivityDetailRecordEncoder, separators=(',', ':')).encode('utf-8')

    @staticmethod
    def from_bytes(byte_array: bytes, decompress: bool=True) -> 'ActivityDetailRecord':
        """Method to create ActivityDetailRecord from byte array (typically stored in the detail db)

        Returns:
            ActivityDetailRecord
        """
        serializer_obj = Serializer()

        obj_dict = json.loads(byte_array.decode('utf-8'))

        # Base64 decode detail data
        for mime_type in obj_dict['d']:
            obj_dict['d'][mime_type] = base64.b64decode(obj_dict['d'][mime_type])

            # Optionally decompress
            if decompress:
                obj_dict['d'][mime_type] = blosc.decompress(obj_dict['d'][mime_type])

            # Deserialize
            obj_dict['d'][mime_type] = serializer_obj.deserialize(mime_type, obj_dict['d'][mime_type])

        # Return new instance
        new_instance = ActivityDetailRecord(detail_type=ActivityDetailType(obj_dict['t']),
                                            show=bool(obj_dict["s"]),
                                            importance=obj_dict["i"])

        # add tags if present (missing in "old" labbooks)
        if "a" in obj_dict:
            new_instance.tags = obj_dict['a']

        # add action if present (missing in "old" labbooks)
        if "n" in obj_dict:
            new_instance.action = ActivityAction(int(obj_dict['n']))

        new_instance.data = obj_dict['d']
        new_instance.is_loaded = True
        return new_instance

    def to_json(self) -> str:
        """Method to convert to a single dictionary of data, that will serialize to JSON

        Returns:
            dict
        """
        # Get base dict
        dict_data = self.to_dict()

        # jsonify the data
        serializer_obj = Serializer()
        for mime_type in dict_data['data']:
            dict_data['data'][mime_type] = serializer_obj.jsonify(mime_type, dict_data['data'][mime_type])

        # At this point everything in dict_data should be ready to go for JSON serialization
        return json.dumps(dict_data, cls=ActivityDetailRecordEncoder, separators=(',', ':'))

    def jsonify_data(self) -> Dict[str, Any]:
        """Method to convert just the data to JSON safe dictionary

        Returns:
            dict
        """
        dict_data: dict = dict()

        # jsonify the data
        serializer_obj = Serializer()
        for mime_type in self.data:
            dict_data[mime_type] = serializer_obj.jsonify(mime_type, self.data[mime_type])

        # At this point everything in dict_data should be ready to go for JSON serialization
        return dict_data


class ActivityRecord(object):
    """Class representing an Activity Record"""

    def __init__(self, activity_type: ActivityType, show: bool = True, message: str = None,
                 importance: Optional[int] = None, tags: Optional[List[str]] = None,
                 linked_commit: Optional[str] = None, timestamp: Optional[datetime.datetime] = None,
                 username: Optional[str] = None, email: Optional[str] = None) -> None:
        """Constructor

        Args:
            key(str): Key used to access and identify the object
        """
        # Commit hash of this record in the git log
        self.commit: Optional[str] = None

        # Commit hash of the commit this references
        self.linked_commit = linked_commit

        # Message summarizing the event
        self.message = message

        # Storage for detail objects in a tuple of (show, type (enum *value*), importance, object)
        self._detail_objects: List[Tuple[bool, int, int, ActivityDetailRecord]] = list()

        # Are we safely editing self._detail_objects?
        self._in_modify = False

        # During an inspection, we can set modifications to entire sets based on a tag
        self._tags_to_update: Dict[str, str] = {}

        # Type indicating the category of detail
        self.type = activity_type

        # Boolean indicating if this item should be "shown" or "hidden"
        self.show = show

        # A score indicating the importance, currently expected to range from 0-255
        self.importance = importance

        # The datetime that the record was written to the git log
        self.timestamp = timestamp

        # A list of tags for the entire record
        self.tags = tags or []

        # Username of the user who created the activity record
        self.username = username

        # Email of the user who created the activity record
        self.email = email

    @property
    def num_detail_objects(self):
        return len(self._detail_objects)

    @contextmanager
    def inspect_detail_objects(self):
        """To modify _detail_objects, use this in a `with` block

        Returns a new list, so that you can update the objects, or even delete them (but be careful to maintain
        correspondence!). The list in ActivityRecord is sorted upon exiting the with context.

            with ar.inspect_detail_objects() as detail_objs:
        ...   for i, obj in enumerate(detail_objs):
        ...       new_obj = mutate_obj(obj)
        ...       ar.update_detail_object(i, new_obj)
        ... # ar._detail_objects is sorted on exiting `with` block
        """
        self._in_modify = True
        try:
            # Using unpacking here to get implicit assertion that records are four elements
            yield [obj for _, _, _, obj in self._detail_objects]
        finally:
            if self._tags_to_update:
                logger.info(f'_tags_to_update: {self._tags_to_update}')
                # We regenerate our list, in case the user modified it:
                old_details = [obj for _, _, _, obj in self._detail_objects]
                self._detail_objects = []
                for idx, detail in enumerate(old_details):
                    # Default behavior is 'auto' whether it's in the comment or not
                    directive = 'auto'

                    # We don't filter on .startswith('ex') here, so we can use other tags in future
                    # Note also that
                    for tag in detail.tags:
                        try:
                            # Currently show is the only attribute we update
                            directive = self._tags_to_update[tag]
                            if directive == 'show':
                                detail.show = True
                                break
                            elif directive == 'hide':
                                detail.show = False
                                break
                            elif directive in ['ignore', 'auto']:
                                # 'ignore' is handled below - this will be dropped
                                break

                        except KeyError:
                            pass

                    if directive != 'ignore':
                        self.add_detail_object(detail)

                self._tags_to_update = {}

            self._sort_detail_objects()
            self._in_modify = False

    @staticmethod
    def from_log_str(log_str: str, commit: str, timestamp: datetime.datetime,
                     username: Optional[str] = None, email: Optional[str] = None) -> 'ActivityRecord':
        """Static method to create a ActivityRecord instance from the identifying string stored in the git log

        Args:
            log_str(str): the identifying string stored in the git log
            commit(str): Optional commit hash for this activity record
            timestamp(datetime.datetime): datetime the record was written to the git log
            username(str): Username of the user who created the commit
            email(str): email of the user who created the commit

        Returns:
            ActivityRecord
        """
        # Validate it is a record
        if log_str[0:20] == "_GTM_ACTIVITY_START_" and log_str[-18:] == "_GTM_ACTIVITY_END_":
            lines = log_str.split("**\n")
            message = lines[1][4:]
            metadata = json.loads(lines[2][9:])

            # Create record
            activity_record = ActivityRecord(ActivityType(metadata["type"]), message=message,
                                             show=metadata["show"],
                                             importance=metadata["importance"],
                                             timestamp=timestamp,
                                             tags=metadata["tags"],
                                             linked_commit=metadata['linked_commit'],
                                             username=username,
                                             email=email)
            if commit:
                activity_record.commit = commit

            # Add detail records
            for line in lines[4:]:
                if line == "_GTM_ACTIVITY_END_":
                    break

                # Append records
                activity_record.add_detail_object(ActivityDetailRecord.from_log_str(line))

            return activity_record
        else:
            raise ValueError("Malformed git log record. Cannot parse.")

    @property
    def log_str(self) -> str:
        """A property to create the identifying string stored in the git log

        Returns:
            str
        """
        if self.message:
            log_str = f"_GTM_ACTIVITY_START_**\nmsg:{self.message}**\n"
        else:
            raise ValueError("Message required when creating an activity object")

        meta = {"show": self.show, "importance": self.importance or 0, "type": self.type.value,
                'linked_commit': self.linked_commit, 'tags': self.tags}
        log_str = f"{log_str}metadata:{json.dumps(meta, separators=(',', ':'))}**\n"
        log_str = f"{log_str}details:**\n"
        if self._detail_objects:
            for d in self._detail_objects:
                log_str = f"{log_str}{d[3].log_str}**\n"

        log_str = f"{log_str}_GTM_ACTIVITY_END_"

        return log_str

    def _sort_detail_objects(self):
        """Method to sort detail objects by show, type, then importance"""
        self._detail_objects = sorted(self._detail_objects, key=operator.itemgetter(0, 1, 2), reverse=True)

    def add_detail_object(self, obj: ActivityDetailRecord) -> None:
        """Method to add a detail object

        Args:
            obj(ActivityDetailRecord): detail record to add

        Returns:
            None
        """
        self._detail_objects.append((obj.show, obj.type.value, obj.importance, obj))
        self._sort_detail_objects()

    def update_detail_object(self, obj: ActivityDetailRecord, index: int) -> None:
        """Method to update a detail object in place

        Can only be used while in the context of self.inspect_detail_objects

        Args:
            obj: detail record to add
            index: index to update
        """
        if not self._in_modify:
            raise GigantumException("Attempt to use ActivityRecord.update_detail_object() outside of "
                                    "ActivityRecord.inspect_detail_objects()")
        if index < 0 or index >= len(self._detail_objects):
            raise ValueError("Index out of range when updating detail object")

        self._detail_objects[index] = (obj.show, obj.type.value, obj.importance, obj)

    def modify_tag_visibility(self, tag: str, show: str):
        """Modify all detail objecvts with matching tag to have visibility specified in show"""
        if not self._in_modify:
            raise GigantumException("Attempt to use ActivityRecord.modify_tag_visibility() outside of "
                                    "ActivityRecord.inspect_detail_objects()")

        # We'll actually do the modifications in one pass when we exit the with-context
        self._tags_to_update[tag] = show
