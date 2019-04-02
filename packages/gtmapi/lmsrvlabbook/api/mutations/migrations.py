# Copyright (c) 2018 FlashX, LLC
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
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import os
import time
import graphene

from gtmcore.logging import LMLogger

from gtmcore.inventory.inventory import InventoryManager
from gtmcore.workflows import LabbookWorkflow, MergeOverride

from lmsrvcore.auth.user import get_logged_in_username, get_logged_in_author
from lmsrvlabbook.api.objects.labbook import Labbook

logger = LMLogger.get_logger()


class MigrateLabbookSchema(graphene.relay.ClientIDMutation):

    class Input:
        owner = graphene.String(required=True)
        labbook_name = graphene.String(required=True)

    labbook = graphene.Field(Labbook)

    @classmethod
    def mutate_and_get_payload(cls, root, info, owner, labbook_name, client_mutation_id=None):
        username = get_logged_in_username()
        lb = InventoryManager().load_labbook(username, owner, labbook_name,
                                             author=get_logged_in_author())

        migrated = False
        with lb.lock():
            t0 = time.time()
            workflow = LabbookWorkflow(lb)
            migrated = workflow.migrate()
            tf = time.time()

        if migrated:
            logger.info(f"Migrated {str(lb)} in {tf-t0:.2}sec")
        else:
            logger.info(f"No migration needed for {str(lb)}")

        return MigrateLabbookSchema(Labbook(id=f"{owner}&{labbook_name}",
                                            name=labbook_name, owner=owner))
