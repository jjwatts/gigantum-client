import {
  commitMutation,
  graphql,
} from 'react-relay';
import RelayRuntime from 'relay-runtime';
import environment from 'JS/createRelayEnvironment';


const mutation = graphql`
  mutation DeleteLabbookFilesMutation($input: DeleteLabbookFilesInput!){
    deleteLabbookFiles(input: $input){
      success
      clientMutationId
    }
  }
`;

let tempID = 0;

export default function DeleteLabbookFilesMutation(
  connectionKey,
  owner,
  labbookName,
  labbookId,
  filePaths,
  section,
  edgesToDelete,
  callback,
) {
  const variables = {
    input: {
      owner,
      labbookName,
      filePaths,
      section,
      clientMutationId: `${tempID++}`,
    },
  };

  function sharedUpdater(store, labbookID, deletedID, connectionKey) {
    const userProxy = store.get(labbookID);

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
        }],
        parentId: labbookId,
        pathToConnection: ['labbook', 'allFiles'],
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
            sharedUpdater(store, labbookId, edge.node.id, connectionKey);

            store.delete(edge.node.id);
          }
        });
      },
      optimisticUpdater: (store) => {
        edgesToDelete.forEach((edge) => {
          if (edge) {
            sharedUpdater(store, labbookId, edge.node.id, connectionKey);
            store.delete(edge.node.id);
          }
        });
      },
    },
  );
}
