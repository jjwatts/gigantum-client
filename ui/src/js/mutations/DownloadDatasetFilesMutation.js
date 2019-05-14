import {
  commitMutation,
  graphql,
} from 'react-relay';
import environment from 'JS/createRelayEnvironment';
// utils
import FooterUtils from 'Components/common/footer/FooterUtils';
import FooterCallback from 'Components/common/footer/utils/DownloadDatasetFiles';

const mutation = graphql`
mutation DownloadDatasetFilesMutation($input: DownloadDatasetFilesInput!){
    downloadDatasetFiles(input: $input){
        backgroundJobKey
        clientMutationId
    }
}
`;

let tempID = 0;


export default function DownloadDatasetFilesMutation(
  datasetOwner,
  datasetName,
  labbookName,
  labbookOwner,
  successCall,
  failureCall,
  keys,
  allKeys,
  callback,
) {
  const variables = {
    input: {
      datasetOwner,
      datasetName,
      clientMutationId: tempID++,
    },
  };
  if (allKeys) {
    variables.input.allKeys = allKeys;
  } else {
    variables.input.keys = keys;
  }
  if (labbookName) {
    variables.input.labbookName = labbookName;
  }
  if (labbookOwner) {
    variables.input.labbookOwner = labbookOwner;
  }

  commitMutation(environment, {
    mutation,
    variables,
    onCompleted: (response, error) => {
      if (error) {
        console.log(error);
      }
      const footerData = {
        result: response,
        type: 'downloadDatasetFiles',
        key: 'backgroundJobKey',
        FooterCallback,
        successCall,
        failureCall,
      };

      FooterUtils.getJobStatus(footerData);

      callback(error);
    },
    onError: err => console.error(err),
  });
}
