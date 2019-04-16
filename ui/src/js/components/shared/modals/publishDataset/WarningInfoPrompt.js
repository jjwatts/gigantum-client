// vendor
import React, { Component } from 'react';
import { boundMethod } from 'autobind-decorator';
// component
import MoreInfo from './MoreInfo';

class WarningInfoPrompt extends Component {
  state = {
    moreInfo: false,
  }

  /**
  *  @param {} -
  *  toggles moreInfo menu
  *  @return {}
  */
  @boundMethod
  _toggleMoreInfo() {
    this.setState((prevState) => {
      return ({ moreInfo: !prevState.moreInfo });
    });
  }

  render() {
    const { props, state } = this;
    const {
      localDatasets,
    } = props;
    const moreInfoText = state.moreInfo ? 'Hide' : 'More Info';

    return (
      <div class="PublishDatasetsModal">
        <div className="PublishDatasetsModal__container">
          <div className="PublishDatasetsModal__header-text">
            <p>This Project is linked to unpublished (local-only) Datasets</p>
            <p>
              In order to publish a Project, all linked Datasets must also be published.
              <button
                type="submit"
                className="Btn--flat"
                onClick={() => this.setState({ moreInfo: !state.moreInfo })}
              >
                {moreInfoText}
              </button>
            </p>
          </div>

          { state.moreInfo
            && <MoreInfo />
          }

          <p className="PublishDatasetsModal__ul-label">Local Datasets:</p>
          <ul className="PublishDatasetsModal__list">
            { localDatasets.map(localDataset => (
              <li key={`${localDataset.owner}/${localDataset.name}`}>
                {`${localDataset.owner}/${localDataset.name}`}
              </li>
            ))}
          </ul>

        </div>

        <div className="PublishDatasetsModal__buttons">
          <button
            type="submit"
            className="Btn Btn--flat"
            onClick={() => { props.toggleModal(false, true); }}
          >
            Cancel
          </button>
          <button
            className="Btn"
            type="submit"
            onClick={() => { props.hidePrompt(); }}
          >
            Continue
          </button>
        </div>
      </div>
    );
  }
}


export default WarningInfoPrompt;
