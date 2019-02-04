
// components
import NewActivity from 'Components/shared/activity/NewActivity';

describe('NewActivity', () => {
  it('Returns a promise', () => {
    const promise = NewActivity.getNewActivity('uitest', 'ui-test-project');

    promise.then((e) => { expect(e).toBeTruthy() });
  });
});
