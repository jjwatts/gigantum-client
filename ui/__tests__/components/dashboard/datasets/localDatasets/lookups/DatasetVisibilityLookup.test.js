// vendor
import React from 'react';
import renderer from 'react-test-renderer';
import { mount } from 'enzyme';
import relayTestingUtils from '@gigantum/relay-testing-utils';
// data
import json from './../__relaydata__/LocalDatasets.json';
// components
import DatasetVisibilityLookup from 'Components/dashboard/datasets/localDatasets/lookups/DatasetVisibilityLookup';

test('Test DatasetVisibilityLookup', async () => {
  let id = json.data.datasetList.localDatasets.edges[0].node.id;
  DatasetVisibilityLookup.query([id]).then((response) => {
    expect(response.data.ids.length).toEqual(0);
  });
});
