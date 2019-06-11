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
  idToken,
  section,
  transactionId,
  deleteId,
  callback,
) {
  const date = new Date();
  const size = chunk.fileSizeKb * 1000;
  const modifiedAt = (date.getTime() / 1000);
  const tempString = transactionId + filePath;
  const tempId = tempString.replace(/\W/g, '');
  /* eslint-disable */
  const optimisticId = self ? self.btoa((tempId)) : self.btoa((tempId));
  /* eslint-enable */
  const clientMutationId = uuidv4();
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
        cursor: '',
      },
      clientMutationId,
    },
  };
  const uploadables = [chunk.blob, accessToken, idToken];

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
      clientMutationId,
    },
  };
  // TODO remove this, connections should be passed down from section
  const recentConnectionKey = section === 'code'
    ? 'MostRecentCode_allFiles'
    : section === 'input' ? 'MostRecentInput_allFiles'
      : 'MostRecentOutput_allFiles';
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
      updater: (store, response) => {
        if (response.addLabbookFile
          && response.addLabbookFile.newLabbookFileEdge
          && response.addLabbookFile.newLabbookFileEdge.node) {

          const responseNode = response.addLabbookFile.newLabbookFileEdge.node;
          deleteEdge(store, sectionId, optimisticId, connectionKey);
          deleteEdge(store, sectionId, optimisticId, recentConnectionKey);
          const { id } = responseNode;
          const nodeExists = store.get(id);

          const node = nodeExists ? store.get(id) : store.create(id, 'LabbookFile');

          node.setValue(responseNode.size, 'size');
          node.setValue(false, 'isDir');
          node.setValue(responseNode.id, 'id');
          node.setValue(responseNode.key, 'key');
          node.setValue(responseNode.modifiedAt, 'modifiedAt');

          sharedUpdater(store, sectionId, connectionKey, node);
          sharedUpdater(store, sectionId, recentConnectionKey, node);
        }
      },
    },
  );
}
