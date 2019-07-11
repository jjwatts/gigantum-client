export default {
  failed: (callbackData) => {
    const { response } = callbackData;
    const reportedFailureMessage = response.data.jobStatus.failureMessage;
    let errorMessage = response.data.jobStatus.failureMessage;

    if (reportedFailureMessage.indexOf('terminated unexpectedly') > -1) {
      errorMessage = 'Build Canceled.';
    } else {
      errorMessage = 'Project failed to build: Check for and remove invalid dependencies and try again.';
    }
    return {
      errorMessage,
      reportedFailureMessage,
    };
  },
};
