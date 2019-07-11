import tempfile
import pytest
import time
import pprint
import os

from gtmcore.inventory.inventory import InventoryManager
from gtmcore.fixtures import mock_config_file
from gtmcore.labbook import SecretStore, SecretStoreException


def init(config):
    im = InventoryManager(config)
    lb = im.create_labbook('test', 'test', 'labbook1')
    return SecretStore(lb, 'test')


class TestLabbookSecret(object):
    def test_init(self, mock_config_file):
        """
        Test a simple secret store that is empty.
        """
        secstore = init(mock_config_file[0])
        assert len(secstore) == 0
        assert [x for x in secstore] == []

    def test_create_registry_void_of_files(self, mock_config_file):
        secstore = init(mock_config_file[0])
        mnt_target = '/opt/.ssh'

        secstore['ID_SSH.KEY'] = mnt_target
        secstore['ID_SSH.PUB'] = mnt_target
        secstore['PUBKEY.DAT'] = '/var/tmp'

        print('xxxxxxx', [x for x in secstore.list_files()])

        # Assert all files are not found, but exist in registry.
        assert all([e[1] == False for e in secstore.list_files()])
        assert len(secstore.list_files()) == 3

        del secstore['PUBKEY.DAT']
        assert len(secstore.list_files()) == 2

        del secstore['ID_SSH.KEY']
        assert len(secstore.list_files()) == 1

        del secstore['ID_SSH.PUB']
        assert len(secstore.list_files()) == 0

    def test_insert_file_delete_files_list_files(self, mock_config_file):
        secstore = init(mock_config_file[0])
        mnt_target = '/opt/.ssh'

        secstore['ID_SSH.KEY'] = mnt_target
        secstore['ID_SSH.PUB'] = mnt_target

        with tempfile.TemporaryDirectory() as tempdir:
            with open(os.path.join(tempdir, 'ID_SSH.KEY'), 'w') as t1:
                t1.write('<<SUPER SECRET PRIVATE KEY>>')
            with open(os.path.join(tempdir, 'ID_SSH.PUB'), 'w') as t2:
                t2.write('((NOT SO SECRET PUBLIC KEY))')

            keyfile_dst_1 = secstore.insert_file(t1.name)
            keyfile_dst_2 = secstore.insert_file(t2.name)

        parts = [secstore.labbook.client_config.app_workdir, '.labmanager',
                 'secrets', 'test', secstore.labbook.owner, secstore.labbook.name,
                 os.path.basename(keyfile_dst_1)]
        assumed_path = os.path.join(*parts)
        assert assumed_path == keyfile_dst_1

        # But properly return the two inserted files for the correct keys
        assert secstore.list_files() == [('ID_SSH.KEY', True), ('ID_SSH.PUB', True)]

        # Test that delete removes a file properly by using list_files
        secstore.delete_file('ID_SSH.KEY')
        assert secstore.list_files() == [('ID_SSH.KEY', False), ('ID_SSH.PUB', True)]

        # Deleting from the registry should ALSO delete the actual file.
        del secstore['ID_SSH.PUB']
        assert secstore.list_files() == [('ID_SSH.KEY', False)]

        # Test clear_files works by making sure the vault itself doesn't exist
        secstore.clear_files()
        toks = [secstore.labbook.client_config.app_workdir, '.labmanager', 'secrets',
                'test', secstore.labbook.owner, secstore.labbook.name]
        assert not os.path.exists(os.path.join(*toks))

    def test_insert_must_be_for_valid_file(self, mock_config_file):
        secstore = init(mock_config_file[0])
        mnt_target = '/opt/.ssh'

        with tempfile.TemporaryDirectory() as tempdir:
            with open(os.path.join(tempdir, 'ID_SSH.KEY'), 'w') as t1:
                t1.write('CORRECT_DATA')

            # Raises this exception because we have not yet made
            # an entry to account for this file.
            with pytest.raises(SecretStoreException):
                secstore.insert_file(t1.name)

    def test_insert_cannot_overwrite(self, mock_config_file):
        """
        Confirm that you cannot overwrite a given file.
        """
        secstore = init(mock_config_file[0])
        mnt_target = '/opt/.ssh'

        secstore['ID_SSH.KEY'] = mnt_target

        with tempfile.TemporaryDirectory() as tempdir:
            with open(os.path.join(tempdir, 'ID_SSH.KEY'), 'w') as t1:
                t1.write('CORRECT_DATA')
            keyfile_dst_1 = secstore.insert_file(t1.name)

        with tempfile.TemporaryDirectory() as tempdir:
            with open(os.path.join(tempdir, 'ID_SSH.KEY'), 'w') as t2:
                t2.write('BAD_DATA')
            with pytest.raises(SecretStoreException):
                keyfile_dst_2 = secstore.insert_file(t2.name)

        assert secstore.list_files() == [('ID_SSH.KEY', True)]
        assert open(keyfile_dst_1).read() == 'CORRECT_DATA'
        assert len(secstore.as_mount_dict) == 1

    def test_remove_keyfile_not_existing(self, mock_config_file):
        secstore = init(mock_config_file[0])
        mnt_target = '/opt/.ssh'

        with pytest.raises(SecretStoreException):
            secstore.delete_file('catfile')

        assert secstore.list_files() == []
        assert len(secstore.as_mount_dict) == 0

    def test_clean(self, mock_config_file):
        secstore = init(mock_config_file[0])
        mnt_target = '/opt/.ssh'
        secstore['ID_SSH.KEY'] = mnt_target
        with tempfile.TemporaryDirectory() as tempdir:
            with open(os.path.join(tempdir, 'ID_SSH.KEY'), 'w') as t1:
                t1.write('CORRECT_DATA')
            keyfile_dst_1 = secstore.insert_file(t1.name)

        del secstore['ID_SSH.KEY']
        with open(os.path.join(os.path.dirname(keyfile_dst_1), 'badfile'), 'w') as bf:
            bf.write('This file must get cleaned.')

        # Even though an incorrect file is in there, it should not be listed.
        assert len(secstore.list_files()) == 0

        # Assert that _clean removes this extraneous file.
        secstore2 = SecretStore(secstore.labbook, secstore.username)
        assert not os.path.exists(bf.name)
