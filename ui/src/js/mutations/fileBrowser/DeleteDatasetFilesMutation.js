import {
  commitMutation,
  graphql,
} from 'react-relay';
import RelayRuntime from 'relay-runtime';
import environment from 'JS/createRelayEnvironment';


const mutation = graphql`
  mutation DeleteDatasetFilesMutation($input: DeleteDatasetFilesInput!){
    deleteDatasetFiles(input: $input){
      success
      clientMutationId
    }
  }
`;

let tempID = 0;

export default function DeleteDatasetFilesMutation(
  connectionKey,
  datasetOwner,
  datasetName,
  datasetId,
  keys,
  section,
  edgesToDelete,
  callback,
) {
  const variables = {
    input: {
      datasetOwner,
      datasetName,
      keys,
      clientMutationId: `${tempID++}`,
    },
  };
  const recentConnectionKey = section === 'code'
    ? 'MostRecentCode_allFiles'
    : section === 'input'
      ? 'MostRecentInput_allFiles'
      : 'MostRecentOutput_allFiles';

  function sharedUpdater(store, datasetID, deletedID, connectionKey) {
    const userProxy = store.get(datasetID);

    const conn = RelayRuntime.ConnectionHandler.getConnection(
      userProxy,
      connectionKey,
    );

    if (conn) {
      RelayRuntime.ConnectionHandler.deleteNode(
        conn,
        deletedID,
      );
    }

    if (store.get(deletedID)) {
      store.delete(deletedID);
    }
  }

  commitMutation(
    environment,
    {
      mutation,
      variables,
      configs: [{
        type: 'NODE_DELETE',
        connectionKeys: [{
          key: connectionKey,
        }, {
          key: recentConnectionKey,
        }],
        parentId: datasetId,
        pathToConnection: ['dataset', 'allFiles'],
      }],
      onCompleted: (response, error) => {
        if (error) {
          console.log(error);
        }
        callback(response, error);
      },
      onError: err => console.error(err),

      updater: (store) => {
        edgesToDelete.forEach((edge) => {
          if (edge) {
            sharedUpdater(store, datasetId, edge.node.id, connectionKey);
            sharedUpdater(store, datasetId, edge.node.id, recentConnectionKey);

            store.delete(edge.node.id);
          }
        });
      },
      optimisticUpdater: (store) => {
        edgesToDelete.forEach((edge) => {
          if (edge) {
            sharedUpdater(store, datasetId, edge.node.id, connectionKey);
            sharedUpdater(store, datasetId, edge.node.id, recentConnectionKey);
            store.delete(edge.node.id);
          }
        });
      },
    },
  );
}
