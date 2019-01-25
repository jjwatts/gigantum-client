// vendor
import React, { Component } from 'react';
import classNames from 'classnames';
// assets
import './LabbookFilterBy.scss';


class LabbookFilterBy extends Component {

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
      LabbookFilterBy__selector: true,
      'LabbookFilterBy__selector--open': props.filterMenuOpen,
      'LabbookFilterBy__selector--collapsed': !props.filterMenuOpen,
    });

    const labbookFilterMenuCSS = classNames({
      'LabbookFilterBy__menu box-shadow': true,
      hidden: !props.filterMenuOpen,
    });

    return (

      <div className="LabbookFilterBy">
        Filter by:
        <span
          className={labbookFilterSeclectorCSS}
          onClick={props.toggleFilterMenu}
        >
          {this._getFilter()}
        </span>

        <ul
          className={labbookFilterMenuCSS}>
          <li
            className="LabbookFilterBy__list-item"
            onClick={() => props.setFilter('all')}>
            All {props.filter === 'all' ? '✓ ' : ''}
          </li>
          <li
            className="LabbookFilterBy__list-item"
            onClick={() => props.setFilter('owner')}>
           My Projects {props.filter === 'owner' ? '✓ ' : ''}
          </li>
          <li
            className="LabbookFilterBy__list-item"
            onClick={() => props.setFilter('others')}>
            Shared with me {props.filter === 'others' ? '✓ ' : ''}
          </li>
        </ul>

      </div>);
  }
}

export default LabbookFilterBy;
