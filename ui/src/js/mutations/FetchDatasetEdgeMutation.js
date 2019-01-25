import {
  commitMutation,
  graphql,
} from 'react-relay';
import environment from 'JS/createRelayEnvironment';


const mutation = graphql`
mutation FetchDatasetEdgeMutation($input: FetchDatasetEdgeInput!){
    fetchDatasetEdge(input: $input){
        newDatasetEdge{
            node{
                owner
                name
                visibility
                defaultRemote
            }
        }
        clientMutationId
    }
}
`;

let tempID = 0;


export default function FetchDatasetEdgeMutation(
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
