// vendor
import React, { Component } from 'react';
import classNames from 'classnames';
import { boundMethod } from 'autobind-decorator';
// assets
import './SectionWrapper.scss';

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
  state = {
    selectedFiles: [],
    selectedFilter: 'recent',
    favoriteRecentAdded: false,
  };

  componentDidMount() {
    const { props, state } = this;
    const { section } = props;
    const hasFavorites = props.labbook
      && props.labbook[section]
      && props.labbook[section].hasFavorites;
    const selectedFilter = hasFavorites ? 'favorites' : state.selectedFilter;

    this.setState({ selectedFilter });
  }

  /**
  *  @param {Object} evt
  *  set state with selected filter
  *  @return {}
  */
  @boundMethod
  _setSelectedFiles(evt) {
    const files = [...evt.target.files];
    this.setState({ selectedFiles: files });
  }

  /**
  *  @param {}
  *  clear selected files
  *  @return {}
  */
  @boundMethod
  _clearSelectedFiles() {
    this.setState({ selectedFiles: [] });
  }

  /**
  *  @param {Object} result
  *  udate loading status if state is not the same as result
  *  @return {}
  */
  @boundMethod
  _loadStatus(result) {
    const { state } = this;
    if (result !== state.loadingStatus) {
      this.setState({ loadingStatus: result });
    }
  }

  /**
  *  @param {string} filterName - Filter for favorites & most recent view.
  *  update filterName and toggle view
  *  @return {}
  */
  @boundMethod
  _selectFilter(filterName) {
    this.setState({ selectedFilter: filterName });
  }

  /**
  *  @param {string} favoriteRecentAdded
  *  shows hides the most recent section after a file has been added or removed
  *  update filterName and toggle view
  *  @return {}
  */
  @boundMethod
  _toggleFavoriteRecent(favoriteRecentAdded) {
    this.setState({ favoriteRecentAdded });
  }

  render() {
    const { props, state } = this;
    const sectionObject = props.labbook || props.dataset;
    const innerSection = props.dataset ? sectionObject : sectionObject[props.section];
    const {
      browserPath,
      favoritePath,
      recentPath,
    } = getComponetPaths(props);

    if (sectionObject) {
      const sectionId = props.labbookId || props.datasetId;
      const { labbook, section } = props;
      const showFavoritesRecent = (section !== 'data')
        && (state.favoriteRecentAdded);
      const Browser = require(`./../../../${browserPath}`).default;

      let Favorites;
      let MostRecent;
      if (section !== 'data') {
        Favorites = require(`./../../../${favoritePath}`).default;
        MostRecent = require(`./../../../${recentPath}`).default;
      }

      // declare css
      const favoritesCSS = classNames({
        SectionWrapper__filter: true,
        'SectionWrapper__filter--selected': state.selectedFilter === 'favorites',
      });
      const recentCSS = classNames({
        SectionWrapper__filter: true,
        'SectionWrapper__filter--selected': state.selectedFilter === 'recent',
      });
      const sectionProps = {
        [section]: innerSection,
      };

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
          { showFavoritesRecent
            && (
            <div>
              <div className="SectionWrapper__header">
                <div className="SectionWrapper__toolbar">
                  <a
                    ref="favorites"
                    className={favoritesCSS}
                    onClick={() => this._selectFilter('favorites')}
                  >
                    Favorites
                  </a>
                  <a
                    ref="recent"
                    className={recentCSS}
                    onClick={() => this._selectFilter('recent')}
                  >
                    Most Recent
                  </a>
                </div>

              </div>

              <div className="SectionWrapper__files">
                { (state.selectedFilter === 'favorites')
                  && (
                    <Favorites
                      sectionId={innerSection.id}
                      labbookId={sectionId}
                      toggleFavoriteRecent={this._toggleFavoriteRecent}
                      section={section}
                      {...sectionProps}
                    />
                  )
                }
                { (state.selectedFilter === 'recent')
                  && (
                    <MostRecent
                      edgeId={innerSection.id}
                      selectedFilter={state.selectedFilter}
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
                selectedFiles={state.selectedFiles}
                clearSelectedFiles={this._clearSelectedFiles}
                labbookId={sectionId}
                sectionId={innerSection.id}
                section={section}
                loadStatus={this._loadStatus}
                isLocked={props.isLocked}
                toggleFavoriteRecent={this._toggleFavoriteRecent}
                {...sectionProps}
                linkedDatasets={sectionObject.linkedDatasets || null}
                containerStatus={props.containerStatus}

              />
            </div>
          </div>
        </div>
      );
    }
    return (<div>No Files Found</div>);
  }
}
