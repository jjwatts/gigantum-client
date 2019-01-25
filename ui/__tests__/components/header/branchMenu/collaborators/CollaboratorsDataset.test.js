// vendor
import React from 'react';
import renderer from 'react-test-renderer';
import { mount } from 'enzyme';
import relayTestingUtils from '@gigantum/relay-testing-utils';
// components
import CollaboratorsDataset from 'Components/header/branchMenu/collaborators/CollaboratorsDataset';

test('Test CollaboratorsDataset', () => {
  const wrapper = renderer.create(
     <CollaboratorsDataset />
  );

  const tree = wrapper.toJSON();

  expect(tree).toMatchSnapshot();
});
