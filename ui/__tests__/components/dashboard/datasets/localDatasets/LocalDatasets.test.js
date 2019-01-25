// vendor
import React from 'react';
import renderer from 'react-test-renderer';
import { mount } from 'enzyme';
import { BrowserRouter as Router } from 'react-router-dom';
import relayTestingUtils from '@gigantum/relay-testing-utils'
import { Provider } from 'react-redux';
// history
import history from 'JS/history';
// data
import json from './__relaydata__/LocalDatasets.json';
// store
import store from 'JS/redux/store';
// components
import LocalDatasets from 'Components/dashboard/datasets/localDatasets/LocalDatasets';

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
