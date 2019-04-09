import {
  commitMutation,
  graphql,
} from 'react-relay';
import environment from 'JS/createRelayEnvironment';


const mutation = graphql`
mutation FetchDatasetEdgeMutation($input: FetchDatasetEdgeInput!, $first: Int!, $cursor: String){
    fetchDatasetEdge(input: $input){
        newDatasetEdge{
            node{
                owner
                name
                visibility
                defaultRemote
                collaborators {
                  id
                  owner
                  name
                  collaboratorUsername
                  permission
                }
                canManageCollaborators
                ...Data_dataset
            }
        }
        clientMutationId
    }
}
`;

const tempID = 0;


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
    first: 10,
    cursor: null,
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
