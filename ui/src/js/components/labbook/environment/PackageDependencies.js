// vendor
import React, { Component } from 'react';
import { createPaginationContainer, graphql } from 'react-relay';
import classNames from 'classnames';
import uuidv4 from 'uuid/v4';
import { connect } from 'react-redux';
import { boundMethod } from 'autobind-decorator';
// store
import store from 'JS/redux/store';
import {
  setPackageMenuVisible,
} from 'JS/redux/actions/labbook/environment/packageDependencies';
import { setErrorMessage, setWarningMessage } from 'JS/redux/actions/footer';
import { setContainerMenuWarningMessage } from 'JS/redux/actions/labbook/environment/environment';
import { setBuildingState } from 'JS/redux/actions/labbook/labbook';
import { setLookingUpPackagesState } from 'JS/redux/actions/labbook/containerStatus';
// Mutations
import AddPackageComponentsMutation from 'Mutations/environment/AddPackageComponentsMutation';
import RemovePackageComponentsMutation from 'Mutations/environment/RemovePackageComponentsMutation';
// config
import config from 'JS/config';
// components
import ButtonLoader from 'Components/common/ButtonLoader';
import Loader from 'Components/common/Loader';
// helpers
import PackageLookup from './PackageLookup';
// assets
import './PackageDependencies.scss';


let owner;
let updateCheck = {};

class PackageDependencies extends Component {
  constructor(props) {
    super(props);

    const { labbookName } = store.getState().routes;
    owner = store.getState().routes.owner; // TODO clean this up when fixing dev environments

    this.state = {
      owner,
      labbookName,
      selectedTab: '',
      packageMenuVisible: false,
      packageName: '',
      version: '',
      packages: [],
      searchValue: '',
      forceRender: false,
      disableInstall: false,
      installDependenciesButtonState: '',
      hardDisable: false,
      removalPackages: {},
      updatePackages: {},
      latestVersionPackages: [],
      currentPackages: this.props.environment.packageDependencies,
    };
  }

  static getDerivedStateFromProps(props, state) {
    const packages = props.environment.packageDependencies.edges;

    const latestVersionPackages = packages.map((edge) => {
      const packageObject = { ...edge.node };
      if (props.packageLatestVersions.length > 0) {
        props.packageLatestVersions.forEach((latestVersionEdge) => {
          if ((packageObject.manager === latestVersionEdge.node.manager) && (packageObject.package === latestVersionEdge.node.package)) {
            packageObject.latestVersion = latestVersionEdge.node.latestVersion;
          }
        });
      }
      return packageObject;
    });

    return {
      ...state,
      latestVersionPackages,
    };
  }

  /*
    handle state and addd listeners when component mounts
  */
  componentDidMount() {
    const { props, state } = this;
    if (state.selectedTab === '') {
      this.setState({ selectedTab: props.base.packageManagers[0] });
    }
  }

  componentDidUpdate() {
    const { props, state } = this;
    const newPackages = props.environment.packageDependencies;

    if (newPackages.edges && (newPackages.edges.length < 11)
      && newPackages.pageInfo.hasNextPage && !state.loadingMore) {
      this._loadMore();
    }

    const newUpdatePackages = Object.assign({}, state.updatePackages, updateCheck);
    Object.keys(newUpdatePackages).forEach((manager) => {
      Object.keys(newUpdatePackages[manager]).forEach((pkg) => {
        if (!newUpdatePackages[manager][pkg].version) {
          delete newUpdatePackages[manager][pkg];
        }
      });
    });

    if (JSON.stringify(newUpdatePackages) !== JSON.stringify(state.updatePackages)) {
      this.setState({ updatePackages: newUpdatePackages });
    }
    updateCheck = {};
  }

