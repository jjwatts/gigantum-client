import uuidv4 from 'uuid/v4';
import config from 'JS/config';
// utilities
import ChunkUploader from 'JS/utils/ChunkUploader';

/**
 * @param {Array:[Object]} files
 * @param {string} prefix
 * @param {Object} mutationData
 *
 * @return {number} totalFiles
 */
const createFiles = (files, prefix, mutationData) => {
  const fileSizeData = checkFileSize(files);


  const fileMetaData = getTotalFileLength(files);


  const transactionId = uuidv4();


  const totalFiles = fileMetaData.fileCount - fileSizeData.fileSizeNotAllowed;


  const hasDirectoryUpload = fileMetaData.hasDirectoryUpload;


  const self = this;
  const folderFiles = [];

  // loop through files and upload if file is a file
  files.forEach((file, index) => {
    if (file.isDirectory) {
      folderFiles.push(file);
    } else if (file.name) {
      const isFileAllowed = fileSizeData.fileSizeNotAllowed.filter(largeFile => largeFile.name === file.name).length === 0;

      if (isFileAllowed) {
        let newKey = prefix;

        if ((prefix !== '') && (prefix.substring(prefix.length - 1, prefix.length) !== '/')) {
          newKey += '/';
        }

        newKey += file.name;

        const fileReader = new FileReader();

        fileReader.onloadend = function (evt) {
          const filepath = newKey;

          const data = {
            file,
            filepath,
            username: mutationData.owner,
            accessToken: localStorage.getItem('access_token'),
            connectionKey: mutationData.connection,
            labbookName: mutationData.labbookName,
            parentId: mutationData.parentId,
            section: mutationData.section,
            transactionId,
          };

          ChunkUploader.chunkFile(data, (response) => {});
        };

        fileReader.readAsArrayBuffer(file);
      } else {
        // WARNING_MESSAGE
      }
    } else {
      folderFiles.push(file);
    }
  });
};

/**
* @param {array} files
*
* @return {number} totalFiles
*/
const getTotalFileLength = (files) => {
  let fileCount = 0;
  let hasDirectoryUpload = false;

  function filesRecursionCount(file) {
    if (Array.isArray(file)) {
      file.forEach((nestedFile) => {
        filesRecursionCount(nestedFile);
      });
    } else if (file.file && Array.isArray(file.file) && (file.file.length > 0)) {
      file.file.forEach((nestedFile) => {
        filesRecursionCount(nestedFile);
      });
    } else {
      const extension = file.name ? file.name.replace(/.*\./, '') : file.entry.fullPath.replace(/.*\./, '');

      if (file.entry && file.entry.isDirectory) {
        hasDirectoryUpload = true;
      }

      if ((config.fileBrowser.excludedFiles.indexOf(extension) < 0) && ((file.entry && file.entry.isFile) || (typeof file.type === 'string'))) {
        fileCount++;
      }
    }
  }

  filesRecursionCount(files);

  return { fileCount, hasDirectoryUpload };
};


/**
* @param {array} files
* @param {boolean} noPrompt
*
* @return {number} totalFiles
*/
const checkFileSize = (files, noPrompt) => {
  const tenMB = 10 * 1000 * 1000;
  const oneHundredMB = 100 * 1000 * 1000;
  const eighteenHundredMB = oneHundredMB * 18;
  const fileSizePrompt = [];
  const fileSizeNotAllowed = [];

  function filesRecursionCount(file) {
    if (Array.isArray(file)) {
      file.forEach((nestedFile) => {
        filesRecursionCount(nestedFile);
      });
    } else if (file.file && Array.isArray(file.file) && (file.file.length > 0)) {
      file.file.forEach((nestedFile) => {
        filesRecursionCount(nestedFile);
      });
    } else {
      const extension = file.name ? file.name.replace(/.*\./, '') : file.entry.fullPath.replace(/.*\./, '');

      if ((config.fileBrowser.excludedFiles.indexOf(extension) < 0) && ((file.entry && file.entry.isFile) || (typeof file.type === 'string'))) {
        if (!noPrompt) {
          if (file.size > oneHundredMB) {
            fileSizeNotAllowed.push(file);
          }

          if ((file.size > tenMB) && (file.size < oneHundredMB)) {
            fileSizePrompt.push(file);
          }
        } else if (file.size > eighteenHundredMB) {
          fileSizeNotAllowed.push(file);
        }
      }
    }
  }

  filesRecursionCount(files);

  return { fileSizeNotAllowed, fileSizePrompt };
};
export default {};

export { createFiles };
