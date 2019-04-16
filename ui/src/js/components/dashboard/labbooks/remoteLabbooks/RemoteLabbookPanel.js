// vendor
import React, { Component } from 'react';
import uuidv4 from 'uuid/v4';
import Highlighter from 'react-highlight-words';
import classNames from 'classnames';
import Moment from 'moment';
// muations
import ImportRemoteLabbookMutation from 'Mutations/ImportRemoteLabbookMutation';
import BuildImageMutation from 'Mutations/container/BuildImageMutation';
// store
import store from 'JS/redux/store';
import { setWarningMessage, setMultiInfoMessage } from 'JS/redux/actions/footer';
// queries
import UserIdentity from 'JS/Auth/UserIdentity';
// components
import LoginPrompt from 'Components/shared/modals/LoginPrompt';
import Loader from 'Components/common/Loader';
// assets
import './RemoteLabbookPanel.scss';
// config
import config from 'JS/config';

export default class RemoteLabbookPanel extends Component {
  constructor(props) {
    super(props);

    this.state = {
      labbookName: props.edge.node.name,
      owner: props.edge.node.owner,
      isImporting: false,
      showLoginPrompt: false,
    };
    this._importingState = this._importingState.bind(this);
    this._clearState = this._clearState.bind(this);
    this._closeLoginPromptModal = this._closeLoginPromptModal.bind(this);
    this._handleDelete = this._handleDelete.bind(this);
  }

  /**
    * @param {object} edge
    * validates user's session and then triggers toggleDeleteModal which passes parameters to the DeleteLabbook component
  */
  _handleDelete(edge) {
    if (localStorage.getItem('username') !== edge.node.owner) {
      setWarningMessage('You can only delete remote Projects that you have created.');
    } else {
      UserIdentity.getUserIdentity().then((response) => {
        if (navigator.onLine) {
          if (response.data) {
            if (response.data.userIdentity.isSessionValid) {
              this.props.toggleDeleteModal({
                remoteId: edge.node.id, remoteOwner: edge.node.owner, remoteLabbookName: edge.node.name, existsLocally: this.props.existsLocally,
              });
            } else {
              this.props.auth.renewToken(true, () => {
                this.setState({ showLoginPrompt: true });
              }, () => {
                this.props.toggleDeleteModal({
                  remoteId: edge.node.id, remoteOwner: edge.node.owner, remoteLabbookName: edge.node.name, existsLocally: this.props.existsLocally,
                });
              });
            }
          }
        } else {
          this.setState({ showLoginPrompt: true });
        }
      });
    }
  }

  /**
    * @param {}
    * fires when user identity returns invalid session
    * prompts user to revalidate their session
  */
  _closeLoginPromptModal() {
    this.setState({
      showLoginPrompt: false,
    });
  }

  /**
    *  @param {}
    *  changes state of isImporting to false
  */
  _clearState = () => {
    if (document.getElementById('dashboard__cover')) {
      document.getElementById('dashboard__cover').classList.add('hidden');
    }
    this.setState({
      isImporting: false,
    });
  }

  /**
    *  @param {}
    *  changes state of isImporting to true
  */
  _importingState = () => {
    document.getElementById('modal__cover').classList.remove('hidden');
    document.getElementById('loader').classList.remove('hidden');
    this.setState({
      isImporting: true,
    });
  }

  /**
    *  @param {owner, labbookName}
    *  imports labbook from remote url, builds the image, and redirects to imported labbook
    *  @return {}
  */
 importLabbook = (owner, labbookName) => {
   const self = this;
   const id = uuidv4();
   const remote = `https://repo.${config.domain}/${owner}/${labbookName}`;

   UserIdentity.getUserIdentity().then((response) => {
     if (navigator.onLine) {
       if (response.data) {
         if (response.data.userIdentity.isSessionValid) {
           this._importingState();
           setMultiInfoMessage(id, 'Importing Project please wait', false, false);
           const successCall = () => {
             this._clearState();

             setMultiInfoMessage(id, `Successfully imported remote Project ${labbookName}`, true, false);


             BuildImageMutation(
               owner,
               labbookName,
               false,
               (response, error) => {
                 if (error) {
                   console.error(error);
                   setMultiInfoMessage(id, `ERROR: Failed to build ${labbookName}`, null, true, error);
                 }
               },
             );

             self.props.history.replace(`/projects/${owner}/${labbookName}`);
           };
           const failureCall = (error) => {
             this._clearState();
             setMultiInfoMessage(id, 'ERROR: Could not import remote Project', null, true, error);
           };
           self.setState({ isImporting: true });

           ImportRemoteLabbookMutation(
             owner,
             labbookName,
             remote,
             successCall,
             failureCall,
             (response, error) => {
               if (error) {
                 failurecall(error);
               }
               self.setState({ isImporting: false });
             },
           );
         } else {
           this.props.auth.renewToken(true, () => {
             this.setState({ showLoginPrompt: true });
           }, () => {
             this.importLabbook(owner, labbookName);
           });
         }
       }
     } else {
       this.setState({ showLoginPrompt: true });
     }
   });
 }

