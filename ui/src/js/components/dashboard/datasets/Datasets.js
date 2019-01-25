// vendor
import React, { Component, Fragment } from 'react';
import queryString from 'querystring';
import classNames from 'classnames';
import { connect } from 'react-redux';
// components
import WizardModal from 'Components/wizard/WizardModal';
import Loader from 'Components/shared/Loader';
import LocalDatasetsContainer, { LocalDatasets } from 'Components/dashboard/datasets/localDatasets/LocalDatasets';
// import RemoteDatasets from 'Components/dashboard/datasets/remoteDatasets/RemoteDatasets';
import LoginPrompt from 'Components/header/branchMenu/modals/LoginPrompt';
import ToolTip from 'Components/shared/ToolTip';
import DatasetFilterBy from './filters/DatasetFilterBy';
import DatasetSort from './filters/DatasetSort';
// utils
import Validation from 'JS/utils/Validation';
// queries
import UserIdentity from 'JS/Auth/UserIdentity';
// config
import config from 'JS/config';
// store
import { setErrorMessage } from 'JS/redux/reducers/footer';
import { setFilterText } from 'JS/redux/reducers/datasetListing/datasetListing';
// assets
import './Datasets.scss';

class Datasets extends Component {
  constructor(props) {
    super(props);

    const {
      filter,
      orderBy,
      sort,
    } = queryString.parse(this.props.history.location.search.slice(1));

    this.state = {
      datasetModalVisible: false,
      oldDatasetName: '',
      newDatasetName: '',
      renameError: '',
      showNamingError: false,
      filter: filter || 'all',
      sortMenuOpen: false,
      refetchLoading: false,
      selectedSection: 'local',
      showLoginPrompt: false,
      orderBy: orderBy || 'modified_on',
      sort: sort || 'desc',
      filterMenuOpen: false,
    };

    this._closeSortMenu = this._closeSortMenu.bind(this);
    this._closeFilterMenu = this._closeFilterMenu.bind(this);
    this._goToDataset = this._goToDataset.bind(this);
    this._showModal = this._showModal.bind(this);
    this._filterSearch = this._filterSearch.bind(this);
    this._setSortFilter = this._setSortFilter.bind(this);
    this._closeLoginPromptModal = this._closeLoginPromptModal.bind(this);
    this._filterDatasets = this._filterDatasets.bind(this);
    this._setFilter = this._setFilter.bind(this);
    this._changeSearchParam = this._changeSearchParam.bind(this);
    this._hideSearchClear = this._hideSearchClear.bind(this);
    this._setFilterValue = this._setFilterValue.bind(this);
    this._toggleSortMenu = this._toggleSortMenu.bind(this);
    this._toggleFilterMenu = this._toggleFilterMenu.bind(this);
  }

  /**
    * @param {}
    * subscribe to store to update state
    * set unsubcribe for store
  */
  UNSAFE_componentWillMount() {
    const paths = this.props.history.location.pathname.split('/');
    let sectionRoute = paths.length > 2 ? paths[2] : 'local';

    if (paths[2] !== 'cloud' && paths[2] !== 'local') {
      sectionRoute = 'local';
    }

    this.setState({ selectedSection: sectionRoute });

    document.title = 'Gigantum';

    window.addEventListener('click', this._closeSortMenu);
    window.addEventListener('click', this._closeFilterMenu);
  }

  /**
    * @param {}
    * fires when component unmounts
    * removes added event listeners
  */
  componentWillUnmount() {
    window.removeEventListener('click', this._closeSortMenu);
    window.removeEventListener('click', this._closeFilterMenu);
    window.removeEventListener('scroll', this._captureScroll);
    window.removeEventListener('click', this._hideSearchClear);
  }

  UNSAFE_componentWillReceiveProps(nextProps) {
    const paths = nextProps.history.location.pathname.split('/');
    const sectionRoute = paths.length > 2 ? paths[2] : 'local';

    if (paths[2] !== 'cloud' && paths[2] !== 'local') {
      this.props.history.replace('../../../../datasets/local');
    }
    this.setState({ selectedSection: sectionRoute });
  }

