
      import React from 'react'
      import renderer from 'react-test-renderer';
      import {mount} from 'enzyme'
      import MostRecentCode from 'Components/labbook/filesShared/mostRecent/mostRecentContainers/MostRecentCode';

      import relayTestingUtils from '@gigantum/relay-testing-utils'

      test('Test MostRecentCode', () => {

        const wrapper = renderer.create(

           <MostRecentCode />

        );

        const tree = wrapper.toJSON()

        expect(tree).toMatchSnapshot()

      })