// vendor
import uuidv4 from 'uuid/v4';
// utilities
import ChunkUploader from 'JS/utils/ChunkUploader';
import config from 'JS/config';
import FolderUpload from './FolderUpload';
import ignore from 'ignore';
import gitIgnoreJson from 'JS/data/gitignore.json';
// store
import {
  setErrorMessage,
  setWarningMessage,
  setInfoMessage,
  setUploadMessageSetter,
  setUploadMessageRemove,
} from 'JS/redux/reducers/footer';
import {
  setStartedUploading,
  setPauseUpload,
  setPauseUploadData,
  setResetChunkUpload,
} from 'JS/redux/reducers/labbook/fileBrowser/fileBrowserWrapper';
import { setUpdateDetailView } from 'JS/redux/reducers/labbook/labbook';
import store from 'JS/redux/store';

const ig = ignore().add(gitIgnoreJson.gitIgnore);
/**
*  @param {string} key - file key
*  @param {string} prefix - prefix is root folder -
*  creates a file using AddLabbookFileMutation by passing a blob
*  @return {}
*/
const createFiles = (files, prefix, mutationData, dropZoneProps, fileSizeData) => {
    let filenames = files.map((file) => {
      let filename = file.entry ? `D:/${file.entry.fullPath}` : file.name;
      return filename;
    });
    let filteredFileNames = ig.filter(filenames);
    let filteredFiles = files.filter((file) => {
      let filename = file.entry ? `D:/${file.entry.fullPath}` : file.name;
      return (filteredFileNames.indexOf(filename) > -1);
    });

    if (mutationData.section === 'code') {
      startFileUpload(filteredFiles, prefix, fileSizeData, mutationData, dropZoneProps);
    } else {
      const fileSizeData = checkFileSize(files, true);
      startFileUpload(filteredFiles, prefix, fileSizeData, mutationData, dropZoneProps);
    }

    if (filenames.length !== filteredFiles.length) {
      let ignoredFiles = filenames.filter(filename => filteredFileNames.indexOf(filename) < 0);
      let ignoredFilesString = ignoredFiles.join(', ').replace(/D:\//g, '');
      setWarningMessage(`The following files have been ignored: ${ignoredFilesString}`);
    }
};
/**
*  @param {Array:[Object]} folderFiles
*  @param {string} prefix
*  @param {number} totalFiles
*  @param {Object} mutationData
*  flattens file Array
*  filters file Array
*  kicks off upload function
*  @return {}
*/
const startFolderUpload = (folderFiles, prefix, totalFiles, mutationData) => {
  const flattenedFiles = [];
  // recursively flattens the file array
  function flattenFiles(filesArray) {
    if (Array.isArray(filesArray)) {
      filesArray.forEach((filesSubArray) => {
        flattenFiles(filesSubArray);
      });
    } else if (Array.isArray(filesArray.file) && (filesArray.file.length > 0)) {
      flattenFiles(filesArray.file);
    } else if (filesArray.entry) {
      flattenedFiles.push(filesArray);
    }
  }

  flattenFiles(folderFiles);

  const filterFiles = flattenedFiles.filter((fileItem) => {
    const extension = fileItem.name ? fileItem.name.replace(/.*\./, '') : fileItem.entry.fullPath.replace(/.*\./, '');

    return (config.fileBrowser.excludedFiles.indexOf(extension) < 0);
  });
  const count = 0;

  FolderUpload.uploadFiles(
    filterFiles,
    prefix,
    mutationData.labbookName,
    mutationData.owner,
    mutationData.section,
    mutationData.connection,
    mutationData.parentId,
    ChunkUploader.chunkFile,
    totalFiles,
    count,
  );
};
/**
*  @param {Array:[Object]} files
*  @param {string} prefix
*  @param {Object} fileSizeData
*  @param {Object} mutationData
*  @param {Object} dropZoneProps
*  gets file count and upload type
*  sets upload message
*  @return {}
*/
const startFileUpload = (files, prefix, fileSizeData, mutationData, dropZoneProps) => {
  let fileMetaData = getTotalFileLength(files),
    transactionId = uuidv4(),
    totalFiles = fileMetaData.fileCount - fileSizeData.fileSizeNotAllowed,
    hasDirectoryUpload = fileMetaData.hasDirectoryUpload,
    self = this,
    folderFiles = [];

  createFilesFooterMessage(totalFiles, hasDirectoryUpload, fileSizeData, mutationData);
  // loop through files and upload if file is a file;
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

        let deleteId = dropZoneProps.childrenState ? dropZoneProps.childrenState[file.name] : null;
        if (deleteId === null && dropZoneProps.files) {
          dropZoneProps.files.edges.forEach((edge) => {
            if (edge.node.key === file.name) {
              deleteId = edge.node.id;
            }
          });
        }

        const filepath = newKey;
        const data = {
          file,
          filepath,
          accessToken: localStorage.getItem('access_token'),
          transactionId,
          ...mutationData,
          username: mutationData.owner,
          connectionKey: mutationData.connection,
          favoriteConnectionKey: mutationData.favoriteConnection,
          deleteId,
        };

        ChunkUploader.chunkFile(data, (data) => {

        }, 0);
      }
    } else {
      folderFiles.push(file);
    }
  });

  if (folderFiles.length > 0) {
    startFolderUpload(folderFiles, prefix, totalFiles, mutationData);
  }
};


/**
* @param {Array:[Object]} files
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
    } else if (file && file.file && Array.isArray(file.file) && (file.file.length > 0)) {
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
*  @param {number} totalFiles
*  @param {boolean} hasDirectoryUpload
*  @param {Object} fileSizeData
*  @param {Object} mutationData
*  updates footer message depending on the type of upload
*/
const createFilesFooterMessage = (totalFiles, hasDirectoryUpload, fileSizeData, mutationData) => {
  if (totalFiles > 0) {
    setStartedUploading();
    setUploadMessageSetter(`Preparing Upload for ${totalFiles} files`, Math.random() * 10000, totalFiles);
  } else if (hasDirectoryUpload && (totalFiles === 0)) {
    setStartedUploading();
    setInfoMessage('Uploading Directories');
  } else if (fileSizeData.fileSizeNotAllowed.length > 0) {
    const fileSizePromptNames = fileSizeData.fileSizePrompt.map(file => file.name);
    const fileSizeNotAllowedNames = fileSizeData.fileSizeNotAllowed
      .map(file => file.name)
      .filter(name => fileSizePromptNames.indexOf(name) < 0);

    const fileSizeNotAllowedString = fileSizeNotAllowedNames.join(', ');

    if (fileSizeNotAllowedString.length > 0) {
      const size = mutationData.section === 'code' ? '100 MB' : '1.8 GB';
      const message = `Cannot upload files over ${size} to the ${mutationData.section} directory. The following files have not been added ${fileSizeNotAllowedString}`;

      setWarningMessage(message);
    }
  } else {
    setWarningMessage('Cannot upload these file types');
  }
};

 /**
  * @param {Array:[Object]} files
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
      } else if (file && file.file && Array.isArray(file.file) && (file.file.length > 0)) {
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

export default {
  createFiles,
  startFileUpload,
  startFolderUpload,
};
