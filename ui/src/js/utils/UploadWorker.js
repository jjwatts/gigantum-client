import AddDatasetFileMutation from 'Mutations/fileBrowser/AddDatasetFileMutation';
import AddLabbookFileMutation from 'Mutations/fileBrowser/AddLabbookFileMutation';
import ImportLabbookMutation from 'Mutations/ImportLabbookMutation';
import ImportDatasetMutation from 'Mutations/ImportDatasetMutation';


/* eslint-disable */
const addFileUpload = (data) => {
  const { file } = data;
  const {
    connection,
    owner,
    labbookName,
    parentId,
    section,
  } = file.mutationData;
  const {
    accessToken,
    idToken,
    transactionId,
    chunkId,
  } = file;
  const {
    fullPath,
  } = file.file.entry;
  const path = `${file.path}${fullPath}`;

  const chunkStart = file.chunkSize * file.chunkIndex;
  const chunkEnd = (file.chunkSize * (file.chunkIndex + 1) < file.size)
    ? file.chunkSize * (file.chunkIndex + 1)
    : file.size;
  const blob = file.file.file.slice(chunkStart, chunkEnd);

  const chunk = {
    blob,
    fileSizeKb: file.size / 1000,
    chunkSize: file.chunkSize,
    totalChunks: file.totalChunks,
    chunkIndex: file.chunkIndex,
    filename: file.file.file.name,
    uploadId: transactionId,
  };

  const callback = (response, error) => {
    if(response) {
      const data = { response, chunkId };
      postMessage(data);
    } else {
      postMessage(error);
    }
  };


  if((connection === "CodeBrowser_allFiles")
    || (connection === "InputBrowser_allFiles")
    || (connection === "OutputBrowser_allFiles")) {

    AddLabbookFileMutation(
      connection,
      owner,
      labbookName,
      parentId,
      path,
      chunk,
      accessToken,
      idToken,
      section,
      transactionId,
      [],
      callback,
    );
  } else if (connection === "DataBrowser_allFiles") {

    AddDatasetFileMutation(
      connection,
      owner,
      labbookName,
      parentId,
      path,
      chunk,
      accessToken,
      idToken,
      transactionId,
      callback,
    );
  }
}

const importFileUpload = (data, connection) => {
  const { file, mutationData } = data;
  const {
    accessToken,
    idToken,
    transactionId,
    chunkId,
  } = file;
  const {
    fullPath,
  } = file.file.entry;
  const path = `${file.path}${fullPath}`;

  const chunkStart = file.chunkSize * file.chunkIndex;
  const chunkEnd = (file.chunkSize * (file.chunkIndex + 1) < file.size)
    ? file.chunkSize * (file.chunkIndex + 1)
    : file.size;
  const blob = file.file.file.slice(chunkStart, chunkEnd);

  const chunk = {
    blob,
    fileSizeKb: file.size / 1000,
    chunkSize: file.chunkSize,
    totalChunks: file.totalChunks,
    chunkIndex: file.chunkIndex,
    filename: file.file.file.name,
    uploadId: transactionId,
  };

  const callback = (response, error) => {
    if(response) {
      const data = { response, chunkId };
      postMessage(data);
    } else {
      postMessage(error);
    }
  };

  if(connection === "ImportLabbookMutation") {

    ImportLabbookMutation(
      chunk,
      accessToken,
      idToken,
      callback,
    );
  } else if (connection === "ImportDatasetMutation") {

    ImportDatasetMutation(
      chunk,
      accessToken,
      idToken,
      callback,
      callback,
    );
  }
}


self.addEventListener('message', (evt) => {
  const { data } = evt;
  const { connection } = data.file.mutationData;
  if (connection.indexOf('allFiles') > -1) {
     addFileUpload(data);
  } else {
    importFileUpload(data, connection);
  }
});
