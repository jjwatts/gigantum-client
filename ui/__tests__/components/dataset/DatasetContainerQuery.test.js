// vendor
import React from 'react';
import renderer from 'react-test-renderer';
import { mount } from 'enzyme';
import relayTestingUtils from '@gigantum/relay-testing-utils';
// components
import DatasetContainerQuery from 'Components/dataset/DatasetContainerQuery';

test('Test DatasetContainerQuery', () => {
  const wrapper = renderer.create(
     <DatasetContainerQuery />
  );

  const tree = wrapper.toJSON();

  expect(tree).toMatchSnapshot();
});
