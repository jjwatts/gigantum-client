export default {
  finished: (callbackData) => {
    const { successCall } = callbackData;
    successCall();
  },
  failed: (callbackData) => {
    const { response, failureCall } = callbackData;
    const reportedFailureMessage = response.data.jobStatus.failureMessage;
    const errorMessage = response.data.jobStatus.failureMessage;
    failureCall();
    return {
      errorMessage,
      reportedFailureMessage,
    };
  },
};
