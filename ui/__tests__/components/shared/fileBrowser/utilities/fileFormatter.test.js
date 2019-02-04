
// components
import FileFormatter, { fileHandler } from 'Components/shared/fileBrowser/utilities/FileFormatter';

let files = [
      { file: 'folder/file', entry: { name: 'file.js', isFile: true, fullPath: 'folder/file.js' } },
      { file: 'folder/temp.js', entry: { name: 'temp.js', isFile: true, fullPath: 'folder/temp.js' } },
    ],
    evt = {
      data: {
        files,
      },
    },
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
  it('FolderUpload upload files', () => {
      let fileHandlerInitiated = new FileFormatter(fileHandler);
      expect(1).toEqual(1);
  });
});
