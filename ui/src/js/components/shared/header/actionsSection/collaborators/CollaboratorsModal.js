// vendor
import React, { Component } from 'react';
import classNames from 'classnames';
import { boundMethod } from 'autobind-decorator';
// Mutations
import AddCollaboratorMutation from 'Mutations/AddCollaboratorMutation';
import AddDatasetCollaboratorMutation from 'Mutations/AddDatasetCollaboratorMutation';
import DeleteCollaboratorMutation from 'Mutations/DeleteCollaboratorMutation';
import DeleteDatasetCollaboratorMutation from 'Mutations/DeleteDatasetCollaboratorMutation';
// components
import ButtonLoader from 'Components/common/ButtonLoader';
import Modal from 'Components/common/Modal';
// store
import { setErrorMessage } from 'JS/redux/reducers/footer';
// config
import config from 'JS/config';
import fetchQuery from 'JS/fetch';
// assets
import './CollaboratorsModal.scss';

export default class CollaboratorsModal extends Component {
  constructor(props) {
  	super(props);
    const {
      labbookName,
      owner,
    } = props;

  	this.state = {
      labbookName,
      owner,
      addCollaboratorButtonDisabled: false,
      newCollaborator: '',
      newPermissions: 'readonly',
      permissionMenuOpen: false,
      userExpanded: null,
      buttonLoaderRemoveCollaborator: {},
      buttonLoaderAddCollaborator: '',
      colloboratorSearchList: [],
      selectedIndex: 0,
    };

    this._addCollaborator = this._addCollaborator.bind(this);
    this._removeCollaborator = this._removeCollaborator.bind(this);
    this._completeColloborator = this._completeColloborator.bind(this);
  }

  componentDidMount() {
    const buttonLoaderRemoveCollaborator = {};

    this.props.collaborators.forEach(({ collaboratorUsername }) => {
      buttonLoaderRemoveCollaborator[collaboratorUsername] = '';
    });
    window.addEventListener('click', this._closePermissionsMenu);

    this.setState({ buttonLoaderRemoveCollaborator });
  }

  /**
    * @param {}
    * fires when component unmounts
    * removes added event listeners
  */
  componentWillUnmount() {
    window.removeEventListener('click', this._closePermissionsMenu);
  }

  /**
    *  @param {String} permission
    *  @param {String} CollaboratorName
    *  gets permissions value and displays it to the UI more clearly
  */
  _getPermissions(permission, collaboratorName) {
    if ((permission === 'readonly') || (permission === 'READ_ONLY')) {
      return 'Read';
    } if ((permission === 'readwrite') || (permission === 'READ_WRITE')) {
      return 'Write';
    } if ((permission === 'owner') || (permission === 'OWNER')) {
      return collaboratorName === this.state.owner ? 'Owner' : 'Admin';
    }
    return 'Read';
  }

  /**
  *  @param {number}
  *  iterate value of index within the bounds of the array size
  *  @return {}
  */
  _setSelectedIndex(iterate) {
    let newSelectedIndex = this.state.selectedIndex + iterate;

    newSelectedIndex = (newSelectedIndex < 0) ? this.state.colloboratorSearchList.length - 1 : newSelectedIndex;
    newSelectedIndex = (newSelectedIndex >= this.state.colloboratorSearchList.length) ? 0 : newSelectedIndex;

    this.setState({ selectedIndex: newSelectedIndex });
  }

  /**
  *  @param {String} newPermissions
  *  assigns new permissions in state
  *  @return {}
  */
  _setPermission(newPermissions) {
    this.setState({ newPermissions });
  }

  /**
  *  @param {event} evt
  *  queries collaborator api and updates list
  *  @return {}
  */
  _getUsers(evt) {
    const userInput = evt.target.value;

    if ((userInput.length > 2) && (evt.key !== 'Enter')) {
      const apiURL = evt.target.value.indexOf('@') > 0 ? config.userAPI.getUserEmailQueryString(evt.target.value) : config.userAPI.getUsersQueryString(evt.target.value);

      fetchQuery(apiURL).then((response) => {
        const collaborators = response.hits.hit.map(hit => hit.fields);

        this.setState({ colloboratorSearchList: collaborators });
      });
    } else {
      this.setState({ colloboratorSearchList: [] });
    }


    this._handleInputKeys(evt);
  }