  /**
  *  @param{}
  *  triggers relay pagination function loadMore
  *  increments by 10
  *  logs callback
  */
  @boundMethod
  _loadMore() {
    const { props, state } = this;
    if (!state.loadingMore) {
      this.setState({ loadingMore: true });

      const self = this;

      props.relay.loadMore(
        10, // Fetch the next 5 feed items
        (response, error) => {
          self.setState({ loadingMore: false });

          if (error) {
            console.error(error);
          }
          if (props.environment.packageDependencies
           && props.environment.packageDependencies.pageInfo.hasNextPage) {
            self._loadMore();
          }
        },
        {
          cursor: props.environment.packageDependencies.pageInfo.endCursor,
        },
      );
    }
  }

  /**
  *  @param {Object}
  *  hides packagemanager modal
  */
  @boundMethod
  _setSelectedTab(selectedTab, isSelected) {
    const { props, state } = this;
    const packageMenuVisible = isSelected ? props.packageMenuVisible : false;
    const packages = isSelected ? state.packages : [];

    this.setState({
      selectedTab,
      packageMenuVisible,
      packages,
    });
  }

  /**
  *  @param {object} node
  *  triggers remove package mutation
  */
  _removePackage() {
    const { status } = store.getState().containerStatus;
    const { props } = this;
    const canEditEnvironment = config.containerStatus.canEditEnvironment(status) && !props.isLocked;

    this.setState({ hardDisable: true });
    // have to get state after setting state
    const { state } = this;

    if (navigator.onLine) {
      if (canEditEnvironment) {
        if (!state.hardDisable) {
          const { labbookName, owner } = store.getState().routes;


          const { environmentId } = props;


          const manager = state.selectedTab;


          const removalPackages = Object.keys(state.removalPackages[manager]);


          const removalIDArr = Object.values(state.removalPackages[manager]);


          const clientMutationId = uuidv4();


          const connection = 'PackageDependencies_packageDependencies';

          this.setState({ removalPackages: {}, updatePackages: {} });

          RemovePackageComponentsMutation(
            labbookName,
            owner,
            manager,
            removalPackages,
            removalIDArr,
            clientMutationId,
            environmentId,
            connection,
            (response, error) => {
              if (error) {
                console.log(error);
              }

              this.setState({ hardDisable: false });
              props.buildCallback();
            },
          );
        }
      } else {
        this._promptUserToCloseContainer();
        this.setState({ hardDisable: false });
      }
    } else {
      props.setErrorMessage('Cannot remove package at this time.', [{ message: 'An internet connection is required to modify the environment.' }]);
    }
  }

  /**
  *  @param {object} node
  *  triggers remove package mutation
  */
  _toggleAddPackageMenu() {
    const { status } = store.getState().containerStatus;
    const canEditEnvironment = config.containerStatus.canEditEnvironment(status) && !this.props.isLocked;

    if (navigator.onLine) {
      if (canEditEnvironment) {
        this.props.setPackageMenuVisible(!this.props.packageMenuVisible);
      } else {
        this._promptUserToCloseContainer();
      }
    } else {
      this.props.setErrorMessage('Cannot add package at this time.', [{ message: 'An internet connection is required to modify the environment.' }]);
    }
  }

  /**
  *  @param {evt}
  *  updates package name in components state
  */
  _updatePackageName(evt) {
    this.setState({ packageName: evt.target.value });

    if (evt.key === 'Enter' && evt.target.value.length) {
      this._addStatePackage(evt);
    }
  }

  /**
  *  @param {evt}
  *  updates package version in components state
  */
  _updateVersion(evt) {
    this.setState({ version: evt.target.value });

    if (evt.key === 'Enter') {
      this._addStatePackage(evt);
    }
  }

  /**
  *  @param {}
  *  updates packages in state
  */
  _addStatePackage() {
    const packages = this.state.packages;

    const { packageName, version } = this.state;
    const manager = this.state.selectedTab;

    packages.push({
      package: packageName,
      version,
      manager,
      validity: 'valid',
    });

    this.setState({
      packages,
      packageName: '',
      version: '',
    });

    this.inputPackageName.value = '';
    this.inputVersion.value = '';
  }

