import {
  commitMutation,
  graphql,
} from 'react-relay';
import environment from 'JS/createRelayEnvironment';


const mutation = graphql`
mutation FetchLabbookEdgeMutation($input: FetchLabbookEdgeInput!, $first: Int!, $cursor: String, $hasNext: Boolean!, $environmentSkip: Boolean!, $overviewSkip: Boolean!, $activitySkip: Boolean!, $codeSkip: Boolean!, $inputSkip: Boolean!, $outputSkip: Boolean!, $labbookSkip: Boolean!){
  fetchLabbookEdge(input: $input){
    newLabbookEdge{
      node {
        ...Labbook_labbook
        collaborators {
          id
          owner
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


export default function FetchLabbookEdgeMutation(
  owner,
  labbookName,
  callback,
) {
  const variables = {
    input: {
      owner,
      labbookName,
    },
    first: 10,
    cursor: null,
    hasNext: false,
    overviewSkip: false,
    activitySkip: false,
    environmentSkip: false,
    codeSkip: false,
    inputSkip: false,
    outputSkip: false,
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
