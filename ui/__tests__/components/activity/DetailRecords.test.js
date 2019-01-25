
import React from 'react';
import renderer from 'react-test-renderer';
import { mount } from 'enzyme';
import DetailRecords from 'Components/activity/DetailRecords';

import relayTestingUtils from '@gigantum/relay-testing-utils';

test('Test DetailRecords', () => {

  const wrapper = renderer.create(
     <DetailRecords />
  );

  const tree = wrapper.toJSON();

  expect(tree).toMatchSnapshot();

})
