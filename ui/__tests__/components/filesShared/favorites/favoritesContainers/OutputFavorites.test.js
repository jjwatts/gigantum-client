// vendor
import React from 'react';
import renderer from 'react-test-renderer';
import { mount } from 'enzyme';
import relayTestingUtils from '@gigantum/relay-testing-utils';
// components
import OutputFavorites from 'Components/filesShared/favorites/favoritesContainers/OutputFavorites';

test('Test OutputFavorites', () => {
  const wrapper = renderer.create(
     <OutputFavorites />
  );

  const tree = wrapper.toJSON();

  expect(tree).toMatchSnapshot();
});
