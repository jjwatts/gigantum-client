// vendor
import React, { Component } from 'react';
import classNames from 'classnames'
import { createFragmentContainer, graphql } from 'react-relay';
// mutations
import ChangeLabbookBaseMutation from 'Mutations/ChangeLabbookBaseMutation';
import BuildImageMutation from 'Mutations/container/BuildImageMutation';
// store
import { setErrorMessage, setInfoMessage } from 'JS/redux/actions/footer';
// components
import PackageCount from 'Components/labbook/overview/PackageCount';
import Loader from 'Components/common/Loader';
import ButtonLoader from 'Components/common/ButtonLoader';
import SelectBaseModal from 'Components/shared/modals/SelectBaseModal';
// assets
import './Base.scss';

/**
*  @param {Boolean} isLocked
*  @param {Boolean} upToDate
*  returns tooltip
*  @return {Object}
*/
const getTooltip = (isLocked, upToDate) => {
  const defaultTooltip = isLocked ? 'Cannot modify environment while Project is in use' : '';
  const upToDateTooltip = upToDate ? 'Base is up to date' : defaultTooltip;
  return {
    upToDateTooltip,
    defaultTooltip,
  }
}

/**
    @param {name, owner}
    builds docker iamge of labbook
*/
const buildImage = (name, owner) => {
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


class Base extends Component {
  state = {
    baseModalVisible: false,
    forceUpdateDisabled: false,
    updateBaseButtonState: '',
  }

  /**
      @param {}
      update base mutation
  */
  _updateBaseMutation = () => {
    const { props } = this;
    const {
      owner,
      name,
    } = props;
    const {
      repository,
      componentId,
    } = props.environment.base;
    const revision = props.baseLatestRevision;

    this.setState({
      forceUpdateDisabled: true,
      updateBaseButtonState: 'loading',
    });

    ChangeLabbookBaseMutation(
      owner,
      name,
      repository,
      componentId,
      revision,
      (response, error) => {
        this.setState({ forceUpdateDisabled: false })
        if (error) {
          setErrorMessage('An error occured while trying to change bases.', error);
          this.setState({
            updateBaseButtonState: 'error',
          });
          setTimeout(() => {
            this.setState({
              updateBaseButtonState: '',
            });
          }, 2000);
        } else {
          setInfoMessage('Updated Base successfully. Rebuilding environment. Pleae wait...');
          this.setState({
            updateBaseButtonState: 'finished',
          });
          setTimeout(() => {
            this.setState({
              updateBaseButtonState: '',
            });
          }, 2000);
          buildImage(name, owner);
        }
      },
    );
  }


  /**
    @param {boolean} baseModalVisible
    sets baseModalVisible value to true or false
  */
  _toggleBaseModal = (baseModalVisible) => {
    this.setState({ baseModalVisible });
  }

  render() {
    const { props, state } = this;
    const { base } = props.environment;
    const isUpToDate = props.baseLatestRevision === base.revision;
    const { defaultTooltip, upToDateTooltip } = getTooltip(props.isLocked, isUpToDate)
    const changeButtonCSS = classNames({
      'Btn Btn__base Btn__base--change Btn--action': true,
      'Tooltip-data Tooltip-data--auto': props.isLocked,
    });
    const updateButtonCSS = classNames({
      'Btn Btn__base Btn__base--update Btn--action': true,
      'Tooltip-data Tooltip-data--auto': (isUpToDate || props.isLocked) && !state.forceUpdateDisabled,
      'Btn__base--loading': state.forceUpdateDisabled,

    });
    if (base) {
      return (
        <div className="Base">
          <div className="Base__info grid">
            <div className="Base__card Card--auto Card--no-hover column-1-span-12">

              <div className="Base__imageContainer">
                <img
                  className="Base__image"
                  height="35
                  "
                  width="35
                  "
                  src={base.icon}
                  alt={base.name}
                />

                <div className="Base__title">
                  <h6 className="Base__name">{base.name}</h6>
                  <p className="Base__revision">{`Revision: ${base.revision}`}</p>
                  <p className="Base__paragraph">{base.description}</p>
                </div>

              </div>

              <div className="Base__languages">
                <h6 className="bold">Languages</h6>
                <ul>
                  {
                    base.languages.map((language, index) => (<li key={language + index}>{language}</li>))
                  }
                </ul>
              </div>

              <div className="Base__tools">
                <h6 className="bold">Tools</h6>
                <ul>
                  {
                    base.developmentTools && base.developmentTools.map((tool, index) => (<li key={tool + index}>{tool}</li>))
                  }
                </ul>
              </div>

              {
                (props.overview) && <PackageCount overview={props.overview} />
              }
              {
                state.baseModalVisible
                && (
                <SelectBaseModal
                  owner={props.owner}
                  name={props.name}
                  toggleModal={() => this._toggleBaseModal(false)}
                />
                )
              }
              {
                !props.overview
                && (
                <div className="Base__actions flex flex--column justify--center">
                  <button
                    className={changeButtonCSS}
                    type="button"
                    data-tooltip={defaultTooltip}
                    disabled={props.isLocked}
                    onClick={() => this._toggleBaseModal(true)}
                  >
                    Change
                  </button>
                  <button
                    className={updateButtonCSS}
                    data-tooltip={upToDateTooltip}
                    disabled={isUpToDate || props.isLocked || state.forceUpdateDisabled}
                    onClick={() => this._updateBaseMutation()}
                    type="button"
                  >
                    Update
                  </button>
                </div>
                )
              }

            </div>

          </div>

        </div>
      );
    }
    return (
      <Loader />
    );
  }
}

export default createFragmentContainer(
  Base,
  {
    environment: graphql`fragment Base_environment on Environment {
    base{
      id
      schema
      repository
      componentId
      revision
      name
      description
      readme
      tags
      icon
      osClass
      osRelease
      license
      url
      revision
      languages
      developmentTools
      packageManagers
      dockerImageServer
      dockerImageNamespace
      dockerImageRepository
      dockerImageTag
    }
  }`,
  },
);
