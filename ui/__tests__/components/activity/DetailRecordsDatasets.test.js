// vendor
import React from 'react';
import renderer from 'react-test-renderer';
import { mount } from 'enzyme';
import relayTestingUtils from '@gigantum/relay-testing-utils';
// component
import DetailRecordsDatasets from 'Components/activity/DetailRecordsDatasets';

test('Test DetailRecordsDatasets', () => {
  const wrapper = renderer.create(<DetailRecordsDatasets />);

  const tree = wrapper.toJSON();

  expect(tree).toMatchSnapshot();
});
