import {
  commitMutation,
  graphql,
} from 'react-relay';
import environment from 'JS/createRelayEnvironment';
import uuidv4 from 'uuid/v4';
import FooterUtils from 'Components/common/footer/FooterUtils';
import { setMultiInfoMessage } from 'JS/redux/actions/footer';

const mutation = graphql`
  mutation PublishLabbookMutation($input: PublishLabbookInput!){
    publishLabbook(input: $input){
      jobKey
      clientMutationId
    }
  }
`;

let tempID = 0;

export default function PublishLabbookMutation(
  owner,
  labbookName,
  labbookId,
  setPublic,
  successCall,
  failureCall,
  callback,
) {
  const variables = {
    input: {
      setPublic,
      owner,
      labbookName,
      clientMutationId: tempID++,
    },
  };
  const id = uuidv4();
  const startMessage = 'Preparing to publish Project...';
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

        callback(response, error);
      },
      onError: (err) => { console.error(err); },
      updater: (store, response) => {
        if (response) {
          FooterUtils.getJobStatus(response, 'publishLabbook', 'jobKey', successCall, failureCall, id);
        }
      },
    },
  );
}
