import {
  commitMutation,
  graphql,
} from 'react-relay';
import environment from 'JS/createRelayEnvironment';


const mutation = graphql`
mutation DownloadDatasetFilesMutation($input: DownloadDatasetFilesInput!){
    downloadDatasetFiles(input: $input){
        updatedFileEdges{
            node{
              isLocal
            }
        }
        statusMessage
        clientMutationId
    }
}
`;

let tempID = 0;


export default function DownloadDatasetFilesMutation(
  owner,
  datasetName,
  labbookName,
  labbookOwner,
  keys,
  allKeys,
  callback,
) {
  const variables = {
    input: {
      owner,
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
      callback(error);
    },
    onError: err => console.error(err),
  });
}