  /**
  *  @param {}
  *  user redux to open stop container button
  *  sends message to footer
  */
  _promptUserToCloseContainer() {
    this.props.setContainerMenuWarningMessage('Stop Project before editing the environment. \n Be sure to save your changes.');
  }

  /**
  *  @param {}
  *  updates packages in state
  */
  _removeStatePackages(node, index) {
    const packages = this.state.packages;

    packages.splice(index, 1);

    this.setState({
      packages,
    });
  }

  /**
  *  @param {}
  *  triggers add package mutation
  */
  @boundMethod
  _addPackageComponentsMutation() {
    const { props } = this;
    const self = this;


    let { packages } = this.state;


    let filteredInput = [];

    const { labbookName, owner } = store.getState().routes;


    const { environmentId } = props;

    packages = packages.map((pkg) => {
      pkg.validity = 'checking';
      filteredInput.push({
        manager: pkg.manager,
        package: pkg.package,
        version: pkg.version,
      });
      return pkg;
    }).slice();

    this.setState({
      packages,
      disableInstall: true,
      installDependenciesButtonState: 'loading',
    });

    setBuildingState(true);
    props.setLookingUpPackagesState(true);

    PackageLookup.query(labbookName, owner, filteredInput).then((response) => {
      props.setLookingUpPackagesState(false);
      if (response.errors) {
        packages = packages.map((pkg) => {
          pkg.validity = 'valid';
          return pkg;
        });
        this.setState({ disableInstall: false, installDependenciesButtonState: 'error', packages });
        setTimeout(() => {
          self.setState({ installDependenciesButtonState: '' });
        }, 2000);
        props.setErrorMessage('Error occured looking up packages', response.errors);

        setBuildingState(false);
      } else {
        let resPackages = response.data.labbook.packages;
        let invalidCount = 0;
        let lastInvalid = null;
        resPackages = resPackages.map((pkg) => {
          if (pkg.isValid) {
            pkg.validity = 'valid';
          } else {
            pkg.validity = 'invalid';
            invalidCount++;
            lastInvalid = { package: pkg.package, manager: pkg.manager };
          }
          return pkg;
        });
        this.setState({ packages: resPackages });

        if (invalidCount) {
          const message = invalidCount === 1 ? `Unable to find package '${lastInvalid.package}'.` : `Unable to find ${invalidCount} packages.`;

          props.setErrorMessage('Packages could not be installed', [{ message }]);

          setBuildingState(false);
          this.setState({
            disableInstall: false,
            installDependenciesButtonState: '',
          });
        } else {
          filteredInput = [];
          const flatPackages = [];


          const versionReference = {};


          const existingPackages = props.environment.packageDependencies;

          resPackages.forEach((pkg) => {
            flatPackages.push(pkg.package);
          });

          const duplicates = existingPackages.edges.reduce((filtered, option) => {
            if (flatPackages.indexOf(option.node.package) > -1) {
              filtered.push(option.node.id);
              versionReference[option.node.package] = option.node.version;
            }

            return filtered;
          }, []);

          resPackages = resPackages.forEach((pkg) => {
            versionReference[pkg.package] !== pkg.version ? filteredInput.push({ package: pkg.package, manager: pkg.manager, version: pkg.version }) : duplicates.splice(duplicates.indexOf(pkg.id), 1);
            flatPackages.push(pkg.package);
          });

          if (filteredInput.length) {
            AddPackageComponentsMutation(
              labbookName,
              owner,
              filteredInput,
              1,
              environmentId,
              'PackageDependencies_packageDependencies',
              duplicates,
              (response, error) => {
                if (error) {
                  self.setState({
                    disableInstall: false,
                    installDependenciesButtonState: 'error',
                  });

                  setTimeout(() => {
                    self.setState({ installDependenciesButtonState: '' });
                  }, 2000);

                  props.setErrorMessage('Error adding packages.', error);
                } else {
                  self.setState({
                    disableInstall: false,
                    packages: [],
                    installDependenciesButtonState: 'finished',
                  });
                  props.fetchPackageVersion();
                  props.buildCallback();
                  setTimeout(() => {
                    self.setState({ installDependenciesButtonState: '' });
                  }, 2000);
                }
              },
            );
          } else {
            this.props.setWarningMessage('All packages attempted to be installed already exist.');
            setBuildingState(false);
            self.setState({
              disableInstall: false,
              packages: [],
              installDependenciesButtonState: 'error',
            });
            setTimeout(() => {
              self.setState({ installDependenciesButtonState: '' });
            }, 2000);
          }
        }
      }
    });
  }

