// vendor
import React from 'react';
import renderer from 'react-test-renderer';
import { mount } from 'enzyme';
import relayTestingUtils from '@gigantum/relay-testing-utils';
import { Provider } from 'react-redux';
// componensts
import DatasetActivityContainer from 'Components/dataset/activity/DatasetActivityContainer';
// store
import store from 'JS/redux/store';
// data
import json from './__relaydata__/DatasetActivityContainer.json';
let dataset = json.data.dataset;
let fixtures = {
  dataset,
  key: 'Dataset_activity',
  activityRecords: dataset.activityRecords,
  datasetId: dataset.id,
  activeBranch: 'master',
  setBuildingState: jest.fn(),
  sectionType: 'dataset',
  // {...this.props}
};

describe('DatasetActivityContainer', () => {
  it('Renders a snapshot', () => {
    const wrapper = renderer.create(<Provider store={store}><DatasetActivityContainer {...fixtures} /></ Provider>);

    const tree = wrapper.toJSON();

    expect(tree).toMatchSnapshot();
  });
});
