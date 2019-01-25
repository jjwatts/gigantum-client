// vendor
import React from 'react';
import renderer from 'react-test-renderer';
import { mount } from 'enzyme';
import relayTestingUtils from '@gigantum/relay-testing-utils';
// components
import MostRecentOutput from 'Components/filesShared/mostRecent/mostRecentContainers/MostRecentOutput';


test('Test MostRecentOutput', () => {
  const wrapper = renderer.create(
     <MostRecentOutput />
  );

  const tree = wrapper.toJSON();

  expect(tree).toMatchSnapshot();
});