  /**
  *  @param {evt}
  *  remove dependency from list
  */
  _setSearchValue(evt) {
    this.setState({ searchValue: evt.target.value });
  }

  /** *
  *  @param {evt}
  *  get tabs data
  * */
  _getPackmanagerTabs() {
    const { props } = this;
    const tabs = props.base && props.base.packageManagers.map((packageName) => {
      let count = 0;
      props.environment.packageDependencies.edges.forEach((edge) => {
        if (packageName === edge.node.manager) {
          count += 1;
        }
      });
      return { tabName: packageName, count };
    });
    return tabs;
  }

  /** *
  *  @param {String, String} pkg manager
  *  adds to removalpackages state pending removal of packages
  * */
  _addRemovalPackage(node) {
    const { state } = this;
    const { manager, id, version } = node;
    const pkg = node.package;
    const newRemovalPackages = Object.assign({}, state.removalPackages);
    const newUpdatePackages = Object.assign({}, state.updatePackages);
    const updateAvailable = node.latestVersion && (node.version !== node.latestVersion);

    if (newRemovalPackages[manager]) {
      const index = Object.keys(newRemovalPackages[manager]).indexOf(pkg);

      if (index > -1) {
        delete newRemovalPackages[manager][pkg];
      } else {
        newRemovalPackages[manager][pkg] = id;
      }
    } else {
      newRemovalPackages[manager] = { [pkg]: id };
    }

    if (!node.version) {
      if (updateCheck[manager]) {
        updateCheck[manager][pkg] = { id, oldVersion: node.version };
      } else {
        updateCheck[manager] = { [pkg]: { id, oldVersion: node.version } };
      }
    }

    if (updateAvailable) {
      if (newUpdatePackages[manager]) {
        const index = Object.keys(newUpdatePackages[manager]).indexOf(pkg);

        if (index > -1) {
          delete newUpdatePackages[manager][pkg];
        } else {
          newUpdatePackages[manager][pkg] = { id, version: node.latestVersion };
        }
      } else {
        newUpdatePackages[manager] = { [pkg]: { id, version: node.latestVersion } };
      }
    }
    this.setState({ removalPackages: newRemovalPackages, updatePackages: newUpdatePackages });
  }

  /** *
  *  @param {}
  *  processes update packages and attempts to update
  * */
  @boundMethod
  _updatePackages() {
    const { props, state } = this;
    const { status } = store.getState().containerStatus;
    const canEditEnvironment = config.containerStatus.canEditEnvironment(status) && !props.isLocked;
    const self = this;

    if (navigator.onLine) {
      if (canEditEnvironment) {
        const { labbookName, owner } = store.getState().routes;
        const { environmentId } = props;
        const filteredInput = [];
        const duplicates = [];

        Object.keys(state.updatePackages).forEach((manager) => {
          Object.keys(state.updatePackages[manager]).forEach((pkg) => {
            filteredInput.push({
              manager,
              package: pkg,
              version: state.updatePackages[manager][pkg].version,
            });
            duplicates.push(state.updatePackages[manager][pkg].id);
          });
        });
        AddPackageComponentsMutation(
          labbookName,
          owner,
          filteredInput,
          1,
          environmentId,
          'PackageDependencies_packageDependencies',
          duplicates,
          (response, error) => {
            this.setState({ removalPackages: {}, updatePackages: {} });

            if (error) {
              this.setState({ disableInstall: false, installDependenciesButtonState: 'error' });
              setTimeout(() => {
                self.setState({ installDependenciesButtonState: '' });
              }, 2000);
              props.setErrorMessage('Error adding packages.', error);
            } else {
              props.buildCallback(true);
              self.setState({
                disableInstall: false,
                packages: [],
                installDependenciesButtonState: 'finished',
              });
              setTimeout(() => {
                self.setState({ installDependenciesButtonState: '' });
              }, 2000);
            }
          },
        );
      } else {
        this._promptUserToCloseContainer();
      }
    } else {
      props.setErrorMessage('Cannot remove package at this time.', [{ message: 'An internet connection is required to modify the environment.' }]);
    }
  }

