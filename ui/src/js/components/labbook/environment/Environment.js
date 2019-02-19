// vendor
import React, { Component } from 'react';
import { createFragmentContainer, graphql } from 'react-relay';
// store
import { setErrorMessage } from 'JS/redux/reducers/footer';
import { setRefetchPending } from 'JS/redux/reducers/labbook/environment/packageDependencies';
import store from 'JS/redux/store';
// mutations
import BuildImageMutation from 'Mutations/container/BuildImageMutation';
import StopContainerMutation from 'Mutations/container/StopContainerMutation';
// components
import ErrorBoundary from 'Components/common/ErrorBoundary';
import ToolTip from 'Components/common/ToolTip';
import Loader from 'Components/common/Loader';
import Base from './Base';
import PackageDependencies from './PackageDependencies';
import CustomDockerfile from './CustomDockerfile';
// assets
import './Environment.scss';

class Environment extends Component {
  constructor(props) {
  	super(props);
    const { owner, labbookName } = store.getState().routes;

    this.state = {
      modal_visible: false,
      readyToBuild: false,
      show: false,
      message: '',
      owner,
      labbookName,
    };

    this._buildCallback = this._buildCallback.bind(this);
    this._setBase = this._setBase.bind(this);
  }

  /**
  *  @param {None}
  *  callback that triggers buildImage mutation
  */
  _buildCallback = (refetchPending) => {
    const { labbookName, owner } = this.state;
    this.props.setBuildingState(true);
    if (store.getState().containerStatus.status === 'Running') {
      StopContainerMutation(
        owner,
        labbookName,
        (response, error) => {
          if (error) {
            console.log(error);
            setErrorMessage(`Problem stopping ${labbookName}`, error);
          } else {
            BuildImageMutation(
              owner,
              labbookName,
              false,
              (response, error) => {
                if (error) {
                  setErrorMessage(`${labbookName} failed to build`, error);
                }

                if (refetchPending) {
                  setRefetchPending(true);
                }

                return 'finished';
              },
            );
          }
        },
      );
    } else {
      BuildImageMutation(
        owner,
        labbookName,
        false,
        (response, error) => {
          if (error) {
            setErrorMessage(`${labbookName} failed to build`, error);
          }

          if (refetchPending) {
            setRefetchPending(true);
          }


          return 'finished';
        },
      );
    }
  }

  /**
  *  @param {Obect}
  *  sets readyToBuild state to true
  */
  _setBase(base) {
    this.setState({ readyToBuild: true });
  }

  render() {
    if (this.props.labbook) {
      const { props, state } = this;
      const { environment } = props.labbook;
      const { base } = environment;
      return (
        <div className="Environment">
          <div className="Base__headerContainer">
            <h5 className="Base__header">Base&nbsp;&nbsp;&nbsp; <ToolTip section="baseEnvironment" /></h5>
          </div>
          <ErrorBoundary type="baseError" key="base">
            <Base
              ref="base"
              environment={environment}
              environmentId={environment.id}
              editVisible
              containerStatus={props.containerStatus}
              setComponent={this._setComponent}
              setBase={this._setBase}
              buildCallback={this._buildCallback}
              blockClass="Environment"
              base={base}
              isLocked={props.isLocked}
            />
          </ErrorBoundary>
          <div className="Environment__headerContainer">
            <h5 className="PackageDependencies__header">
              Packages
              <ToolTip section="packagesEnvironment" />
            </h5>
          </div>
          <ErrorBoundary type="packageDependenciesError" key="packageDependencies">
            <PackageDependencies
              componentRef={ref => this.packageDependencies = ref}
              environment={props.labbook.environment}
              environmentId={props.labbook.environment.id}
              labbookId={props.labbook.id}
              containerStatus={props.containerStatus}
              setBase={this._setBase}
              setComponent={this._setComponent}
              buildCallback={this._buildCallback}
              overview={props.overview}
              base={base}
              isLocked={props.isLocked}
            />
          </ErrorBoundary>
          <CustomDockerfile
            dockerfile={props.labbook.environment.dockerSnippet}
            buildCallback={this._buildCallback}
            isLocked={props.isLocked}
          />
        </div>
      );
    }
    return (
      <Loader />
    );
  }
}

export default createFragmentContainer(
  Environment,
  graphql`fragment Environment_labbook on Labbook {
    environment{
      id
      imageStatus
      containerStatus
      base{
        developmentTools
        packageManagers
      }
      dockerSnippet

      ...Base_environment
      ...PackageDependencies_environment
    }
  }`,
);
