// vendor
import React, { Component } from 'react';
import renderer from 'react-test-renderer';
import { mount } from 'enzyme';
import relayTestingUtils from '@gigantum/relay-testing-utils';
import { Provider } from 'react-redux';
// components
import PaginationLoader from 'Components/shared/activity/loaders/PaginationLoader';
// store
import store from 'JS/redux/store';


describe('Activity', () => {
  it('renders a snapshot', () => {

    const wrapper = renderer.create(<PaginationLoader />);

    const tree = wrapper.toJSON();

    expect(tree).toMatchSnapshot();
  });
});
