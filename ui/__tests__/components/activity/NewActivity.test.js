
import React from 'react'
import renderer from 'react-test-renderer';
import { mount } from 'enzyme'
import NewActivity from 'Components/activity/NewActivity';

import relayTestingUtils from '@gigantum/relay-testing-utils'

test('Test NewActivity', () => {

  const wrapper = renderer.create(

     <NewActivity />

  );

  const tree = wrapper.toJSON()

  expect(tree).toMatchSnapshot()

})
