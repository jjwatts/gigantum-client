
      import React from 'react'
      import renderer from 'react-test-renderer';
      import {mount} from 'enzyme'
      import MostRecentOutput from 'Components/labbook/filesShared/mostRecent/mostRecentContainers/MostRecentOutput';

      import relayTestingUtils from '@gigantum/relay-testing-utils'

      test('Test MostRecentOutput', () => {

        const wrapper = renderer.create(

           <MostRecentOutput />

        );

        const tree = wrapper.toJSON()

        expect(tree).toMatchSnapshot()

      })