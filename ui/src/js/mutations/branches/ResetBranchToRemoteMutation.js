import {
  commitMutation,
  graphql,
} from 'react-relay';
import uuidV4 from 'uuid/v4';
import environment from 'JS/createRelayEnvironment';

const mutation = graphql`
  mutation ResetBranchToRemoteMutation($input: ResetBranchToRemoteInput!, $first: Int, $cursor: String, $skipPackages: Boolean!, $environmentSkip: Boolean!, $overviewSkip: Boolean!, $activitySkip: Boolean!, $codeSkip: Boolean!, $inputSkip: Boolean!, $outputSkip: Boolean!, $labbookSkip: Boolean!){
    resetBranchToRemote(input: $input){
      labbook{
        ...Labbook_labbook
      }
      clientMutationId
    }
  }
`;

export default function ResetBranchToRemoteMutation(
  owner,
  labbookName,
  callback,
) {
  const clientMutationId = uuidV4();
  const variables = {
    input: {
      owner,
      labbookName,
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
    skipPackages: true,
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
