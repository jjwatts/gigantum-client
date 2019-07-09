import {
  commitMutation,
  graphql,
} from 'react-relay';
import environment from 'JS/createRelayEnvironment';
import uuidv4 from 'uuid/v4';
// redux store
import { setErrorMessage } from 'JS/redux/actions/footer';
// utils
import FooterUtils from 'Components/common/footer/FooterUtils';
import footerCallback from 'Components/common/footer/utils/BuildImage';


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
  buildData,
  callback,
) {
  const variables = {
    input: {
      labbookName,
      owner,
      noCache: (buildData && buildData.noCache) || false,
      clientMutationId: tempID++,
    },
  };
  const id = uuidv4();
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
        const footerData = {
          id: (buildData && buildData.overrideId) || id,
          result: response,
          type: 'buildImage',
          key: 'backgroundJobKey',
          footerCallback,
          hideFooter: buildData && buildData.hideFooter,
        };
        FooterUtils.getJobStatus(footerData);
        callback(response, error, id);
      },
      onError: err => console.error(err),

      updater: (store) => {


      },
    },
  );
}
