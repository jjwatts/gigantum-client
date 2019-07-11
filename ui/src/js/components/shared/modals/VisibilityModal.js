// vendor
import React, { Component } from 'react';
import uuidv4 from 'uuid/v4';
import { boundMethod } from 'autobind-decorator';
// mutations
import SetVisibilityMutation from 'Mutations/SetVisibilityMutation';
import SetDatasetVisibilityMutation from 'Mutations/SetDatasetVisibilityMutation';
import PublishLabbookMutation from 'Mutations/branches/PublishLabbookMutation';
import PublishDatasetMutation from 'Mutations/branches/PublishDatasetMutation';
// component
import Modal from 'Components/common/Modal';
// store
import { setErrorMessage, setInfoMessage, setMultiInfoMessage } from 'JS/redux/actions/footer';
import store from 'JS/redux/store';
// assets
import './VisibilityModal.scss';


export default class PublishModal extends Component {
  state = {
    isPublic: (this.props.visibility === 'public'),
  }

  /**
  *  @param {boolean}
  *  sets public state
  *  @return {string}
  */
  _setPublic(isPublic) {
    this.setState({
      isPublic,
    });
  }

  /**
  *  @param {}
  *  adds remote url to labbook
  *  @return {string}
  */
  @boundMethod
  _changeVisibility() {
    const { props, state } = this;
    const self = this;
    const visibility = state.isPublic ? 'public' : 'private';
    const {
      owner,
      labbookName,
    } = props;

    props.toggleModal(props.modalStateValue);


    props.checkSessionIsValid().then((response) => {
      if (navigator.onLine) {
        if (response.data) {
          if (response.data.userIdentity.isSessionValid) {
            if (props.visibility !== visibility) {
              if (props.sectionType === 'labbook') {
                SetVisibilityMutation(
                  owner,
                  labbookName,
                  visibility,
                  (visibilityResponse, error) => {
                    if (error) {
                      console.log(error);
                      setErrorMessage('Visibility change failed', error);
                    } else {
                      setInfoMessage(`Visibility changed to ${visibility}`);
                    }
                  },
                );
              } else {
                SetDatasetVisibilityMutation(
                  owner,
                  labbookName,
                  visibility,
                  (visibilityResponse, error) => {
                    if (error) {
                      console.log(error);
                      setErrorMessage('Visibility change failed', error);
                    } else {
                      setInfoMessage(`Visibility changed to ${visibility}`);
                    }
                  },
                );
              }
            }
          } else {
            props.auth.renewToken(true, () => {
              props.resetState();
            }, () => {
              self._changeVisibility();
            });
          }
        }
      } else {
        props.resetState();
      }
    });
  }

  /**
  *  @param {}
  *  adds remote url to labbook
  *  @return {string}
  */
  @boundMethod
  _publishLabbook() {
    const { props, state } = this;
    const id = uuidv4();
    const self = this;
    const {
      owner,
      labbookName,
      labbookId,
    } = props;

    props.toggleModal();

    props.checkSessionIsValid().then((response) => {
      if (navigator.onLine) {
        if (response.data) {
          if (response.data.userIdentity.isSessionValid) {
            if (store.getState().containerStatus.status !== 'Running') {
              props.resetPublishState(true);

              if (!props.remoteUrl) {
                props.setPublishingState(true);

                const failureCall = () => {
                  props.setPublishingState(false);
                  props.resetPublishState(false);
                };

                const successCall = () => {
                  props.setPublishingState(false);
                  props.resetPublishState(false);
                  // self.props.remountCollab();
                  const messageData = {
                    id,
                    message: `Added remote https://gigantum.com/${props.owner}/${props.labbookName}`,
                    isLast: true,
                    error: false,
                  };
                  setMultiInfoMessage(messageData);

                  props.setRemoteSession();
                };

                if (props.sectionType === 'labbook') {
                  PublishLabbookMutation(
                    owner,
                    labbookName,
                    labbookId,
                    state.isPublic,
                    successCall,
                    failureCall,
                    (publishResponse, error) => {
                      if (error) {
                        failureCall();
                      }
                    },
                  );
                } else {
                  PublishDatasetMutation(
                    owner,
                    labbookName,
                    state.isPublic,
                    successCall,
                    failureCall,
                    (publishResponse, error) => {
                      if (error) {
                        failureCall();
                      }
                    },
                  );
                }
              }
            }
          } else {
            props.auth.renewToken(true, () => {
              props.resetState();
            }, () => {
              self._publishLabbook();
            });
          }
        }
      } else {
        props.resetState();
      }
    });
  }

  /**
  *  @param {} -
  *  triggers publish or change visibility
  *  @return {}
  */
  _modifyVisibility() {
    const { props } = this;
    if (props.header === 'Publish') {
      this._publishLabbook();
    } else {
      this._changeVisibility();
    }
  }


  render() {
    const { props, state } = this;

    return (

      <Modal
        header={props.header}
        handleClose={() => props.toggleModal(props.modalStateValue)}
        size="large"
        icon={props.visibility}
        renderContent={() => (
          <div className="VisibilityModal">
            <div>
              <p>You are about to change the visibility of the project.</p>
            </div>

            <div>
              <div className="VisibilityModal__private">
                <label
                  className="Radio"
                  htmlFor="publish_private"
                >
                  <input
                    defaultChecked={(props.visibility === 'private') || !state.isPublic}
                    type="radio"
                    name="publish"
                    id="publish_private"
                    onClick={() => { this._setPublic(false); }}
                  />
                  <span><b>Private</b></span>
                </label>

                <p className="VisibilityModal__paragraph">Private projects are only visible to collaborators. Users that are added as a collaborator will be able to view and edit.</p>

              </div>

              <div className="VisibilityModal__public">

                <label
                  className="Radio"
                  htmlFor="publish_public"
                >
                  <input
                    defaultChecked={props.visibility === 'public'}
                    name="publish"
                    type="radio"
                    id="publish_public"
                    onClick={() => { this._setPublic(true); }}
                  />
                  <span><b>Public</b></span>
                </label>

                <p className="VisibilityModal__paragraph">Public projects are visible to everyone. Users will be able to import a copy. Only users that are added as a collaborator will be able to edit.</p>

              </div>

            </div>

            <div className="VisibilityModal__buttons">
              <button
                type="submit"
                className="Btn--flat"
                onClick={() => { props.toggleModal(props.modalStateValue); }}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="Btn--last"
                onClick={() => { this._modifyVisibility(); }}
              >
                {props.buttonText}
              </button>
            </div>

          </div>
        )
        }
      />
    );
  }
}
