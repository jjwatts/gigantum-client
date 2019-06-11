import os
from gtmcore.labbook import LabBook, SecretStore
from gtmcore.container import ContainerOperations


class ContainerWorkflows(object):

    @staticmethod
    def start_labbook(labbook: LabBook, username: str) -> str:

        _, container_id = ContainerOperations.start_container(labbook, username)

        secret_store = SecretStore(labbook, username)

        secrets_dir_map = secret_store.as_mount_dict.items()
        for sec_local_src, sec_container_dst in secrets_dir_map:
            ContainerOperations.copy_into_container(labbook, username,
                                                    src_path=sec_local_src,
                                                    dst_dir=sec_container_dst)

        # TODO - if putting a secret fails, then stop container and raise exception

        return container_id