  /**
  *  @param {String} userExpanded
  *  toggles permissionMenuOpen in state or assigns userexpanded a name
  *  @return {}
  */
  _togglePermissionsMenu(userExpanded) {
    if (this.props.canManageCollaborators) {
      if (userExpanded) {
        if (userExpanded !== localStorage.getItem('username')) {
          this.setState({
            userExpanded: (this.state.userExpanded === userExpanded) ? null : userExpanded,
          });
        }
      } else {
        this.setState({ permissionMenuOpen: !this.state.permissionMenuOpen });
      }
    }
  }

  /**
    *  @param {Event} evt
    *  toggles permissionMenuOpen in state
    *  @return {}
    */
  @boundMethod
  _closePermissionsMenu(evt) {
    const isPermissionsMenuOpen = evt.target.className.indexOf('CollaboratorModal__PermissionsSelector--add') > -1;
    const isSinglePermissionsMenuOpen = evt.target.className.indexOf('CollaboratorModal__PermissionsSelector--individual') > -1;

    if (!isPermissionsMenuOpen && this.state.permissionMenuOpen) {
      this.setState({ permissionMenuOpen: false });
    }
    if (!isSinglePermissionsMenuOpen && this.state.userExpanded) {
      this.setState({ userExpanded: null });
    }
  }

  /**
  *  @param {event} evt
  *  queries collaborator api and updates list
  *  @return {}
  */
  _handleInputKeys(evt) {
    if ((evt.type === 'click') || (evt.key === 'Enter')) {
      if (this.state.colloboratorSearchList.length > 0) {
        const collaborator = this.state.colloboratorSearchList[this.state.selectedIndex];

        this._completeColloborator(collaborator);
      } else {
        this._addCollaborator();
      }
    } else if (evt.key === 'ArrowDown') {
      this._setSelectedIndex(1);
    } else if (evt.key === 'ArrowUp') {
      this._setSelectedIndex(-1);
    } else {
      this.setState({ newCollaborator: evt.target.value });
    }
  }

  /**
  *  @param {event} evt
  *  queries collaborator api and updates list
  *  @return {}
  */
  _completeColloborator(collaborator) {
    if (collaborator) {
      this.collaboratorSearch.value = collaborator.username;

      this.setState({
        newCollaborator: collaborator.username,
        colloboratorSearchList: [],
        selectedIndex: 0,
      });
    }
  }

