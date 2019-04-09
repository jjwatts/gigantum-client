// vendor
import React, { Component, Fragment } from 'react';
import classNames from 'classnames';
import { Link } from 'react-router-dom';
import { boundMethod } from 'autobind-decorator';
// config
import Config from 'JS/config';
// store
import store from 'JS/redux/store';
import {
  setSyncingState,
  setPublishingState,
  setExportingState,
  setModalVisible,
  setUpdateDetailView,
} from 'JS/redux/reducers/labbook/labbook';
// components
import Tooltip from 'Components/common/Tooltip';
// assets
import './Navigation.scss';

class Navigation extends Component {
  /**
    @param {string} componentName - input string componenetName
    updates state of selectedComponent
    updates history prop
  */
  @boundMethod
  _setSelectedComponent(componentName) {
    if (componentName !== this.props.selectedComponent) {
      if (store.getState().detailView.selectedComponent === true) {
        setUpdateDetailView(false);
      }
    }
  }

  /**
    @param {object} item
    @returns {Number} selectedIndex
  */
  @boundMethod
  _getSelectedIndex() {
    const { props } = this;


    const pathArray = this.props.location.pathname.split('/');


    const defaultOrder = Config[`${this.props.sectionType}DefaultNavOrder`];


    const selectedPath = (pathArray.length > 4) ? pathArray[pathArray.length - 1] : defaultOrder[0];


    const selectedIndex = defaultOrder.indexOf(selectedPath);
    return selectedIndex;
  }

  render() {
    const { props, state } = this;


    const { visibility } = props[props.sectionType];


    const selectedIndex = this._getSelectedIndex();


    const labbookLockCSS = classNames({
      [`Header__${visibility}`]: true,
      [`Header__${visibility}--sticky`]: props.isSticky,
    });


    const section = (props.sectionType === 'labbook') ? 'projects' : 'datasets';


    const name = (props.sectionType === 'labbook') ? props.match.params.labbookName : props.match.params.datasetName;

    return (
      <div className="Navigation flex-0-0-auto">

        <ul className="Tabs flex flex--row">
          {
          Config[`${this.props.sectionType}_navigation_items`].map((item, index) => {
            const pathArray = props.location.pathname.split('/');


            const selectedPath = (pathArray.length > 4) ? pathArray[pathArray.length - 1] : 'overview';
            // sets avtive nav item to overview if there is no menu item in the url

            const navItemCSS = classNames({
              Tab: true,
              'Tab--selected': (selectedPath === item.id),
            });

            return (
              <li
                id={item.id}
                key={item.id}
                className={navItemCSS}
                onClick={() => this._setSelectedComponent(item.id)}
                title={Config.navTitles[item.id]}
              >

                <Link
                  onClick={this._scrollToTop}
                  to={`../../../${section}/${props.owner}/${name}/${item.id}`}
                  replace
                >
                  {item.name}
                </Link>

              </li>);
          })
        }
        </ul>

      </div>
    );
  }
}

export default Navigation;
