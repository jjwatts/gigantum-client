// vendor
import React, { Component } from 'react';
import classNames from 'classnames';
// assets
import './SectionWrapper.scss';

const component = './';

const getComponetPaths = ((props) => {
  const sectionType = props.labbook ? 'labbook' : 'dataset';


  const sectionPathRoot = `${sectionType}`;


  const sectionUpperCase = props.section[0].toUpperCase() + props.section.slice(1);


  const section = ((props.section === 'code') || props.section === 'data') ? props.section : `${props.section}Data`;


  const browserPath = `${sectionPathRoot}/${section}/${sectionUpperCase}Browser`;


  const favoritePath = props.labbook ? `${sectionPathRoot}/${section}/${sectionUpperCase}Favorites` : '';


  const recentPath = props.labbook ? `${sectionPathRoot}/${section}/MostRecent${sectionUpperCase}` : '';
  return ({
    browserPath,
    favoritePath,
    recentPath,
  });
});

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
    const selectedFilter = this.props.labbook && this.props.labbook[section] && this.props.labbook[section].hasFavorites ? 'favorites' : this.state.selectedFilter;
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
    const sectionObject = this.props.labbook || this.props.dataset;
    const innerSection = this.props.dataset ? sectionObject : sectionObject[this.props.section];
    const {
      browserPath,
      favoritePath,
      recentPath,
    } = getComponetPaths(this.props);

    if (sectionObject) {
      let Favorites;


      let MostRecent;
      const { labbook, section } = this.props;


      const favoritesCSS = classNames({
        SectionWrapper__filter: true,
        'SectionWrapper__filter--selected': this.state.selectedFilter === 'favorites',
      });


      const recentCSS = classNames({
        SectionWrapper__filter: true,
        'SectionWrapper__filter--selected': this.state.selectedFilter === 'recent',
      });


      const Browser = require(`./../../../${browserPath}`).default;


      const sectionProps = {
        [section]: innerSection,
      };
      if (section !== 'data') {
        Favorites = require(`./../../../${favoritePath}`).default;
        MostRecent = require(`./../../../${recentPath}`).default;
      }
      const sectionId = this.props.labbookId || this.props.datasetId;
      return (

        <div className="SectionWrapper">
          {
            (section !== 'data') && sectionObject[section].isUntracked
            && (
            <div className="SectionWrapper__tracked-container">
              <div className="SectionWrapper__tracked">
                Version Tracking Disabled
              </div>
            </div>
            )
          }
          { (section !== 'data') && (labbook[section].hasFiles || labbook[section].hasFavorites)
            && (
            <div>
              <div className="SectionWrapper__header">
                <div className="SectionWrapper__toolbar">
                  <a ref="favorites" className={favoritesCSS} onClick={() => this._selectFilter('favorites')}>Favorites</a>
                  <a ref="recent" className={recentCSS} onClick={() => this._selectFilter('recent')}>Most Recent</a>
                </div>

              </div>

              <div className="SectionWrapper__files">
                {
                this.state.selectedFilter === 'favorites'
                && (
                <Favorites
                  sectionId={innerSection.id}
                  labbookId={sectionId}
                  section={section}
                  {...sectionProps}
                />
                )
                }
                {
                this.state.selectedFilter === 'recent'
                  && (
                  <MostRecent
                    edgeId={innerSection.id}
                    selectedFilter={this.state.selectedFilter}
                    section={section}
                    {...sectionProps}
                  />
                  )
                }
              </div>
            </div>
            )
          }
          <hr className="column-1-span-12" />
          <div className="grid">
            <div className="SectionWrapper__file-browser column-1-span-12">
              <Browser
                selectedFiles={this.state.selectedFiles}
                clearSelectedFiles={this._clearSelectedFiles}
                labbookId={sectionId}
                sectionId={innerSection.id}
                section={section}
                loadStatus={this._loadStatus}
                isLocked={this.props.isLocked}
                {...sectionProps}
                linkedDatasets={sectionObject.linkedDatasets || null}

              />
            </div>
          </div>
        </div>
      );
    }
    return (<div>No Files Found</div>);
  }
}
