from typing import (Any, Dict, List)

from gtmcore.activity.processors.processor import ActivityProcessor, ExecutionData
from gtmcore.activity import ActivityRecord, ActivityDetailType


class ActivityShowBasicProcessor(ActivityProcessor):
    """Class to simply hide an activity record if it doesn't have any detail records that are set to show=True"""

    def process(self, result_obj: ActivityRecord, data: List[ExecutionData],
                status: Dict[str, Any], metadata: Dict[str, Any]) -> ActivityRecord:
        """Method to update a result object based on code and result data

        Args:
            result_obj(ActivityNote): An object containing the note
            data(list): A list of ExecutionData instances containing the data for this record
            status(dict): A dict containing the result of git status from gitlib
            metadata(str): A dictionary containing Dev Env specific or other developer defined data

        Returns:
            ActivityNote
        """
        result_obj.show = False
        with result_obj.inspect_detail_objects() as details:
            for detail in details:
                if detail.show:
                    result_obj.show = True
                    break

        return result_obj