  /**
  *  @param {String} permissionOverride
  *  @param {String} collaboratorName
  *  sets state of Collaborators
  *  @return {}
  */
  _addCollaborator(permissionOverride, collaboratorName) {
    const {
      labbookName,
      owner,
      newCollaborator,
      newPermissions,
    } = this.state;

    // waiting for backend updates
    if (!permissionOverride) {
      this.setState({ addCollaboratorButtonDisabled: true, buttonLoaderAddCollaborator: 'loading' });
    } else {
      const { buttonLoaderRemoveCollaborator } = this.state;
      buttonLoaderRemoveCollaborator[collaboratorName] = 'loading';
      this.setState({ buttonLoaderRemoveCollaborator });
    }

    this.props.sectionType === 'dataset'
      ? AddDatasetCollaboratorMutation(
        labbookName,
        owner,
        collaboratorName || newCollaborator,
        permissionOverride || newPermissions,
        (response, error) => {
          const completeState = this.state.buttonLoaderRemoveCollaborator;

          if (permissionOverride && completeState[collaboratorName]) {
            if (error) {
              completeState[collaboratorName] = 'error';
            } else {
              completeState[collaboratorName] = 'finished';
            }
            this.setState({ buttonLoaderRemoveCollaborator: completeState });

            setTimeout(() => {
              const postCompleteState = this.state.buttonLoaderRemoveCollaborator;
              postCompleteState[collaboratorName] = '';
              this.setState({ buttonLoaderAddCollaborator: postCompleteState });
            }, 2000);
          } else {
            completeState[newCollaborator] = '';

            this.setState({ newCollaborator: '', addCollaboratorButtonDisabled: false, buttonLoaderRemoveCollaborator: completeState });

            this.collaboratorSearch.value = '';

            if (error) {
              setErrorMessage('Could not add collaborator', error);

              this.setState({ buttonLoaderAddCollaborator: 'error' });
            } else {
              this.setState({ buttonLoaderAddCollaborator: 'finished' });
            }

            setTimeout(() => {
              this.setState({ buttonLoaderAddCollaborator: '' });
            }, 2000);
          }
        },

      )
      : AddCollaboratorMutation(
        labbookName,
        owner,
        collaboratorName || newCollaborator,
        permissionOverride || newPermissions,
        (response, error) => {
          const completeState = this.state.buttonLoaderRemoveCollaborator;

          if (permissionOverride && completeState[collaboratorName]) {
            if (error) {
              completeState[collaboratorName] = 'error';
            } else {
              completeState[collaboratorName] = 'finished';
            }
            this.setState({ buttonLoaderRemoveCollaborator: completeState });

            setTimeout(() => {
              const postCompleteState = this.state.buttonLoaderRemoveCollaborator;
              postCompleteState[collaboratorName] = '';
              this.setState({ buttonLoaderAddCollaborator: postCompleteState });
            }, 2000);
          } else {
            completeState[newCollaborator] = '';

            this.setState({ newCollaborator: '', addCollaboratorButtonDisabled: false, buttonLoaderRemoveCollaborator: completeState });

            this.collaboratorSearch.value = '';

            if (error) {
              setErrorMessage('Could not add collaborator', error);

              this.setState({ buttonLoaderAddCollaborator: 'error' });
            } else {
              this.setState({ buttonLoaderAddCollaborator: 'finished' });
            }

            setTimeout(() => {
              this.setState({ buttonLoaderAddCollaborator: '' });
            }, 2000);
          }
        },

      );
  }

  /**
  *  @param {object} params
  *  deletes collaborators using mutation
  *  @return {}
  */
  _removeCollaborator(evt, params) {
    const { collaborator, button } = params;

    const { buttonLoaderRemoveCollaborator } = this.state;

    button.disabled = true;

    buttonLoaderRemoveCollaborator[collaborator] = 'loading';

    this.setState({ buttonLoaderRemoveCollaborator });
    if (this.props.sectionType === 'dataset') {
      DeleteDatasetCollaboratorMutation(
        this.state.labbookName,
        this.state.owner,
        collaborator,
        (response, error) => {
          this.refs[collaborator] && this.refs[collaborator].classList.remove('loading');

          if (button) {
            button.disabled = false;
          }

          if (error) {
            setErrorMessage('Could not remove collaborator', error);

            buttonLoaderRemoveCollaborator[collaborator] = 'error';

            this.setState({ buttonLoaderRemoveCollaborator });
          } else {
            buttonLoaderRemoveCollaborator[collaborator] = 'finished';

            this.setState({ buttonLoaderRemoveCollaborator });
          }

          setTimeout(() => {
            buttonLoaderRemoveCollaborator[collaborator] = '';

            this.setState({ buttonLoaderRemoveCollaborator });
          }, 2000);
        },
      );
    } else {
      DeleteCollaboratorMutation(
        this.state.labbookName,
        this.state.owner,
        collaborator,
        (response, error) => {
          this.refs[collaborator] && this.refs[collaborator].classList.remove('loading');

          if (button) {
            button.disabled = false;
          }

          if (error) {
            setErrorMessage('Could not remove collaborator', error);

            buttonLoaderRemoveCollaborator[collaborator] = 'error';

            this.setState({ buttonLoaderRemoveCollaborator });
          } else {
            buttonLoaderRemoveCollaborator[collaborator] = 'finished';

            this.setState({ buttonLoaderRemoveCollaborator });
          }

          setTimeout(() => {
            buttonLoaderRemoveCollaborator[collaborator] = '';

            this.setState({ buttonLoaderRemoveCollaborator });
          }, 2000);
        },
      );
    }
  }

