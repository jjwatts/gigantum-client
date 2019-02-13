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
import ToolTip from 'Components/common/ToolTip';
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
    this._handleClick = this._handleClick.bind(this);
  }
  /*
    runs state check when component mounts
  */
  componentDidMount() {
    this._setExpand();
    window.addEventListener('click', this._handleClick);
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

        let fullscreenButton = document.getElementsByClassName('fa-arrows-alt')[0],
          sideBySideButton = document.getElementsByClassName('fa-columns')[0];

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
   @param {event} evt
   hides warning when not clicked on
   */
  _handleClick(evt) {
    if ((evt.target.className.indexOf('Overview__readme-save') === -1) && this.state.readMeWarning) {
      this.setState({ readMeWarning: null });
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
    if (this.props.isPublishing) {
      this.setState({ readMeWarning: 'publishing' });
    } else if (this.props.isSyncing) {
      this.setState({ readMeWarning: 'syncing' });
    } else {
      const { owner, labbookName } = store.getState().routes;
      if (this.props.sectionType === 'labbook') {
        this._saveLabbookReadme(owner, labbookName);
      } else {
        this._saveDatasetReadme(owner, labbookName);
      }
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
      }),

      readmeCSS = classNames({
        'ReadmeMarkdown--expanded': state.readmeExpanded,
        ReadmeMarkdown: !state.readmeExpanded,
      }),

      overviewReadmeEditingCSS = classNames({
        'Overview__readme--editing': state.editingReadme,
        hidden: !state.editingReadme,
      }),

      overviewReadmeCSS = classNames({
        'Overview__readme Card Card--auto Card--no-hover': !state.editingReadme,
        hidden: state.editingReadme,
      }),

      overviewReadmeButtonCSS = classNames({
        'Overview__readme-edit-button': true,
        hidden: state.editingReadme,
      });
    const sectionProps = props[props.sectionType],
          typeText = props.sectionType === 'labbook' ? 'Environment' : 'Type';

    if (sectionProps) {
      const { owner, labbookName } = store.getState().routes;
      return (

        <div className={overviewCSS}>
          {
            props.sectionType === 'labbook' ?
            <div>
              <RecentActivity
                recentActivity={sectionProps.overview.recentActivity}
                scrollToTop={props.scrollToTop}
                history={props.history}
              />

            </div>
            :
            <Fragment>
              <div className="Overview__container">
                <h5 className="Overview__title">
                  Summary <ToolTip section="summary" />
                </h5>

              </div>
              <div>
                <Summary
                  isManaged={props.isManaged}
                  {...sectionProps.overview}
                />
              </div>
            </Fragment>
          }

          <div className="Overview__container">

            <h5 className="Overview__title">
              Readme <ToolTip section="readMe" />
            </h5>

            </div>

            {
            state.editingReadme &&

            <div className={overviewReadmeEditingCSS}>

              <textarea
                ref="markdown"
                className="Overview__readme-editor"
                id="markDown"
              />

              <div className="Overview__readme--editing-buttons">

                <button
                  className="Overview__readme-save"
                  disabled={false}
                  onClick={() => { this._saveReadme(); }}
                >
                  Save
                </button>

                {
                  state.readMeWarning &&

                  <Fragment>

                    <div className="BranchMenu__menu-pointer" />

                    <div className="BranchMenu__button-menu">
                      Readme cannot be edited while project is
                      {state.readMeWarning}
                      .
                    </div>
                  </Fragment>
                }
                <button
                  className="Overview__readme-cancel"
                  onClick={() => { this._closeReadme(); }}
                >
                  Cancel
                </button>
              </div>
            </div>
            }
            {
            sectionProps.overview.readme ?
              <div
                className={overviewReadmeCSS}
              >
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

                {
                  state.overflowExists && !state.readmeExpanded &&

                  <div className="Overview__readme-fadeout" />
                }

                <div className="Overview__readme-buttons">
                  {
                    state.overflowExists && (state.readmeExpanded ?
                      <div className="Overview__readme-bar-less">
                        <button
                          className="Overview__readme-less"
                          onClick={() => this._shrinkReadme()}
                        >
                          Collapse
                        </button>
                      </div>
                      :
                      <div className="Overview__readme-bar-more">
                        <button
                          className="Overview__readme-more"
                          onClick={() => this._expandReadme()}
                        >
                          Expand
                        </button>
                      </div>)
                  }
                </div>

              </div>
              :
              !state.editingReadme &&
                <div className="Overview__empty">
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
            }
              <div className="Overview__container">

              <h5 className="Overview__title">
                {typeText}
                <ToolTip section="environmentOverview" />
              </h5>

            </div>
            {
              props.sectionType === 'labbook' ?
              <div className="Overview__environment">
                <button
                  className="Btn--redirect"
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
              :
              <div className="Overview__environment">

                <Type
                  type={props.datasetType}
                  isManaged={props.isManaged}
                />

              </div>
            }
          {
            props.sectionType === 'labbook' &&
            <div>

              <FilePreview
                ref="filePreview"
                scrollToTop={props.scrollToTop}
                history={props.history}
              />

            </div>
          }

        </div>
      );
    }

    return (<Loader />);
  }
}
