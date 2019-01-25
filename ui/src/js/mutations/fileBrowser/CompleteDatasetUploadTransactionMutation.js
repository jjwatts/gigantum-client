import {
  commitMutation,
  graphql,
} from 'react-relay';
import environment from 'JS/createRelayEnvironment';
import uuidv4 from 'uuid/v4';


const mutation = graphql`
  mutation CompleteDatasetUploadTransactionMutation($input: CompleteDatasetUploadTransactionInput!){
    completeDatasetUploadTransaction(input: $input){
      clientMutationId
    }
  }
`;

// commented until fully implimented
// function sharedUpdater(store, datasetId, connectionKey, node) {

//   const datasetProxy = store.get(datasetId);
//   if(datasetProxy){
//     const conn = RelayRuntime.ConnectionHandler.getConnection(
//       datasetProxy,
//       connectionKey
//     );

//     if(conn){
//       const newEdge = RelayRuntime.ConnectionHandler.createEdge(
//         store,
//         conn,
//         node,
//         "newLabbookFileEdge"
//       )

//       RelayRuntime.ConnectionHandler.insertEdgeAfter(
//         conn,
//         newEdge
//       );
//     }
//   }
// }


//   function deleteEdge(store, datasetID, deletedID, connectionKey) {

//     const datasetProxy = store.get(datasetID);
//     if(datasetProxy){

//       const conn = RelayRuntime.ConnectionHandler.getConnection(
//         datasetProxy,
//         connectionKey,
//       );

//       if(conn){
//         RelayRuntime.ConnectionHandler.deleteNode(
//           conn,
//           deletedID,
//         );
//       }
//     }
//   }

export default function CompleteDatasetUploadTransactionMutation(
  connectionKey,
  owner,
  datasetName,
  cancel,
  rollback,
  transactionId,
  callback,
) {
  const id = uuidv4();

  const variables = {
    input: {
      owner,
      datasetName,
      cancel,
      rollback,
      transactionId,
      clientMutationId: id,
    },
  };


  commitMutation(
    environment,
    {
      mutation,
      variables,
      onCompleted: (response, error) => {
        if (error) {
          console.log(error);
        }
        callback(response, error);
      },
      onError: err => console.error(err),
      optimisticUpdater: (store) => {

      },
      updater: (store, response) => {

      },
    },
  );
}