  /**
  *  @param {Object}
  *  hides packagemanager modal
  */
  _filterPackageDependencies(packageDependencies) {
    const { state } = this;
    const searchValue = state.searchValue && state.searchValue.toLowerCase();

    const packages = state.latestVersionPackages.filter((node) => {
      const name = node && node.package ? node.package.toLowerCase() : '';


      const searchMatch = ((searchValue === '') || (name.indexOf(searchValue) > -1));
      return (searchMatch && (node.manager === state.selectedTab));
    });

    return packages;
  }

  /**
  *  @param {Object}
  *  hides packagemanager modal
  */
  _packageRow(node, index) {
    const { state } = this;
    const installer = node.fromBase ? 'Base' : 'User';
    const checkboxDisabled = node.fromBase || (node.id === undefined);
    const isSelected = state.removalPackages[node.manager]
      && Object.keys(state.removalPackages[node.manager]).indexOf(node.package) > -1;
    // declare css here
    const buttonCSS = classNames({
      'PackageDependencies__btn--round PackageDependencies__btn--remove': !isSelected,
      'PackageDependencies__btn--round PackageDependencies__btn--remove--selected': isSelected,
    });
    const tableRowCSS = classNames({
      'PackageDependencies__cell--optimistic-updating': node.id === undefined,
    });

    const checkboxCSS = classNames({
      Checkbox: true,
      'Tooltip-data Tooltip-data--left': checkboxDisabled,
    });

    return (
      <tr
        className={tableRowCSS}
        key={node.package + node.manager + index}
      >
        <td>{node.package}</td>

        <td>
          {node.version}
        </td>

        <td className="PackageDependencies__cell--latest-column">

          <span>
            {node.latestVersion}
          </span>
          {
            node.latestVersion && (node.latestVersion !== node.version) && !node.fromBase
            && <div className="PackageDependencies__updateAvailable" />
          }
        </td>

        <td>{installer}</td>

        <td width="60" className="PackageDependencies__cell--select">
          <label
            data-tooltip="Packages installed by the base cannot be modified"
            className={checkboxCSS}
            htmlFor={node.id}
          >
            <input
              id={node.id}
              type="checkbox"
              className={buttonCSS}
              disabled={checkboxDisabled}
              onClick={() => this._addRemovalPackage(node)}
            />
            <span />
          </label>
        </td>
      </tr>
    );
  }

