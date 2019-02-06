// vendor
import React, { Component, Fragment } from 'react';
import uuidv4 from 'uuid/v4';
import classNames from 'classnames';
// mutations
import PublishLabbookMutation from 'Mutations/branches/PublishLabbookMutation';
import PublishDatasetMutation from 'Mutations/branches/PublishDatasetMutation';
import SyncLabbookMutation from 'Mutations/branches/SyncLabbookMutation';
import ModifyDatasetLinkMutation from 'Mutations/ModifyDatasetLinkMutation';
import BuildImageMutation from 'Mutations/BuildImageMutation';
// component
import Modal from 'Components/common/Modal';
// store
import { setErrorMessage, setInfoMessage, setMultiInfoMessage } from 'JS/redux/reducers/footer';
import { setContainerMenuVisibility } from 'JS/redux/reducers/labbook/environment/environment';
import store from 'JS/redux/store';
// assets
import './PublishDatasetsModal.scss';
// query
import LocalDatasetsQuery from '../queries/LocalDatasetsQuery';

export default class PublishDatasetsModal extends Component {
  constructor(props) {
    super(props);

    this._publishLabbook = this._publishLabbook.bind(this);
  }

  state = {
    showPrompt: true,
    isProcessing: false,
    visibilityStatus: {
      project: null,
    },
    progress: {

    },
  }
  /**
    @param {object} nextProps
    @param {object} nextState
    handles new localDatasets from props
  */
  static getDerivedStateFromProps(nextProps, nextState) {
    const NewVisibilityStatus = Object.assign({}, nextState.visibilityStatus);
    nextProps.localDatasets.forEach(({ owner, name }) => {
      if (!NewVisibilityStatus[`${owner}/${name}`]) {
        NewVisibilityStatus[`${owner}/${name}`] = null;
      }
      if (nextProps.header === 'Sync') {
        delete NewVisibilityStatus.project;
      }
    });

    return {
      ...nextState,
      visibilityStatus: NewVisibilityStatus,
    };
  }

  /**
  *  @param {string} name
  *  @param {boolean} isPublic
  *  sets public state
  *  @return {string}
  */
  _setPublic(name, isPublic) {
    const NewVisibilityStatus = Object.assign({}, this.state.visibilityStatus);
    NewVisibilityStatus[name] = isPublic ? 'public' : 'private';
    this.setState({ visibilityStatus: NewVisibilityStatus });
  }

