// vendor
import React, { Component, Fragment } from 'react';
import {
  createFragmentContainer,
  graphql,
} from 'react-relay';
import { Link } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import SimpleMDE from 'simplemde';
import classNames from 'classnames';
// components
import Base from 'Components/labbook/environment/Base';
import FilePreview from './FilePreview';
import RecentActivity from './RecentActivity';
import Loader from 'Components/common/Loader';
import FileEmpty from 'Components/labbook/overview/FileEmpty';
import CodeBlock from 'Components/labbook/renderers/CodeBlock';
import ToolTip from 'Components/common/ToolTip';
// mutations
import WriteReadmeMutation from 'Mutations/WriteReadmeMutation';
import SetLabbookDescriptionMutation from 'Mutations/SetLabbookDescriptionMutation';
// store
import store from 'JS/redux/store';
import { setErrorMessage } from 'JS/redux/reducers/footer';
// assets
import './Overview.scss';

let simple;

class Overview extends Component {
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
    this._editReadme = this._editReadme.bind(this);
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

    if (!this.state.simpleExists) {
      if (document.getElementById('markDown')) {
        simple = new SimpleMDE({
          element: document.getElementById('markDown'),
          spellChecker: true,
        });

        simple.value(this.props.readme ? this.props.readme : '');
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
  _closeReadme() {
    this.setState({ editingReadme: false, simpleExists: false });
  }
  _saveReadme() {
    if (this.props.isPublishing) {
      this.setState({ readMeWarning: 'publishing' });
    } else if (this.props.isSyncing) {
      this.setState({ readMeWarning: 'syncing' });
    } else {
      const { owner, labbookName } = store.getState().routes;
      WriteReadmeMutation(
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
  }
  _editReadme() {
    this.setState({ editingReadme: true });
  }

  render() {
    const overviewCSS = classNames({
        Overview: true,
        'Overview--fullscreen': this.state.editorFullscreen,
      }),

      readmeCSS = classNames({
        'ReadmeMarkdown--expanded': this.state.readmeExpanded,
        ReadmeMarkdown: !this.state.readmeExpanded,
      }),

      overviewReadmeEditingCSS = classNames({
        'Overview__readme--editing': this.state.editingReadme,
        hidden: !this.state.editingReadme,
      }),

      overviewReadmeCSS = classNames({
        'Overview__readme Card Card--auto Card--no-hover': !this.state.editingReadme,
        hidden: this.state.editingReadme,
      }),

      overviewReadmeButtonCSS = classNames({
        'Overview__readme-edit-button': true,
        hidden: this.state.editingReadme || !this.props.readme,
      });


    if (this.props.labbook) {
      const { owner, labbookName } = store.getState().routes;

      return (

        <div className={overviewCSS}>

          <div>

            <RecentActivity
              recentActivity={this.props.labbook.overview.recentActivity}
              scrollToTop={this.props.scrollToTop}
            />

          </div>

          <div className="Overview__container">

            <h5 className="Overview__title">
              Readme <ToolTip section="readMe" />

              <button
                className={overviewReadmeButtonCSS}
                onClick={() => this.setState({ editingReadme: true })}
              />

            </h5>

            </div>

            {
            this.state.editingReadme &&

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
                  this.state.readMeWarning &&

                  <Fragment>

                    <div className="BranchMenu__menu-pointer" />

                    <div className="BranchMenu__button-menu">
                      Readme cannot be edited while project is {this.state.readMeWarning}.
                    </div>

                  </Fragment>
                }
                <button
                  className="Overview__readme-cancel"
                  onClick={() => { this._closeReadme(); }}
                >Cancel
                </button>
              </div>
            </div>
            }
            {
            this.props.readme ?
              <div
                className={overviewReadmeCSS}
              >

                <ReactMarkdown
                  className={readmeCSS}
                  source={this.props.readme}
                  renderers={{ code: props => <CodeBlock {...props} /> }}
                />

                {
                  this.state.overflowExists && !this.state.readmeExpanded &&

                  <div className="Overview__readme-fadeout" />
                }

                <div className="Overview__readme-buttons">
                  {
                    this.state.overflowExists && (this.state.readmeExpanded ?
                      <div className="Overview__readme-bar-less">
                        <button
                          className="Overview__readme-less"
                          onClick={() => { this.setState({ readmeExpanded: false }); }}
                        >
                          Collapse
                        </button>
                      </div>
                      :
                      <div className="Overview__readme-bar-more">
                        <button
                          className="Overview__readme-more"
                          onClick={() => { this.setState({ readmeExpanded: true }); }}
                        >
                          Expand
                        </button>
                      </div>)
                  }
                </div>

              </div>

              :
              !this.state.editingReadme &&
                <FileEmpty
                  section="edit"
                  mainText="This Project does not have a readme."
                  subText="Click here to create one"
                  callback={this._editReadme}
                />
            }

          <div className="Overview__container">

            <h5 className="Overview__title">
              Environment<ToolTip section="environmentOverview" />
            </h5>

            <Link
              onClick={this.props.scrollToTop}
              to={{ pathname: `../../../../projects/${owner}/${labbookName}/environment` }}
              replace
            >
              Environment Details >
            </Link>

          </div>

          <div className="Overview__environment">

            <Base
              ref="base"
              environment={this.props.labbook.environment}
              blockClass="Overview"
              overview={this.props.labbook.overview}
            />

          </div>

          <div>

            <FilePreview
              ref="filePreview"
              scrollToTop={this.props.scrollToTop}
            />

          </div>

        </div>
      );
    }

    return (<Loader />);
  }
}


export default createFragmentContainer(
  Overview,
  graphql`fragment Overview_labbook on Labbook {
    overview{
      id
      owner
      name
      numAptPackages
      numConda2Packages
      numConda3Packages
      numPipPackages
      recentActivity{
        id
        owner
        name
        message
        detailObjects {
          id
          data
        }
        type
        timestamp
        username
        email
      }
      remoteUrl
    }
    environment{
      id
      imageStatus
      containerStatus
      ...Base_environment
    }
  }`,
);