  /**
    * @param {}
    * fires when user identity returns invalid session
    * prompts user to revalidate their session
  */
  _closeLoginPromptModal() {
    this.setState({
      showLoginPrompt: false,
    });
  }

  /**
    * @param {event} evt
    * fires when sort menu is open and the user clicks elsewhere
    * hides the sort menu dropdown from the view
  */

  _closeSortMenu(evt) {
    const isSortMenu = evt && evt.target && evt.target.className && (evt.target.className.indexOf('DatasetSort__selector') > -1);

    if (!isSortMenu && this.state.sortMenuOpen) {
      this.setState({ sortMenuOpen: false });
    }
  }

  /**
    * @param {event} evt
    * fires when filter menu is open and the user clicks elsewhere
    * hides the filter menu dropdown from the view
  */
  _closeFilterMenu(evt) {
    const isFilterMenu = evt.target.className.indexOf('DatasetFilterBy__selector') > -1;

    if (!isFilterMenu && this.state.filterMenuOpen) {
      this.setState({ filterMenuOpen: false });
    }
  }


  /**
    * @param {}
    * fires when a componet mounts
    * adds a scoll listener to trigger pagination
  */
  componentDidMount() {
    window.addEventListener('scroll', this._captureScroll);
    window.addEventListener('click', this._hideSearchClear);
  }

  /**
    * @param {}
    * fires on window clock
    * hides search cancel button when clicked off
  */
  _hideSearchClear(evt) {
    if (this.state.showSearchCancel && evt.target.className !== 'Datasets__search-cancel' && evt.target.className !== 'Datasets__search no--margin') {
      this.setState({ showSearchCancel: false });
    }
  }

  /**
    *  @param {string} datasetName - inputs a dataset name
    *  routes to that dataset
  */
  _goToDataset = (datasetName, owner) => {
    this.setState({ datasetName, owner });
  }


  /**
    *  @param {string} datasetName
    *  closes dataset modal and resets state to initial state
  */
  _closeDataset(datasetName) {
    this.setState({
      datasetModalVisible: false,
      oldDatasetName: '',
      newDatasetName: '',
      showNamingError: false,
    });
  }

  /**
    *  @param {event} evt
    *  sets new dataset title to state
  */
  _setDatasetTitle(evt) {
    const isValid = Validation.datasetName(evt.target.value);
    if (isValid) {
      this.setState({
        newDatasetName: evt.target.value,
        showNamingError: false,
      });
    } else {
      this.setState({ showNamingError: true });
    }
  }

  /**
   * @param {string} filter
   sets state updates filter
  */
  _setFilter(filter) {
    this.setState({ filterMenuOpen: false, filter });
    this._changeSearchParam({ filter });
  }
  /**
     sets state for filter menu
  */
  _toggleFilterMenu() {
    this.setState({ filterMenuOpen: !this.state.filterMenuOpen });
  }
  /**
   sets state for sort menu
  */
  _toggleSortMenu() {
    this.setState({ sortMenuOpen: !this.state.sortMenuOpen });
  }
  /**
   * @param {string} section
   replaces history and checks session
  */
  _setSection(section) {
    if (section === 'cloud') {
      this._viewRemote();
    } else {
      this.props.history.replace(`../datasets/${section}${this.props.history.location.search}`);
    }
  }
  /**
   * @param {object} dataset
   * returns true if dataset's name or description exists in filtervalue, else returns false
  */
  _filterSearch(dataset) {
    if (dataset.node && dataset.node.name && (this.props.filterText === '' || dataset.node.name.toLowerCase().indexOf(this.props.filterText.toLowerCase()) > -1 || (dataset.node.description && dataset.node.description.toLowerCase().indexOf(this.props.filterText.toLowerCase()) > -1))) {
      return true;
    }
    return false;
  }
  /**
   * @param {array, string} localDatasets.edges,filter
   * @return {array} filteredDatasets
  */
  _filterDatasets(datasets, filter) {
    const username = localStorage.getItem('username');
    let self = this,
      filteredDatasets = [];


    if (filter === 'owner') {
      filteredDatasets = datasets.filter(dataset => ((dataset.node.owner === username) && self._filterSearch(dataset)));
    } else if (filter === 'others') {
      filteredDatasets = datasets.filter(dataset => (dataset.node.owner !== username && self._filterSearch(dataset)));
    } else {
      filteredDatasets = datasets.filter(dataset => self._filterSearch(dataset));
    }

    return filteredDatasets;
  }

