import {
  commitMutation,
  graphql,
} from 'react-relay';
import environment from 'JS/createRelayEnvironment';
import RelayRuntime from 'relay-runtime';
import uuidv4 from 'uuid/v4';


const mutation = graphql`
  mutation AddDatasetFileMutation($input: AddDatasetFileInput!){
    addDatasetFile(input: $input){
      newDatasetFileEdge{
        node{
          id
          isDir
          isLocal
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


function sharedUpdater(store, datasetId, data, node) {
  const datasetProxy = store.get(datasetId);
  if (datasetProxy) {
    const conn = RelayRuntime.ConnectionHandler.getConnection(
      datasetProxy,
      data,
    );

    if (conn) {
      const newEdge = RelayRuntime.ConnectionHandler.createEdge(
        store,
        conn,
        node,
        'newDatasetFileEdge',
      );

      RelayRuntime.ConnectionHandler.insertEdgeAfter(
        conn,
        newEdge,
      );
    }
  }
}


function deleteEdge(store, datasetID, deletedID, data) {
  const datasetProxy = store.get(datasetID);
  if (datasetProxy) {
    const conn = RelayRuntime.ConnectionHandler.getConnection(
      datasetProxy,
      data,
    );

    if (conn) {
      RelayRuntime.ConnectionHandler.deleteNode(
        conn,
        deletedID,
      );
    }
  }
}

export default function AddDatasetFileMutation(
  connectionKey,
  owner,
  datasetName,
  datasetId,
  filePath,
  chunk,
  accessToken,
  transactionId,
  callback,
) {
  const uploadables = [chunk.blob, accessToken];

  const id = uuidv4();
  const optimisticId = uuidv4();

  const variables = {
    input: {
      owner,
      datasetName,
      filePath,
      chunkUploadParams: {
        fileSizeKb: chunk.fileSizeKb,
        chunkSize: chunk.chunkSize,
        totalChunks: chunk.totalChunks,
        chunkIndex: chunk.chunkIndex,
        filename: chunk.filename,
        uploadId: chunk.uploadId,
      },
      transactionId,
      clientMutationId: id,
    },
  };

  commitMutation(
    environment,
    {
      mutation,
      variables,
      uploadables,
      configs: [{ // commented out until nodes are returned
        type: 'RANGE_ADD',
        parentID: datasetId,
        connectionInfo: [{
          key: connectionKey,
          rangeBehavior: 'append',
        }],
        edgeName: 'newDatasetFileEdge',
      }],
      onCompleted: (response, error) => {
        if (error) {
          console.log(error);
        }
        callback(response, error);
      },
      onError: err => console.error(err),
      optimisticUpdater: (store) => {
        const node = store.create(optimisticId, 'DatasetFile');

        node.setValue(optimisticId, 'id');
        node.setValue(false, 'isDir');
        node.setValue(filePath, 'key');
        node.setValue(0, 'modifiedAt');
        node.setValue(chunk.chunkSize, 'size');

        sharedUpdater(store, datasetId, connectionKey, node);
      },
      updater: (store, response) => {
        deleteEdge(store, datasetId, optimisticId, connectionKey);

        if (response.addDatasetFile && response.addDatasetFile.newDatasetFileEdge && response.addDatasetFile.newDatasetFileEdge.node) {
          const { id } = response.addDatasetFile.newDatasetFileEdge.node;

          const nodeExists = store.get(id);

          const responseKey = response.addDatasetFile.newDatasetFileEdge.node.key;
          const responseKeyArr = responseKey.split('/');
          let temp = '';

          responseKeyArr.forEach((key, index) => {
            if (!nodeExists || index !== responseKeyArr.length - 1) {
              let node;

              if (index === responseKeyArr.length - 1) {
                temp += key;
              } else {
                temp = `${temp + key}/`;
              }

              if (index === responseKeyArr.length - 1) {
                node = store.create(id, 'DatasetFile');
                node.setValue(response.addDatasetFile.newDatasetFileEdge.node.size, 'size');
                node.setValue(false, 'isDir');
                node.setValue(response.addDatasetFile.newDatasetFileEdge.node.id, 'id');
                node.setValue(response.addDatasetFile.newDatasetFileEdge.node.key, 'key');
                node.setValue(response.addDatasetFile.newDatasetFileEdge.node.modifiedAt, 'modifiedAt');
                sharedUpdater(store, datasetId, connectionKey, node);
              } else if (!store.get(temp)) {
                node = store.create(temp, 'DatasetFile');
                node.setValue(temp, 'id');
                node.setValue(true, 'isDir');
                node.setValue(temp, 'key');
                node.setValue(0, 'size');
                node.setValue(response.addDatasetFile.newDatasetFileEdge.node.modifiedAt, 'modifiedAt');
                sharedUpdater(store, datasetId, connectionKey, node);
              }
            }
          });
        }
      },
    },
  );
}
