// vendor
import React, { Component, Fragment } from 'react';
import { Link } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import SimpleMDE from 'simplemde';
import classNames from 'classnames';
// components
import Base from 'Components/labbook/environment/Base';
import Type from 'Components/dataset/overview/Type';
import FilePreview from 'Components/labbook/overview/FilePreview';
import RecentActivity from 'Components/labbook/overview/RecentActivity';
import Loader from 'Components/common/Loader';
import CodeBlock from 'Components/labbook/renderers/CodeBlock';
import Tooltip from 'Components/common/Tooltip';
import Summary from 'Components/dataset/overview/Summary';
// mutations
import WriteLabbookReadmeMutation from 'Mutations/WriteLabbookReadmeMutation';
import WriteDatasetReadmeMutation from 'Mutations/WriteDatasetReadmeMutation';
// store
import store from 'JS/redux/store';
import { setErrorMessage } from 'JS/redux/reducers/footer';
// assets
import './Overview.scss';

let simple;

export default class Overview extends Component {
  constructor(props) {
    super(props);

    this._openJupyter = this._openJupyter.bind(this);

    this.state = {
      editingReadme: false,
      readmeExpanded: false,
      overflowExists: false,
      simpleExists: false,
      editorFullscreen: false,
    };
  }

  /*
    runs state check when component mounts
  */
  componentDidMount() {
    this._setExpand();
  }

  /*
    runs state check when component updates
  */
  componentDidUpdate() {
    this._setExpand();
    const { props } = this;
    const sectionProps = props[props.sectionType];

    if (!this.state.simpleExists) {
      if (document.getElementById('markDown')) {
        simple = new SimpleMDE({
          element: document.getElementById('markDown'),
          spellChecker: true,
        });

        simple.value(sectionProps.overview.readme ? sectionProps.overview.readme : '');
        this.setState({ simpleExists: true });

        const fullscreenButton = document.getElementsByClassName('fa-arrows-alt')[0];


        const sideBySideButton = document.getElementsByClassName('fa-columns')[0];

        fullscreenButton && fullscreenButton.addEventListener('click', () => this.setState({ editorFullscreen: !this.state.editorFullscreen }));


        sideBySideButton && sideBySideButton.addEventListener('click', () => this.setState({ editorFullscreen: true }));
      }
    }
  }

  _openJupyter() {
    window.open('http://localhost:8888', '_blank');
  }


  checkOverflow(el) {
    const curOverflow = el.style.overflow;

    if (!curOverflow || curOverflow === 'visible') { el.style.overflow = 'hidden'; }

    const isOverflowing = el.clientWidth < el.scrollWidth
      || el.clientHeight < el.scrollHeight;

    el.style.overflow = curOverflow;
    return isOverflowing;
  }

  _setExpand() {
    const element = Array.prototype.slice.call(document.getElementsByClassName('ReadmeMarkdown'))[0];
    if (element && this.checkOverflow(element) && !this.state.overflowExists) {
      this.setState({ overflowExists: true });
    } else if (element && !this.checkOverflow(element) && this.state.overflowExists) {
      this.setState({ overflowExists: false });
    }
  }

  /**
   @param {}
   reverts readme to have a max size
   resets vertical scroll
   */
  _shrinkReadme() {
    this.setState({ readmeExpanded: false });
    if (window.pageYOffset > 345) {
      window.scrollTo(0, 345);
    }
  }

  /**
   @param {}
   sets readmeExpanded as true in state
   */
  _expandReadme() {
    this.setState({ readmeExpanded: true });
  }

  /**
   @param {Boolean} editingReadme
   sets state for editing readme
   */
  _setEditingReadme(editingReadme) {
    this.setState({ editingReadme });
  }

  /**
   @param {}
   sets readme state to false
   */
  _closeReadme() {
    this.setState({ editingReadme: false, simpleExists: false });
  }

  /**
   @param {String} owner
   @param {String} labbookName
   calls mutation to save labbook readme
   */
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
  _saveReadme() {
    const { owner, labbookName } = store.getState().routes;
    if (this.props.sectionType === 'labbook') {
      this._saveLabbookReadme(owner, labbookName);
    } else {
      this._saveDatasetReadme(owner, labbookName);
    }
  }

