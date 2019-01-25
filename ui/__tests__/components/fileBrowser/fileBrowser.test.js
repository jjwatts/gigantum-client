import React from 'react';
import renderer from 'react-test-renderer';

import FileBrowserDropZone from 'Components/fileBrowser/FileBrowser';
import { mount, shallow } from 'enzyme';
import Auth from 'JS/Auth/Auth';
import history from 'JS/history';
import { BrowserRouter as Router } from 'react-router-dom';
import data from './../labbook/filesShared/__relayData__/MostRecentCode.json';
import codeData from './../labbook/code/__relayData__/CodeBrowser.json';
import codeDataFavorites from './../labbook/code/__relayData__/CodeFavorites.json';
import DeleteLabbookFilesMutation from 'Mutations/fileBrowser/DeleteLabbookFilesMutation';

const auth = new Auth();


const variables = { first: 20, labbook: 'ui-test-project' };
export default variables;

const { labbook } = codeData.data;

const setRootFolder = () => {};

const fixtures = {
  connectDropTarget: jsx => jsx,
  clearSelectedFiles: jest.fn(),
  loadStatus: jest.fn(),
  setRootFolder: jest.fn(),
  selectedFiles: [],
  labbookId: labbook.id,
  sectionId: labbook.code.id,
  section: 'code',
  isLocked: false,
  ...labbook.code,
  labbook,
  files: labbook.code.allFiles,
  parentId: labbook.id,
  connection: 'CodeBrowser_allFiles',
  favoriteConnection: 'CodeFavorites_favorites',
  favorites: codeDataFavorites.data.labbook.code.favorites,
};

jest.mock('Mutations/fileBrowser/DeleteLabbookFilesMutation', () => jest.fn());


auth.isAuthenticated = function () { return true; };
const FileBrowser = FileBrowserDropZone.DecoratedComponent;

describe('FileBrowser component', () => {
  it('Test FileBrowser Rendering', () => {
        const component = renderer.create(<FileBrowserDropZone.DecoratedComponent
              {...fixtures}
            />);

        let tree = component.toJSON();
        expect(tree).toMatchSnapshot();
   });

   const component = mount(<FileBrowserDropZone.DecoratedComponent {...fixtures}/>);
   let deleteCount = 0;
   const MockFn = jest.fn();
   const mockDeleteMutation = new MockFn();
   component._deleteMutation = mockDeleteMutation;

   it('Sorts by date', () => {
     component.find('.FileBrowser__header--date').simulate('click');
     expect(component.state('sort')).toEqual('modified');
   });

   it('Multiselect selects all', () => {
     component.find('.Btn--multiSelect').simulate('click');
     expect(component.state('multiSelect')).toEqual('all');
   });


   it('Shows delete popup', () => {
     component.find('.Btn--delete').simulate('click');
     expect(component.state('popupVisible')).toEqual(true);
   });

   it('Cancel delete popup', () => {
     component.find('.File__btn--delete').simulate('click');
     expect(component.state('popupVisible')).toEqual(false);
   });

   it('Delete Files', () => {
     component.find('.Btn--delete').simulate('click');
     component.find('.File__btn--delete-files').simulate('click');
     expect(component.state('popupVisible')).toEqual(false);
   });

   it('Updates search input', () => {
     const evt = {
       target: {
         value: 'png',
       },
     };
     component.find('.FileBrowser__input.full--border').simulate('change', evt);
     expect(component.state('search')).toEqual('png');
   });


   it('Sorts by az', () => {
     component.find('.FileBrowser__header--name').simulate('click');
     expect(component.state('sort')).toEqual('az');
   });

   it('Sorts by size', () => {
     component.find('.FileBrowser__header--size').simulate('click');
     expect(component.state('sort')).toEqual('size');
   });

   it('Sorts by modified', () => {
     component.find('.FileBrowser__header--date').simulate('click');
     expect(component.state('sort')).toEqual('modified');
   });

});
