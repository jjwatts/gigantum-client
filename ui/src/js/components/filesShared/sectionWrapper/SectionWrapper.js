// vendor
import React, { Component } from 'react';
import classNames from 'classnames';

// assets
import './SectionWrapper.scss';

export default class SectionWrapper extends Component {
  constructor(props) {
  	super(props);
    this.state = {
      selectedFiles: [],
      selectedFilter: 'recent',
    };
    this._setSelectedFiles = this._setSelectedFiles.bind(this);
    this._clearSelectedFiles = this._clearSelectedFiles.bind(this);
    this._loadStatus = this._loadStatus.bind(this);
    this._selectFilter = this._selectFilter.bind(this);
  }

  componentDidMount() {
    const { section } = this.props;
    let selectedFilter = this.props.labbook && this.props.labbook[section] && this.props.labbook[section].hasFavorites ? 'favorites' : this.state.selectedFilter;
    this.setState({ selectedFilter });
  }

  /**
  *  @param {Object} evt
  *  set state with selected filter
  *  @return {}
  */
  _setSelectedFiles(evt) {
    const files = [...evt.target.files];
    this.setState({ selectedFiles: files });
  }

  /**
  *  @param {}
  *  clear selected files
  *  @return {}
  */
  _clearSelectedFiles() {
    this.setState({ selectedFiles: [] });
  }

  /**
  *  @param {Object} result
  *  udate loading status if state is not the same as result
  *  @return {}
  */
  _loadStatus(result) {
    if (result !== this.state.loadingStatus) {
      this.setState({ loadingStatus: result });
    }
  }

  /**
  *  @param {string} filterName - Filter for favorites & most recent view.
  *  update filterName and toggle view
  *  @return {}
  */
  _selectFilter(filterName) {
    this.setState({ selectedFilter: filterName });
  }

  render() {
    const sectionType = this.props.labbook || this.props.dataset;
    const innerSection = this.props.dataset ? sectionType : sectionType[this.props.section];
    if (sectionType) {
      let Favorites,
          MostRecent;
      const { labbook, section } = this.props,
            favoritesCSS = classNames({
              SectionWrapper__filter: true,
              'SectionWrapper__filter--selected': this.state.selectedFilter === 'favorites',
            }),
            recentCSS = classNames({
              SectionWrapper__filter: true,
              'SectionWrapper__filter--selected': this.state.selectedFilter === 'recent',
            }),
            sectionUpperCase = section[0].toUpperCase() + section.slice(1),
            Browser = require(`../sectionBrowser/sectionBrowserContainers/${sectionUpperCase}Browser`).default,
            sectionProps = {
                [section]: innerSection,
                };
        if (section !== 'data') {
          Favorites = require(`../favorites/favoritesContainers/${sectionUpperCase}Favorites`).default;
          MostRecent = require(`../mostRecent/mostRecentContainers/MostRecent${sectionUpperCase}`).default;
        }
      const sectionId = this.props.labbookId || this.props.datasetId;
      return (

        <div className="SectionWrapper">
          {
            (section !== 'data') && sectionType[section].isUntracked &&
            <div className="SectionWrapper__tracked-container">
              <div className="SectionWrapper__tracked">
                Version Tracking Disabled
              </div>
            </div>
          }
          { (section !== 'data') && (labbook[section].hasFiles || labbook[section].hasFavorites) &&
            <div>
              <div className="SectionWrapper__header">
                <div className="SectionWrapper__toolbar">
                  <a ref="favorites" className={favoritesCSS} onClick={() => this._selectFilter('favorites')}>Favorites</a>
                  <a ref="recent" className={recentCSS} onClick={() => this._selectFilter('recent')}>Most Recent</a>
                </div>

              </div>

              <div className="SectionWrapper__files">
                {
                this.state.selectedFilter === 'favorites' &&
                <Favorites
                    sectionId={innerSection.id}
                    labbookId={sectionId}
                    section={section}
                    {...sectionProps}
                />
                }
                {
                this.state.selectedFilter === 'recent' &&
                  <MostRecent
                    edgeId={innerSection.id}
                    selectedFilter={this.state.selectedFilter}
                    section={section}
                    {...sectionProps}

                  />
                }
              </div>
              <hr />
            </div>
          }

          <div className="SectionWrapper__file-browser">
            <Browser
              selectedFiles={this.state.selectedFiles}
              clearSelectedFiles={this._clearSelectedFiles}
              labbookId={sectionId}
              sectionId={innerSection.id}
              section={section}
              loadStatus={this._loadStatus}
              isLocked={this.props.isLocked}
              {...sectionProps}
              linkedDatasets={sectionType.linkedDatasets || null}

            />
          </div>
        </div>
      );
    }
    return (<div>No Files Found</div>);
  }
}
