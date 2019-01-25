
      import React from 'react'
      import renderer from 'react-test-renderer';
      import {mount} from 'enzyme'
      import fetchContainerStatus from 'Components/labbook/labbookHeader/containerStatus/fetchContainerStatus';

      import relayTestingUtils from '@gigantum/relay-testing-utils'

      test('Test fetchContainerStatus', () => {

        const wrapper = renderer.create(

           <fetchContainerStatus />

        );

        const tree = wrapper.toJSON()

        expect(tree).toMatchSnapshot()

      })