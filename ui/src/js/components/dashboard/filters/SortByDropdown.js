// vendor
import React, { Component } from 'react';
import classNames from 'classnames';
// assets
import './DashboardDropdown.scss';


class SortByDropdown extends Component {
  /**
    *  @param {}
    *  gets orderBy and sort value and displays it to the UI more clearly
    *  @return{}
  */
  _getSelectedSort() {
    if (this.props.orderBy === 'modified_on') {
      const modifiedDirection = this.props.sort === 'asc' ? '(Oldest)' : '(Newest)';
      return `Modified Date ${modifiedDirection}`;
    } if (this.props.orderBy === 'created_on') {
      const creationDirection = this.props.sort === 'asc' ? '(Oldest)' : '(Newest)';
      return `Creation Date ${creationDirection}`;
    }

    return this.props.sort === 'asc' ? 'A-Z' : 'Z-A';
  }

  render() {
    const { props } = this;

    const labbookSortSeclectorCSS = classNames({
      'Dropdown__sort-selector Dropdown': true,
      'Dropdown--open': props.sortMenuOpen,
      'Dropdown--collapsed': !props.sortMenuOpen,
    });

    const labbookSortMenuCSS = classNames({
      'Dropdown__menu box-shadow': true,
      hidden: !props.sortMenuOpen,
    });

    return (

      <div className="DashboardDropdown column-4-span-3 padding--0">
        <div>Sort by:</div>

        <div
          className={labbookSortSeclectorCSS}
          onClick={props.toggleSortMenu}
        >
          {this._getSelectedSort()}
        </div>

        <ul className={labbookSortMenuCSS}>

          <li
            className="DashboardDropdown__list-item"
            onClick={() => props.setSortFilter('modified_on', 'desc')}
          >
            Modified Date (Newest)
            { (props.orderBy === 'modified_on') && (props.sort !== 'asc') ? ' ✓ ' : '' }
          </li>

          <li
            className="DashboardDropdown__list-item"
            onClick={() => props.setSortFilter('modified_on', 'asc')}
          >
            Modified Date (Oldest)
            { (props.orderBy === 'modified_on') && (props.sort === 'asc') ? ' ✓ ' : '' }
          </li>

          <li
            className="DashboardDropdown__list-item"
            onClick={() => props.setSortFilter('created_on', 'desc')}
          >
            Creation Date (Newest)
            { (props.orderBy === 'created_on') && (props.sort !== 'asc') ? ' ✓ ' : '' }
          </li>

          <li
            className="DashboardDropdown__list-item"
            onClick={() => props.setSortFilter('created_on', 'asc')}
          >
            Creation Date (Oldest)
            { (props.orderBy === 'created_on') && (props.sort === 'asc') ? ' ✓ ' : ''}
          </li>

          <li
            className="DashboardDropdown__list-item"
            onClick={() => props.setSortFilter('name', 'asc')}
          >
            A-Z
            { (props.orderBy === 'name') && (props.sort === 'asc') ? ' ✓ ' : '' }
          </li>

          <li
            className="DashboardDropdown__list-item"
            onClick={() => props.setSortFilter('name', 'desc')}
          >
            Z-A
            { (props.orderBy === 'name') && (props.sort !== 'asc') ? ' ✓ ' : '' }
          </li>

        </ul>

      </div>);
  }
}

export default SortByDropdown;
