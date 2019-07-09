// vendor
import React from 'react';
import classNames from 'classnames';
// mutations
import CreateLabbookMutation from 'Mutations/CreateLabbookMutation';
import CreateDatasetMutation from 'Mutations/CreateDatasetMutation';
import BuildImageMutation from 'Mutations/container/BuildImageMutation';
// store
import { setErrorMessage } from 'JS/redux/actions/footer';
// components
import Loader from 'Components/common/Loader';
import ButtonLoader from 'Components/common/ButtonLoader';
import Modal from 'Components/common/Modal';
import CreateLabbook from './CreateLabbook';
import SelectBase from './SelectBase';
// assets
import './WizardModal.scss';

export default class WizardModal extends React.Component {
  constructor(props) {
  	super(props);

  	this.state = {
      name: '',
      description: '',
      repository: '',
      componentId: '',
      revision: '',
      selectedComponentId: 'createLabbook',
      nextComponentId: 'selectBase',
      previousComponentId: null,
      continueDisabled: true,
      modalBlur: false,
      menuVisibility: true,
      createLabbookButtonState: '',
    };

    this._createLabbookCallback = this._createLabbookCallback.bind(this);
    this._createLabbookMutation = this._createLabbookMutation.bind(this);
    this._createDatasetMutation = this._createDatasetMutation.bind(this);
    this._selectBaseCallback = this._selectBaseCallback.bind(this);
    this._continueSave = this._continueSave.bind(this);
    this._setComponent = this._setComponent.bind(this);
    this._hideModal = this._hideModal.bind(this);
    this._updateTextState = this._updateTextState.bind(this);
    this._setLabbookName = this._setLabbookName.bind(this);
    this._getSelectedComponentId = this._getSelectedComponentId.bind(this);
    this._toggleDisabledContinue = this._toggleDisabledContinue.bind(this);
    this._toggleMenuVisibility = this._toggleMenuVisibility.bind(this);
  }

  /**
    @param {Object, string} evt,field
    updates text in a state object and passes object to setState method
  */
  _updateTextState = (evt, field) => {
    const state = {};
    state[field] = evt.target.value;
    this.setState(state);
  }

  /**
    @param {boolean} menuVisibility
    shows hides navigation menu
  */
  _toggleMenuVisibility(menuVisibility) {
    this.setState({ menuVisibility });
  }


  /**
    @param {}
    shows modal window by update component state
  */
  _showModal = () => {
    this.setState({
      modal_visible: true,
      selectedComponentId: 'createLabbook',
      nextComponentId: 'selectBase',
      previousComponent: null,
    });
  }

  /**
    @param {}
    hides modal window by update component state
  */
  _hideModal = () => {
    this.setState({ modal_visible: false, menuVisibility: true });
  }

  /**
    @param {string} componentId
    sets view for child components using and id
  */
  _setComponent = (componentId) => {
    this.setState({ selectedComponentId: componentId });
  }

  /**
    @param {string} labbookName
    sets labbookName for mini session
  */
  _setLabbookName = (labbookName) => {
    this.setState({ labbookName });
  }

  /**
    @param {Object} base
    sets baseimage object for mini session
  */
  _setBase = (base) => {
    this.setState({ base });
  }

  /**
    @param {}
    gets id of current selected component for view navigation
    @return {string} selectedComponentId
  */
  _getSelectedComponentId = () => this.state.selectedComponentId

  /**
    @param {boolean} isDisabled
    setsContinueDisabled value to true or false
  */
  _toggleDisabledContinue = (isDisabled) => {
    this.setState({
      continueDisabled: isDisabled,
    });
  }

  /**
    @param { boolean} isSkip
    gets selected id and triggers continueSave function using refs
  */
  _continueSave = ({ isSkip, text }) => {
    const { props } = this;
    if (props.datasets) {
      this.refs[this._getSelectedComponentId()].continueSave(isSkip);
    } else {
      this.refs[this._getSelectedComponentId()].continueSave(isSkip);
      this.setState({ continueDisabled: true });
      if (text === 'Create Labbook') {
        this.setState({ modalBlur: true });
      }
    }
  }

