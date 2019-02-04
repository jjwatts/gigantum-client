// vendor
import JobStatus from 'JS/utils/JobStatus';
import store from 'JS/redux/store';
import AnsiUp from 'ansi_up';
import { setMultiInfoMessage, setErrorMessage } from 'JS/redux/reducers/footer';
import { setForceRefetch, setRefetchPending } from 'JS/redux/reducers/labbook/environment/packageDependencies';
// mutations
import FetchLabbookEdgeMutation from 'Mutations/FetchLabbookEdgeMutation';
import FetchDatasetEdgeMutation from 'Mutations/FetchDatasetEdgeMutation';

const ansi_up = new AnsiUp();

const FooterUtils = {
  /**
   *  @param {number}
   *  iterate value of index within the bounds of the array size
   *  @return {}
   */
  getJobStatus: (result, type, key, successCall, failureCall) => {
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
          if (response.data &&
            response.data.jobStatus &&
            response.data.jobStatus.jobMetadata) {
            let fullMessage = (response.data.jobStatus.jobMetadata.indexOf('feedback') > -1) ? JSON.parse(response.data.jobStatus.jobMetadata).feedback : '';
            fullMessage = fullMessage.lastIndexOf('\n') === (fullMessage.length - 1)
              ? fullMessage.slice(0, fullMessage.length - 1)
              : fullMessage;

            let html = ansi_up.ansi_to_html(fullMessage);

            const lastIndex = (fullMessage.lastIndexOf('\n') > -1)
              ? fullMessage.lastIndexOf('\n')
              : 0;


            let message = fullMessage.slice(lastIndex, fullMessage.length);

            if (message.indexOf('[0m') > 0) {
              let res = [],
                index = 0;

              while (fullMessage.indexOf('\n', index + 1) > 0) {
                index = fullMessage.indexOf('\n', index + 1);
                res.push(index);
              }

              message = fullMessage.slice(res[res.length - 2], res[res.length - 1]);
            }

            if ((response.data.jobStatus.status === 'started' || response.data.jobStatus.status === 'finished') && store.getState().packageDependencies.refetchPending) {
              setForceRefetch(true);
              setRefetchPending(false);
            }

            if (response.data.jobStatus.status === 'started') {
              if (html.length) {
                setMultiInfoMessage(response.data.jobStatus.id, message, false, false, [{ message: html }]);
              }
              refetch();
            } else if (response.data.jobStatus.status === 'finished') {
              setMultiInfoMessage(response.data.jobStatus.id, message, true, null, [{ message: html }]);
              if ((type === 'syncLabbook') || (type === 'publishLabbook') || (type === 'publishDataset') || (type === 'syncDataset')) {
                successCall();
                const section = type.indexOf('Dataset') > -1 ? 'dataset' : 'labbook';
                const metaDataArr = JSON.parse(response.data.jobStatus.jobMetadata)[section].split('|');
                const owner = metaDataArr[1];
                const labbookName = metaDataArr[2];
                section === 'labbook' ?
                  FetchLabbookEdgeMutation(
                    owner,
                    labbookName,
                    (error) => {
                      if (error) {
                        console.error(error);
                      }
                    },
                  )
                  :
                  FetchDatasetEdgeMutation(
                    owner,
                    labbookName,
                    (error) => {
                      if (error) {
                        console.error(error);
                      }
                    },
                  );
              }
            } else if (response.data.jobStatus.status === 'failed') {
              const method = JSON.parse(response.data.jobStatus.jobMetadata).method;
              let errorMessage = response.data.jobStatus.failureMessage;
              if (method === 'build_image') {
                errorMessage = 'Project failed to build: Check for and remove invalid dependencies and try again.';
              }
              if ((type === 'syncLabbook') || (type === 'publishLabbook')) {
                failureCall(response.data.jobStatus.failureMessage);
              }
              html += `\n<span style="color:rgb(255,85,85)">${response.data.jobStatus.failureMessage}</span>`;
              setMultiInfoMessage(response.data.jobStatus.id, errorMessage, true, true, [{ message: html }]);
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
