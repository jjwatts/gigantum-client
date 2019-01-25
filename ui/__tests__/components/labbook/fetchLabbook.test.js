
      import React from 'react'
      import renderer from 'react-test-renderer';
      import {mount} from 'enzyme'
      import fetchLabbook from 'Components/labbook/fetchLabbook';

      import relayTestingUtils from '@gigantum/relay-testing-utils'

      test('Test fetchLabbook', () => {

        const wrapper = renderer.create(

           <fetchLabbook />

        );

        const tree = wrapper.toJSON()

        expect(tree).toMatchSnapshot()

      })