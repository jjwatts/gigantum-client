import {
  commitMutation,
  graphql,
} from 'react-relay';
import environment from 'JS/createRelayEnvironment';
import uuidv4 from 'uuid/v4';
import { setMultiInfoMessage } from 'JS/redux/actions/footer';
import FooterUtils from 'Components/common/footer/FooterUtils';
import footerCallback from 'Components/common/footer/utils/SyncLabbook';

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
  const messageData = {
    id,
    message: startMessage,
    isLast: false,
    error: false,
    messageBody: [{ message: startMessage }],
    messageListOpen: false,
  };
  setMultiInfoMessage(messageData);

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
          const footerData = {
            result: response,
            type: 'syncLabbook',
            key: 'jobKey',
            footerCallback,
            successCall,
            failureCall,
            id,
            hideFooter: true,
          };

          FooterUtils.getJobStatus(footerData);
        }
      },
    },
  );
}
