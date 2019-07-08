import graphene


class LabbookMutationInput:
    repository_type = graphene.String(required=False, default="labbook")
    owner = graphene.String(required=True)
    name = graphene.String(required=True)


class DatasetMutationInput:
    repository_type = graphene.String(required=False, default="dataset")
    owner = graphene.String(required=True)
    name = graphene.String(required=True)
