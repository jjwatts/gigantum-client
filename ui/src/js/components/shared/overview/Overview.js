// vendor
import React, { Component, Fragment } from 'react';
import ReactMarkdown from 'react-markdown';
import SimpleMDE from 'simplemde';
import classNames from 'classnames';
import { boundMethod } from 'autobind-decorator';
// mutations
import WriteLabbookReadmeMutation from 'Mutations/WriteLabbookReadmeMutation';
import WriteDatasetReadmeMutation from 'Mutations/WriteDatasetReadmeMutation';
// store
import store from 'JS/redux/store';
import { setErrorMessage } from 'JS/redux/actions/footer';
// components
import Base from 'Components/labbook/environment/Base';
import Type from 'Components/dataset/overview/Type';
import FilePreview from 'Components/labbook/overview/FilePreview';
import RecentActivity from 'Components/labbook/overview/RecentActivity';
import Loader from 'Components/common/Loader';
import CodeBlock from 'Components/labbook/renderers/CodeBlock';
import Tooltip from 'Components/common/Tooltip';
import Summary from 'Components/dataset/overview/Summary';
import ReadmeEdit from './ReadmeEdit';
import EmptyReadme from './EmptyReadme';
// assets
import './Overview.scss';

let simple;

/**
  @param {}
  sets element to expand
 */
const checkOverflow = (element) => {
  const curOverflow = element.style.overflow;
  if (!curOverflow || curOverflow === 'visible') {
    element.style.overflow = 'hidden';
  }

  const isOverflowing = element.clientWidth < element.scrollWidth
   || element.clientHeight < element.scrollHeight;

  element.style.overflow = curOverflow;

  return isOverflowing;
};

export default class Overview extends Component {
  state = {
    editingReadme: false,
    readmeExpanded: false,
    overflowExists: false,
    simpleExists: false,
    editorFullscreen: false,

  };

  /*
    runs state check when component mounts
  */
  componentDidMount() {
    const { props } = this;
    this._setExpand();
    props.refetch('overview');
  }

  /*
    runs state check when component updates
  */
  componentDidUpdate() {
    this._setExpand();
    const { props, state } = this;
    const sectionProps = props[props.sectionType];

    if (!state.simpleExists) {
      if (document.getElementById('markDown')) {
        simple = new SimpleMDE({
          element: document.getElementById('markDown'),
          spellChecker: true,
        });

        simple.value(sectionProps.overview.readme ? sectionProps.overview.readme : '');

        this.setState({ simpleExists: true });

        const fullscreenButton = document.getElementsByClassName('fa-arrows-alt')[0];
        const sideBySideButton = document.getElementsByClassName('fa-columns')[0];

        fullscreenButton && fullscreenButton.addEventListener('click', () => this.setState({ editorFullscreen: !state.editorFullscreen }));

        sideBySideButton && sideBySideButton.addEventListener('click', () => this.setState({ editorFullscreen: true }));
      }
    }
  }

  /**
   @param {}
   sets element to expand
   */
  @boundMethod
  _openJupyter() {
    window.open('http://localhost:8888', '_blank');
  }

  /**
   @param {}
   sets element to expand
   */
  @boundMethod
  _setExpand() {
    const { state } = this;
    const element = Array.prototype.slice.call(document.getElementsByClassName('ReadmeMarkdown'))[0];
    if (element && checkOverflow(element) && !state.overflowExists) {
      this.setState({ overflowExists: true });
    } else if (element && !checkOverflow(element) && state.overflowExists) {
      this.setState({ overflowExists: false });
    }
  }

  /**
   @param {}
   reverts readme to have a max size
   resets vertical scroll
   */
  @boundMethod
  _toggleReadme(readmeExpanded) {
    if (!readmeExpanded) {
      if (window.pageYOffset > 345) {
        window.scrollTo(0, 345);
      }
    }
    this.setState({ readmeExpanded: !readmeExpanded });

    this._setExpand()
  }

  /**
   @param {Boolean} editingReadme
   sets state for editing readme
   */
  @boundMethod
  _setEditingReadme(editingReadme) {
    this.setState({ editingReadme });
  }

  /**
   @param {}
   sets readme state to false
   */
  @boundMethod
  _closeReadme() {
    this.setState({ editingReadme: false, simpleExists: false });
  }

  /**
   @param {String} owner
   @param {String} labbookName
   calls mutation to save labbook readme
   */
  @boundMethod
  _saveLabbookReadme(owner, labbookName) {
    WriteLabbookReadmeMutation(
      owner,
      labbookName,
      simple.value(),
      (res, error) => {
        if (error) {
          console.log(error);
          setErrorMessage('Readme was not set: ', error);
        } else {
          this.setState({ editingReadme: false, simpleExists: false });
        }
      },
    );
  }

  /**
   @param {String} owner
   @param {String} labbookName
   calls mutation to save dataset readme
   */
  @boundMethod
  _saveDatasetReadme(owner, labbookName) {
    WriteDatasetReadmeMutation(
      owner,
      labbookName,
      simple.value(),
      (res, error) => {
        if (error) {
          console.log(error);
          setErrorMessage('Readme was not set: ', error);
        } else {
          this.setState({ editingReadme: false, simpleExists: false });
        }
      },
    );
  }