  /**
  *  @param {}
  *  adds remote url to labbook
  *  @return {string}
  */
  _publishLabbook() {
    const id = uuidv4();
    const self = this;

    const {
      owner,
      labbookName,
      labbookId,
    } = this.props;
    const isPublishing = this.props.header === 'Publish';
    this.props.checkSessionIsValid().then((response) => {
      if (navigator.onLine) {
        if (response.data) {
          if (response.data.userIdentity.isSessionValid) {
            if (store.getState().containerStatus.status !== 'Running') {
              self.props.resetPublishState(true);

              if (isPublishing) {
                self.props.setPublishingState(true);

                self.props.showContainerMenuMessage('publishing');
              } else {
                self.props.setSyncingState(true);

                self.props.showContainerMenuMessage('syncing');
              }

              const failureCall = (errorMessage) => {
                setTimeout(() => this.props.toggleModal(false, true), 2000);
                if (isPublishing) {
                  self.props.setPublishingState(false);
                  self.props.resetPublishState(false);
                } else {
                  self.props.setSyncingState(false);
                  if ((errorMessage.indexOf('MergeError') > -1) || (errorMessage.indexOf('Cannot merge') > -1) || (errorMessage.indexOf('Merge conflict') > -1)) {
                    self.props.toggleSyncModal();
                  }
                }
                setContainerMenuVisibility(false);
              };

              const successCall = () => {
                const successProgress = Object.assign({}, this.state.progress);
                successProgress.project = { step: 3 };
                this.setState({ progress: successProgress });
                setTimeout(() => this.props.toggleModal(false, true), 2000);
                setContainerMenuVisibility(false);
                if (isPublishing) {
                  self.props.setPublishingState(false);
                  self.props.resetPublishState(false);
                  self.props.remountCollab();

                  setMultiInfoMessage(id, `Added remote https://gigantum.com/${self.props.owner}/${self.props.labbookName}`, true, false);

                  self.props.setRemoteSession();
                } else {
                  BuildImageMutation(
                    this.props.labbookName,
                    this.props.owner,
                    false,
                    (response, error) => {
                      if (error) {
                        console.error(error);

                        setMultiInfoMessage(id, `ERROR: Failed to build ${this.state.labookName}`, null, true, error);
                      }
                    },
                  );
                  self.props.setSyncingState(false);
                }

              };

              let datasetsToPublish = this.props.localDatasets.length;
              this.setState({ isProcessing: true });
              this.props.localDatasets.forEach(({ owner, name }) => {
                const initialProgress = Object.assign({}, this.state.progress);
                initialProgress[`${owner}/${name}`] = { step: 1 };
                initialProgress.project = { step: 1 };
                this.setState({ progress: initialProgress });
                const datasetPublicSuccessCall = () => {
                  const newProgress = Object.assign({}, this.state.progress);
                  newProgress[`${owner}/${name}`] = { step: 2 };
                  this.setState({ progress: newProgress });
                  ModifyDatasetLinkMutation(
                    this.props.owner,
                    this.props.labbookName,
                    owner,
                    name,
                    'unlink',
                    null,
                    (response, error) => {
                        if (error) {
                            setErrorMessage('Unable to unlink dataset', error);
                        } else {
                          const updatedProgress = Object.assign({}, this.state.progress);
                          updatedProgress[`${owner}/${name}`] = { step: 3 };
                          this.setState({ progress: updatedProgress });
                          LocalDatasetsQuery.getLocalDatasets({ owner, name }).then((res) => {
                            ModifyDatasetLinkMutation(
                              this.props.owner,
                              this.props.labbookName,
                              owner,
                              name,
                              'link',
                              res.data.dataset.defaultRemote,
                              (response, error) => {
                                  if (error) {
                                      setErrorMessage('Unable to relink dataset', error);
                                  } else {
                                    datasetsToPublish -= 1;
                                    const finalProgress = Object.assign({}, this.state.progress);
                                    finalProgress[`${owner}/${name}`] = { step: 4 };
                                    if (datasetsToPublish === 0) {
                                      finalProgress.project = { step: 2 };
                                    }
                                    this.setState({ progress: finalProgress });
                                    if (datasetsToPublish === 0) {
                                      if (isPublishing) {
                                        PublishLabbookMutation(
                                          this.props.owner,
                                          this.props.labbookName,
                                          labbookId,
                                          this.state.visibilityStatus.project,
                                          successCall,
                                          failureCall,
                                          (response, error) => {
                                            if (error) {
                                              failureCall();
                                            }
                                          },
                                        );
                                      } else {
                                        SyncLabbookMutation(
                                          this.props.owner,
                                          this.props.labbookName,
                                          false,
                                          successCall,
                                          failureCall,
                                          (error) => {
                                            if (error) {
                                              failureCall();
                                            }
                                          },
                                        );
                                      }
                                    }
                                  }
                              },
                            );
                          });
                        }
                    },
                  );
                };
                LocalDatasetsQuery.getLocalDatasets({ owner, name }).then((res) => {
                  if (res.data.dataset.defaultRemote) {
                    datasetPublicSuccessCall();
                  } else {
                    PublishDatasetMutation(
                      owner,
                      name,
                      this.state.visibilityStatus[`${owner}/${name}`],
                      datasetPublicSuccessCall,
                      failureCall,
                      (response, error) => {
                        if (error) {
                          failureCall();
                        }
                      },
                    );
                  }
                })
              });
            } else {
              self.props.showContainerMenuMessage('publishing', true);
            }
          } else {
            self.props.auth.renewToken(true, () => {
              self.props.resetState();
            }, () => {
              self._publishLabbook();
            });
          }
        }
      } else {
        self.props.resetState();
      }
    });
  }

