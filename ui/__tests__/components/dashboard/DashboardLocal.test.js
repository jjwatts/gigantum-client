import { Provider } from 'react-redux';
import React from 'react';
import renderer from 'react-test-renderer';
import history from 'JS/history';
import { mount } from 'enzyme';
import LocalLabbooksContainer from 'Components/dashboard/labbooks/localLabbooks/LocalLabbooksContainer';
import store from 'JS/redux/store';
import { BrowserRouter as Router } from 'react-router-dom';

import relayTestingUtils from '@gigantum/relay-testing-utils';
import json from './__relaydata__/DashboardLocal.json';


const fixtures = {
  auth: () => {},
  localLabbooks: json.data.labbookList,
  labbookList: json.data.labbookList,
  history,
  refetchSort: () => {},
  loading: false,
};


describe('DashboardLocal', () => {
  test('Renders a snapshot', () => {
    const wrapper = renderer.create(
        relayTestingUtils.relayWrap(
          <Provider store={store}>
            <Router>
              <LocalLabbooksContainer {...fixtures} />
            </Router>
          </Provider>,
         {}, json.data,
       ),
    );

    const tree = wrapper.toJSON();

    expect(tree).toMatchSnapshot();
  });
});
