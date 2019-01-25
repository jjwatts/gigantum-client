// vendor
import React from 'react'
import renderer from 'react-test-renderer';
import { mount } from 'enzyme'
import relayTestingUtils from '@gigantum/relay-testing-utils';
// components
import Collaborators from 'Components/header/branchMenu/collaborators/Collaborators';

test('Test Collaborators', () => {
  const wrapper = renderer.create(
     <Collaborators />
  );

  const tree = wrapper.toJSON();

  expect(tree).toMatchSnapshot();
});
