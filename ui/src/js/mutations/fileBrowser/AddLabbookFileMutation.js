import {
  commitMutation,
  graphql,
} from 'react-relay';
import environment from 'JS/createRelayEnvironment';
import RelayRuntime from 'relay-runtime';
import uuidv4 from 'uuid/v4';


const mutation = graphql`
  mutation AddLabbookFileMutation($input: AddLabbookFileInput!){
    addLabbookFile(input: $input){
      newLabbookFileEdge{
        node{
          id
          isDir
          modifiedAt
          key
          size
        }
        cursor
      }
      clientMutationId
    }
  }
`;


function sharedUpdater(store, sectionId, connectionKey, node) {
  const sectionProxy = store.get(sectionId);
  if (sectionProxy) {
    const conn = RelayRuntime.ConnectionHandler.getConnection(
      sectionProxy,
      connectionKey,
    );
    if (conn) {
      const newEdge = RelayRuntime.ConnectionHandler.createEdge(
        store,
        conn,
        node,
        'LabbookFileEdge',
      );
      RelayRuntime.ConnectionHandler.insertEdgeAfter(
        conn,
        newEdge,
      );
    }
  }
}


function deleteEdge(store, labbookID, deletedID, connectionKey) {
  const sectionProxy = store.get(labbookID);
  if (sectionProxy) {
    const conn = RelayRuntime.ConnectionHandler.getConnection(
      sectionProxy,
      connectionKey,
    );

    if (conn) {
      RelayRuntime.ConnectionHandler.deleteNode(
        conn,
        deletedID,
      );
    }
  }
}


export default function AddLabbookFileMutation(
  connectionKey,
  owner,
  labbookName,
  sectionId,
  filePath,
  chunk,
  accessToken,
  section,
  transactionId,
  deleteId,
  callback,
) {
  const date = new Date();
  const size = chunk.fileSizeKb * 1000;
  const modifiedAt = (date.getTime() / 1000)
  const optimisticResponse = {
    addLabbookFile: {
      newLabbookFileEdge: {
        node: {
          id: optimisticId,
          isDir: false,
          key: filePath,
          modifiedAt,
          size,
        },
      },
    },
  };
  const uploadables = [chunk.blob, accessToken];

  const id = uuidv4();
  const tempString = transactionId + filePath;
  const tempId = tempString.replace(/\W/g, '');
  const optimisticId = window.btoa((tempId));

  const variables = {
    input: {
      owner,
      labbookName,
      filePath,
      chunkUploadParams: {
        fileSizeKb: chunk.fileSizeKb,
        chunkSize: chunk.chunkSize,
        totalChunks: chunk.totalChunks,
        chunkIndex: chunk.chunkIndex,
        filename: chunk.filename,
        uploadId: chunk.uploadId,
      },
      section,
      transactionId,
      clientMutationId: id,
    },
  };

  const recentConnectionKey = section === 'code' ? 'MostRecentCode_allFiles' :
    section === 'input' ? 'MostRecentInput_allFiles' :
      'MostRecentOutput_allFiles';
  commitMutation(
    environment,
    {
      mutation,
      variables,
      uploadables,
      optimisticResponse,
      configs: [],
      onCompleted: (response, error) => {
        if (error) {
          console.log(error);
        }
        callback(response, error);
      },
      onError: err => console.error(err),
      optimisticUpdater: (store) => {

        if (deleteId && store.get(deleteId)) {
          let node = store.get(deleteId)
          node.setValue(modifiedAt, 'modifiedAt');
          node.setValue(size, 'size');
        } else {
          if (store.get(optimisticId)) {
            deleteEdge(store, sectionId, optimisticId, connectionKey);
          }
          let nodeExists = store.get(optimisticId);
          const node = store.create(optimisticId, 'LabbookFile');
          node.setValue(optimisticId, 'id');
          node.setValue(false, 'isDir');
          node.setValue(filePath, 'key');
          node.setValue(modifiedAt, 'modifiedAt');
          node.setValue(size, 'size');
          sharedUpdater(store, sectionId, connectionKey, node);
        }
      },
      updater: (store, response) => {

        if (response.addLabbookFile && response.addLabbookFile.newLabbookFileEdge && response.addLabbookFile.newLabbookFileEdge.node) {
          deleteEdge(store, sectionId, optimisticId, connectionKey);
          deleteEdge(store, sectionId, optimisticId, recentConnectionKey);
          const { id } = response.addLabbookFile.newLabbookFileEdge.node;
          const nodeExists = store.get(id);

          const node = nodeExists ? store.get(id) : store.create(id, 'LabbookFile');

          node.setValue(response.addLabbookFile.newLabbookFileEdge.node.size, 'size');
          node.setValue(false, 'isDir');
          node.setValue(response.addLabbookFile.newLabbookFileEdge.node.id, 'id');
          node.setValue(response.addLabbookFile.newLabbookFileEdge.node.key, 'key');
          node.setValue(response.addLabbookFile.newLabbookFileEdge.node.modifiedAt, 'modifiedAt');

          sharedUpdater(store, sectionId, connectionKey, node);
          sharedUpdater(store, sectionId, recentConnectionKey, node);

        }
      },
    },
  );
}
