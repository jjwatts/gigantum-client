import {
  commitMutation,
  graphql,
} from 'react-relay';
import environment from 'JS/createRelayEnvironment';


const mutation = graphql`
mutation FetchDatasetFilesMutation($input: FetchDatasetEdgeInput!){
    fetchDatasetEdge(input: $input){
        newDatasetEdge{
          node {
            allFiles {
              edges {
                node {
                  isLocal
                }
              }
            }
          }
        }
        clientMutationId
    }
}
`;

const tempID = 0;


export default function FetchDatasetFilesMutation(
  owner,
  datasetName,
  callback,
) {
  const variables = {
    input: {
      owner,
      datasetName,
    },
  };
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
