import { QueryRenderer, graphql } from 'react-relay';
import React, { Component } from 'react';
import classNames from 'classnames';
import { connect } from 'react-redux';
// environment
import environment from 'JS/createRelayEnvironment';
// store
import store from 'JS/redux/store';
import { setCollaborators, setCanManageCollaborators } from 'JS/redux/actions/shared/collaborators/collaborators';
import { setInfoMessage } from 'JS/redux/actions/footer';
// components
import CollaboratorsModal from './CollaboratorsModal';
// assets
import './Collaborators.scss';

export const CollaboratorsQuery = graphql`
  query CollaboratorsQuery($name: String!, $owner: String!){
    labbook(name: $name, owner: $owner){
      collaborators {
        id
        owner
        name
        collaboratorUsername
        permission
      }
      canManageCollaborators
    }
  }`;

export const CollaboratorsDatasetQuery = graphql`
query CollaboratorsDatasetQuery($name: String!, $owner: String!){
  dataset(name: $name, owner: $owner){
    collaborators {
      id
      owner
      name
      collaboratorUsername
      permission
    }
    canManageCollaborators
  }
}`;


class CollaboratorButton extends Component {
  constructor(props) {
    	super(props);
    	this.state = {
      collaboratorModalVisible: false,
      canClickCollaborators: false,
      sessionValid: true,
    };

    this._toggleCollaborators = this._toggleCollaborators.bind(this);
  }

  static getDerivedStateFromProps(nextProps, nextState) {
    if (nextProps.menuOpen) {
      return nextProps.checkSessionIsValid().then((res) => {
        if (res.data && res.data.userIdentity && res.data.userIdentity.isSessionValid) {
          return {
            ...nextState,
            sessionValid: true,
          };
        }
        return {
          ...nextState,
          sessionValid: false,
        };
      });
    }
    return nextState;
  }

  /**
  *  @param {}
  *  shows hide collaborators modal
  *  @return {}
  */
  _toggleCollaborators() {
    if (navigator.onLine) {
      if (this.state.sessionValid) {
        this.setState({ collaboratorModalVisible: !this.state.collaboratorModalVisible });
      } else {
        this.props.auth.renewToken(true, () => {
          this.props.showLoginPrompt();
        }, () => {
          this.setState({ collaboratorModalVisible: !this.state.collaboratorModalVisible });
        });
      }
    } else {
      this.props.showLoginPrompt();
    }
  }

  /**
  *  @param {Array} collaborators
  *  @param {Array} collaboratorFilteredArr
  *  gets list of collaborators
  *  @return {}
  */
  _getCollaboratorList(collaborators, collaboratorFilteredArr) {
    let lastParsedIndex;
    let collaboratorSubText = collaboratorFilteredArr ? collaboratorFilteredArr.join(', ') : '';

    if (collaboratorSubText.length > 18 && collaboratorSubText.length) {
      collaboratorSubText = collaboratorSubText.slice(0, 18);

      lastParsedIndex = collaboratorSubText.split(', ').length - 1;

      const lastParsed = collaboratorSubText.split(', ')[lastParsedIndex];

      if (collaborators[lastParsedIndex] !== lastParsed) {
        lastParsedIndex--;

        collaboratorSubText = collaboratorSubText.split(', ');
        collaboratorSubText.pop();
        collaboratorSubText = collaboratorSubText.join(', ');
      }
      const collaboratorLength = collaboratorFilteredArr.length - lastParsedIndex - 1;
      collaboratorSubText += `...+${collaboratorLength}`;
    }
    return collaboratorSubText;
  }

  /**
  *  @param {String} name
  *  gets info for a collaborator
  *  @return {}
  */
  _getCollabororInfo(name) {
    let { collaborators, canManageCollaborators } = store.getState().collaborators;
    collaborators = collaborators && collaborators[name] || null;
    canManageCollaborators = canManageCollaborators && canManageCollaborators[name] || null;
    return { collaborators, canManageCollaborators };
  }

