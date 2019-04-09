import {
  commitMutation,
  graphql,
} from 'react-relay';
import RelayRuntime from 'relay-runtime';
import environment from 'JS/createRelayEnvironment';

import { setErrorMessage } from 'JS/redux/reducers/footer';

const mutation = graphql`
  mutation MoveDatasetFileMutation($input: MoveDatasetFileInput!){
    moveDatasetFile(input: $input){
      updatedEdges{
        node{
            id
            isDir
            modifiedAt
            isLocal
            key
            size
          }
          cursor
      }
      clientMutationId
    }
  }
`;

let tempID = 0;

function sharedDeleteUpdater(store, datasetID, removeIds, connectionKey) {
  const datasetProxy = store.get(datasetID);
  if (datasetProxy) {
    removeIds.forEach((deletedID) => {
      const conn = RelayRuntime.ConnectionHandler.getConnection(
        datasetProxy,
        connectionKey,
      );

      if (conn) {
        RelayRuntime.ConnectionHandler.deleteNode(
          conn,
          deletedID,
        );
        store.delete(deletedID);
      }
    });
  }
}


export default function MoveDatasetFileMutation(
  connectionKey,
  datasetOwner,
  datasetName,
  datasetId,
  edge,
  srcPath,
  dstPath,
  section,
  removeIds,
  callback,
) {
  const variables = {
    input: {
      datasetOwner,
      datasetName,
      srcPath,
      dstPath,
      clientMutationId: `${tempID++}`,
    },
  };

  // TODO: remove this, key should propogate down from each section and get passed to the mutation data class
  const recentConnectionKey = section === 'code' ? 'MostRecentCode_allFiles'
    : section === 'input' ? 'MostRecentInput_allFiles'
      : 'MostRecentOutput_allFiles';

  const configs = [{
    type: 'RANGE_ADD',
    parentID: datasetId,
    connectionInfo: [{
      key: connectionKey,
      rangeBehavior: 'append',
    }],
    edgeName: 'newDatasetFileEdge',
  }, {
    type: 'RANGE_ADD',
    parentID: datasetId,
    connectionInfo: [{
      key: recentConnectionKey,
      rangeBehavior: 'append',
    }],
    edgeName: 'newDatasetFileEdge',
  }];

  if (removeIds && removeIds.length) {
    removeIds.forEach((id) => {
      configs.unshift({
        type: 'NODE_DELETE',
        deletedIDFieldName: id,
      });
    });
  }


  commitMutation(
    environment,
    {
      mutation,
      variables,
      onCompleted: (response, error) => {
        if (error) {
          console.log(error);
          setErrorMessage(`ERROR: Could not Move dataset file ${srcPath}`, error);
        }
        callback(response, error);
      },
      onError: err => console.error(err),
      optimisticUpdater: (store) => {
        const datasetProxy = store.get(datasetId);

        if (datasetProxy && (edge.node !== null)) {
          const conn = RelayRuntime.ConnectionHandler.getConnection(
            datasetProxy,
            connectionKey,
          );

          const node = store.get(edge.node.id);
          node.setValue(edge.node.id, 'id');
          node.setValue(edge.node.isDir, 'isDir');
          node.setValue(dstPath, 'key');
          node.setValue(edge.node.modifiedAt, 'modifiedAt');
          node.setValue(edge.node.size, 'size');
          const newEdge = RelayRuntime.ConnectionHandler.createEdge(
            store,
            conn,
            node,
            'newDatasetFileEdge',
          );
          RelayRuntime.ConnectionHandler.insertEdgeAfter(
            conn,
            newEdge,
            edge.cursor,
          );
        }
      },
      updater: (store, response) => {
        sharedDeleteUpdater(store, datasetId, removeIds, connectionKey);
        sharedDeleteUpdater(store, datasetId, removeIds, recentConnectionKey);
        if (response && response.moveDatasetFile && response.moveDatasetFile.updatedEdges) {
          response.moveDatasetFile.updatedEdges.forEach((edge) => {
            const datasetProxy = store.get(datasetId);

            if (datasetProxy && (edge.node !== null)) {
              const conn = RelayRuntime.ConnectionHandler.getConnection(
                datasetProxy,
                connectionKey,
              );

              const node = store.get(edge.node.id) ? store.get(edge.node.id) : store.create(edge.node.id, 'DatasetFile');

              node.setValue(edge.node.id, 'id');
              node.setValue(edge.node.isDir, 'isDir');
              node.setValue(edge.node.key, 'key');
              node.setValue(edge.node.modifiedAt, 'modifiedAt');
              node.setValue(edge.node.size, 'size');
              const newEdge = RelayRuntime.ConnectionHandler.createEdge(
                store,
                conn,
                node,
                'newDatasetFileEdge',
              );
              RelayRuntime.ConnectionHandler.insertEdgeAfter(
                conn,
                newEdge,
                edge.cursor,
              );
            }
          });
        }
      },

    },
  );
}
