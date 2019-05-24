// vendor
import uuidv4 from 'uuid/v4';
// mutations
import ImportLabbookMutation from 'Mutations/ImportLabbookMutation';
import ImportDatasetMutation from 'Mutations/ImportDatasetMutation';
import AddLabbookFileMutation from 'Mutations/fileBrowser/AddLabbookFileMutation';
import AddDatasetFileMutation from 'Mutations/fileBrowser/AddDatasetFileMutation';
import CompleteBatchUploadTransactionMutation from 'Mutations/fileBrowser/CompleteBatchUploadTransactionMutation';
import CompleteDatasetUploadTransactionMutation from 'Mutations/fileBrowser/CompleteDatasetUploadTransactionMutation';
import store from 'JS/redux/store';
import {
  setUploadMessageUpdate,
  setUploadMessageRemove,
  setWarningMessage,
  setErrorMessage,
} from 'JS/redux/actions/footer';
import { setFinishedUploading, setPauseChunkUpload } from 'JS/redux/actions/shared/fileBrowser/fileBrowserWrapper';
import { setIsProcessing } from 'JS/redux/actions/dataset/dataset';
import config from 'JS/config';

const uploadImportChunk = (file, chunk, accessToken, getChunkCallback, type) => {
  if (type === 'dataset') {
    ImportDatasetMutation(chunk.blob, chunk, accessToken, (result, error) => {
      if (result && !error) {
        getChunkCallback(file, result);
      } else {
        getChunkCallback(error);
      }
    });
  } else {
    ImportLabbookMutation(chunk.blob, chunk, accessToken, (result, error) => {
      if (result && !error) {
        getChunkCallback(file, result);
      } else {
        getChunkCallback(error);
      }
    });
  }
};

const updateTotalStatus = (file, labbookName, owner, transactionId, section) => {
  const fileCount = store.getState().footer.fileCount + 1;
  const totalFiles = store.getState().footer.totalFiles;
  const progressBarPercentage = ((fileCount / totalFiles) * 100);
  setUploadMessageUpdate(`Uploaded ${fileCount} of ${totalFiles} files`, fileCount, progressBarPercentage);

  if (fileCount === totalFiles) {
    setUploadMessageUpdate(`Uploaded ${totalFiles} files. Please wait while upload is finalizing.`, null, progressBarPercentage);
    if (section === 'data') {
      setIsProcessing(true);
      CompleteDatasetUploadTransactionMutation(
        'connectionKey',
        owner,
        labbookName,
        false,
        false,
        transactionId,
        (response, error) => {
          setTimeout(() => {
            setIsProcessing(false);
            setFinishedUploading();
          }, 1100);
          setUploadMessageRemove(`Uploaded ${totalFiles} files. Please wait while upload is finalizing.`, null, progressBarPercentage);
        },
      );
    } else {
      CompleteBatchUploadTransactionMutation(
        'connectionKey',
        owner,
        labbookName,
        false,
        false,
        transactionId,
        (response, error) => {
          setFinishedUploading();
          setUploadMessageRemove(`Uploaded ${totalFiles} files. Please wait while upload is finalizing.`, null, progressBarPercentage);
        },
      );
    }
  }
};

const updateChunkStatus = (file, chunkData, labbookName, owner, transactionId, section) => {
  const {
    fileSizeKb,
    chunkSize,
  } = chunkData;
  const chunkIndex = chunkData.chunkIndex + 1;
  const uploadedChunkSize = ((chunkSize / 1000) * chunkIndex) > fileSizeKb ? config.humanFileSize(fileSizeKb * 1000) : config.humanFileSize((chunkSize) * chunkIndex);
  const fileSize = config.humanFileSize(fileSizeKb * 1000);
  setUploadMessageUpdate(`${uploadedChunkSize} of ${fileSize} files`, 1, (((chunkSize * chunkIndex) / (fileSizeKb * 1000)) * 100));

  if ((chunkSize * chunkIndex) >= (fileSizeKb * 1000)) {
    setUploadMessageUpdate('Please wait while upload is finalizing.', null, (((chunkSize * chunkIndex) / (fileSizeKb * 1000)) * 100));
    if (section === 'data') {
      setIsProcessing(true);
      CompleteDatasetUploadTransactionMutation(
        'connectionKey',
        owner,
        labbookName,
        false,
        false,
        transactionId,
        (response, error) => {
          setTimeout(() => {
            setIsProcessing(false);
            setFinishedUploading();
          }, 1100);
          setUploadMessageRemove('Please wait while upload is finalizing.', null, (((chunkSize * chunkIndex) / (fileSizeKb * 1000)) * 100));
        },
      );
    } else {
      CompleteBatchUploadTransactionMutation(
        'connectionKey',
        owner,
        labbookName,
        false,
        false,
        transactionId,
        (response, error) => {
          setFinishedUploading();
          setUploadMessageRemove('Please wait while upload is finalizing.', null, (((chunkSize * chunkIndex) / (fileSizeKb * 1000)) * 100));
        },
      );
    }
  }
};

