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
    const failureDetail = JSON.parse(response.data.jobStatus.jobMetadata).failure_detail;
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

    reportedFailureMessage = failureDetail;
    errorMessage = errorMessage.indexOf(':') ? errorMessage.split(':')[1] : errorMessage;
    return {
      errorMessage,
      reportedFailureMessage,
    };
  },
};