  /**
    @param {string ,string} name,description
    sets name and description to state for create labbook mutation
  */
  _createLabbookCallback(name, description) {

    const { props } = this;
    this.setState({
      name,
      description,
    }, () => {
      if (props.datasets) {
        this._toggleDisabledContinue(true);
        this._createDatasetMutation();
      }
    });
    if (!props.datasets) {
      this._setComponent('selectBase');
    }
  }

  /**
    @param {string, string ,Int} repository, componentId revision
    sets (repository, componentId and revision to state for create labbook mutation
  */
  _selectBaseCallback(node) {
    const {
      repository,
      componentId,
      revision,
      storageType,
    } = node;
    const selectedType = this.props.datasets ? storageType : componentId;
    this.setState({
      repository,
      componentId: selectedType,
      revision,
    });
    // this._creatLabbookMutation();
  }

  /**
      @param {}
      sets name and description to state for create labbook mutation
  */
  _createLabbookMutation() {
    const self = this;
    const {
      name,
      description,
      repository,
      componentId,
      revision,
    } = this.state;

    this.setState({
      createLabbookButtonState: 'loading',
      modal_visible: false,
    });

    document.getElementById('modal__cover').classList.remove('hidden');
    document.getElementById('loader').classList.remove('hidden');

    CreateLabbookMutation(
      name,
      description,
      repository,
      componentId,
      revision,
      (response, error) => {
        if (error) {
          setErrorMessage(`An error occured while trying to create Project '${name}'.`, error);
          document.getElementById('modal__cover').classList.add('hidden');
          document.getElementById('loader').classList.add('hidden');
          this.setState({
            modalBlur: false,
            createLabbookButtonState: 'error',
          });

          setTimeout(() => {
            this.setState({
              createLabbookButtonState: '',
            });
          }, 2000);
        } else {
          const { owner, name } = response.createLabbook.labbook;
          localStorage.setItem('latest_base', componentId);
          this.setState({
            createLabbookButtonState: 'finished',
          });

          setTimeout(() => {
            self._buildImage(name, owner);

            this.setState({
              createLabbookButtonState: '',
            }, () => {
              self.props.history.push(`../projects/${owner}/${name}`);
              document.getElementById('modal__cover').classList.add('hidden');
              document.getElementById('loader').classList.add('hidden');
            });
          }, 2000);
        }
      },
    );
  }

  /**
      @param {}
      sets name and description to state for create labbook mutation
  */
  _createDatasetMutation() {
    const self = this;
    const {
      name,
      description,
      componentId,
    } = this.state;

    this.setState({
      createLabbookButtonState: 'loading',
    });

    CreateDatasetMutation(
      name,
      description,
      'gigantum_object_v1',
      (response, error) => {
        if (error) {
          setErrorMessage(`An error occured while trying to create Dataset '${name}'.`, error);
          this.setState({
            modalBlur: false,
            createLabbookButtonState: 'error',
          });

          setTimeout(() => {
            this.setState({
              createLabbookButtonState: '',
            });
          }, 2000);
        } else {
          const { owner, name } = response.createDataset.dataset;

          this.setState({
            createLabbookButtonState: 'finished',
          });

          setTimeout(() => {
            this.setState({
              createLabbookButtonState: '',
            }, () => {
              self.props.history.push(`../datasets/${owner}/${name}`);
            });
          }, 2000);
        }
      },
    );
  }

  /**
      @param {name, owner}
      builds docker iamge of labbook
  */
  _buildImage(name, owner) {
    BuildImageMutation(
      owner,
      name,
      false,
      (response, error) => {
        if (error) {
          console.error(error);
          setErrorMessage(`ERROR: Failed to build ${name}`, error);
        }
      },
    );
  }

