import {
  commitMutation,
  graphql,
} from 'react-relay';
import environment from 'JS/createRelayEnvironment';

import FooterUtils from 'Components/shared/footer/FooterUtils';

const mutation = graphql`
  mutation PublishDatasetMutation($input: PublishDatasetInput!){
    publishDataset(input: $input){
      jobKey
      clientMutationId
    }
  }
`;

let tempID = 0;

export default function PublishDatasetMutation(
  owner,
  datasetName,
  setPublic,
  successCall,
  failureCall,
  callback,
) {
  const variables = {
    input: {
      setPublic,
      owner,
      datasetName,
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
        }

        callback(response, error);
      },
      onError: (err) => { console.error(err); },
      updater: (store, response) => {
        if (response) {
          FooterUtils.getJobStatus(response, 'publishDataset', 'jobKey', successCall, failureCall);
        }
      },
    },
  );
}
