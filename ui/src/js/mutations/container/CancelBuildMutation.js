import {
  commitMutation,
  graphql,
} from 'react-relay';
import environment from 'JS/createRelayEnvironment';
// redux store
import { setErrorMessage } from 'JS/redux/actions/footer';

const mutation = graphql`
  mutation CancelBuildMutation($input: CancelBuildInput!){
    cancelBuild(input: $input){
      buildStopped
      message
    }
  }
`;

let tempID = 0;

export default function CancelBuildMutation(
  owner,
  labbookName,
  callback,
) {
  const variables = {
    input: {
      labbookName,
      owner,
      clientMutationId: tempID,
    },
  };
  tempID += 1;
  commitMutation(
    environment,
    {
      mutation,
      variables,
      onCompleted: (response, error) => {
        if (error) {
          console.log(error);
          setErrorMessage('ERROR: Failed to cancel build:', error);
        }

        callback(response, error);
      },
      onError: err => console.error(err),

      updater: (store) => {


      },
    },
  );
}
