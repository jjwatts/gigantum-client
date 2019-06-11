// vendor
import React, { Component } from 'react';
import classNames from 'classnames';
// components
import Tooltip from 'Components/common/Tooltip';
// assets
import './PackageTable.scss';

export default class PackageHeader extends Component {
  /**
  *  @param{}
  *  removes singular package
  */
  _removePackages() {
    const { props } = this;
    const data = {
      packages: [...props.selectedPackages.values()],
    };

    props.setBuildingState(true);
    const callback = () => {
      props.selectPackages(true);
      props.buildCallback();
    };
    props.packageMutations.removePackages(data, callback);
  }

  render() {
    const { props } = this;
    const multiSelectButtonCSS = classNames({
      CheckboxMultiselect: true,
      CheckboxMultiselect__check: props.multiSelect === 'all',
      CheckboxMultiselect__uncheck: props.multiSelect === 'none',
      CheckboxMultiselect__partial: props.multiSelect === 'partial',
    });
    const managerHeaderCSS = classNames({
      'Table__Header--sort Btn--noStyle': true,
      PackageHeader__manager: true,
      'Table__Header--asc': props.sort === 'manager' && !props.reverse,
      'Table__Header--desc': props.sort === 'manager' && props.reverse,
    });
    const nameHeaderCSS = classNames({
      'Table__Header--sort Btn--noStyle flex-1': true,
      PackageHeader__name: true,
      'Table__Header--asc': props.sort === 'package' && !props.reverse,
      'Table__Header--desc': props.sort === 'package' && props.reverse,
    });
    return (
      <div className="Table__Header">
        {
          (props.selectedPackages.size !== 0)
          && (
          <div className="PackageHeader__toolbar flex align-items--center">
            <div className="PackageHeader__toolbar-text">
              {`${props.selectedPackages.size} packages selected`}
            </div>
            <button
              type="button"
            >
              Update
            </button>
            <button
              type="button"
              onClick={() => this._removePackages()}
            >
              Delete
            </button>
          </div>
          )
        }
        <div className="flex align-items--end">
          <button
            className={multiSelectButtonCSS}
            onClick={() => { props.selectPackages(); }}
            type="button"
          />
          <button
            className={managerHeaderCSS}
            onClick={() => props.handleSort('manager')}
            type="button"
          >
            Package Manager
          </button>
          <button
            className={nameHeaderCSS}
            onClick={() => props.handleSort('package')}
            type="button"
          >
            Package Name
          </button>
          <div className="flex">
            <div className="PackageHeader__version">Version</div>
            <div className="PackageHeader__actions">Actions</div>
          </div>
        </div>
      </div>
    );
  }
}
