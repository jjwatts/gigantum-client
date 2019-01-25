
      import React from 'react'
      import renderer from 'react-test-renderer';
      import {mount} from 'enzyme'
      import OutputBrowser from 'Components/labbook/filesShared/sectionBrowser/sectionBrowserContainers/OutputBrowser';

      import relayTestingUtils from '@gigantum/relay-testing-utils'

      test('Test OutputBrowser', () => {

        const wrapper = renderer.create(

           <OutputBrowser />

        );

        const tree = wrapper.toJSON()

        expect(tree).toMatchSnapshot()

      })