  render() {
    const { props, state } = this;
    const { packageDependencies } = props.environment;
    const packageManagersTabs = this._getPackmanagerTabs();
    const removalKeysLength = state.removalPackages[state.selectedTab] ? Object.keys(state.removalPackages[state.selectedTab]).length : 0;
    const noRemovalPackages = ((!state.removalPackages[state.selectedTab])
      || (state.removalPackages[state.selectedTab] && !removalKeysLength));
    const updateButtonAvailable = state.removalPackages[state.selectedTab]
      && state.updatePackages[state.selectedTab]
      && (removalKeysLength === Object.keys(state.updatePackages[state.selectedTab]).length);

    const removeButtonCSS = classNames({
      Btn: true,
      'PackageDependencies__remove-button--full': !updateButtonAvailable,
      'PackageDependencies__remove-button--half': updateButtonAvailable,
    });

    if (state.latestVersionPackages) {
      const filteredPackageDependencies = this._filterPackageDependencies(state.latestVersionPackages);
      const packagesProcessing = state.packages.filter(packageItem => packageItem.validity === 'checking');
      const disableInstall = state.disableInstall || ((state.packages.length === 0) || (packagesProcessing.length > 0));

      const packageMenu = classNames({
        PackageDependencies__menu: true,
        'PackageDependencies__menu--min-height': !props.packageMenuVisible,
      });
      const addPackageCSS = classNames({
        PackageDependencies__btn: true,
        'PackageDependencies__btn--line-18': true,
        'PackageDependencies__btn--open': props.packageMenuVisible,
      });
      const addPackageContainer = classNames({
        PackageDependencies__addPackage: true,
        'Tooltip-data': props.isLocked,
      });
      const tooltipCSS = classNames({
        'Tooltip-data': props.isLocked,
      });

      return (
        <div className="PackageDependencies grid">
          <div className="PackageDependencies__card Card Card--auto Card--no-hover column-1-span-12">
            <div className="PackageDependencies__tabs">
              <ul className="Tabs">
                {
                packageManagersTabs.map((tab, index) => {
                  const packageTab = classNames({
                    'PackageDependencies__tab Tab Tab--light': true,
                    'PackageDependencies__tab--selected Tab-selected': (state.selectedTab === tab.tabName),
                  });

                  return (
                    <li
                      key={tab + index}
                      className={packageTab}
                      onClick={() => this._setSelectedTab(tab.tabName, state.selectedTab === tab.tabName)}
                    >
                      {`${tab.tabName} (${tab.count})`}
                    </li>
                  );
                })
              }
              </ul>

            </div>
            <div
              className={addPackageContainer}
              data-tooltip="Container must be turned off to add packages."
            >

              <button
                disabled={props.isLocked}
                data-container-popup
                onClick={() => this._toggleAddPackageMenu()}
                className={addPackageCSS}
                type="button"
              >
                Add Packages
              </button>

              <div className={packageMenu}>
                <div className="PackageDependencies__packageMenu">
                  <input
                    ref={el => this.inputPackageName = el}
                    disabled={packagesProcessing.length > 0}
                    className="PackageDependencies__input"
                    placeholder="Enter Dependency Name"
                    type="text"
                    onKeyUp={evt => this._updatePackageName(evt)}
                  />
                  <input
                    ref={el => this.inputVersion = el}
                    className="PackageDependencies__input--version"
                    placeholder="Version (Optional)"
                    disabled={state.selectedTab === 'apt' || (packagesProcessing.length > 0)}
                    type="text"
                    onKeyUp={evt => this._updateVersion(evt)}
                  />
                  <button
                    disabled={(state.packageName.length === 0)}
                    onClick={() => this._addStatePackage()}
                    type="button"
                    className="PackageDependencies__btn--margin Btn__plus Btn--round Btn--medium"
                  />
                </div>

                <div className="PackageDependencies__table--border">
                  <table>
                    <tbody>
                      {
                        state.packages.map((node, index) => {
                          const version = node.version === '' ? 'latest' : `${node.version}`;
                          const versionText = `${version === 'latest' ? node.validity === 'checking' ? 'retrieving latest version' : 'latest version' : `${version}`}`;
                          return (
                            <tr
                              className={`PackageDependencies__table-row PackageDependencies__table-row--${node.validity} flex`}
                              key={node.package + node.version}
                            >
                              <td className="PackageDependencies__td--package">{`${node.package}`}</td>
                              <td className="PackageDependencies__td--version">
                                {versionText}
                                {
                                node.validity === 'checking'
                                && <div className="PackageDependencies__versionLoading" />
                              }

                              </td>
                              <td className="PackageDependencies__table--no-right-padding" width="30">
                                {
                                !disableInstall
                                && (
                                <button
                                  className="PackageDependencies__btn--round PackageDependencies__btn--remove--adder"
                                  onClick={() => this._removeStatePackages(node, index)}
                                  type="button"
                                />
                                )
                              }
                              </td>
                            </tr>);
                        })
                      }
                    </tbody>
                  </table>

                  <ButtonLoader
                    buttonState={state.installDependenciesButtonState}
                    buttonText="Install Selected Packages"
                    className="Btn Btn--wide PackageDependencies__btn--absolute"
                    params={{}}
                    buttonDisabled={disableInstall}
                    clicked={this._addPackageComponentsMutation}
                  />

                </div>
              </div>
            </div>
            <div className="PackageDependencies__table-container">

              <table className="PackageDependencies__table">
                <thead>
                  <tr>
                    <th className="PackageDependencies__th">Package Name</th>
                    <th className="PackageDependencies__th">Current</th>
                    <th className="PackageDependencies__th">Latest</th>
                    <th className="PackageDependencies__th">Installed By</th>
                    { noRemovalPackages
                      ? (
                        <th className="PackageDependencies__th--last">
                          Select
                        </th>
                      )
                      : (
                        <th className="PackageDependencies__th--remove">
                          <div
                            data-tooltip="Container must be turned off to remove packages or update packages"
                            className={tooltipCSS}
                          >
                            { updateButtonAvailable
                              && (
                                <button
                                  type="button"
                                  disabled={props.isLocked}
                                  className="PackageDependencies__update-button"
                                  onClick={() => this._updatePackages()}
                                >
                                  Update
                                </button>
                              )
                            }
                            <button
                              type="button"
                              disabled={props.isLocked}
                              className={removeButtonCSS}
                              onClick={() => this._removePackage()}
                            >
                            Delete
                            </button>

                          </div>
                        </th>
                      )
                  }
                  </tr>
                </thead>
                <tbody>
                  { filteredPackageDependencies.map((node, index) => (
                    this._packageRow(node, index)))
                  }
                </tbody>
              </table>
            </div>
          </div>
        </div>
      );
    }
    return (<Loader />);
  }
}

