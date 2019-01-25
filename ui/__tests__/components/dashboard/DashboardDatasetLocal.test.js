// vendor
import React from 'react';
import renderer from 'react-test-renderer';
import { mount } from 'enzyme';
import relayTestingUtils from '@gigantum/relay-testing-utils';
import { BrowserRouter as Router } from 'react-router-dom';
import { Provider } from 'react-redux';
// components;
import LocalDatasets from 'Components/dashboard/datasets/localDatasets/LocalDatasets';
// data
import json from './datasets/localDatasets/__relaydata__/LocalDatasets.json';
// store
import store from 'JS/redux/store';

const fixtures = {
  auth: () => {},
  datasetList: json.data.datasetList,
  localDatasets: json.data.datasetList,
  history,
  refetchSort: () => {},
  filterDatasets: data => data,
};

test('Test LocalDatasets', () => {
  const wrapper = renderer.create(
    relayTestingUtils.relayWrap(
      <Provider store={store}>
        <Router>
          <LocalDatasets
              {...fixtures}
          />
        </Router>
      </Provider>, {}, json.data)
  );

  const tree = wrapper.toJSON();

  expect(tree).toMatchSnapshot();

})
