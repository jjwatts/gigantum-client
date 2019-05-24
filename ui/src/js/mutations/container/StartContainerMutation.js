import {
  commitMutation,
  graphql,
} from 'react-relay';
import environment from 'JS/createRelayEnvironment';
import { updateTransitionState } from 'JS/redux/actions/labbook/labbook';

const mutation = graphql`
  mutation StartContainerMutation($input: StartContainerInput!){
    startContainer(input: $input){
      clientMutationId
    }
  }
`;

let tempID = 0;

export default function StartContainerMutation(
  owner,
  labbookName,
  callback,
) {
  const variables = {
    input: {
      labbookName,
      owner,
      clientMutationId: `${tempID++}`,
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
        updateTransitionState(labbookName, '');
        callback(response, error);
      },
      onError: err => console.error(err),

      updater: (store) => {


      },
    },
  );
}
