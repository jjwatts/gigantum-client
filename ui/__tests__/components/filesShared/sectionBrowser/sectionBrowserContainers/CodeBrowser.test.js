// vendor
import React from 'react';
import renderer from 'react-test-renderer';
import { mount } from 'enzyme';
import relayTestingUtils from '@gigantum/relay-testing-utils';
// components
import CodeBrowser from 'Components/filesShared/sectionBrowser/sectionBrowserContainers/CodeBrowser';

test('Test CodeBrowser', () => {
  const wrapper = renderer.create(
     <CodeBrowser />
  );

  const tree = wrapper.toJSON();

  expect(tree).toMatchSnapshot();
});
