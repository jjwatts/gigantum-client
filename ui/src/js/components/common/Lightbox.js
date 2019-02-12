// vendor
import React, { Component } from 'react';
import ReactDom from 'react-dom';
// assets
import './Lightbox.scss';

export default class Lightbox extends Component {
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
    const { imageMetadata, onClose } = this.props;
    return (
      ReactDom
      .createPortal(
        <div className="Lightbox">
            <div
                className="Lightbox__cover"
                onClick={onClose}
            />
            <div className="Lightbox__container">
                <button
                    className="Btn--expandable-close"
                    onClick={onClose}>
                    <span>Close</span>
                </button>
                <img src={imageMetadata} alt="detail">
            </img>
        </div>
      </div>,
    document.getElementById('lightbox'),
  )
  );
  }
}
