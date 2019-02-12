// vendor
import React, { Component } from 'react';
import uuidv4 from 'uuid/v4';
import Highlighter from 'react-highlight-words';
import classNames from 'classnames';
import Moment from 'moment';
// muations
import ImportRemoteDatasetMutation from 'Mutations/ImportRemoteDatasetMutation';
import BuildImageMutation from 'Mutations/BuildImageMutation';
// store
import store from 'JS/redux/store';
import { setWarningMessage, setMultiInfoMessage } from 'JS/redux/reducers/footer';
// queries
import UserIdentity from 'JS/Auth/UserIdentity';
// components
import LoginPrompt from 'Components/shared/header/branchMenu/modals/LoginPrompt';
import Loader from 'Components/common/Loader';
// assets
import './RemoteDatasetsPanel.scss';
// config
import config from 'JS/config';

export default class RemoteDatasetPanel extends Component {
  constructor(props) {
    super(props);

    this.state = {
      datasetName: props.edge.node.name,
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
    * validates user's session and then triggers toggleDeleteModal which passes parameters to the DeleteDataset component
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
                remoteId: edge.node.id, remoteOwner: edge.node.owner, remoteDatasetName: edge.node.name, existsLocally: this.props.existsLocally,
              });
            } else {
              this.props.auth.renewToken(true, () => {
                this.setState({ showLoginPrompt: true });
              }, () => {
                this.props.toggleDeleteModal({
                  remoteId: edge.node.id, remoteOwner: edge.node.owner, remoteDatasetName: edge.node.name, existsLocally: this.props.existsLocally,
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
    this.setState({
      isImporting: false,
    });
  }
  /**
    *  @param {}
    *  changes state of isImporting to true
  */
  _importingState = () => {
    this.setState({
      isImporting: true,
    });
  }

  /**
    *  @param {}
    *  changes state of isImporting to true
  */
  _importingState = () => {
    this.setState({
      isImporting: true,
    });
  }

  /**
    *  @param {String} owner
    *  @param {String} datasetName
    *  @param {String} remote
    *  handles importing dataset mutation
  */
  _handleImportDataset = (owner, datasetName, remote) => {
    ImportRemoteDatasetMutation(
      owner,
      datasetName,
      remote,
      (response, error) => {
        this._clearState();

        if (error) {
          console.error(error);
          setMultiInfoMessage(id, 'ERROR: Could not import remote Project', null, true, error);
        } else if (response) {
          const datasetName = response.importRemoteDataset.newDatasetEdge.node.name;
          const owner = response.importRemoteDataset.newDatasetEdge.node.owner;
          setMultiInfoMessage(id, `Successfully imported remote Dataset ${datasetName}`, true, false);

          this.props.history.replace(`/datasets/${owner}/${datasetName}`);
        }
      },
    );
  }

  /**
    *  @param {owner, datasetName}
    *  imports dataset from remote url, builds the image, and redirects to imported dataset
    *  @return {}
  */
 importDataset = (owner, datasetName) => {
   const self = this;
   const id = uuidv4();
   const remote = `https://repo.${config.domain}/${owner}/${datasetName}`;

   UserIdentity.getUserIdentity().then((response) => {
     if (navigator.onLine) {
       if (response.data) {
         if (response.data.userIdentity.isSessionValid) {
           this._importingState();
           setMultiInfoMessage(id, 'Importing Project please wait', false, false);
           this._handleImportDataset(owner, datasetName, remote);
         } else {
           this.props.auth.renewToken(true, () => {
             this.setState({ showLoginPrompt: true });
           }, () => {
             this.importDataset(owner, datasetName);
           });
         }
       }
     } else {
       this.setState({ showLoginPrompt: true });
     }
   });
 }

 render() {
   const edge = this.props.edge;

   const descriptionCss = classNames({
     'RemoteDatasets__row RemoteDatasets__row--text': true,
     blur: this.state.isImporting,
   });

   const deleteCSS = classNames({
     RemoteDatasets__icon: true,
     'RemoteDatasets__icon--delete': localStorage.getItem('username') === edge.node.owner,
     'RemoteDatasets__icon--delete-disabled': localStorage.getItem('username') !== edge.node.owner,
   });

   return (
     <div
       key={edge.node.name}
       className="Card Card--300 column-4-span-3 flex flex--column justify--space-between"
     >
       {

        }
       <div className="RemoteDatasets__row RemoteDatasets__row--icon">
         {
          this.props.existsLocally ?
            <button
              className="RemoteDatasets__icon RemoteDatasets__icon--cloud"
              data-tooltip="Project exists locally"
              disabled
            >
              Imported
            </button>
          :
            <button
              disabled={this.state.isImporting}
              className="RemoteDatasets__icon RemoteDatasets__icon--cloud-download"
              onClick={() => this.importDataset(edge.node.owner, edge.node.name)}
            >
              Import
            </button>
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

         <div className="RemoteDatasets__row RemoteDatasets__row--title">
           <h6
             className="RemoteDatasets__panel-title"
           >
             <Highlighter
               highlightClassName="LocalDatasets__highlighted"
               searchWords={[store.getState().datasetListing.filterText]}
               autoEscape={false}
               caseSensitive={false}
               textToHighlight={edge.node.name}
             />
           </h6>

         </div>

         <p className="RemoteDatasets__paragraph RemoteDatasets__paragraph--owner">{edge.node.owner}</p>
         <p className="RemoteDatasets__paragraph RemoteDatasets__paragraph--owner">{`Created on ${Moment(edge.node.creationDateUtc).format('MM/DD/YY')}`}</p>
         <p className="RemoteDatasets__paragraph RemoteDatasets__paragraph--owner">{`Modified ${Moment(edge.node.modifiedDateUtc).fromNow()}`}</p>

         <p
           className="RemoteDatasets__paragraph RemoteDatasets__paragraph--description"
         >
         {
          edge.node.description && edge.node.description.length ?
           <Highlighter
             highlightClassName="LocalDatasets__highlighted"
             searchWords={[store.getState().datasetListing.filterText]}
             autoEscape={false}
             caseSensitive={false}
             textToHighlight={edge.node.description}
           />
           :
           <span
           className="RemoteDatasets__description--blank"
         >
            No description provided
         </span>
         }
         </p>
       </div>
       { !(edge.node.visibility === 'local') &&
       <div data-tooltip={`${edge.node.visibility}`} className={`Tooltip-Listing RemoteDatasets__${edge.node.visibility}`} />
        }
       {
          this.state.isImporting &&
          <div className="RemoteDatasets__loader">
            <Loader />
          </div>
        }

       {
          this.state.showLoginPrompt &&
          <LoginPrompt closeModal={this._closeLoginPromptModal} />
        }
     </div>);
 }
}
