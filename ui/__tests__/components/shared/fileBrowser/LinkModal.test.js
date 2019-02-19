// vendor
import React from 'react';
import renderer from 'react-test-renderer';
import { mount } from 'enzyme';
import relayTestingUtils from '@gigantum/relay-testing-utils';
// components
import LinkModal from 'Components/shared/fileBrowser/LinkModal';
import ReactDOM from 'react-dom';

ReactDOM.createPortal = node => node


const fixtures = {
  closeLinkModal: jest.fn(),
}

test('Test LinkModal', () => {
  const wrapper = renderer.create(
     <LinkModal {...fixtures}/>
  );
  const tree = wrapper.toJSON();
  expect(tree).toMatchSnapshot();
});
