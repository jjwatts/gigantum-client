// vendor
import React from 'react';
import renderer from 'react-test-renderer';
import { mount } from 'enzyme';
import relayTestingUtils from '@gigantum/relay-testing-utils';
// components
import CodeFavorites from 'Components/filesShared/favorites/favoritesContainers/CodeFavorites';

test('Test CodeFavorites', () => {
  const wrapper = renderer.create(
     <CodeFavorites />
  );

  const tree = wrapper.toJSON();

  expect(tree).toMatchSnapshot();
});