  render() {
    const { state } = this;
    const autoCompleteMenu = classNames({
      'CollaboratorsModal__auto-compelte-menu box-shadow': true,
      'CollaboratorsModal__auto-compelte-menu--visible': this.state.colloboratorSearchList.length > 0,
    });


    const permissionsSelectorCSS = classNames({
      'CollaboratorModal__PermissionsSelector Dropdown': true,
      'Dropdown--open': this.state.permissionMenuOpen,
      'CollaboratorModal__PermissionsSelector--add': true,
      'Dropdown--collapsed': !this.state.permissionMenuOpen,
    });


    const permissionsMenuCSS = classNames({
      'CollaboratorModal__PermissionsMenu Dropdown__menu box-shadow': true,
      hidden: !this.state.permissionMenuOpen,
    });


    const collaboratorList = classNames({
      CollaboratorsModal__list: true,
      'CollaboratorsModal__list--overflow': (state.userExpanded !== null),
    });
    const disableAddButton = this.state.addCollaboratorButtonDisabled || !this.state.newCollaborator.length;
    return (
      <Modal
        header="Manage Collaborators"
        icon="user"
        size="large"
        overflow="visible"
        handleClose={() => { this.props.toggleCollaborators(); }}
        renderContent={() => (
          <div>
            {
              this.props.canManageCollaborators
                ? (
                  <div className="CollaboratorsModal__add">

                    <input
                      className="CollaboratorsModal__input--collaborators"
                      ref={el => this.collaboratorSearch = el}

                      onChange={evt => this._getUsers(evt)}
                      onKeyUp={evt => this._getUsers(evt)}

                      type="text"
                      placeholder="Add Collaborator"

                      disabled={this.state.addCollaboratorButtonDisabled}
                    />

                    <div className={autoCompleteMenu}>
                      <ul className="CollaboratorsModal__list">
                        {
                  this.state.colloboratorSearchList.map((collaborator, index) => {
                    const listItemCSS = classNames({
                      CollaboratorsModal__listItem: true,
                      'CollaboratorsModal__listItem--selected': (index === this.state.selectedIndex),
                    });
                    return (
                      <li
                        onClick={() => this._completeColloborator(collaborator)}
                        className={listItemCSS}
                        key={collaborator.username}
                      >

                        <div className="CollaboratorsModal__listItem--username">{collaborator.username}</div>

                        <div className="CollaboratorsModal__listItem--name">{collaborator.name}</div>
                      </li>
                    );
                  })
                }
                      </ul>
                    </div>
                    <div className="CollaboratorsModal__permissions">
                      <span
                        className={permissionsSelectorCSS}
                        onClick={() => this._togglePermissionsMenu()}
                      >
                        {this._getPermissions(this.state.newPermissions)}
                      </span>
                      <ul className={permissionsMenuCSS}>
                        <li onClick={() => this._setPermission('readonly')}>
                          <div className="CollaboratorsModal__permissions-header">Read</div>
                          <div className="CollaboratorsModal__permissions-subtext">Read-only permissions. Can only pull updates</div>
                        </li>
                        <li onClick={() => this._setPermission('readwrite')}>
                          <div className="CollaboratorsModal__permissions-header">Write</div>
                          <div className="CollaboratorsModal__permissions-subtext">Read/Write permissions. Can sync to branches other than master</div>
                        </li>
                        <li onClick={() => this._setPermission('owner')}>
                          <div className="CollaboratorsModal__permissions-header">Admin</div>
                          <div className="CollaboratorsModal__permissions-subtext">Admin permissions. Can sync to master and manage collaborators</div>
                        </li>
                      </ul>
                    </div>
                    <ButtonLoader
                      className="Btn__plus Btn--round Btn--medium"
                      ref="addCollaborator"

                      buttonState={this.state.buttonLoaderAddCollaborator}
                      buttonText=""

                      params={{}}
                      buttonDisabled={disableAddButton}
                      clicked={() => this._addCollaborator()}
                    />

                  </div>
                )
                : this.props.collaborators.length
                  ? (
                    <div className="CollaboratorsModal__message">
              To add and edit collaborators,
                      <b>
                        {' Administrator '}
                      </b>
              access is required. Contact the Project
                      <b>
                        {' Owner '}
                      </b>
              or a Project
                      <b>
                        {' Administrator '}
                      </b>
              to manage collaborator settings.
                    </div>
                  )
                  : (
                    <div className="CollaboratorsModal__message">
                      <b>
                This project needs to be published before collaborators can be added.
                      </b>
                    </div>
                  )
            }

            <div className="CollaboratorsModal__collaborators">

              <h5 className="CollaboratorsModal__h5">Collaborators</h5>

              <div className="CollaboratorsModal__listContainer">

                {this.props.collaborators

                && (
                <ul className={collaboratorList}>
                  {
                    this.props.collaborators.map((collaborator) => {
                      const collaboratorName = collaborator.collaboratorUsername;
                      const collaboratorItemCSS = classNames({
                        'CollaboratorsModal__item CollaboratorsModal__item--me': collaborator.collaboratorUsername === localStorage.getItem('username'),
                        CollaboratorsModal__item: !(collaborator.collaboratorUsername === localStorage.getItem('username')),
                      });


                      const individualPermissionsSelectorCSS = classNames({
                        CollaboratorModal__PermissionsSelector: true,
                        'CollaboratorModal__PermissionsSelector--individual': true,
                        'CollaboratorModal__PermissionsSelector--open': this.state.userExpanded === collaboratorName,
                        'CollaboratorModal__PermissionsSelector--disabled': (collaboratorName === localStorage.getItem('username')) || !this.props.canManageCollaborators || (collaboratorName === this.state.owner),
                        'CollaboratorModal__PermissionsSelector--collapsed': this.state.userExpanded !== collaboratorName,
                      });


                      const individualPermissionsMenuCSS = classNames({
                        'CollaboratorModal__PermissionsMenu box-shadow': true,
                        'CollaboratorModal__PermissionsMenu--individual': true,
                        hidden: this.state.userExpanded !== collaboratorName,
                      });
                      return (

                        <li
                          key={collaboratorName}
                          ref={collaboratorName}
                          className={collaboratorItemCSS}
                        >

                          <div className="CollaboratorsModal__collaboratorName">{collaboratorName}</div>
                          <div className="CollaboratorsModal__permissions CollaboratorsModal__permissions--individual">
                            <span
                              className={individualPermissionsSelectorCSS}
                              onClick={() => this._togglePermissionsMenu(collaboratorName)}
                            >
                              {this._getPermissions(collaborator.permission, collaboratorName)}
                            </span>
                            <ul className={individualPermissionsMenuCSS}>
                              <li onClick={() => this._addCollaborator('readonly', collaboratorName)}>
                                <div className="CollaboratorsModal__permissions-header">Read</div>
                                <div className="CollaboratorsModal__permissions-subtext">Read-only permissions. Can only pull updates</div>
                              </li>
                              <li onClick={() => this._addCollaborator('readwrite', collaboratorName)}>
                                <div className="CollaboratorsModal__permissions-header">Write</div>
                                <div className="CollaboratorsModal__permissions-subtext">Read/Write permissions. Can sync to branches other than master</div>
                              </li>
                              <li onClick={() => this._addCollaborator('owner', collaboratorName)}>
                                <div className="CollaboratorsModal__permissions-header">Admin</div>
                                <div className="CollaboratorsModal__permissions-subtext">Admin permissions. Can sync to master and managed collaborators</div>
                              </li>
                            </ul>
                          </div>

                          <ButtonLoader
                            ref={collaboratorName}
                            buttonState={this.state.buttonLoaderRemoveCollaborator[collaboratorName]}
                            buttonText=""
                            className="Btn__remove Btn--round Btn--small"
                            params={{ collaborator: collaboratorName, button: this }}
                            buttonDisabled={collaboratorName === localStorage.getItem('username') || !this.props.canManageCollaborators}
                            clicked={this._removeCollaborator}
                          />

                        </li>);
                    })
                  }
                </ul>
                )
              }
              </div>
            </div>
          </div>
        )
        }
      />
    );
  }
}
