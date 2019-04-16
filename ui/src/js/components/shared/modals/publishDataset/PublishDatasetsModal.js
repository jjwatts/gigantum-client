// vendor
import React, { Component } from 'react';
import uuidv4 from 'uuid/v4';
import classNames from 'classnames';
import { boundMethod } from 'autobind-decorator';
// store
import { setErrorMessage, setMultiInfoMessage } from 'JS/redux/actions/footer';
import store from 'JS/redux/store';
// query
import LocalDatasetsQuery from 'Components/shared/header/actionsSection/queries/LocalDatasetsQuery';
// component
import Modal from 'Components/common/Modal';
import DatasetPublish from './DatasetPublish';
import ProjectPublish from './ProjectPublish';
import WarningInfoPrompt from './WarningInfoPrompt';
// Mutations
import PublishMutations from './mutations/PublishMutations';
// assets
import './PublishDatasetsModal.scss';

export default class PublishDatasetsModal extends Component {
  state = {
    showPrompt: true,
    isProcessing: false,
    visibilityStatus: {
      project: null,
    },
    mutations: new PublishMutations(this.props),
    progress: {},
    datasetsToPublish: 0,
  }

  /**
    @param {object} nextProps
    @param {object} nextState
    handles new localDatasets from props
  */
  static getDerivedStateFromProps(nextProps, nextState) {
    const NewVisibilityStatus = Object.assign({}, nextState.visibilityStatus);
    nextProps.localDatasets.forEach(({ owner, name }) => {
      if (NewVisibilityStatus[`${owner}/${name}`] === undefined) {
        NewVisibilityStatus[`${owner}/${name}`] = null;
      }
      if (nextProps.header === 'Sync') {
        delete NewVisibilityStatus.project;
      }
    });

    return {
      ...nextState,
      visibilityStatus: NewVisibilityStatus,
      datasetsToPublish: nextProps.localDatasets.length,
    };
  }

  /**
  *  @param {} -
  *  sets public state
  *  @return {}
  */
  @boundMethod
  _passedSuccessCall() {
    const { props, state } = this;
    const successProgress = Object.assign({}, state.progress);

    successProgress.project = { step: 3 };
    this.setState({ progress: successProgress });

    setTimeout(() => props.toggleModal(false, true), 2000);
  }

  /**
  *  @param {}
  *  sets public state
  *  @return {}
  */
  @boundMethod
  _successCall() {
    const { props, state } = this;
    const { owner, labbookName } = props;
    const isPublishing = props.header === 'Publish';
    const id = uuidv4();
    const successProgress = Object.assign({}, state.progress);

    successProgress.project = { step: 3 };
    this.setState({ progress: successProgress });

    setTimeout(() => props.toggleModal(false, true), 2000);

    if (isPublishing) {
      props.setPublishingState(false);
      props.resetPublishState(false);

      setMultiInfoMessage(id, `Added remote https://gigantum.com/${owner}/${labbookName}`, true, false);

      props.setRemoteSession();
    } else {
      this._buildImage(id);
    }
  }

  /**
  *  @param {string} errorMessage
  *  sets public state
  *  @return {}
  */
  @boundMethod
  _failureCall(errorMessage) {
    const { props } = this;
    const isPublishing = props.header === 'Publish';

    setTimeout(() => props.toggleModal(false, true), 2000);

    if (isPublishing) {
      props.setPublishingState(false);
      props.resetPublishState(false);
    } else {
      props.setSyncingState(false);
      if (errorMessage.indexOf('Merge conflict') > -1) {
        props.toggleSyncModal();
      }
    }
  }

  /**
  *  @param {} -
  *  triggers publish labbook mutation
  *  @return {}
  */
  @boundMethod
  _publishLabbookMutation() {
    const { state } = this;
    const data = {
      setPublic: state.visibilityStatus.project,
      successCall: this._successCall,
      failureCall: this._failureCall,
    };

    state.mutations._publishLabbook(
      data,
      (publishResponse, error) => {
        if (error) {
          this._failureCall();
        }
      },
    );
  }

