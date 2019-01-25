import {
  commitMutation,
  graphql,
} from 'react-relay';
import RelayRuntime from 'relay-runtime';
import environment from 'JS/createRelayEnvironment';

import { setErrorMessage } from 'JS/redux/reducers/footer';

const mutation = graphql`
  mutation MoveLabbookFileMutation($input: MoveLabbookFileInput!){
    moveLabbookFile(input: $input){
      updatedEdges{
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

let tempID = 0;

function sharedDeleteUpdater(store, labbookID, removeIds, connectionKey) {
  const labbookProxy = store.get(labbookID);
  if (labbookProxy) {
    removeIds.forEach((deletedID) => {
      const conn = RelayRuntime.ConnectionHandler.getConnection(
        labbookProxy,
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


export default function MoveLabbookFileMutation(
  connectionKey,
  owner,
  labbookName,
  labbookId,
  edge,
  srcPath,
  dstPath,
  section,
  removeIds,
  callback,
) {
  const variables = {
    input: {
      owner,
      labbookName,
      srcPath,
      dstPath,
      section,
      clientMutationId: `${tempID++}`,
    },
  };

  // TODO: remove this, key should propogate down from each section and get passed to the mutation data class
  const recentConnectionKey = section === 'code' ? 'MostRecentCode_allFiles' :
    section === 'input' ? 'MostRecentInput_allFiles' :
      'MostRecentOutput_allFiles';

  const configs = [{
    type: 'RANGE_ADD',
    parentID: labbookId,
    connectionInfo: [{
      key: connectionKey,
      rangeBehavior: 'append',
    }],
    edgeName: 'newLabbookFileEdge',
  }, {
    type: 'RANGE_ADD',
    parentID: labbookId,
    connectionInfo: [{
      key: recentConnectionKey,
      rangeBehavior: 'append',
    }],
    edgeName: 'newLabbookFileEdge',
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
          setErrorMessage(`ERROR: Could not Move labbook file ${srcPath}`, error);
        }
        callback(response, error);
      },
      onError: err => console.error(err),
      optimisticUpdater: (store) => {

        const labbookProxy = store.get(labbookId);

        if (labbookProxy && (edge.node !== null)) {
          const conn = RelayRuntime.ConnectionHandler.getConnection(
            labbookProxy,
            connectionKey,
          );

          const node = store.get(edge.node.id);
          node.setValue(edge.node.id, 'id');
          node.setValue(edge.node.isDir, 'isDir');
          node.setValue(dstPath, 'key');
          node.setValue(edge.node.modifiedAt, 'modifiedAt');
          node.setValue(edge.node.size, 'size');

          if (!store.get(edge.node.id)) {
            const newEdge = RelayRuntime.ConnectionHandler.createEdge(
              store,
              conn,
              node,
              'newLabbookFileEdge',
            );
            RelayRuntime.ConnectionHandler.insertEdgeAfter(
              conn,
              newEdge,
              edge.cursor,
            );
          }
        }
      },
      updater: (store, response) => {
        sharedDeleteUpdater(store, labbookId, removeIds, connectionKey);
        sharedDeleteUpdater(store, labbookId, removeIds, recentConnectionKey);
        if (response && response.moveLabbookFile && response.moveLabbookFile.updatedEdges) {
          response.moveLabbookFile.updatedEdges.forEach((edge) => {
            const labbookProxy = store.get(labbookId);

            if (labbookProxy && (edge.node !== null)) {
              const conn = RelayRuntime.ConnectionHandler.getConnection(
                labbookProxy,
                connectionKey,
              );
              const recentConn = RelayRuntime.ConnectionHandler.getConnection(
                labbookProxy,
                recentConnectionKey,
              );

              const node = store.get(edge.node.id) ? store.get(edge.node.id) : store.create(edge.node.id, 'LabbookFile');

              node.setValue(edge.node.id, 'id');
              node.setValue(edge.node.isDir, 'isDir');
              node.setValue(edge.node.key, 'key');
              node.setValue(edge.node.modifiedAt, 'modifiedAt');
              node.setValue(edge.node.size, 'size');
              const newEdge = RelayRuntime.ConnectionHandler.createEdge(
                store,
                conn,
                node,
                'newLabbookFileEdge',
              );
              RelayRuntime.ConnectionHandler.insertEdgeAfter(
                conn,
                newEdge,
                edge.cursor,
              );

              const newRecentEdge = RelayRuntime.ConnectionHandler.createEdge(
                store,
                recentConn,
                node,
                'newLabbookFileEdge',
              );
              RelayRuntime.ConnectionHandler.insertEdgeAfter(
                recentConn,
                newRecentEdge,
                edge.cursor,
              );
            }
          });
        }
      },

    },
  );
}
