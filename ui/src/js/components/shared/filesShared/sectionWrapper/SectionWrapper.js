// vendor
import React, { Component } from 'react';
import classNames from 'classnames';
import { boundMethod } from 'autobind-decorator';
// components
import Loader from 'Components/common/Loader';
// assets
import './SectionWrapper.scss';

const getComponetPaths = ((props) => {
  const sectionType = props.labbook ? 'labbook' : 'dataset';
  const sectionPathRoot = `${sectionType}`;
  const sectionUpperCase = props.section[0].toUpperCase() + props.section.slice(1);
  const section = ((props.section === 'code') || props.section === 'data') ? props.section : `${props.section}Data`;
  const browserPath = `${sectionPathRoot}/${section}/${sectionUpperCase}Browser`;
  const recentPath = props.labbook ? `${sectionPathRoot}/${section}/MostRecent${sectionUpperCase}` : '';

  return ({
    browserPath,
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
    const { props } = this;
    const { section } = props;
    props.refetch(section);
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
      recentPath,
    } = getComponetPaths(props);

    if (sectionObject) {
      const sectionId = props.labbookId || props.datasetId;
      const { section } = props;
      const showFavoritesRecent = (section !== 'data')
        && (state.favoriteRecentAdded);
      const Browser = require(`./../../../${browserPath}`).default;

      let MostRecent;
      if (section !== 'data') {
        MostRecent = require(`./../../../${recentPath}`).default;
      }

      // declare css
      const recentCSS = classNames({
        SectionWrapper__filter: true,
        'SectionWrapper__filter--selected': state.selectedFilter === 'recent',
      });
      const sectionProps = {
        [section]: innerSection,
      };
      if (!((section === 'data') || (sectionObject[section]))) {
        return <Loader />;
      }

      if (!((section === 'data' && sectionObject.id) || (sectionObject[section]))) {
        return <Loader />;
      }

      return (

        <div className="SectionWrapper">
          { showFavoritesRecent
            && (
            <div>
              <div className="SectionWrapper__header">
                <div className="SectionWrapper__toolbar">
                  <a
                    ref="recent"
                    className={recentCSS}
                  >
                    Most Recent
                  </a>
                </div>

              </div>

              <div className="SectionWrapper__files">
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
                isManaged={props.isManaged}
                {...sectionProps}
                linkedDatasets={sectionObject.linkedDatasets || null}
                containerStatus={props.containerStatus}
                lockFileBrowser={props.lockFileBrowser}

              />
            </div>
          </div>
        </div>
      );
    }
    return (<div>No Files Found</div>);
  }
}