const mapStateToProps = state => state.packageDependencies;

const mapDispatchToProps = () => ({
  setPackageMenuVisible,
  setErrorMessage,
  setContainerMenuWarningMessage,
  setBuildingState,
  setWarningMessage,
  setLookingUpPackagesState,
});

const PackageDependenciesContainer = connect(mapStateToProps, mapDispatchToProps)(PackageDependencies);


export default createPaginationContainer(
  PackageDependenciesContainer,
  {
    environment: graphql`fragment PackageDependencies_environment on Environment {
    packageDependencies(first: $first, after: $cursor) @connection(key: "PackageDependencies_packageDependencies", filters: []){
        edges{
          node{
            id
            schema
            manager
            package
            version
            latestVersion @include(if: $hasNext)
            fromBase
          }
          cursor
        }
        pageInfo{
          hasNextPage
          hasPreviousPage
          startCursor
          endCursor
        }
      }
    }`,
  },
  {
    direction: 'forward',
    getConnectionFromProps(props) {
      return props.environment && props.environment.packageDependencies;
    },
    getFragmentVariables(prevVars, first) {
      return {
        ...prevVars,
        first,
      };
    },
    getVariables(props, { count }, fragmentVariables) {
      const length = props.environment.packageDependencies.edges.length;
      const { labbookName } = store.getState().routes;

      const cursor = props.environment.packageDependencies.edges[length - 1].cursor;
      const hasNext = !props.environment.packageDependencies.pageInfo.hasNextPage;
      const first = count;

      return {
        first,
        cursor,
        name: labbookName,
        owner,
        hasNext,
        // in most cases, for variables other than connection filters like
        // `first`, `after`, etc. you may want to use the previous values.
        // orderBy: fragmentVariables.orderBy,
      };
    },
    query: graphql`
    query PackageDependenciesPaginationQuery($name: String!, $owner: String!, $first: Int!, $cursor: String, $hasNext: Boolean!){
     labbook(name: $name, owner: $owner){
       environment{
         ...PackageDependencies_environment
       }
     }
   }`,
  },
);
