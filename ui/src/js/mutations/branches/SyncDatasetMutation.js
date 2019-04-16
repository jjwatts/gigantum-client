import {
  commitMutation,
  graphql,
} from 'react-relay';
import environment from 'JS/createRelayEnvironment';
import uuidv4 from 'uuid/v4';
import { setMultiInfoMessage } from 'JS/redux/actions/footer';
import FooterUtils from 'Components/common/footer/FooterUtils';

const mutation = graphql`
  mutation SyncDatasetMutation($input: SyncDatasetInput!){
    syncDataset(input: $input){
      jobKey
      clientMutationId
    }
  }
`;

let tempID = 0;

export default function SyncDatasetMutation(
  owner,
  datasetName,
  overrideMethod,
  pullOnly,
  successCall,
  failureCall,
  callback,
) {
  const variables = {
    input: {
      owner,
      datasetName,
      pullOnly,
      clientMutationId: tempID++,
    },
    first: 10,
    cursor: null,
    hasNext: false,
  };
  const id = uuidv4();
  const startMessage = 'Preparing to sync Project...';
  setMultiInfoMessage(id, startMessage, false, false, [{ message: startMessage }]);
  if (overrideMethod) {
    variables.input.overrideMethod = overrideMethod;
  }
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
          FooterUtils.getJobStatus(response, 'syncDataset', 'jobKey', successCall, failureCall, id);
        }
      },
    },
  );
}
