// vendor
import React, { Component, Fragment } from 'react';
import classNames from 'classnames';

export default class Modal extends Component {
  componentDidMount() {
    if (document.getElementById('root')) {
      document.getElementById('root').classList.add('no-overflow');
    }
  }
  componentWillUnmount() {
    if (document.getElementById('root')) {
      document.getElementById('root').classList.remove('no-overflow');
    }
  }

  render() {
    const modalContentCSS = classNames({
      Modal__content: true,
      [this.props.size]: this.props.size, // large, medium, small
      [this.props.icon]: this.props.icon,
    });
    const modalContainerCSS = classNames({
      'Modal__sub-container': true,
      'Modal__sub-container--nopadding': this.props.noPadding,
    });
    return (
      <div className="Modal">

        <div
          className="Modal__cover"
          onClick={this.props.handleClose}
        />

        <div className={modalContentCSS}>
          {
            this.props.handleClose &&
            <div
              className="Modal__close"
              onClick={() => this.props.handleClose()}
            />
          }
          <div className="Modal__container">
            {
              this.props.preHeader &&
              <p className="Modal__pre-header">{this.props.preHeader}</p>
            }
            {
              this.props.header &&
              <Fragment>
                <h4 className="Modal__header">{this.props.header}</h4>
                <hr />
              </Fragment>
            }
            <div className={modalContainerCSS}>
              {
                this.props.renderContent()
              }
            </div>
          </div>
        </div>
      </div>
    );
  }
}
