import {
  commitMutation,
  graphql,
} from 'react-relay';
import environment from 'JS/createRelayEnvironment';
// store
import { setErrorMessage } from 'JS/redux/reducers/footer';

const mutation = graphql`
  mutation AddDatasetCollaboratorMutation($input: AddDatasetCollaboratorInput!){
    addDatasetCollaborator(input: $input){
      updatedDataset{
        id
        collaborators
      }
      clientMutationId
    }
  }
`;

let tempID = 0;

export default function AddCollaboratorMutation(
  datasetName,
  owner,
  username,
  callback,
) {
  const variables = {
    input: {
      datasetName,
      owner,
      username,
      clientMutationId: tempID++,
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
          setErrorMessage(`ERROR: Could not add Collaborator ${username}`, error);
        }
        callback(response, error);
      },
      onError: err => console.error(err),
    },
  );
}
