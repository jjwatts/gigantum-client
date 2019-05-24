import {
  commitMutation,
  graphql,
} from 'react-relay';
import uuidV4 from 'uuid/v4';
import environment from 'JS/createRelayEnvironment';

const mutation = graphql`
  mutation WorkonExperimentalBranchMutation($input: WorkonBranchInput!, $first: Int, $cursor: String, $hasNext: Boolean!, $environmentSkip: Boolean!, $overviewSkip: Boolean!, $activitySkip: Boolean!, $codeSkip: Boolean!, $inputSkip: Boolean!, $outputSkip: Boolean!, $labbookSkip: Boolean!){
    workonExperimentalBranch(input: $input){
      labbook{
        id
        isDeprecated
        shouldMigrate
        ...Labbook_labbook
      }
      clientMutationId
    }
  }
`;

export default function WorkonExperimentalBranchMutation(
  owner,
  labbookName,
  branchName,
  callback,
) {
  const clientMutationId = uuidV4();
  const variables = {
    input: {
      owner,
      labbookName,
      branchName,
      clientMutationId,
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
    labbookSkip: false,
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
      },
    },
  );
}