 render() {
   const { props, state } = this;
   const { edge } = props;

   const descriptionCss = classNames({
     'RemoteLabbooks__row RemoteLabbooks__row--text': true,
     blur: state.isImporting,
   });
   const deleteCSS = classNames({
     RemoteLabbooks__icon: true,
     'Tooltip-data Tooltip-data--small': localStorage.getItem('username') !== edge.node.owner,
     'RemoteLabbooks__icon--delete': localStorage.getItem('username') === edge.node.owner,
     'RemoteLabbooks__icon--delete-disabled': localStorage.getItem('username') !== edge.node.owner,
   });

   return (
     <div
       key={edge.node.name}
       className="Card Card--300 column-4-span-3 flex flex--column justify--space-between"
     >

       <div className="RemoteLabbooks__row RemoteLabbooks__row--icon">
         {
          this.props.existsLocally
            ? (
              <button
                className="RemoteLabbooks__icon RemoteLabbooks__icon--cloud Tooltip-data Tooltip-data--small"
                data-tooltip="Project exists locally"
                disabled
              >
              Imported
              </button>
            )
            : (
              <button
                disabled={state.isImporting}
                className="RemoteLabbooks__icon RemoteLabbooks__icon--cloud-download"
                onClick={() => this.importLabbook(edge.node.owner, edge.node.name)}
              >
              Import
              </button>
            )
        }
         <button
           className={deleteCSS}
           data-tooltip={localStorage.getItem('username') !== edge.node.owner ? 'Can only delete remote projects created by you' : ''}
           disabled={this.state.isImporting || localStorage.getItem('username') !== edge.node.owner}
           onClick={() => this._handleDelete(edge)}
         >
           Delete
         </button>

       </div>

       <div className={descriptionCss}>

         <div className="RemoteLabbooks__row RemoteLabbooks__row--title">
           <h6 className="RemoteLabbooks__panel-title">
             <Highlighter
               highlightClassName="LocalLabbooks__highlighted"
               searchWords={[store.getState().labbookListing.filterText]}
               autoEscape={false}
               caseSensitive={false}
               textToHighlight={edge.node.name}
             />
           </h6>

         </div>

         <p className="RemoteLabbooks__paragraph RemoteLabbooks__paragraph--owner">{edge.node.owner}</p>
         <p className="RemoteLabbooks__paragraph RemoteLabbooks__paragraph--owner">{`Created on ${Moment(edge.node.creationDateUtc).format('MM/DD/YY')}`}</p>
         <p className="RemoteLabbooks__paragraph RemoteLabbooks__paragraph--owner">{`Modified ${Moment(edge.node.modifiedDateUtc).fromNow()}`}</p>

         <p className="RemoteLabbooks__paragraph RemoteLabbooks__paragraph--description">
           {
            (edge.node.description && edge.node.description.length)
              ? (
                <Highlighter
                  highlightClassName="LocalLabbooks__highlighted"
                  searchWords={[store.getState().labbookListing.filterText]}
                  autoEscape={false}
                  caseSensitive={false}
                  textToHighlight={edge.node.description}
                />
              )
              : (
                <span className="RemoteDatasets__description--blank">
              No description provided
                </span>
              )
           }
         </p>
       </div>

       { !(edge.node.visibility === 'local')
          && (
          <div
            data-tooltip={`${edge.node.visibility}`}
            className={`Tooltip-Listing RemoteLabbooks__${edge.node.visibility}   Tooltip-data Tooltip-data--small`}
          />
          )
       }

       {
          state.isImporting
          && (
          <div className="RemoteLabbooks__loader">
            <Loader />
          </div>
          )
        }

       {
          state.showLoginPrompt
          && <LoginPrompt closeModal={this._closeLoginPromptModal} />
        }
     </div>);
 }
}
