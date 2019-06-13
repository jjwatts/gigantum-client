import {
  commitMutation,
  graphql,
} from 'react-relay';
import environment from 'JS/createRelayEnvironment';

import FooterUtils from 'Components/common/footer/FooterUtils';

const mutation = graphql`
mutation ConfigureDatasetMutation($input: ConfigureDatasetInput!){
  configureDataset(input: $input){
        dataset{
          backendIsConfigured
          backendConfiguration{
            parameter
            description
            parameterType
            value
          }
        }
        isConfigured
        shouldConfirm
        errorMessage
        confirmMessage
        hasBackgroundJob
        backgroundJobKey
        clientMutationId
    }
}
`;

let tempID = 0;


export default function ConfigureDatasetMutation(
  datasetOwner,
  datasetName,
  parameters,
  confirm,
  successCall,
  failureCall,
  callback,
) {
  const variables = {
    input: {
      datasetOwner,
      datasetName,
      parameters,
    },
  };
  if (confirm !== null) {
    variables.input.confirm = confirm;
  }

  commitMutation(environment, {
    mutation,
    variables,
    onCompleted: (response, error) => {
      if (error) {
        console.log(error);
      }
      callback(response, error);
      if (response.configureDataset && response.configureDataset.backgroundJobKey) {
        FooterUtils.getJobStatus(response, 'configureDataset', 'backgroundJobKey', successCall, failureCall);
      }
    },
    onError: err => console.error(err),
  });
}
