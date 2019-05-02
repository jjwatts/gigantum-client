// vendor
import JobStatus from 'JS/utils/JobStatus';
import AnsiUp from 'ansi_up';
// store
import { setMultiInfoMessage, setErrorMessage } from 'JS/redux/actions/footer';
// mutations
import FetchLabbookEdgeMutation from 'Mutations/FetchLabbookEdgeMutation';
import FetchDatasetEdgeMutation from 'Mutations/FetchDatasetEdgeMutation';
import FetchDatasetFilesMutation from 'Mutations/FetchDatasetFilesMutation';
import FetchLabbookDatasetFilesMutation from 'Mutations/FetchLabbookDatasetFilesMutation';

const ansiUp = new AnsiUp();

const FooterUtils = {
  /**
   *  @param {number}
   *  iterate value of index within the bounds of the array size
   *  @return {}
   */
  getJobStatus: (result, type, key, successCall, failureCall, id) => {
    /**
      *  @param {}
      *  refetches job status
      *  @return {}
      */
    const refetch = () => {
      setTimeout(() => {
        fetchStatus();
      }, 1000);
    };
    /**
      *  @param {}
      *  fetches job status for background message
      *  updates footer with a message
      *  @return {}
      */
    const fetchStatus = () => {
      const resultType = result[type];
      const resultKey = resultType ? resultType[key] : false;

      if (resultKey) {
        JobStatus.updateFooterStatus(result[type][key]).then((response) => {
          if (response.data
              && response.data.jobStatus
              && response.data.jobStatus.jobMetadata) {
            let fullMessage = (response.data.jobStatus.jobMetadata.indexOf('feedback') > -1) ? JSON.parse(response.data.jobStatus.jobMetadata).feedback : '';
            fullMessage = fullMessage.lastIndexOf('\n') === (fullMessage.length - 1)
              ? fullMessage.slice(0, fullMessage.length - 1)
              : fullMessage;

            let html = ansiUp.ansi_to_html(fullMessage);

            const lastIndex = (fullMessage.lastIndexOf('\n') > -1)
              ? fullMessage.lastIndexOf('\n')
              : 0;

            let message = fullMessage.slice(lastIndex, fullMessage.length);

            if (message.indexOf('[0m') > 0) {
              const res = [];
              let index = 0;

              while (fullMessage.indexOf('\n', index + 1) > 0) {
                index = fullMessage.indexOf('\n', index + 1);
                res.push(index);
              }

              message = fullMessage.slice(res[res.length - 2], res[res.length - 1]);
            }

            if (response.data.jobStatus.status === 'started') {
              if (html.length) {
                const repsonseId = id || response.data.jobStatus.id;
                setMultiInfoMessage(repsonseId, message, false, false, [{ message: html }]);
              }
              refetch();
            } else if (response.data.jobStatus.status === 'finished') {
              const repsonseId = id || response.data.jobStatus.id;
              setMultiInfoMessage(repsonseId, message, true, null, [{ message: html }]);

              document.getElementById('modal__cover').classList.add('hidden');
              document.getElementById('loader').classList.add('hidden');

              if ((type === 'syncLabbook') || (type === 'publishLabbook') || (type === 'publishDataset') || (type === 'syncDataset')) {
                const section = type.indexOf('Dataset') > -1 ? 'dataset' : 'labbook';
                const metaDataArr = JSON.parse(response.data.jobStatus.jobMetadata)[section].split('|');
                const owner = metaDataArr[1];
                const labbookName = metaDataArr[2];
                successCall(owner, labbookName);

                section === 'labbook'
                  ? FetchLabbookEdgeMutation(
                    owner,
                    labbookName,
                    (error) => {
                      if (error) {
                        console.error(error);
                      }
                    },
                  )
                  : FetchDatasetEdgeMutation(
                    owner,
                    labbookName,
                    (error) => {
                      if (error) {
                        console.error(error);
                      }
                    },
                  );
              } else if (type === 'downloadDatasetFiles') {
                const successKeys = JSON.parse(response.data.jobStatus.jobMetadata).success_keys;
                const metaDataArr = JSON.parse(response.data.jobStatus.jobMetadata).dataset.split('|');
                const isLabbookSection = metaDataArr[3] === 'LINKED';
                if (!isLabbookSection) {
                  const owner = metaDataArr[1];
                  const labbookName = metaDataArr[2];
                  FetchDatasetFilesMutation(
                    owner,
                    labbookName,
                    () => {
                      successCall();
                    },
                  );
                } else {
                  const owner = metaDataArr[1];
                  const labbookName = metaDataArr[2];
                  FetchLabbookDatasetFilesMutation(
                    owner,
                    labbookName,
                    () => {
                      successCall();
                    },
                  );
                }
              } else if (type === 'importRemoteLabbook') {
                successCall();
              }
            } else if (response.data.jobStatus.status === 'failed') {
              const { method } = JSON.parse(response.data.jobStatus.jobMetadata);
              let reportedFailureMessage = response.data.jobStatus.failureMessage;
              let errorMessage = response.data.jobStatus.failureMessage;

              document.getElementById('modal__cover').classList.add('hidden');
              document.getElementById('loader').classList.add('hidden');
              if (method === 'build_image') {
                if (reportedFailureMessage.indexOf('terminated unexpectedly') > -1) {
                  errorMessage = 'Build Canceled.';
                } else {
                  errorMessage = 'Project failed to build: Check for and remove invalid dependencies and try again.';
                }
              }
              if ((type === 'syncLabbook') || (type === 'publishLabbook') || (type === 'syncDataset') || (type === 'publishDataset')) {
                failureCall(response.data.jobStatus.failureMessage);
              }
              if (type === 'downloadDatasetFiles') {
                const successKeys = JSON.parse(response.data.jobStatus.jobMetadata).success_keys;
                const failureKeys = JSON.parse(response.data.jobStatus.jobMetadata).failure_keys;
                const totalAmount = successKeys.length + failureKeys.length;
                const metaDataArr = JSON.parse(response.data.jobStatus.jobMetadata).dataset.split('|');
                const isLabbookSection = metaDataArr[3] === 'LINKED';
                if (!isLabbookSection) {
                  const owner = metaDataArr[1];
                  const labbookName = metaDataArr[2];
                  FetchDatasetFilesMutation(
                    owner,
                    labbookName,
                    () => {
                      failureCall(response.data.jobStatus.failureMessage);
                    },
                  );
                } else {
                  const owner = metaDataArr[1];
                  const labbookName = metaDataArr[2];
                  FetchDatasetFilesMutation(
                    owner,
                    labbookName,
                    () => {
                      failureCall(response.data.jobStatus.failureMessage);
                    },
                  );
                }
                errorMessage = `Failed to download ${failureKeys.length} of ${totalAmount} Files.`;
                reportedFailureMessage = 'Failed to download the following Files:';
                failureKeys.forEach(failedKey => reportedFailureMessage = `${reportedFailureMessage}\n${failedKey}`);
              } else if (type === 'importRemoteLabbook') {
                failureCall();
              }
              html += `\n<span style="color:rgb(255,85,85)">${reportedFailureMessage}</span>`;
              setMultiInfoMessage(id || response.data.jobStatus.id, errorMessage, true, true, [{ message: html }]);
            } else {
              // refetch status data not ready
              refetch();
            }
          } else {
            // refetch status data not ready
            refetch();
          }
        });
      } else {
        setErrorMessage('There was an error fetching job status.', [{ message: 'Callback error from the API' }]);
      }
    };

    // trigger fetch
    fetchStatus();
  },
};

export default FooterUtils;