  /**
    * @param {}
    * fires when handleSortFilter triggers refetch
    * references child components and triggers their refetch functions
  */
  _showModal() {
    this.refs.wizardModal._showModal();
  }

  /**
    *  @param {string} selected
    * fires when setSortFilter validates user can sort
    * triggers a refetch with new sort parameters
  */
  _handleSortFilter(orderBy, sort) {
    this.setState({ sortMenuOpen: false, orderBy, sort });
    this._changeSearchParam({ orderBy, sort });
    this.props.refetchSort(orderBy, sort);
  }

  /**
    *  @param {string, boolean} orderBy sort
    * fires when user selects a sort option
    * checks session and selectedSection state before handing off to handleSortFilter
  */
  _setSortFilter(orderBy, sort) {
    if (this.state.selectedSection === 'remoteDatasets') {
      UserIdentity.getUserIdentity().then((response) => {
        if (navigator.onLine) {
          if (response.data) {
            if (response.data.userIdentity.isSessionValid) {
              this._handleSortFilter(orderBy, sort);
            } else {
              this.props.auth.renewToken(true, () => {
                if (!this.state.showLoginPrompt) {
                  this.setState({ showLoginPrompt: true });
                }
              }, () => {
                this._handleSortFilter(orderBy, sort);
              });
            }
          }
        } else if (!this.state.showLoginPrompt) {
          this.setState({ showLoginPrompt: true });
        }
      });
    } else {
      this._handleSortFilter(orderBy, sort);
    }
  }

  /**
    * @param {}
    * fires when user selects remote dataset view
    * checks user auth before changing selectedSection state
  */
  _viewRemote() {
    UserIdentity.getUserIdentity().then((response) => {
      if (navigator.onLine) {
        if (response.data && response.data.userIdentity.isSessionValid) {
          this.props.history.replace(`../datasets/cloud${this.props.history.location.search}`);
          this.setState({ selectedSection: 'cloud' });
        } else {
          this.props.auth.renewToken(true, () => {
            if (!this.state.showLoginPrompt) {
              this.setState({ showLoginPrompt: true });
            }
          }, () => {
            this.props.history.replace(`../datasets/cloud${this.props.history.location.search}`);
            this.setState({ selectedSection: 'cloud' });
          });
        }
      } else if (!this.state.showLoginPrompt) {
        this.setState({ showLoginPrompt: true });
      }
    });
  }

  /**
  *  @param {evt}
  *  sets the filterValue in state
  */
  _setFilterValue(evt) {
    setFilterText(evt.target.value);

    if (this.refs.datasetSearch.value !== evt.target.value) {
      this.refs.datasetSearch.value = evt.target.value;
    }
  }

  /**
    *  @param {object} newValues
    *  changes the query params to new sort and filter values
  */
  _changeSearchParam(newValues) {
    const searchObj = Object.assign({}, queryString.parse(this.props.history.location.search.slice(1)), newValues);
    this.props.history.replace(`..${this.props.history.location.pathname}?${queryString.stringify(searchObj)}`);
  }

