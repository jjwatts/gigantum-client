// vendor
import React from 'react';
import renderer from 'react-test-renderer';
import { mount } from 'enzyme';
import relayTestingUtils from '@gigantum/relay-testing-utils'
// components
import DataBrowser from 'Components/dataset/data/DataBrowser';


test('Test DataBrowser', () => {
  const wrapper = renderer.create(
     <DataBrowser />
  );

  const tree = wrapper.toJSON();

  expect(tree).toMatchSnapshot();
});
