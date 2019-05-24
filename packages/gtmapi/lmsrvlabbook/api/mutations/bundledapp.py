import graphene

from gtmcore.inventory.inventory import InventoryManager
from lmsrvcore.auth.user import get_logged_in_username, get_logged_in_author
from lmsrvlabbook.api.objects.environment import Environment
from gtmcore.environment.bundledapp import BundledAppManager


class SetBundledApp(graphene.relay.ClientIDMutation):
    """Mutation to add or update a bundled app configuration to a project
    """

    class Input:
        owner = graphene.String(required=True, description="Owner of the labbook")
        labbook_name = graphene.String(required=True, description="Name of the labbook")
        app_name = graphene.String(required=True, description="Name of the bundled app")
        description = graphene.String(required=True, description="Description of the bundled app")
        port = graphene.Int(required=True, description="Port internally exposed")
        command = graphene.String(description="Optional command run to start the bundled app if needed")

    environment = graphene.Field(Environment)

    @classmethod
    def mutate_and_get_payload(cls, root, info, owner, labbook_name, app_name, description, port, command=None,
                               client_mutation_id=None):
        username = get_logged_in_username()
        lb = InventoryManager().load_labbook(username, owner, labbook_name,
                                             author=get_logged_in_author())
        bam = BundledAppManager(lb)
        with lb.lock():
            bam.add_bundled_app(port, app_name, description, command)

        return SetBundledApp(environment=Environment(name=labbook_name, owner=owner))


class RemoveBundledApp(graphene.relay.ClientIDMutation):
    """Mutation to remove a bundled app from a container"""

    class Input:
        owner = graphene.String(required=True, description="Owner of the labbook")
        labbook_name = graphene.String(required=True, description="Name of the labbook")
        app_name = graphene.String(required=True, description="Name of the bundled app")

    environment = graphene.Field(Environment)

    @classmethod
    def mutate_and_get_payload(cls, root, info, owner, labbook_name, app_name,
                               client_mutation_id=None):
        username = get_logged_in_username()
        lb = InventoryManager().load_labbook(username, owner, labbook_name,
                                             author=get_logged_in_author())
        bam = BundledAppManager(lb)
        with lb.lock():
            bam.remove_bundled_app(app_name)

        return SetBundledApp(environment=Environment(name=labbook_name, owner=owner))