  _modifyVisibility() {
    if (this.props.header === 'Publish') {
      this._publishLabbook();
    } else {
      this._changeVisibility();
    }
  }


  render() {
    const { props } = this;
    const moreInfoText = this.state.moreInfo ? 'Hide' : 'More Info';
    const isDisabled = Object.keys(this.state.visibilityStatus).filter(key => this.state.visibilityStatus[key] === null).length;
    const containerCSS = classNames({
      PublishDatasetsModal__container: true,
      'PublishDatasetsModal__container--processing': this.state.isProcessing,
    });
    const currentStep = this.state.progress.project ? this.state.progress.project.step : 1;
    const firstProjectStepCSS = classNames({
      'is-active': currentStep === 1,
      'is-completed': currentStep > 1,
    });
    const secondProjectStepCSS = classNames({
      'is-active': currentStep === 2,
      'is-completed': currentStep > 2,
    });
    const thirdProjectStepCSS = classNames({
      'is-completed': currentStep === 3,
    });
    const action = this.props.header === 'Publish' ? 'Publishing' : 'Syncing';

    return (
        <Modal
          header={props.header}
          handleClose={this.state.isProcessing ? null : () => props.toggleModal(false, true)}
          size="large"
          icon="project"
          renderContent={() => (
            <div className="PublishDatasetsModal">
              {
                this.state.showPrompt ?
                <div>
                  <div className="PublishDatasetsModal__container">
                    <div className="PublishDatasetsModal__header-text">
                      <p>This Project is linked to unpublished (local-only) Datasets</p>
                      <p>
                        In order to publish a Project, all linked Datasets must also be published.
                         <button className="button--flat" onClick={() => this.setState({ moreInfo: !this.state.moreInfo })}>{moreInfoText}</button>
                        </p>
                    </div>
                    {
                      this.state.moreInfo &&
                      <Fragment>
                        <p>Click  “Continue” to publish the Dataset(s) listed below along with the Project. You will be able to set the visibility (public or private) for each Dataset and the Project.</p>
                        <p>If you do not want to publish any of the Dataset(s) listed below, click “Cancel” and then unlink the Dataset(s) before attempting to publish the Project.</p>
                      </Fragment>
                    }
                    <p className="PublishDatasetsModal__ul-label">Local Datasets:</p>
                    <ul className="PublishDatasetsModal__list">
                      {
                        props.localDatasets.map(localDataset => (
                          <li
                            key={`${localDataset.owner}/${localDataset.name}`}
                          >
                            {`${localDataset.owner}/${localDataset.name}`}
                          </li>
                        ))
                      }
                    </ul>

                  </div>

                  <div className="PublishDatasetsModal__buttons">
                    <button className="button--flat" onClick={() => { props.toggleModal(false, true); }}>Cancel</button>
                    <button onClick={() => { this.setState({ showPrompt: false }); }}>Continue</button>
                  </div>
                </div>
              :
              <div>
                  <div className={containerCSS}>
                    {
                      this.props.header === 'Publish' || this.state.isProcessing ?
                      <Fragment>
                        <p>Select the visibility for the project and datasets to be published.</p>

                        <h5 className="PublishDatasetsModal__Label">Project</h5>
                        <div className="PublishDatasetsModal__radio-container">
                        {`${this.props.owner}/${this.props.labbookName}`}
                          <div className="PublishDatasetsModal__radio-subcontainer">
                          {
                            !this.state.isProcessing ?
                              <Fragment>
                                  <div className="PublishDatasetsModal__private">
                                    <input
                                      type="radio"
                                      name="publishProject"
                                      id="project_private"
                                      onClick={() => { this._setPublic('project', false); }}
                                    />

                                    <label htmlFor="project_private">
                                      <b>Private</b>
                                    </label>

                                    {/* <p className="PublishDatasetsModal__paragraph">Private projects are only visible to collaborators. Users that are added as a collaborator will be able to view and edit.</p> */}

                                    </div>

                                    <div className="PublishDatasetsModal__public">

                                    <input
                                      name="publishProject"
                                      type="radio"
                                      id="project_public"
                                      onClick={() => { this._setPublic('project', true); }}
                                    />

                                    <label htmlFor="project_public">
                                      <b>Public</b>
                                    </label>

                                    {/* <p className="PublishDatasetsModal__paragraph">Public projects are visible to everyone. Users will be able to import a copy. Only users that are added as a collaborator will be able to edit.</p> */}

                                    </div>
                              </Fragment>
                            :
                            <div className="container-fluid">
                              <ul className="list-unstyled multi-steps project">
                                <li className={firstProjectStepCSS}>Waiting</li>
                                <li className={secondProjectStepCSS}>{action}</li>
                                <li className={thirdProjectStepCSS}>Finished</li>
                              </ul>
                            </div>
                          }

                          </div>
                        </div>
                      </Fragment>
                      :
                      <p>Select the visibility for the datasets to be published.</p>
                    }
                    <h5 className="PublishDatasetsModal__Label">Datasets</h5>
                    <ul>
                      {
                        props.localDatasets.map((localDataset) => {
                          const name = `${localDataset.owner}/${localDataset.name}`;
                          const currentStep = this.state.progress[name] ? this.state.progress[name].step : 2;
                          const firstStepCSS = classNames({
                            'is-active': currentStep === 1,
                            'is-completed': currentStep > 1,
                          });
                          const secondStepCSS = classNames({
                            'is-active': currentStep === 2,
                            'is-completed': currentStep > 2,
                          });
                          const thirdStepCSS = classNames({
                            'is-active': currentStep === 3,
                            'is-completed': currentStep > 3,
                          });
                          const fourthStepCSS = classNames({
                            'is-completed': currentStep === 4,
                          });
                          return (
                          <li
                            key={name}
                            className="flex"
                          >
                            {name}
                            <div className="PublishDatasetsModal__Datasets-radio-container">
                            {
                              !this.state.isProcessing ?
                              <Fragment>
                                <div>
                                  <input
                                    type="radio"
                                    name={name}
                                    id={`${name}_private`}
                                    onClick={() => { this._setPublic(name, false); }}
                                  />
                                  <label
                                    htmlFor={`${name}_private`}
                                    className="PublishDatasetsModal__private-label"
                                  >
                                    <b>Private</b>
                                  </label>
                                </div>
                                <div>
                                  <input
                                    type="radio"
                                    name={name}
                                    id={`${name}_public`}
                                    onClick={() => { this._setPublic(name, true); }}
                                  />
                                  <label
                                    htmlFor={`${name}_public`}
                                    className="PublishDatasetsModal__public-label"
                                  >
                                    <b>Public</b>
                                  </label>
                                </div>
                              </Fragment>
                              :
                            <div className="container-fluid">
                              <ul className="list-unstyled multi-steps">
                                <li className={firstStepCSS}>Publishing</li>
                                <li className={secondStepCSS}>Unlinking</li>
                                <li className={thirdStepCSS}>Relinking</li>
                                <li className={fourthStepCSS}>Finished</li>
                              </ul>
                            </div>
                            }

                            </div>
                          </li>
                        );
                      })
                      }
                    </ul>

                    </div>
                    {
                      !this.state.isProcessing &&
                      <div className="PublishDatasetsModal__buttons">
                        <button className="button--flat" onClick={() => { props.toggleModal(false, true); }}>Cancel</button>
                        <button disabled={isDisabled} onClick={() => { this._publishLabbook(); }}>
                          {props.buttonText}
                          {this.props.header === 'Sync' && ' And Sync'}
                        </button>

                      </div>
                    }
              </div>
              }
            </div>)
          }
        />
    );
  }
}
