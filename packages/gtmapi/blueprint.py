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
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import json
import os

import graphene
from flask import Blueprint
from flask_graphql import GraphQLView

from gtmcore.configuration import Configuration
from lmsrvcore.middleware import AuthorizationMiddleware, DataloaderMiddleware, time_all_resolvers_middleware, \
    error_middleware
from lmsrvlabbook.api import LabbookQuery, LabbookMutations


# ** This blueprint is the combined full LabBook service with all components served together from a single schema ** #


# Load config data for the LabManager instance
config = Configuration()

# Create Blueprint
complete_labbook_service = Blueprint('complete_labbook_service', __name__)

# Create Schema
full_schema = graphene.Schema(query=LabbookQuery, mutation=LabbookMutations)

# Add route and require authentication
complete_labbook_service.add_url_rule(f'{config.config["proxy"]["labmanager_api_prefix"]}/labbook/',
                                      view_func=GraphQLView.as_view('graphql', schema=full_schema,
                                                                    graphiql=config.config["flask"]["DEBUG"],
                                                                    middleware=[error_middleware,
                                                                                #time_all_resolvers_middleware,
                                                                                AuthorizationMiddleware(),
                                                                                DataloaderMiddleware()]),
                                      methods=['GET', 'POST', 'OPTION'])


if __name__ == '__main__':
    # If the blueprint file is executed directly, generate a schema file
    introspection_dict = full_schema.introspect()

    # Save the schema
    with open('full_schema.json', 'wt') as fp:
        json.dump(introspection_dict, fp)
        print("Wrote full schema to {}".format(os.path.realpath(fp.name)))

