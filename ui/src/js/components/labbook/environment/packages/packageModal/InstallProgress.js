// vendor
import React, { Component } from 'react';
import { boundMethod } from 'autobind-decorator';
import { connect } from 'react-redux';
// components
// assets
import './InstallProgress.scss';

class InstallPackages extends Component {
  state = {
    showBuild: false,
  }
  /** *
  * @param {}
  * sets mounted to true for component
  */
  componentDidMount() {
    this.mounted = true;
  }

  /** *
  * @param {}
  * sets mounted to false for component
  */
  componentWillUnmount() {
    this.mounted = false;
  }

  /**
  *  @param {Boolean} showBuild
  *  sets entry method state
  */
  @boundMethod
  _setShowbuild(showBuild) {
    this.setState({ showBuild });
  }

  /**
    @param {}
    gets percentage for progress
  */
  _getPercentageComplete() {
    const { props } = this;
    const { buildId, messageStack } = props;
    const footerMessage = messageStack.filter(message => message.id === buildId);

    if (footerMessage[0] && footerMessage[0].messageBody) {
      const { message } = footerMessage[0].messageBody[0];
      const regex = /(Step [0-9]+\/[0-9]+)/g;
      const percentRegex = /[0-9]+\/[0-9]+/;
      const matches = message.match(regex);
      const lastMatchPct = matches[matches.length - 1].match(percentRegex)[0].split('/');

      if ((lastMatchPct[0] === lastMatchPct[1])) {
        setTimeout(() => {
          if (this.mounted) {
            props.toggleModal(false);
          }
        }, 2000);
      }

      return {
        percentageComplete: `${Math.round((lastMatchPct[0] / lastMatchPct[1]) * 100)}%`,
        message: message.replace(regex, '<span style="color:#fcd430">$1</span>'),
        isComplete: lastMatchPct[0] === lastMatchPct[1],
      };
    }
    return {
      percentageComplete: '',
      message: '',
    };
  }

  render() {
    const { props, state } = this;
    const { percentageComplete, message, isComplete } = this._getPercentageComplete();
    const buildButtonText = state.showBuild ? 'Back' : 'View Build Ouput';
    return (
      <div className="InstallProgress">
        <div className="InstallProgress__header">
          <h4>Installing Packages</h4>
        </div>
        {
          state.showBuild
          && (
            <div
              className="InstallProgress__output"
              dangerouslySetInnerHTML={{ __html: message }}
            />
          )
        }
        {
          !state.showBuild
          && (
            <div className="InstallProgress__body flex flex--column align-items--center">
              <p className="InstallProgress__close-text">
                Close this window to continue using Gigantum while your environment is building.
              </p>
              <div className="InstallProgress__progress">
                {percentageComplete}
              </div>
              <p className="InstallProgress__apply-text">
                Applying changes and rebuilding Project environment...
              </p>
            </div>
          )
        }

        <div className="InstallProgress__buttons flex justify--right">
          <button
            className="Btn Btn--flat margin-right--auto"
            type="button"
            disabled={message.length === 0}
            onClick={() => this._setShowbuild(!state.showBuild)}
          >
            {buildButtonText}
          </button>
          <button
            className="Btn Btn--inverted align-self--end"
            type="button"
            disabled={isComplete}
          >
            Cancel Build
          </button>
          <button
            className="align-self--end"
            type="button"
            onClick={() => props.toggleModal(false)}
          >
            Close
          </button>
        </div>
      </div>
    );
  }
}

const mapStateToProps = state => state.footer;

const mapDispatchToProps = () => ({});

export default connect(mapStateToProps, mapDispatchToProps)(InstallPackages);
