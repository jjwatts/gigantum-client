// vendor
import React from 'react';
import renderer from 'react-test-renderer';
import { mount } from 'enzyme';
import relayTestingUtils from '@gigantum/relay-testing-utils';
// data
import codeData from 'Tests/components/labbook/code/__relaydata__/CodeBrowser.json';
// components
import AddSubFolder from 'Components/shared/fileBrowser/fileRow/AddSubfolder';

const edge = codeData.data.labbook.code.allFiles.edges[0];

const mutationData = {
  owner: 'uitest',
  labbookName: 'ui-test-project',
  section: 'code',
  connection: 'CodeBrowser_allFiles',
  favoriteConnection: 'CodeFavorite_favorites',
  parentId: codeData.data.labbook.id,
};

const fixtures = {
  setAddFolderVisible: jest.fn(),
  rowStyle: {},
  key: 'Folder__subfolder',
  folderKey: edge.node.key,
  mutationData,
  mutations: {},
  addFolderVisible: true,
};

describe('AddSubFolder Component', () => {
  it('Renders a Snapshot', () => {

    const wrapper = renderer.create(<AddSubFolder {...fixtures}/>);

    const tree = wrapper.toJSON();

    expect(tree).toMatchSnapshot();
  })
});
