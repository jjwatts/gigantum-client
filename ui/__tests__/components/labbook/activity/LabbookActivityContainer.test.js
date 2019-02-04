// vendor
import React from 'react';
import renderer from 'react-test-renderer';
import { mount } from 'enzyme';
import relayTestingUtils from '@gigantum/relay-testing-utils';
import { Provider } from 'react-redux';
// componensts
import LabbookActivityContainer from 'Components/labbook/activity/LabbookActivityContainer';
// store
import store from 'JS/redux/store';
// data
import json from './__relaydata__/LabbookActivityContainer.json';
let labbook = json.data.labbook;
let fixtures = {
  labbook,
  key: 'Labbook_activity',
  activityRecords: labbook.activityRecords,
  labbookId: labbook.id,
  activeBranch: 'master',
  setBuildingState: jest.fn(),
  isMainWorkspace: true,
  sectionType: 'labbook',
};

describe('LabbookActivityContainer', () => {
  it('Renders a snapshot', () => {
    const wrapper = renderer.create(<Provider store={store}><LabbookActivityContainer {...fixtures} /></Provider>);

    const tree = wrapper.toJSON();

    expect(tree).toMatchSnapshot();
  });

});