  /**
  *  @param {string} datasetOwner
  *  @param {string} datasetName
  *  loops through local datasets and triggers mutatiob to relink and publish
  *  @return {}
  */
  _relinkDataset(datasetOwner, datasetName) {
    const { props, state } = this;
    const isPublishing = props.header === 'Publish';

    LocalDatasetsQuery.getLocalDatasets(
      {
        owner: datasetOwner,
        name: datasetName,
      },
    ).then((result) => {
      const linkData = {
        datasetOwner,
        datasetName,
        linkType: 'link',
        remote: result.data.dataset.defaultRemote,
      };

      state.mutations._modifyDatasetLink(
        linkData,
        (localResponse, error) => {
          if (error) {
            setErrorMessage('Unable to relink dataset', error);
          } else {
            const datasetsToPublish = (state.datasetsToPublish - 1);
            const finalProgress = Object.assign({}, state.progress);

            finalProgress[`${datasetOwner}/${datasetName}`] = { step: 4 };

            if (datasetsToPublish === 0) {
              finalProgress.project = { step: 2 };
            }
            this.setState({ progress: finalProgress });

            if (datasetsToPublish === 0) {
              if (isPublishing) {
                this._publishLabbookMutation();
              } else {
                props.handleSync(false, true, true, this._passedSuccessCall);
              }
            } else {
              this.setState({ datasetsToPublish });
            }
          }
        },
      );
    });
  }

  /**
  *  @param {} -
  *  gets a list of local datasets to publish
  *  @return {}
  */
  @boundMethod
  _unlinkDataset(datasetOwner, datasetName) {
    const { state } = this;
    const newProgress = Object.assign({}, state.progress);

    newProgress[`${datasetOwner}/${datasetName}`] = { step: 2 };

    this.setState({ progress: newProgress });


    const linkData = {
      datasetOwner,
      datasetName,
      linkType: 'unlink',
      remote: null,
    };

    state.mutations._modifyDatasetLink(
      linkData,
      (modifyResponse, error) => {
        if (error) {
          setErrorMessage('Unable to unlink dataset', error);
        } else {
          const updatedProgress = Object.assign({}, state.progress);
          updatedProgress[`${datasetOwner}/${datasetName}`] = { step: 3 };
          this.setState({ progress: updatedProgress });

          this._relinkDataset(datasetOwner, datasetName);
        }
      },
    );
  }

  /**
  *  @param {string} name
  *  @param {boolean} isPublic
  *  sets public state
  *  @return {string}
  */
  @boundMethod
  _setPublic(name, isPublic) {
    const { state } = this;
    const NewVisibilityStatus = Object.assign({}, state.visibilityStatus);

    NewVisibilityStatus[name] = isPublic;
    this.setState({ visibilityStatus: NewVisibilityStatus });
  }

  /**
  *  @param {string} name
  *  @param {string} owner
  *  sets public state
  *  @return {string}
  */
  @boundMethod
  _publishDataset(owner, name) {
    const { state } = this;
    const data = {
      datasetName: name,
      setPublic: state.visibilityStatus[`${owner}/${name}`],
      successCall: this._unlinkDataset,
      failureCall: this._failureCall,
    };

    state.mutations._publishDataset(
      data,
      (publishDatasetResponse, error) => {
        if (error) {
          this._failureCall();
        }
      },
    );
  }

