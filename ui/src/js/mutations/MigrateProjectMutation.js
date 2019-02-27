import {
  commitMutation,
  graphql,
} from 'react-relay';
import environment from 'JS/createRelayEnvironment';
// store
import { setErrorMessage } from 'JS/redux/reducers/footer';

const mutation = graphql`
  mutation MigrateProjectMutation($input: MigrateLabbookSchemaInput!, $first: Int, $cursor: String, $hasNext: Boolean!){
    migrateLabbookSchema(input: $input){
      labbook{
        ...Labbook_labbook
      }
      clientMutationId
    }
  }
`;

let tempID = 0;

export default function MigrateProjectMutation(
  owner,
  labbookName,
  callback,
) {
  const variables = {
    input: {
      owner,
      labbookName,
      clientMutationId: tempID++,
    },
    first: 10,
    cursor: null,
    hasNext: false,
  };
  commitMutation(
    environment,
    {
      mutation,
      variables,
      onCompleted: (response, error) => {
        if (error) {
          console.log(error);
          setErrorMessage('ERROR: Could not migrate project', error);
        }
        callback(response, error);
      },
      onError: err => console.error(err),
    },
  );
}
