// vendor
import React, { Component } from 'react';
import classNames from 'classnames';
// assets
import './DashboardDropdown.scss';


class FilterByDropdown extends Component {
  /**
    *  @param {}
    *  gets filter value and displays it to the UI more clearly
    * @return {}
  */
  _getFilter() {
    switch (this.props.filter) {
      case 'all':
        return 'All';
      case 'owner':
        return 'My Projects';
      case 'others':
        return 'Shared With Me';
      default:
        return this.props.filter;
    }
  }

  render() {
    const { props } = this;

    const labbookFilterSeclectorCSS = classNames({
      'Dropdown__filter-selector Dropdown': true,
      'Dropdown--open': props.filterMenuOpen,
      'Dropdown--collapsed': !props.filterMenuOpen,
    });

    const labbookFilterMenuCSS = classNames({
      'Dropdown__menu box-shadow': true,
      hidden: !props.filterMenuOpen,
    });

    return (

      <div className="DashboardDropdown column-4-span-3 padding--0">
        <div>Filter by:</div>
        <div
          className={labbookFilterSeclectorCSS}
          onClick={props.toggleFilterMenu}
        >
          {this._getFilter()}
        </div>

        <ul
          className={labbookFilterMenuCSS}
        >
          <li
            className="DashboardDropdown__list-item"
            onClick={() => props.setFilter('all')}
          >
            All
            {props.filter === 'all' ? ' ✓ ' : ''}
          </li>
          <li
            className="DashboardDropdown__list-item"
            onClick={() => props.setFilter('owner')}
          >
           My
            {` ${props.type}`}
            {props.filter === 'owner' ? ' ✓ ' : ''}
          </li>
          <li
            className="DashboardDropdown__list-item"
            onClick={() => props.setFilter('others')}
          >
            Shared with me
            {props.filter === 'others' ? ' ✓ ' : ''}
          </li>
        </ul>

      </div>);
  }
}

export default FilterByDropdown;