  render() {
    const self = this;


    const { props, state } = this;


    const { sectionType } = props;
    // either labbook or dataset
    // get section from props

    const section = props[sectionType];


    const {
      name,
      owner,
    } = section;


    const query = (sectionType === 'dataset') ? CollaboratorsDatasetQuery : CollaboratorsQuery;


    const { collaborators, canManageCollaborators } = this._getCollabororInfo(name);

    return (
      <QueryRenderer
        query={query}
        environment={environment}
        variables={{
          name,
          owner,
        }}
        render={(response) => {
          const error = response.error;


          const queryProps = response.props;
          if (queryProps) {
            const section = sectionType === 'dataset' ? queryProps.dataset : queryProps.labbook;
            this.canManageCollaborators = section.canManageCollaborators;
            this.collaborators = section.collaborators;
            props.setCollaborators({ [name]: this.collaborators });
            props.setCanManageCollaborators({ [name]: this.canManageCollaborators });

            const collaboratorButtonCSS = classNames({
              'Collaborators__btn Btn--flat Btn--no-underline': true,
            });


            const collaboratorCSS = classNames({
              Collaborators: true,
            });


            const collaboratorFilteredArr = section.collaborators && section.collaborators.filter(({ collaboratorUsername }) => collaboratorUsername !== owner).map(({ collaboratorUsername }) => collaboratorUsername);

            const collaboratorNames = self._getCollaboratorList(section.collaborators, collaboratorFilteredArr);

            return (

              <div className={collaboratorCSS}>
                <button
                  onClick={() => this._toggleCollaborators()}
                  className={collaboratorButtonCSS}
                >
                      Collaborators
                  <p className="BranchMenu__collaborator-names">{collaboratorNames}</p>
                </button>

                {
                      this.state.collaboratorModalVisible
                        && (
                        <CollaboratorsModal
                          sectionType={props.sectionType}
                          key="CollaboratorsModal"
                          ref="collaborators"
                          collaborators={section.collaborators}
                          owner={owner}
                          labbookName={name}
                          toggleCollaborators={this._toggleCollaborators}
                          canManageCollaborators={section.canManageCollaborators}
                        />
                        )

                    }
              </div>
            );
          } if (collaborators !== null) {
            const collaboratorButtonCSS = classNames({
              Collaborators__btn: true,
              'Btn--flat': true,
            });

            const collaboratorCSS = classNames({
              Collaborators: true,
            });

            const collaboratorFilteredArr = collaborators && collaborators.filter(({ collaboratorUsername }) => collaboratorUsername !== owner).map(({ collaboratorUsername }) => collaboratorUsername);

            const collaboratorNames = self._getCollaboratorList(collaborators, collaboratorFilteredArr);

            return (

              <div className={collaboratorCSS}>
                <button
                  onClick={() => this._toggleCollaborators()}
                  className={collaboratorButtonCSS}
                >
                      Collaborators
                  <p className="BranchMenu__collaborator-names">{collaboratorNames}</p>
                </button>

                {
                      this.state.collaboratorModalVisible
                        && (
                        <CollaboratorsModal
                          key="CollaboratorsModal"
                          ref="collaborators"
                          collaborators={collaborators}
                          canManageCollaborators={canManageCollaborators}
                          owner={owner}
                          labbookName={name}
                          toggleCollaborators={this._toggleCollaborators}
                        />
                        )
                    }
              </div>
            );
          }
          return (
            <div className="Collaborators disabled">
              <button
                onClick={() => props.showLoginPrompt()}
                className="Collaborators__btn Btn--flat disabled"
              >
                      Collaborators
              </button>
            </div>
          );
        }}
      />

    );
  }
}

const mapStateToProps = (state, ownProps) => ({

});

const mapDispatchToProps = dispatch => ({
  setCollaborators,
  setCanManageCollaborators,
});

export default connect(mapStateToProps, mapDispatchToProps)(CollaboratorButton);
