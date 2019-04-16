import {
  commitMutation,
  graphql,
} from 'react-relay';
import environment from 'JS/createRelayEnvironment';
// redux store
import { setErrorMessage } from 'JS/redux/actions/footer';
// utils
import FooterUtils from 'Components/common/footer/FooterUtils';


const mutation = graphql`
  mutation BuildImageMutation($input: BuildImageInput!){
    buildImage(input: $input){
      clientMutationId
      backgroundJobKey
    }
  }
`;

let tempID = 0;

export default function BuildImageMutation(
  owner,
  labbookName,
  noCache,
  callback,
) {
  const variables = {
    input: {
      labbookName,
      owner,
      noCache,
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
          setErrorMessage('ERROR: Project failed to build:', error);
        }

        FooterUtils.getJobStatus(response, 'buildImage', 'backgroundJobKey');
        callback(response, error);
      },
      onError: err => console.error(err),

      updater: (store) => {


      },
    },
  );
}
