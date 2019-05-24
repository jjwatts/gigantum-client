import Routes from 'Components/Routes';

import React from 'react';
// import toJson from 'enzyme-to-json';
import { mount, shallow } from 'Enzyme';
import Auth from 'JS/Auth/Auth';
import renderer from 'react-test-renderer';
import relayTestingUtils from '@gigantum/relay-testing-utils';
import { MemoryRouter } from 'react-router';

const variables = { first: 20, owner: 'uitest', name: 'ui-test-labbook' };
export default variables;

test('Test Routes Rendering', () => {
      const auth = new Auth();
      auth.isAuthenticated = function () { return true; };
      auth.login = function () { return true; };
      auth.logout = function () { return true; };

      const component = renderer.create(

          relayTestingUtils.relayWrap(<Routes />, {}, config.data),

      );
      let tree = component.toJSON();

      expect(tree).toMatchSnapshot();
});


describe('Test Routes View Change', () => {

      const auth = new Auth();
      auth.isAuthenticated = function () { return true; };
      auth.login = function () { return true; };
      auth.logout = function () { return true; };

      const component = shallow(<Routes />);

      it('renders header routes', () => {
        component.find('.Header__nav-item').at(0).simulate('click');
        expect(component).toMatchSnapshot();
      });

      it('renders header routes', () => {
        component.find('.Header__nav-item').at(1).simulate('click');
        expect(component).toMatchSnapshot();
      });
});


describe('Test Router', () => {
      const auth = new Auth();
      auth.isAuthenticated = function () { return true; };
      auth.login = function () { return true; };
      auth.logout = function () { return true; };

      const component = mount(<MemoryRouter initialEntries={['/labbooks/']}>
                                <Routes />
                              </MemoryRouter>);

      it('check history props is labbook', () => {
        expect(component.node.history.location.pathname === '/labbooks/').toBeTruthy();
      });


      it('check history props is datasets', () => {
        component.node.history.replace('/datasets/');
        expect(component.node.history.location.pathname === '/datasets/').toBeTruthy();
      });

      // if('test datasets snapshot'){
      //   expect(component.node).toMatchSnapshot();
      // }
});


describe('Test Labbooks routes', () => {
      const auth = new Auth();
      auth.isAuthenticated = function () { return true; };
      auth.login = function () { return true; };
      auth.logout = function () { return true; };

      it('with data', () => {
        const component = shallow(
          <MemoryRouter initialEntries={[`/labbooks/${variables.name}/`]}>
              <Routes />
            </MemoryRouter>,
        );
        expect(component).toMatchSnapshot();
      });
      it('without data', () => {
        const component = shallow(
            <MemoryRouter initialEntries={[`/labbooks/${variables.name}/`]}>
              <Routes />
            </MemoryRouter>,
        );
        console.log(component);
        console.log(component.node);
        console.log(component.node.children);
        expect(component).toMatchSnapshot();
      });

      it('test callback', () => {
        const component = shallow(
            <MemoryRouter initialEntries={['/callback']}>

              <Routes />

            </MemoryRouter>,
        );

        expect(component).toMatchSnapshot();
      });
});
