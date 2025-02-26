import graphene
from lmsrvlabbook.api.mutations import (CreateLabbook, BuildImage, StartContainer,
                                        AddPackageComponents, CreateUserNote, StopContainer,
                                        ImportLabbook, DeleteLabbook, ImportRemoteDataset,
                                        ImportRemoteLabbook, AddLabbookRemote,
                                        ExportLabbook, AddLabbookFile, MoveLabbookFile, DeleteLabbookFiles,
                                        MakeLabbookDirectory, RemoveUserIdentity,
                                        AddLabbookFavorite, RemoveLabbookFavorite, UpdateLabbookFavorite,
                                        AddLabbookCollaborator,
                                        DeleteLabbookCollaborator, SyncLabbook, PublishLabbook, PublishDataset,
                                        RemovePackageComponents,
                                        StartDevTool, SetLabbookDescription, CreateExperimentalBranch,
                                        DeleteExperimentalBranch, MigrateLabbookSchema,
                                        MergeFromBranch, WorkonBranch, WriteLabbookReadme, AddCustomDocker, 
                                        RemoveCustomDocker, DeleteRemoteLabbook,
                                        CompleteBatchUploadTransaction, SetVisibility, FetchLabbookEdge,
                                        CreateDataset, DeleteDataset, AddDatasetFile, CompleteDatasetUploadTransaction,
                                        DeleteDatasetFiles, MoveDatasetFile, MakeDatasetDirectory,
                                        FetchDatasetEdge, SetDatasetVisibility, SyncDataset,
                                        AddDatasetCollaborator, DeleteDatasetCollaborator, DownloadDatasetFiles,
                                        ModifyDatasetLink, WriteDatasetReadme, SetDatasetDescription,
                                        ResetBranchToRemote, CancelBuild)

from lmsrvlabbook.api.mutations import (ImportDataset, ExportDataset)

# TODO - Group related mutations into classes, that will each have a corresponding
# test file.


class BranchMutations(object):
    """ All mutations found in mutations/branching.py """

    migrate_labbook_schema = MigrateLabbookSchema.Field()

    # Create a Rollback or Feature branch
    create_experimental_branch = CreateExperimentalBranch.Field()

    # Delete a Rollback or Feature branch
    delete_experimental_branch = DeleteExperimentalBranch.Field()

    # Merge from a given branch into the current checked-out branch
    merge_from_branch = MergeFromBranch.Field()

    # Work on a given feature branch (perform a git checkout).
    workon_experimental_branch = WorkonBranch.Field()


class LabbookEnvironmentMutations(graphene.ObjectType):

    # Build a docker image for a given Labbook.
    build_image = BuildImage.Field()

    # Abort a build-in-progress
    cancel_build = CancelBuild.Field()

    # Start a labbook's Docker container.
    start_container = StartContainer.Field()

    # Start a labbook's Docker container.
    stop_container = StopContainer.Field()

    # Start a tool such as Jupyer Lab
    start_dev_tool = StartDevTool.Field()

    # Add a package to a Labbook environment (e.g., pip package, apt)
    add_package_components = AddPackageComponents.Field()

    # Remove a package from a Labbook environment (e.g., pip package, apt)
    remove_package_components = RemovePackageComponents.Field()

    # Add an arbitrary docker snippet (supplement to custom dependency)
    add_custom_docker = AddCustomDocker.Field()

    # Delete the arbitrary docker snippet.
    remove_custom_docker = RemoveCustomDocker.Field()


class LabbookSharingMutations(graphene.ObjectType):
    """ All mutations found in mutations/labbooksharing.py """

    # Import a labbook from an uploaded file (Archive as zip).
    import_labbook = ImportLabbook.Field()

    # Export a labbook and return URL to its zipped archive.
    export_labbook = ExportLabbook.Field()

    # Import a labbook from a remote Git repository.
    import_remote_labbook = ImportRemoteLabbook.Field()

    # Delete a labbook from a remote server
    delete_remote_labbook = DeleteRemoteLabbook.Field()

    # Sync a Labbook with remote (for collaboration)
    sync_labbook = SyncLabbook.Field()

    # Publish a labbook to a remote (for the first time
    publish_labbook = PublishLabbook.Field()

    # Set a remote project visibility
    set_visibility = SetVisibility.Field()

    # Add a remote to the labbook
    add_labbook_remote = AddLabbookRemote.Field()

    # Add a collaborator to a LabBook
    add_collaborator = AddLabbookCollaborator.Field()

    # Delete a collaborator from a LabBook
    delete_collaborator = DeleteLabbookCollaborator.Field()


