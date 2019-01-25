import {
  commitMutation,
  graphql,
} from 'react-relay';
import environment from 'JS/createRelayEnvironment';
// utils
import FooterUtils from 'Components/shared/footer/FooterUtils';

const mutation = graphql`
  mutation ImportDatasetMutation($input: ImportDatasetInput!){
    importDataset(input: $input){
      clientMutationId
      importJobKey
    }
  }
`;

let tempID = 0;

export default function ImportDatasetMutation(
  blob,
  chunk,
  accessToken,
  callback,
) {
  const uploadables = [blob, accessToken];

  const variables = {
    input: {
      chunkUploadParams: {
        fileSizeKb: chunk.fileSizeKb,
        chunkSize: chunk.chunkSize,
        totalChunks: chunk.totalChunks,
        chunkIndex: chunk.chunkIndex,
        filename: chunk.filename,
        uploadId: chunk.uploadId,
      },
      clientMutationId: `${tempID++}`,
    },

  };
  commitMutation(
    environment,
    {
      mutation,
      variables,
      uploadables,
      onCompleted: (response, error) => {
        if (error) {
          console.log(error);
        }

        if (response.importDataset.importJobKey) {
          FooterUtils.getJobStatus(response, 'importDataset', 'importJobKey');
        }

        callback(response, error);
      },
      onError: err => console.error(err),

      updater: (store) => {

      },
    },
  );
}
