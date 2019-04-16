import {
  commitMutation,
  graphql,
} from 'react-relay';
import environment from 'JS/createRelayEnvironment';
import uuidv4 from 'uuid/v4';
import { setMultiInfoMessage } from 'JS/redux/actions/footer';
import FooterUtils from 'Components/common/footer/FooterUtils';

const mutation = graphql`
  mutation SyncLabbookMutation($input: SyncLabbookInput!){
    syncLabbook(input: $input){
      jobKey
      clientMutationId
    }
  }
`;

let tempID = 0;

export default function SyncLabbookMutation(
  owner,
  labbookName,
  overrideMethod,
  pullOnly,
  successCall,
  failureCall,
  callback,
) {
  const variables = {
    input: {
      owner,
      labbookName,
      pullOnly,
      clientMutationId: tempID++,
    },
    first: 10,
    cursor: null,
    hasNext: false,
  };
  if (overrideMethod) {
    variables.input.overrideMethod = overrideMethod;
  }
  const id = uuidv4();
  const startMessage = `Preparing to ${pullOnly ? 'pull' : 'sync'} Project...`;
  setMultiInfoMessage(id, startMessage, false, false, [{ message: startMessage }]);
  commitMutation(
    environment,
    {
      mutation,
      variables,
      onCompleted: (response, error) => {
        if (error) {
          console.log(error);
        }

        callback(error);
      },
      onError: (err) => { console.error(err); },
      updater: (store, response) => {
        if (response) {
          FooterUtils.getJobStatus(response, 'syncLabbook', 'jobKey', successCall, failureCall, id);
        }
      },
    },
  );
}
