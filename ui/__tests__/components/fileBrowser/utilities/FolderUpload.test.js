// vendor
import renderer from 'react-test-renderer';
import { mount } from 'enzyme';
import relayTestingUtils from '@gigantum/relay-testing-utils';
// components
import FolderUpload from 'Components/fileBrowser/utilities/FolderUpload';


let files = [
      { file: 'folder/file', entry: { name: 'file.js', isFile: true, fullPath: 'folder/file.js' } },
      { file: 'folder/temp.js', entry: { name: 'temp.js', isFile: true, fullPath: 'folder/temp.js' } },
    ],
    prefix = '',
    labbookName = 'ui-test-project',
    owner = 'uitest',
    section = 'code',
    connectionKey = 'CodeBrowser__allFiles',
    sectionId = 'tempID',
    chunkLoader = jest.fn(),
    totalFiles: 2,
    count = 0,
    type = '';


describe('FolderUpload', () => {
  it('FolderUpload upload files', async () => {
      await FolderUpload.uploadFiles(files, prefix, labbookName, owner, section, connectionKey, sectionId, chunkLoader, totalFiles, count, type);

      expect(chunkLoader.mock.calls.length).toEqual(0);
  });
});
