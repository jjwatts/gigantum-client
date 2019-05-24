import {
  commitMutation,
  graphql,
} from 'react-relay';
import environment from 'JS/createRelayEnvironment';


const mutation = graphql`
mutation FetchDatasetEdgeMutation($input: FetchDatasetEdgeInput!, $first: Int!, $cursor: String, $overviewSkip: Boolean!, $activitySkip: Boolean!, $dataSkip: Boolean!, $datasetSkip: Boolean!){
    fetchDatasetEdge(input: $input){
        newDatasetEdge{
            node{
                ...Dataset_dataset
                collaborators {
                  id
                  owner
                  name
                  collaboratorUsername
                  permission
                }
                canManageCollaborators
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
    datasetSkip: false,
    dataSkip: false,
    overviewSkip: false,
    activitySkip: false,
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
