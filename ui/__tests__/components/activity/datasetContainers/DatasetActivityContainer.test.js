
      import React from 'react'
      import renderer from 'react-test-renderer';
      import {mount} from 'enzyme'
      import DatasetActivityContainer from 'Components/activity/datasetContainers/DatasetActivityContainer';

      import relayTestingUtils from '@gigantum/relay-testing-utils'

      test('Test DatasetActivityContainer', () => {

        const wrapper = renderer.create(

           <DatasetActivityContainer />

        );

        const tree = wrapper.toJSON()

        expect(tree).toMatchSnapshot()

      })