  /**
    @param {String} section
    handles redirect and scrolling to top
  */
  _handleRedirect(section) {
    const { owner, labbookName } = store.getState().routes;
    const { props } = this;
    props.scrollToTop();
    props.history.push(`/projects/${owner}/${labbookName}/${section}`);
  }

  render() {
    const { props, state } = this;


    const overviewCSS = classNames({
      Overview: true,
      'Overview--fullscreen': state.editorFullscreen,
    });


    const readmeCSS = classNames({
      'ReadmeMarkdown--expanded': state.readmeExpanded,
      ReadmeMarkdown: !state.readmeExpanded,
    });


    const overviewReadmeEditingCSS = classNames({
      'Overview__readme--editing column-1-span-12': state.editingReadme,
      hidden: !state.editingReadme,
    });


    const overviewReadmeCSS = classNames({
      'Overview__readme Readme Card Card--auto Card--no-hover column-1-span-12': !state.editingReadme,
      hidden: state.editingReadme,
    });


    const overviewReadmeButtonCSS = classNames({
      'Btn Btn--feature Btn__edit': true,
      hidden: state.editingReadme,
    });


    const sectionProps = props[props.sectionType];


    const isLabbook = (props.sectionType === 'labbook');


    const typeText = isLabbook ? 'Environment' : 'Type';


    const overViewComponent = isLabbook
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

    if (sectionProps) {
      const { owner, labbookName } = store.getState().routes;
      return (

        <div className={overviewCSS}>
          { overViewComponent }

          <div className="Overview__container">

            <h2 className="Overview__title">
              Readme
              <Tooltip section="readMe" />
            </h2>

          </div>

          { state.editingReadme
              && (
              <div className="grid">
                <div className={overviewReadmeEditingCSS}>

                  <textarea
                    ref="markdown"
                    className="Overview__readme-editor"
                    id="markDown"
                  />

                  <div className="Overview__readme--editing-buttons">
                    <button
                      className="Overview__readme-cancel Btn--flat"
                      onClick={() => { this._closeReadme(); }}
                    >
                    Cancel
                    </button>

                    <button
                      className="Overview__readme-save"
                      disabled={false}
                      onClick={() => { this._saveReadme(); }}
                    >
                    Save
                    </button>
                  </div>
                </div>
              </div>
              )
            }
          { sectionProps.overview.readme
            ? (
              <div className="grid">
                <div className={overviewReadmeCSS}>
                  <button
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

                  <div className="Overview__readme-buttons">
                    { (state.overflowExists && state.readmeExpanded)
                      ? (
                        <div className="Overview__readme-bar-less">
                          <button
                            className="Btn__loadMore Btn__loadMore--up"
                            onClick={() => this._shrinkReadme()}
                          />
                        </div>
                      )
                      : (
                        <div className="Overview__readme-bar-more">
                          <button
                            className="Btn__loadMore Btn__loadMore--down"
                            onClick={() => this._expandReadme()}
                          />
                        </div>
                      )
                      }
                  </div>
                </div>
              </div>
            )
            : !state.editingReadme
              && (
              <div className="grid">
                <div className="Overview__empty column-1-span-12">
                  <button
                    className={overviewReadmeButtonCSS}
                    onClick={() => this._setEditingReadme(true)}
                  >
                    <span>Edit Readme</span>
                  </button>
                  <div className="Overview__empty-content">
                    <p>This Project Has No Readme</p>
                    <p
                      className="Overview__empty-action"
                      onClick={() => this._setEditingReadme(true)}
                    >
                        Create a Readme
                    </p>
                  </div>
                </div>
              </div>
              )
            }

          <div className="Overview__container">
            <h2>
              {typeText}
              <Tooltip section="environmentOverview" />
            </h2>
          </div>

          { isLabbook
            ? (
              <div className="grid">
                <div className="Overview__environment column-1-span-12">
                  <button
                    className="Btn Btn--feature Btn__redirect Btn__overview"
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