const uploadFileBrowserChunk = (data, chunkData, file, chunk, accessToken, username, filepath, section, getChunkCallback, componentCallback, type) => {
  const { footer, fileBrowser } = store.getState();
  if (fileBrowser.pause || (footer.totalFiles > 0)) {
    const cbFunction = (result, error) => {
      if (result && !error) {
        getChunkCallback(file, result);
        if (store.getState().footer.totalFiles > 1) {
          const lastChunk = (chunkData.totalChunks - 1) === chunkData.chunkIndex;

          if (lastChunk) {
            updateTotalStatus(file, data.labbookName, username, data.transactionId, section);
          }
        } else {
          updateChunkStatus(file, chunkData, data.labbookName, username, data.transactionId, section);
        }
      } else {
        const errorBody = error.length && error[0].message ? error[0].message : error;
        setErrorMessage(errorBody);
      }
    };

    if (section === 'data') {
      AddDatasetFileMutation(
        data.connectionKey,
        username,
        data.labbookName,
        data.parentId,
        filepath,
        chunk,
        accessToken,
        data.transactionId,
        cbFunction,
      );
    } else {
      AddLabbookFileMutation(
        data.connectionKey,
        username,
        data.labbookName,
        data.parentId,
        filepath,
        chunk,
        accessToken,
        section,
        data.transactionId,
        [],
        cbFunction,
      );
    }
  } else if (chunk.fileSizeKb > (48 * 1000)) {
    setPauseChunkUpload(data, chunkData, section, username);
  }
};

const ChunkUploader = {
  /*
    @param {object} data includes file filepath username and accessToken
  */
  chunkFile: (data, postMessage, passedChunkIndex) => {

    const {
      file,
      filepath,
      username,
      section,
    } = data;


    const componentCallback = (response) => { // callback to trigger postMessage from initializer
      postMessage(response, false);
    };

    const id = uuidv4();
    const chunkSize = 1000 * 1000 * 48;
    const fileSize = file.size;
    const fileSizeKb = Math.round(fileSize / 1000, 10);
    let fileLoadedSize = 0;
    let chunkIndex = passedChunkIndex || 0;
    const totalChunks = (file.size === 0) ? 1 : Math.ceil(file.size / chunkSize);

    /*
      @param{object, object} response result
    */
    const getChunk = (response, result) => {
      if (response && response.name) { // checks if response is a file
        const sliceUpperBound = (fileSize > (fileLoadedSize + chunkSize))
          ? (fileLoadedSize + chunkSize)
          : ((fileSize - fileLoadedSize) + fileLoadedSize);


        const blob = file.slice(fileLoadedSize, sliceUpperBound);

        fileLoadedSize += chunkSize;

        chunkIndex++;

        const chunkData = {
          blob,
          fileSizeKb,
          chunkSize,
          totalChunks,
          chunkIndex: chunkIndex - 1,
          filename: file.name,
          uploadId: id,
        };
        if (chunkIndex <= totalChunks) { // if  there is still chunks to process do next chunk
          // select type of mutation
          if (file.name.indexOf('.lbk') > -1 || file.name.indexOf('.zip') > -1) {
            if (!data.connectionKey) {
              uploadImportChunk(
                file,
                chunkData,
                data.accessToken,
                getChunk,
                data.type,
              );
              postMessage(chunkData, false); // post progress back to worker instantiator file
            }
          } else {
            uploadFileBrowserChunk(
              data,
              chunkData,
              file,
              chunkData,
              data.accessToken,
              username,
              filepath,
              section,
              getChunk,
              componentCallback,
            );

            postMessage(chunkData, false);
            // }else{
            //   postMessage(chunkData, true)
            // }
          }
        } else if (result) { // completes chunk upload task
          componentCallback(result);
        } else { // chunk upload fails
          componentCallback(response);
        }
      } else { // chunk upload fails
        componentCallback(response);
      }
    };

    getChunk(file);
  },
};
/*
  @param: {event} evt
  waits for data to be passed before starting chunking
*/

export default ChunkUploader;
