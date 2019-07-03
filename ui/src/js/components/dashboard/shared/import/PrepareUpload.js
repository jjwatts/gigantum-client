// vendor
import uuidv4 from 'uuid/v4';
// store
import {
  setUploadMessageUpdate,
  setUploadMessageRemove,
  setWarningMessage,
} from 'JS/redux/actions/footer';
import {
  setFileBrowserLock,
} from 'JS/redux/actions/labbook/labbook';
// utils
import MutlithreadUploader from 'JS/utils/MultithreadUploader';


/**
  * @param {array} files
  * removes files not allowed for upload
  * @return {array}
*/
const removeExcludedFiles = (files) => {
  const filesNotAllowedList = [];
  const newFileArray = files.filter((fileItem) => {
    const extension = fileItem.file.name
      ? fileItem.file.name.replace(/.*\./, '')
      : fileItem.entry.fullPath.replace(/.*\./, '');
    const fileAllowed = ((extension === 'zip') || (extension === 'lbk'));

    if (!fileAllowed) {
      filesNotAllowedList.push(fileItem.file.name);
    }

    return fileAllowed;
  });


  if (filesNotAllowedList.length > 0) {
    const filesNotAllowed = filesNotAllowedList.join(', ');
    setWarningMessage(`The following files are not allowed ${filesNotAllowed}`);
  }

  return newFileArray;
};

/**
  * @param {object} file
  * @param {string} typeOfUpload
  * @param {function} buildImage
  * @param {object} state
  * @param {object} history
  * starts upload process and triggers import
  *
  * @return {array}
*/
const prepareUpload = (file, typeOfUpload, buildImage, state, history) => {
  const newFileArray = removeExcludedFiles([
    {
      file,
      entry: {
        fullPath: file.name,
        name: file.name,
      },
    },
  ]);


  const uploadInstance = new MutlithreadUploader({
    files: newFileArray,
    path: '',
    mutationData: {
      connection: typeOfUpload,
    },
    maxThreads: 4,
    refetch: () => {},
  });


  /**
    * @param {object} evt
    * function to warn user on reload or navigating away from the user
    *
    * @return {array}
  */
  const navigateConfirm = (evt) => {
    evt.preventDefault();
    evt.returnValue = '';
    return '';
  };

  /**
    * @param {object} response
    * triggers when upolad has finished
    * builds image and redirects to new project
    *
    * @return {array}
  */
  const finishedCallback = (response) => {
    const {
      name,
      owner,
    } = state.ready;

    window.removeEventListener('beforeunload', navigateConfirm);
    setFileBrowserLock(false);
    setUploadMessageRemove('Completed Import');

    if (response.data.jobStatus.status === 'finished') {
      if (buildImage) {
        buildImage(
          name,
          owner,
          uuidv4(),
        );
      }

      history.replace(`/projects/${owner}/${name}`);
    }
  };

  window.addEventListener('beforeunload', navigateConfirm);
  uploadInstance.startUpload(finishedCallback);

  setFileBrowserLock(true);
  setUploadMessageUpdate('Uploading import file, 0% complete');
};

export default prepareUpload;