  render() {
    const { props, state } = this;


    const loaderCSS = classNames({
      hidden: !this.state.modalBlur,
    });


    const currentComponent = this._currentComponent();


    const modalSize = (currentComponent.header === 'Select A Type' || currentComponent.header === 'Select A Base') ? 'large-long' : 'large';

    return (
      <div>
        { state.modal_visible
          && (
          <Modal
            size={modalSize}
            icon="add"
            handleClose={() => this._hideModal()}
            header={currentComponent.header}
            preHeader={currentComponent.preHeader}
            noPadding
            renderContent={() => (
              <div className="WizardModal">
                { currentComponent.component }
                <ModalNav
                  self={this}
                  state={state}
                  getSelectedComponentId={this._getSelectedComponentId}
                  setComponent={this._setComponent}
                  hideModal={this._hideModal}
                  continueSave={this._continueSave}
                  createLabbookCallback={this._createLabbookCallback}
                  isDataset={props.datasets}
                />
              </div>
            )
              }
          />
          )
        }
        { state.modalBlur
          && <Loader className={loaderCSS} />
        }
      </div>
    );
  }

  _currentComponent() {
    switch (this._getSelectedComponentId()) {
      case 'createLabbook':
        return {
          component:
            (<CreateLabbook
              ref="createLabbook"
              createLabbookCallback={this._createLabbookCallback}
              toggleDisabledContinue={this._toggleDisabledContinue}
              history={this.props.history}
              hideModal={this._hideModal}
              auth={this.props.auth}
              datasets={this.props.datasets}
            />),
          header: this.props.datasets ? 'Create Dataset' : 'Create Project',
        };

      case 'selectBase':
        return {
          component:
          (<SelectBase
            ref="selectBase"
            selectBaseCallback={this._selectBaseCallback}
            toggleDisabledContinue={this._toggleDisabledContinue}
            createLabbookMutation={this._createLabbookMutation}
            createDatasetMutation={this._createDatasetMutation}
            toggleMenuVisibility={this._toggleMenuVisibility}
            datasets={this.props.datasets}
          />),
          header: this.props.datasets ? 'Select A Type' : 'Select A Base',
          preHeader: this.props.datasets ? 'Create Dataset' : 'Create Project',
        };
      default:
        return {
          component:
          (<CreateLabbook
            ref="createLabbook"
            createLabbookCallback={this._createLabbookCallback}
            toggleDisabledContinue={this._toggleDisabledContinue}
            history={this.props.history}
            hideModal={this._hideModal}
            auth={this.props.auth}
          />),
          header: 'Create Project',
        };
    }
  }
}

/**
  @param {}
  gets button text for current componenet
  @return {string} text
*/
function ModalNav({
  self, state, getSelectedComponentId, setComponent, hideModal, continueSave, isDataset,
}) {
  const backButton = classNames({
    'WizardModal__progress-button': true,
    'Btn--flat': true,
    hidden: (state.selectedComponentId === 'createLabbook'),
  });

  const wizardModalNav = classNames({
    WizardModal__actions: true,
    hidden: !state.menuVisibility,
  });


  const buttonText = isDataset ? 'Create Dataset' : 'Create Project';
  const continueText = isDataset ? 'Create Dataset' : 'Continue';

  return (
    <div className={wizardModalNav}>
      <div className="WizardModal__buttons">
        <button
          onClick={() => { setComponent('createLabbook'); }}
          className={backButton}
        >
          Back
        </button>

        <button
          onClick={() => { hideModal(); }}
          className="Btn--flat"
        >
          Cancel
        </button>

        <div>
          { (state.selectedComponentId === 'createLabbook')
            && (
            <button
              className="Btn--last"
              onClick={() => { continueSave({ isSkip: false, text: 'Continue' }); }}
              disabled={(state.continueDisabled)}
            >
              {continueText}
            </button>
            )
          }

          { (state.selectedComponentId === 'selectBase')
            && (
            <ButtonLoader
              buttonState={state.createLabbookButtonState}
              buttonText={buttonText}
              className="Btn--last"
              params={{
                isSkip: false,
                text: 'Create Project',
              }}
              buttonDisabled={state.continueDisabled}
              clicked={continueSave}
            />
            )
          }
        </div>
      </div>
    </div>);
}
