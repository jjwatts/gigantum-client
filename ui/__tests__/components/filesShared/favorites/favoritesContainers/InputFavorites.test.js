// vendor
import React from 'react';
import renderer from 'react-test-renderer';
import { mount } from 'enzyme';
import relayTestingUtils from '@gigantum/relay-testing-utils';
// components
import InputFavorites from 'Components/filesShared/favorites/favoritesContainers/InputFavorites';

test('Test InputFavorites', () => {
  const wrapper = renderer.create(
     <InputFavorites />
  );

  const tree = wrapper.toJSON();

  expect(tree).toMatchSnapshot();
});
