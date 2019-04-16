// vendor
import React, { Component } from 'react';
// assets
import './ErrorBoundary.scss';

export default class ErrorBoundary extends Component {
  constructor() {
    super();
    this.state = {
      hasError: false,
    };
  }

  componentDidCatch(error, info) {
    console.log(error, info);
    this.setState({ hasError: true });
  }

  render() {
    let text = 'There was an error fetching data for this component. Refresh the page and try again.';
    if (this.props.type === 'containerStatusError') {
      text = 'Error';
    }
    if (this.state.hasError) {
      return (
        <div className={`ErrorBoundary ErrorBoundary--${this.props.type}`}>
          <p>{text}</p>
        </div>
      );
    }
    return this.props.children;
  }
}
