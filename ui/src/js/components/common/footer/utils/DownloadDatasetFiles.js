export default {
  finished: (callbackData) => {
    const { response, successCall, mutations } = callbackData;
    const metaDataArr = JSON.parse(response.data.jobStatus.jobMetadata).dataset.split('|');
    const isLabbookSection = metaDataArr[3] === 'LINKED';
    if (!isLabbookSection) {
      const owner = metaDataArr[1];
      const labbookName = metaDataArr[2];
      mutations.FetchDatasetFilesMutation(
        owner,
        labbookName,
        () => {
          successCall();
        },
      );
    } else {
      const owner = metaDataArr[1];
      const labbookName = metaDataArr[2];
      mutations.FetchLabbookDatasetFilesMutation(
        owner,
        labbookName,
        () => {
          successCall();
        },
      );
    }
  },
  failed: (callbackData) => {
    const { response, failureCall, mutations } = callbackData;
    let reportedFailureMessage = response.data.jobStatus.failureMessage;
    let errorMessage = response.data.jobStatus.failureMessage;
    const successKeys = JSON.parse(response.data.jobStatus.jobMetadata).success_keys;
    const failureKeys = JSON.parse(response.data.jobStatus.jobMetadata).failure_keys;
    const totalAmount = successKeys.length + failureKeys.length;
    const metaDataArr = JSON.parse(response.data.jobStatus.jobMetadata).dataset.split('|');
    const isLabbookSection = metaDataArr[3] === 'LINKED';
    if (!isLabbookSection) {
      const owner = metaDataArr[1];
      const labbookName = metaDataArr[2];
      mutations.FetchDatasetFilesMutation(
        owner,
        labbookName,
        () => {
          failureCall(response.data.jobStatus.failureMessage);
        },
      );
    } else {
      const owner = metaDataArr[1];
      const labbookName = metaDataArr[2];
      mutations.FetchDatasetFilesMutation(
        owner,
        labbookName,
        () => {
          failureCall(response.data.jobStatus.failureMessage);
        },
      );
    }
    errorMessage = `Failed to download ${failureKeys.length} of ${totalAmount} Files.`;
    reportedFailureMessage = 'Failed to download the following Files:';
    failureKeys.forEach((failedKey) => {
      reportedFailureMessage = `${reportedFailureMessage}\n${failedKey}`;
    });
    return {
      errorMessage,
      reportedFailureMessage,
    };
  },
};
