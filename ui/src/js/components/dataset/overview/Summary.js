// vendor
import React, { Component } from 'react';
// components
import Tooltip from 'Components/common/Tooltip';
// assets
import './Summary.scss';
// config
import config from 'JS/config';

export default class Summary extends Component {
  constructor(props) {
    super(props);
    this.state = {
      tooltipShown: false,
    };
    this._resetTooltip = this._resetTooltip.bind(this);
  }

  /**
         *  @param {}
         *  add event listeners
     */
  componentDidMount() {
    window.addEventListener('click', this._resetTooltip);
  }

  /**
         *  @param {}
         *  cleanup event listeners
     */
  componentWillUnmount() {
    window.removeEventListener('click', this._resetTooltip);
  }

  /**
     *  @param {event} evt
     *  resets expanded index state
     *
     */
  _resetTooltip(evt) {
    if (evt.target.className.indexOf('Summary__info') === -1) {
      this.setState({ tooltipShown: false });
    }
  }

  render() {
    const mangagedType = this.props.isManaged ? 'Managed' : 'Unmanaged';
    const tooltipText = this.props.isManaged ? 'The contents of a Managed Dataset can be modified via file browser on the data tab.  ' : 'The contents of an Unmanaged Dataset are verified by the Gigantum Client, but managed externally.  ';
    return (
      <div className="Summary">
        <div className="Overview__container">
          <h2>
              Summary
            <Tooltip section="summary" />
          </h2>
        </div>
        <div className="grid">
          <div className="Summary__card Card column-1-span-12">
            <div className="Summary__file-count">
              <div className="Summary__subheader">Number of Files</div>
              <div className="Summary__content">{this.props.numFiles}</div>
            </div>
            <div className="Summary__size">
              <div className="Summary__total-size">
                <div className="Summary__subheader">Total Size</div>
                <div className="Summary__content">{config.humanFileSize(this.props.totalBytes)}</div>
              </div>
              <div className="Summary__disk-size">
                <div className="Summary__subheader">Size On-Disk</div>
                <div className="Summary__content">{config.humanFileSize(this.props.localBytes)}</div>
              </div>
            </div>
            <div className="Summary__file-type">
              <div className="Summary__subheader">Common File Types</div>
              <ul className="Summary__list">
                {
                              this.props.fileTypeDistribution.length
                                ? this.props.fileTypeDistribution.slice(0, 6).map((type, index) => {
                                  const splitType = type.split('|');
                                  const adjustedType = splitType[1].length > 10 ? `${splitType[1].slice(0, 7)}...` : splitType[1];
                                  const percentage = Math.round(Number(splitType[0]) * 100);
                                  if ((index === 5) && (this.props.fileTypeDistribution.length !== 6)) {
                                    return <li key={type}>{`+ ${this.props.fileTypeDistribution.length - 6} other types`}</li>;
                                  }
                                  return (
                                    <li key={type}>{`${adjustedType} (${percentage}%)`}</li>
                                  );
                                })
                                : <li> No files found.</li>
                          }
              </ul>
            </div>
            <div className="Summary__manage-type">
              <div className="Summary__header">
                {mangagedType}
                <div
                  className="Summary__info"
                  onClick={() => this.setState({ tooltipShown: !this.state.tooltipShown })}
                >
                  {
                              this.state.tooltipShown
                              && (
                              <div className="InfoTooltip summary">
                                {tooltipText}
                                <a
                                  target="_blank"
                                  href="https://docs.gigantum.com/docs/datasets-overview#section-dataset-overview"
                                  rel="noopener noreferrer"
                                >
                                    Learn more.
                                </a>
                              </div>
                              )
                              }
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }
}
