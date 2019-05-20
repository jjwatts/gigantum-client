// vendor
import React, { Component } from 'react';
import { createFragmentContainer, graphql } from 'react-relay';
// store
import { setErrorMessage } from 'JS/redux/actions/footer';
import { setBuildingState } from 'JS/redux/actions/labbook/labbook';
import store from 'JS/redux/store';
// mutations
import BuildImageMutation from 'Mutations/container/BuildImageMutation';
import StopContainerMutation from 'Mutations/container/StopContainerMutation';
// components
import ErrorBoundary from 'Components/common/ErrorBoundary';
import Tooltip from 'Components/common/Tooltip';
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

  componentDidMount() {
    const { props } = this;
    props.refetch('environment');
  }

  /**
  *  @param {}
  *  callback that triggers buildImage mutation
  */
  _buildCallback = () => {
    const { labbookName, owner } = this.state;

    setBuildingState(true);
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
    const { props } = this;
    if (props.labbook && props.labbook.environment && props.labbook.environment.id) {
      const { environment } = props.labbook;
      const { base } = environment;
      return (
        <div className="Environment">
          <div className="Base__headerContainer">
            <h4>
                Base&nbsp;&nbsp;&nbsp;
              <Tooltip section="baseEnvironment" />
            </h4>
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
            <h4>
              Packages
              <Tooltip section="packagesEnvironment" />
            </h4>
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
              packageLatestVersions={props.packageLatestVersions}
              fetchPackageVersion={props.fetchPackageVersion}
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
    environment @skip (if: $environmentSkip){
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