  /**
   @param {}
   handles calling mutation functions to save readme
   */
  @boundMethod
  _saveReadme() {
    const { props } = this;
    const { owner, labbookName } = store.getState().routes;
    if (props.sectionType === 'labbook') {
      this._saveLabbookReadme(owner, labbookName);
    } else {
      this._saveDatasetReadme(owner, labbookName);
    }
  }

  /**
    @param {String} section
    handles redirect and scrolling to top
  */
  @boundMethod
  _handleRedirect(section) {
    const { owner, labbookName } = store.getState().routes;
    const { props } = this;
    props.scrollToTop();
    props.history.push(`/projects/${owner}/${labbookName}/${section}`);
  }

  render() {
    const { props, state } = this;
    const sectionProps = props[props.sectionType];
    const isLabbook = (props.sectionType === 'labbook');
    const typeText = isLabbook ? 'Environment' : 'Type';
    const showLoadMoreButton = state.overflowExists
      || (state.readmeExpanded && !state.overflowExists);

    const overViewComponent = (isLabbook && sectionProps.overview)
      ? (
        <RecentActivity
          recentActivity={sectionProps.overview.recentActivity}
          scrollToTop={props.scrollToTop}
          history={props.history}
        />
      )
      : (
        <Summary
          isManaged={props.isManaged}
          {...sectionProps.overview}
        />
      );

    // decalre css here
    const overviewCSS = classNames({
      Overview: true,
      'Overview--fullscreen': state.editorFullscreen,
    });
    const readmeCSS = classNames({
      ReadmeMarkdown: true,
      'ReadmeMarkdown--collapsed': !state.readmeExpanded,
      'ReadmeMarkdown--expanded': state.readmeExpanded,
    });
    const overviewReadmeCSS = classNames({
      'Overview__readme Readme Card Card--auto Card--no-hover column-1-span-12': !state.editingReadme,
      hidden: state.editingReadme,
    });
    const overviewReadmeButtonCSS = classNames({
      'Btn Btn--feature Btn__edit Btn__edit--featurePosition': true,
      hidden: state.editingReadme,
    });

    const loadMoreCSS = classNames({
      'Btn Btn__expandadble': true,
      'Btn__expandadble--expand': !state.readmeExpanded,
      'Btn__expandadble--collapse': state.readmeExpanded,
    });

    if (sectionProps && sectionProps.overview) {
      return (

        <div className={overviewCSS}>
          { overViewComponent }

          <div className="Overview__container">

            <h4 className="Overview__title">
              Readme
              <Tooltip section="readMe" />
            </h4>

          </div>

          { state.editingReadme
            && (
              <ReadmeEdit
                {...state}
                closeReadme={this._closeReadme}
                saveReadme={this._saveReadme}
              />
            )
          }
          { sectionProps.overview.readme
            ? (
              <div className="grid">
                <div className={overviewReadmeCSS}>
                  <button
                    type="button"
                    className={overviewReadmeButtonCSS}
                    onClick={() => this._setEditingReadme(true)}
                  >
                    <span>Edit Readme</span>
                  </button>
                  <ReactMarkdown
                    className={readmeCSS}
                    source={sectionProps.overview.readme}
                    renderers={{ code: props => <CodeBlock {...props} /> }}
                  />

                  { (state.overflowExists && !state.readmeExpanded)
                      && <div className="Overview__readme-fadeout" />
                  }
                  { showLoadMoreButton
                    && (
                      <div className="Overview__readme-buttons">
                        <div className="Overview__readme-bar-less">
                          <button
                            type="button"
                            className={loadMoreCSS}
                            onClick={() => this._toggleReadme(state.readmeExpanded)}
                          />
                        </div>
                      </div>
                    )
                  }
                </div>
              </div>
            )
            : !state.editingReadme
              && (
              <EmptyReadme
                sectionType={props.sectionType}
                editingReadme={state.editingReadme}
                setEditingReadme={this._setEditingReadme}
              />
            )
          }

          <div className="Overview__container">
            <h4>
              {typeText}
              <Tooltip section="environmentOverview" />
            </h4>
          </div>

          { isLabbook
            ? (
              <div className="grid">
                <div className="Overview__environment column-1-span-12">
                  <button
                    type="button"
                    className="Btn Btn--feature Btn__redirect Btn__redirect--featurePosition Btn__overview"
                    onClick={() => this._handleRedirect('environment')}
                  >
                    <span>View Environment Details</span>
                  </button>
                  <Base
                    ref="base"
                    environment={sectionProps.environment}
                    blockClass="Overview"
                    overview={sectionProps.overview}
                  />

                </div>
              </div>
            )
            : (
              <div className="Overview__environment">
                <Type
                  type={props.datasetType}
                  isManaged={props.isManaged}
                />
              </div>
            )
          }

          { isLabbook
            && (
            <FilePreview
              ref="filePreview"
              scrollToTop={props.scrollToTop}
              history={props.history}
            />
            )
          }
        </div>
      );
    }

    return (<Loader />);
  }
}