  /**
  *  @param {}
  *  adds remote url to labbook
  *  @return {string}
  */
  @boundMethod
  _publishLabbook() {
    const { props, state } = this;
    const self = this;
    const conatinerStatus = store.getState().containerStatus.status;
    const isPublishing = props.header === 'Publish';

    props.checkSessionIsValid().then((response) => {
      if (navigator.onLine) {
        if (response.data) {
          if (response.data.userIdentity.isSessionValid) {
            if (conatinerStatus !== 'Running') {
              props.resetPublishState(true);

              if (isPublishing) {
                props.setPublishingState(true);
              } else {
                props.setSyncingState(true);
              }

              this.setState({ isProcessing: true });

              props.localDatasets.forEach(({ owner, name }) => {
                const initialProgress = Object.assign({}, state.progress);
                initialProgress[`${owner}/${name}`] = { step: 1 };
                initialProgress.project = { step: 1 };
                this.setState({ progress: initialProgress });

                LocalDatasetsQuery.getLocalDatasets({ owner, name }).then((res) => {
                  if (res.data.dataset.defaultRemote) {
                    this._unlinkDataset(owner, name);
                  } else {
                    this._publishDataset(owner, name);
                  }
                });
              });
            }
          } else {
            self.props.auth.renewToken(true, () => {
              self.props.resetState();
            }, () => {
              self._publishLabbookMutation();
            });
          }
        }
      } else {
        self.props.resetState();
      }
    });
  }

  /**
  *  @param {string} id
  *  triggers build mutation
  *  updates sync state
  *  @return {}
  */
  @boundMethod
  _buildImage(id) {
    const { props, state } = this;
    const { labbookName } = props;
    const data = { noCache: false };

    state.mutations._buildImage(data, (response, error) => {
      if (error) {
        console.error(error);
        setMultiInfoMessage(id, `ERROR: Failed to build ${labbookName}`, null, true, error);
      }
    });

    props.setSyncingState(false);
  }

  /**
  *  @param {} -
  *  set visibility
  *  @return {string}
  */
  _modifyVisibility() {
    const { props } = this;
    if (props.header === 'Publish') {
      this._publishLabbook();
    } else {
      this._changeVisibility();
    }
  }

  /**
  *  @param {} -
  *  sets prompt state to false
  *  @return {}
  */
  @boundMethod
  _hidePrompt() {
    this.setState({ showPrompt: false });
  }


  render() {
    const { props, state } = this;
    // Declare Variables here
    const keys = Object.keys(state.visibilityStatus);
    const isDisabled = keys.filter(key => state.visibilityStatus[key] === null).length;
    // Declare CSS classNames here
    const containerCSS = classNames({
      PublishDatasetsModal__container: true,
      'PublishDatasetsModal__container--processing': state.isProcessing,
    });

    return (
      <Modal
        header={props.header}
        handleClose={state.isProcessing ? null : () => props.toggleModal(false, true)}
        size="large"
        icon="dataset"
        renderContent={() => (
          <div className="PublishDatasetsModal">
            { state.showPrompt
              ? (
                <WarningInfoPrompt
                  localDatasets={props.localDatasets}
                  toggleModal={props.toggleModal}
                  hidePrompt={this._hidePrompt}
                />
              )
              : (
                <div>
                  <div className={containerCSS}>
                    { (props.header === 'Publish') || state.isProcessing
                      ? (
                        <ProjectPublish
                          isProcessing={state.isProcessing}
                          owner={props.owner}
                          labbookName={props.labbookName}
                          setPublic={this._setPublic}
                          header={props.header}
                          progress={state.progress}
                        />
                      )
                      : <p>Select the visibility for the datasets to be published.</p>
                    }
                    <h5 className="PublishDatasetsModal__Label">Datasets</h5>
                    <ul>
                      { props.localDatasets.map(localDataset => (
                        <DatasetPublish
                          localDataset={localDataset}
                          setPublic={this._setPublic}
                          progress={state.progress}
                          isProcessing={state.isProcessing}
                        />
                      ))
                      }
                    </ul>

                  </div>
                  { (!state.isProcessing)
                      && (
                      <div className="PublishDatasetsModal__buttons">
                        <button
                          type="button"
                          className="Btn--flat"
                          onClick={() => { props.toggleModal(false, true); }}
                        >
                        Cancel
                        </button>
                        <button
                          type="button"
                          className="Btn Btn--last"
                          disabled={isDisabled}
                          onClick={() => { this._publishLabbook(); }}
                        >
                          {props.buttonText}
                          {props.header === 'Sync' && ' And Sync'}
                        </button>
                      </div>
                      )
                    }
                </div>
              )
              }
          </div>
        )
        }
      />
    );
  }
}
