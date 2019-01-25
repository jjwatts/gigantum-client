
      // vendor
      import React from 'react';
      import renderer from 'react-test-renderer';
      import {mount} from 'enzyme';
      import relayTestingUtils from 'relay-testing-utils';
      // components;
      import FolderUpload from 'Components/labbook/fileBrowser/FolderUpload';

      test('Test FolderUpload', () => {
        const wrapper = renderer.create(<FolderUpload />);

        const tree = wrapper.toJSON();

        expect(tree).toMatchSnapshot();
      });