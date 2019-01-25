
      import React from 'react'
      import renderer from 'react-test-renderer';
      import {mount} from 'enzyme'
      import CodeBrowser from 'Components/labbook/filesShared/sectionBrowser/sectionBrowserContainers/CodeBrowser';

      import relayTestingUtils from '@gigantum/relay-testing-utils'

      test('Test CodeBrowser', () => {

        const wrapper = renderer.create(

           <CodeBrowser />

        );

        const tree = wrapper.toJSON()

        expect(tree).toMatchSnapshot()

      })