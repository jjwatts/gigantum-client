import {
  commitMutation,
  graphql,
} from 'react-relay';
import environment from 'JS/createRelayEnvironment';
import uuidv4 from 'uuid/v4';


const mutation = graphql`
  mutation CompleteDatasetUploadTransactionMutation($input: CompleteDatasetUploadTransactionInput!){
    completeDatasetUploadTransaction(input: $input){
      clientMutationId,
      backgroundJobKey
    }
  }
`;

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
    },
  );
}
