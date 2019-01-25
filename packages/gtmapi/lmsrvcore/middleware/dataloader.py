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
from lmsrvlabbook.dataloader.labbook import LabBookLoader
from lmsrvlabbook.dataloader.dataset import DatasetLoader


class DataloaderMiddleware(object):
    """Middleware to insert an instance of the LabBookLoader and DatasetLoader dataloaders into the request context"""
    def resolve(self, next, root, info, **args):
        if hasattr(info.context, "labbook_loader"):
            if not info.context.labbook_loader:
                info.context.labbook_loader = LabBookLoader()
        else:
            info.context.labbook_loader = LabBookLoader()

        if hasattr(info.context, "dataset_loader"):
            if not info.context.dataset_loader:
                info.context.dataset_loader = DatasetLoader()
        else:
            info.context.dataset_loader = DatasetLoader()

        return next(root, info, **args)
