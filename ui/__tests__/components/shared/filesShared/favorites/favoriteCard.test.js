import React from 'react';
import renderer from 'react-test-renderer';

import FavoriteCard from 'Components/shared/filesShared/FavoriteCard';
import { mount, shallow } from 'enzyme';
import Auth from 'JS/Auth/Auth';
import history from 'JS/history';
import { BrowserRouter as Router } from 'react-router-dom';
import data from 'Tests/components/labbook/filesShared/__relaydata__/MostRecentCode.json';
import codeData from 'Tests/components/labbook/code/__relaydata__/CodeBrowser.json';
import codeDataFavorites from 'Tests/components//labbook/code/__relaydata__/CodeFavorites.json';
import DeleteLabbookFilesMutation from 'Mutations/fileBrowser/DeleteLabbookFilesMutation';

const auth = new Auth();

const variables = { first: 20, labbook: 'demo-lab-book' };
export default variables;

const edge = codeDataFavorites.data.labbook.code.favorites.edges[0];

const fixtures = {
  connectDropTarget: jsx => jsx,
  key: edge.node.key,
  id: edge.node.id,
  index: 0,
  labbookName: codeDataFavorites.data.labbook.name,
  parentId: codeDataFavorites.data.labbook.id,
  section: 'code',
  connection: 'CodeFavorites_favorites',
  favorite: edge.node,
  owner: 'owner',
  moveCard: jest.fn(),
};

jest.mock('Mutations/fileBrowser/DeleteLabbookFilesMutation', () => jest.fn());


auth.isAuthenticated = function () { return true; };

describe('FavoriteCard component', () => {
  it('Test FileBrowser Rendering', () => {
        const component = renderer.create(<FavoriteCard
              {...fixtures}
            />);

        let tree = component.toJSON();
        expect(tree).toMatchSnapshot();
   });

 })
