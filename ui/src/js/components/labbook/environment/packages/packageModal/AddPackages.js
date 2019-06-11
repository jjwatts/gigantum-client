// vendor
import React, { Component } from 'react';
import classNames from 'classnames';
import { boundMethod } from 'autobind-decorator';
// store
import store from 'JS/redux/store';
// components
import AddPackageForm from './AddPackageForm';
import Requirements from './Requirements';
import PackageQueue from './PackageQueue';
// assets
import './AddPackages.scss';
// util
import PackageLookup from '../utils/PackageLookup';

export default class AddPackages extends Component {

  state = {
    selectedEntryMethod: 'manual',
    packageQueue: [],
  };

  /**
  *  @param {}
  *  installs packages in queue
  */
  @boundMethod
  _installPackages() {
    const { props, state } = this;
    const existingPackages = props.packages;
    const newPackages = state.packageQueue.slice();
    const existingPackagesObject = {};
    const duplicates = [];
    existingPackages.forEach((pkg) => {
      if (existingPackagesObject[pkg.manager]) {
        existingPackagesObject[pkg.manager][pkg.package] = {
          id: pkg.id,
        };
      } else {
        existingPackagesObject[pkg.manager] = {
          [pkg.package]: {
            id: pkg.id,
          },
        };
      }
    });
    newPackages.forEach((newPackage) => {
      if (existingPackagesObject[newPackage.manager] && existingPackagesObject[newPackage.manager][newPackage.package]) {
        duplicates.push(existingPackagesObject[newPackage.manager][newPackage.package].id);
      }
    });
    const data = {
      packages: newPackages,
      duplicates,
    };
    props.setBuildingState(true);
    const buildCb = (response, error, id) => {
      props.setBuildId(id);
    };
    const callback = () => {
      props.buildCallback(buildCb);
    };
    props.packageMutations.addPackages(data, callback);
  }

  /**
  *  @param {String} selectedEntryMethod
  *  sets entry method state
  */
  @boundMethod
  _setSelectedEntryMethod(selectedEntryMethod) {
    this.setState({ selectedEntryMethod });
  }

  /**
  *  @param {Object} file
  *  parses requirements file
  *  @return {}
  */
  @boundMethod
  _parseFile(file) {
    const reader = new FileReader();
    reader.onload = (evt) => {
      const packages = evt.target.result.split('\n');
      packages.forEach((pkg) => {
        const splitPackage = pkg.split('==');
        this._queuePackage({ manager: 'pip', package: splitPackage[0], version: splitPackage[1] })
      });
    };
    reader.readAsText(file);
  }

  /**
  *  @param {Object} packageData
  *  @param {Number} index
  *  runs verification on current entered package
  *  @return {}
  */
  @boundMethod
  _queuePackage(packageData, index) {
    const { state, props } = this;
    const newPackageData = [packageData];
    const newPackageQueue = state.packageQueue.slice();
    const currentPosition = index !== undefined ? index : newPackageQueue.length;
    if (index !== undefined) {
      newPackageQueue[index] = Object.assign({}, newPackageData[0], { verified: false, error: false });
    } else {
      newPackageQueue.push(Object.assign({}, newPackageData[0], { verified: false }));
    }
    this.setState({ packageQueue: newPackageQueue });
    PackageLookup.query(props.name, props.owner, newPackageData).then((response) => {
      const newState = this.state;
      const responsePackageQueue = newState.packageQueue.slice();
      if (response.errors) {
        responsePackageQueue[currentPosition].error = true;
        responsePackageQueue[currentPosition].verified = true;
        this.setState({ packageQueue: responsePackageQueue });
      } else {
        const {
          version,
          isValid,
          latestVersion,
          description,
        } = response.data.labbook.checkPackages[0];

        responsePackageQueue[currentPosition].latestVersion = latestVersion;
        responsePackageQueue[currentPosition].version = version;
        responsePackageQueue[currentPosition].description = description;
        responsePackageQueue[currentPosition].verified = true;
        responsePackageQueue[currentPosition].error = !isValid;
        this.setState({ packageQueue: responsePackageQueue });
      }
    });
  }

  /**
  *  @param {Integer} index
  *  removes package from queue
  *  @return {}
  */
  @boundMethod
  _removePackageFromQueue(index) {
    const { state } = this;
    const newPackageQueue = state.packageQueue.slice();
    newPackageQueue.splice(index, 1);
    this.setState({ packageQueue: newPackageQueue });
  }

  render() {
    const { props, state } = this;
    const manualEntryCSS = classNames({
      'AddPackages__header--manual flex-1': true,
      'AddPackages__header-title': true,
      'AddPackages__header--selected': state.selectedEntryMethod === 'manual',
    });
    const fileEntryCSS = classNames({
      'AddPackages__header--file flex-1': true,
      'AddPackages__header-title': true,
      'AddPackages__header--selected': state.selectedEntryMethod === 'file',
    });

    const disableInstall = state.packageQueue.length === 0 || state.packageQueue.filter(pkg => pkg.verified && !pkg.error).length !== state.packageQueue.length;

    return (
      <div className="AddPackages">
        <div className="AddPackages__header--top">
          <h4>Add Packages</h4>
        </div>
        <div className="AddPackages__body flex">
          <div className="AddPackages__entry">
            <div className="AddPackages__header flex">
              <h5
                className={manualEntryCSS}
                onClick={() => this._setSelectedEntryMethod('manual')}
              >
                Enter Packages
              </h5>
              <h5
                className={fileEntryCSS}
                onClick={() => this._setSelectedEntryMethod('file')}
              >
                Add Requirements File
              </h5>
            </div>
            {
              state.selectedEntryMethod === 'file' && (
                <Requirements
                  queuePackage={this._queuePackage}
                />
              )
            }
            {
              state.selectedEntryMethod === 'manual' && (
                <AddPackageForm
                  queuePackage={this._queuePackage}
                  defaultManager={props.base.packageManagers[0]}
                  base={props.base}
                  buildCallback={props.buildCallback}
                />
              )
            }
          </div>
          <PackageQueue
            queuePackage={this._queuePackage}
            packageQueue={state.packageQueue}
            disableInstall={disableInstall}
            toggleModal={props.toggleModal}
            installPackages={this._installPackages}
            removePackageFromQueue={this._removePackageFromQueue}
            buildCallback={props.buildCallback}
          />
        </div>
      </div>
    );
  }
}