  render() {
    const { props } = this;

    const datasetsCSS = classNames({
      Datasets: true,
      'Datasets--demo': window.location.hostname === config.demoHostName,
    });

    if (props.datasetList !== null || props.loading) {
      const localNavItemCSS = classNames({
        'Datasets__nav-item': true,
        'Datasets__nav-item--local': true,
        'Datasets__nav-item--selected': this.state.selectedSection === 'local',
      });

      const cloudNavItemCSS = classNames({
        'Datasets__nav-item': true,
        'Datasets__nav-item--cloud': true,
        'Datasets__nav-item--selected': this.state.selectedSection === 'cloud',
      });

      return (

        <div className={datasetsCSS}>

          <WizardModal
            ref="wizardModal"
            handler={this.handler}
            history={this.props.history}
            datasets
            {...props}
          />

          <div className="Datasets__panel-bar">
            <h6 className="Datasets__username">{localStorage.getItem('username')}</h6>
            <h2 className="Datasets__title">
                Datasets
            </h2>

          </div>
          <div className="Datasets__menu  mui-container flex-0-0-auto">
            <ul className="Datasets__nav  flex flex--row">
              <li className={localNavItemCSS}>
                <a onClick={() => this._setSection('local')}>Local</a>
              </li>
              <li className={cloudNavItemCSS}>
                <a onClick={() => this._setSection('cloud')}>Cloud</a>
              </li>

              <hr className={`Datasets__navigation-slider Datasets__navigation-slider--${this.state.selectedSection}`} />

              <ToolTip section="cloudLocal" />
            </ul>

          </div>
          <div className="Datasets__subheader">
            <div className="Datasets__search-container">
              {
                  this.state.showSearchCancel &&
                  (this.props.filterText.length !== 0) &&
                  <Fragment>
                    <div
                      className="Datasets__search-cancel"
                      onClick={() => this._setFilterValue({ target: { value: '' } })}
                    />
                    <div className="Datasets__search-cancel--text">Clear</div>
                  </Fragment>
                }
              <input
                type="text"
                ref="datasetSearch"
                className="Datasets__search no--margin"
                placeholder="Filter Datasets by name or description"
                defaultValue={this.props.filterText}
                onKeyUp={evt => this._setFilterValue(evt)}
                onFocus={() => this.setState({ showSearchCancel: true })}
              />
            </div>

            <DatasetFilterBy
              {...this.state}
              toggleFilterMenu={this._toggleFilterMenu}
              setFilter={this._setFilter}
            />
            <DatasetSort
              {...this.state}
              toggleSortMenu={this._toggleSortMenu}
              setSortFilter={this._setSortFilter}
            />
          </div>
          {
            props.loading ?
              <LocalDatasets
                loading
                showModal={this._showModal}
                section={this.props.section}
              />
            :
            this.state.selectedSection === 'local' ?
              <LocalDatasetsContainer
                datasetListId={props.datasetList.id}
                localDatasets={props.datasetList.datasetList}
                showModal={this._showModal}
                goToDataset={this._goToDataset}
                filterDatasets={this._filterDatasets}
                filterState={this.state.filter}
                setFilterValue={this._setFilterValue}
                changeRefetchState={bool => this.setState({ refetchLoading: bool })}
                {...props}
              />
            :
            <div/>
          }
          {
            this.state.showLoginPrompt &&
            <LoginPrompt closeModal={this._closeLoginPromptModal} />
          }
        </div>
      );
    } else if (props.datasetList === null) {
      UserIdentity.getUserIdentity().then((response) => {
        if (response.data && response.data.userIdentity.isSessionValid) {
          setErrorMessage('Failed to fetch Datasets.', [{ message: 'There was an error while fetching Datasets. This likely means you have a corrupted Dataset directory.' }]);
          return (
            <div className="Datasets__fetch-error">
                There was an error attempting to fetch Datasets. <br />
                Try restarting Gigantum and refresh the page.<br />
                If the problem persists <a target="_blank" href="https://docs.gigantum.com/discuss" rel="noopener noreferrer">request assistance here.</a>
            </div>
          );
        }
        this.props.auth.login();
      });
    } else {
      return (<Loader />);
    }
  }
}

const mapStateToProps = (state, ownProps) => ({
  filterText: state.datasetListing.filterText,
});

const mapDispatchToProps = dispatch => ({
});

export default connect(mapStateToProps, mapDispatchToProps)(Datasets);
