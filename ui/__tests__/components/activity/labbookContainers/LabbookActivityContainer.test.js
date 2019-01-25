
import React from 'react';
import renderer from 'react-test-renderer';
import { mount } from 'enzyme';
import LabbookActivityContainer from 'Components/activity/labbookContainers/LabbookActivityContainer';

import relayTestingUtils from '@gigantum/relay-testing-utils';

test('Test LabbookActivityContainer', () => {

  const wrapper = renderer.create(
     <LabbookActivityContainer />
  );

  const tree = wrapper.toJSON();

  expect(tree).toMatchSnapshot();

});
