// vendor
import React, { Component } from 'react';
// components
import Tooltip from 'Components/common/Tooltip';
// assets
import './PackageActions.scss';

export default class PackageActions extends Component {

  /**
  *  @param{}
  *  removes singular package
  */
  _updatePackage() {
    const { props } = this;
    const data = {
      packages: [{
        ...props.packageNode,
        version: props.packageNode.latestVersion,
      }],
      duplicates: [props.id],
    };
    props.selectPackages(true);
    props.setBuildingState(true);
    const callback = () => {
      props.buildCallback();
    };
    props.packageMutations.addPackages(data, callback);
  }

  /**
  *  @param{}
  *  removes singular package
  */
  _removePackage() {
    const { props } = this;
    const data = {
      packages: [props.packageNode],
    };
    props.selectPackages(true);
    props.setBuildingState(true);
    const callback = () => {
      props.buildCallback();
    };
    props.packageMutations.removePackages(data, callback);
  }

  render() {
    const { props } = this;
    const disableUpdate = (!props.latestVersion) || (props.version === props.latestVersion) || props.isLocked;
    const disableDelete = (props.fromBase) || (props.isLocked);

    return (
      <div className="PackageActions flex flex--column justify--space-between">
        <button
          className="Btn Btn--medium Btn--round Btn__upArrow-grey"
          type="button"
          onClick={() => this._updatePackage()}
          disabled={disableUpdate}
        />
        <button
          className="Btn Btn--medium Btn--round Btn__delete-grey"
          type="button"
          onClick={() => this._removePackage()}
          disabled={disableDelete}
        />
      </div>
    );
  }
}
