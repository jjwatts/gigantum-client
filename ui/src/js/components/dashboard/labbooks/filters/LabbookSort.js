// vendor
import React, { Component } from 'react';
import classNames from 'classnames';
// assets
import './LabbookSort.scss';


class LabbookSort extends Component {
  /**
    *  @param {}
    *  gets orderBy and sort value and displays it to the UI more clearly
    *  @return{}
  */
  _getSelectedSort() {
    if (this.props.orderBy === 'modified_on') {
      const modifiedDirection = this.props.sort === 'asc' ? '(Oldest)' : '(Newest)';
      return `Modified Date ${modifiedDirection}`;
    } else if (this.props.orderBy === 'created_on') {
      const creationDirection = this.props.sort === 'asc' ? '(Oldest)' : '(Newest)';
      return `Creation Date ${creationDirection}`;
    }

    return this.props.sort === 'asc' ? 'A-Z' : 'Z-A';
  }

  render() {
    const { props } = this;

    const labbookSortSeclectorCSS = classNames({
      LabbookSort__selector: true,
      'LabbookSort__selector--open': props.sortMenuOpen,
      'LabbookSort__selector--collapsed': !props.sortMenuOpen,
    });

    const labbookSortMenuCSS = classNames({
      'LabbookSort__menu box-shadow': true,
      hidden: !props.sortMenuOpen,
    });

    return (

      <div className="LabbookSort">
        Sort by:

        <span
          className={labbookSortSeclectorCSS}
          onClick={props.toggleSortMenu}
        >
          {this._getSelectedSort()}
        </span>

        <ul className={labbookSortMenuCSS}>

          <li
            className="LabbookSort__list-item"
            onClick={() => props.setSortFilter('modified_on', 'desc')}
          >
            Modified Date (Newest) {props.orderBy === 'modified_on' && props.sort !== 'asc' ? '✓ ' : ''}
          </li>

          <li
            className="LabbookSort__list-item"
            onClick={() => props.setSortFilter('modified_on', 'asc')}
          >
            Modified Date (Oldest) {props.orderBy === 'modified_on' && props.sort === 'asc' ? '✓ ' : ''}
          </li>

          <li
            className="LabbookSort__list-item"
            onClick={() => props.setSortFilter('created_on', 'desc')}
          >
            Creation Date (Newest) {props.orderBy === 'created_on' && props.sort !== 'asc' ? '✓ ' : ''}
          </li>

          <li
            className="LabbookSort__list-item"
            onClick={() => props.setSortFilter('created_on', 'asc')}
          >
            Creation Date (Oldest) {props.orderBy === 'created_on' && props.sort === 'asc' ? '✓ ' : ''}
          </li>

          <li
            className="LabbookSort__list-item"
            onClick={() => props.setSortFilter('name', 'asc')}
          >
            A-Z {props.orderBy === 'name' && props.sort === 'asc' ? '✓ ' : ''}
          </li>

          <li
            className="LabbookSort__list-item"
            onClick={() => props.setSortFilter('name', 'desc')}
          >
            Z-A {this.props.orderBy === 'name' && this.props.sort !== 'asc' ? '✓ ' : ''}
          </li>

        </ul>

      </div>);
  }
}

export default LabbookSort;
