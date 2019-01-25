// vendor
import React, { Component } from 'react';
import { QueryRenderer, graphql } from 'react-relay';
import store from 'JS/redux/store';
import environment from 'JS/createRelayEnvironment';
import classNames from 'classnames';
// mutations
import ModifyDatasetLinkMutation from 'Mutations/ModifyDatasetLinkMutation';
// component
import Modal from 'Components/shared/Modal';
import Loader from 'Components/shared/Loader';
import ButtonLoader from 'Components/shared/ButtonLoader';
import LocalDatasetsPanel from 'Components/dashboard/datasets/localDatasets/LocalDatasetsPanel';
// store
import { setErrorMessage, setInfoMessage } from 'JS/redux/reducers/footer';
// assets
import './LinkModal.scss';

export const LinkModalQuery = graphql`
  query LinkModalQuery($first: Int!, $cursor: String, $orderBy: String $sort: String){
      datasetList{
        localDatasets(first: $first, after: $cursor, orderBy: $orderBy, sort: $sort)@connection(key: "LocalDatasets_localDatasets", filters: []){
            edges {
              node {
                id
                name
                description
                owner
                #createdOnUtc
                modifiedOnUtc
                defaultRemote
              }
              cursor
            }
            pageInfo {
              endCursor
              hasNextPage
              hasPreviousPage
              startCursor
            }
          }
      }
  }`;

export default class LinkModal extends Component {
  constructor(props) {
    super(props);
    this.state = {
        selectedDataset: null,
        buttonState: '',
    };
    this._linkDataset = this._linkDataset.bind(this);
  }
  /**
    * @param {}
    * triggers link datraset mutation
  */
  _linkDataset() {
    const { owner, labbookName } = store.getState().routes;
    this.setState({ buttonState: 'loading' });
    ModifyDatasetLinkMutation(
        owner,
        labbookName,
        this.state.selectedDataset.owner,
        this.state.selectedDataset.name,
        'link',
        this.state.selectedUrl,
        (response, error) => {
            if (error) {
                setErrorMessage('Unable to link dataset', error);
                this.setState({ buttonState: 'error' });
                setTimeout(() => {
                    this.setState({ buttonState: '' });
                }, 2000);
            } else {
                this.setState({ buttonState: 'finished' });
                setTimeout(() => {
                    this.props.closeLinkModal();
                }, 2000);
            }
        },
    );
  }
  /**
    * @param {object} edge
    * sets update selected state
  */
  _updateSelected(edge) {
    this.setState({
      selectedDataset: {
        owner: edge.node.owner,
        name: edge.node.name,
      },
      selectedUrl: edge.node.defaultRemote,
    });
  }
  render() {
    const { props } = this;
    return (

      <Modal
        header="Link Dataset"
        handleClose={() => props.closeLinkModal()}
        size="large"
        renderContent={() =>

          (<div className="LinkModal">
            <QueryRenderer
                environment={environment}
                query={LinkModalQuery}
                variables={{
                    first: 100,
                    cursor: null,
                    orderBy: 'modified_on',
                    sort: 'desc',
                }}
                render={({ error, props }) => {
                    if (error) {
                        console.log(error);
                    } else if (props) {
                        const existingDatasets = this.props.linkedDatasets.map(dataset => dataset.name);
                        const localDatasetEdges = props.datasetList.localDatasets.edges.filter(dataset => existingDatasets.indexOf(dataset.node.name) === -1);
                        return (
                            <div className="LinkModal__flex flex flex--column justify--space-between">
                                <div className="LinkModal__container">
                                    {
                                        localDatasetEdges.map((edge) => {
                                                const LinkModalCard = classNames({
                                                  'LinkModal__card--border': this.state.selectedDataset && this.state.selectedDataset.owner === edge.node.owner && this.state.selectedDataset.name === edge.node.name,
                                                  LinkModal__card: true,
                                                });
                                                return (<div key={edge.node.id}>
                                                  {
                                                    edge.node.defaultRemote &&
                                                    <div
                                                        className={LinkModalCard}
                                                        onClick={() => { this._updateSelected(edge); }}>
                                                        <LocalDatasetsPanel
                                                          key={`${edge.node.id}__LocalDatasetsPanel`}
                                                          ref={`LocalDatasetPanel${edge.node.name}`}
                                                          className="LocalDatasets__panel Card--auto"
                                                          edge={edge}
                                                          visibility={'local'}
                                                          filterText={''}
                                                          noLink
                                                          />
                                                    </div>
                                                }
                                               </div>);
                                        })
                                    }
                                </div>
                                <div className="Link__buttonContainer">
                                <ButtonLoader
                                    buttonState={this.state.buttonState}
                                    buttonText="Link Dataset"
                                    className=""
                                    params={{}}
                                    buttonDisabled={!this.state.selectedDataset}
                                    clicked={this._linkDataset}
                                />
                                    <button onClick={() => this.props.closeLinkModal()}>Cancel</button>
                                </div>
                            </div>
                        );
                    }
                    return <Loader/>;
                }}
            />

           </div>)
        }
      />
    );
  }
}