class LabbookMutations(BranchMutations, LabbookSharingMutations,
                       LabbookEnvironmentMutations, graphene.ObjectType):
    """Entry point for all graphql mutations"""

    # Import a Dataset from the Gitlab repository
    import_remote_dataset = ImportRemoteDataset.Field()

    # Import/Export datasets as zip files
    import_dataset = ImportDataset.Field()
    export_dataset = ExportDataset.Field()

    # Create a new labbook on the file system.
    create_labbook = CreateLabbook.Field()

    # Delete a labbook off the file system
    delete_labbook = DeleteLabbook.Field()

    # (Re-)set labbook description
    set_labbook_description = SetLabbookDescription.Field()

    # Publish a dataset to a remote (for the first time
    publish_dataset = PublishDataset.Field()

    # Perform a git reset to remote on current branch
    reset_branch_to_remote = ResetBranchToRemote.Field()

    # Create a user note in the labbook's current working branch
    create_user_note = CreateUserNote.Field()

    # Add a file to a labbook
    add_labbook_file = AddLabbookFile.Field()

    # Indicate a (potentially) mutlifile batched upload is finished
    # Also contains options to cancel (and rollback aborted changes).
    complete_batch_upload_transaction = CompleteBatchUploadTransaction.Field()

    # Move files or directory within a labbook
    move_labbook_file = MoveLabbookFile.Field()

    # Delete a file or directory inside of a Labbook.
    delete_labbook_files = DeleteLabbookFiles.Field()

    # Make a directory (with auto-included .gitkeep) inside of a Labbook
    make_labbook_directory = MakeLabbookDirectory.Field()

    # Remove a locally stored user identity (no-op for non-local installations)
    remove_user_identity = RemoveUserIdentity.Field()

    # Add a favorite file or dir in a labbook subdirectory (code, input, output)
    add_favorite = AddLabbookFavorite.Field()

    # Update a favorite file or dir in a labbook subdirectory (code, input, output)
    update_favorite = UpdateLabbookFavorite.Field()

    # Remove a favorite file or dir in a labbook subdirectory (code, input, output)
    remove_favorite = RemoveLabbookFavorite.Field()

    # Adds a dataset collaborator
    add_dataset_collaborator = AddDatasetCollaborator.Field()
    delete_dataset_collaborator = DeleteDatasetCollaborator.Field()

    # Write a readme to a LabBook
    write_labbook_readme = WriteLabbookReadme.Field()

    # Kludge-query to return a labbook edge when querying for job status
    fetch_labbook_edge = FetchLabbookEdge.Field()

    # Create a new dataset on the file system.
    create_dataset = CreateDataset.Field()

    # Delete a dataset
    delete_dataset = DeleteDataset.Field()

    # Add a file to a dataset
    add_dataset_file = AddDatasetFile.Field()

    # Close an upload transaction to a dataset
    complete_dataset_upload_transaction = CompleteDatasetUploadTransaction.Field()

    # Kludge-query to return a dataset edge when querying for job status
    fetch_dataset_edge = FetchDatasetEdge.Field()

    # Set a remote dataset visibility
    set_dataset_visibility = SetDatasetVisibility.Field()

    # Sync a Dataset with remote (for collaboration)
    sync_dataset = SyncDataset.Field()

    # Download dataset files locally
    download_dataset_files = DownloadDatasetFiles.Field()

    # Link/Unlink a dataset to a project
    modify_dataset_link = ModifyDatasetLink.Field()

    # Delete a file or directory inside of a Dataset
    delete_dataset_files = DeleteDatasetFiles.Field()

    # Move a file or directory inside of a Dataset
    move_dataset_file = MoveDatasetFile.Field()

    # Create an empty directory inside of a Dataset
    make_dataset_directory = MakeDatasetDirectory.Field()

    # Write a readme to a Dataset
    write_dataset_readme = WriteDatasetReadme.Field()

    # Write a description to a Dataset
    set_dataset_description = SetDatasetDescription.Field()
