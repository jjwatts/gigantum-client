// vendor
import React, { Component } from 'react';
import renderer from 'react-test-renderer';
import { mount } from 'enzyme';
import relayTestingUtils from '@gigantum/relay-testing-utils';
import { Provider } from 'react-redux';
// components
import Activity from 'Components/shared/activity/Activity';
// Data
import json from 'Tests/components/labbook/__relaydata__/LabbookContainerQuery.json';
// store
import store from 'JS/redux/store';

let { labbook } = json.data;

let fixtures = {
  setBuildingState: jest.fn(),
  key: 'Activity',
  labbook,
  activityRecords: labbook.activityRecords,
  labbookId: labbook.id,
  activeBranch: 'master',
  isMainWorkspace: true,
  sectionType: 'labbook',
  labbookName: 'ui-test-project',
  owner: 'uitest',
  refetch: jest.fn(),
  relay: {
    refetchConnection: jest.fn(),
  },
};


global.counter = 0;

describe('Activity', () => {
  it('renders a snapshot', () => {
    class ActivityInstance extends Component {
      render() {
        return (relayTestingUtils.relayWrap(<Provider store={store}><Activity {...fixtures}/></Provider>, {}, json.data.labbook));
      }
    }

    const wrapper = renderer.create(<ActivityInstance {...fixtures} />);

    const tree = wrapper.toJSON();

    expect(tree).toMatchSnapshot();
  });
});
