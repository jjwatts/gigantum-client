# Copyright (c) 2017 FlashX, LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THEt
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from gtmcore.logging import LMLogger
from time import time as timer
import json

logger = LMLogger.get_logger()


def time_all_resolvers_middleware(next, root, info, **args):
    """Middleware to time and log all resolvers"""
    start = timer()
    return_value = next(root, info, **args)
    duration = timer() - start

    data = {"metric_type": "field_resolver_duration",
            "parent_type": root._meta.name if root and hasattr(root, '_meta') else '',
            "field_name": info.field_name,
            "duration_ms": round(duration * 1000, 2)}

    if duration * 1000 > 10:
        logger.info(f"METRIC :: {json.dumps(data)}")
    return return_value
