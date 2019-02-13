// vendor
import React, { Component } from 'react';
import ReactDOM from 'react-dom';
import ReactMarkdown from 'react-markdown';
import Moment from 'moment';
// components
import CodeBlock from 'Components/labbook/renderers/CodeBlock';
import ToolTip from 'Components/common/ToolTip';
import Lightbox from 'Components/common/Lightbox';
// store
import store from 'JS/redux/store';
// assets
import './RecentActivity.scss';

export default class RecentActivity extends Component {

  state = {
    imageExpanded: false,
  }

  componentDidMount() {
    this._setLinks();
    window.addEventListener('resize', this._setLinks.bind(this));
  }
  componentWillUnmount() {
    window.removeEventListener('resize', this._setLinks.bind(this));
  }

  /** *
    @param {object} elenodement
    return markdown
    @return {jsx}
  */
  _renderDetail(node) {
    const item = node.detailObjects[0].data[0]
      ? node.detailObjects[0].data[0]
      : ['text/markdown', node.message];
    if (item) {
      // TODO: remove switch and use if else to match an image vs text
      switch (item[0]) {
        case 'text/plain':
          return (<div className="ReactMarkdown">
            <p>{item[1]}</p>
          </div>);
        case 'image/png':
          return (<p className="ReactMarkdown"><img alt="detail" src={item[1]} /></p>);
        case 'image/jpg':
          return (<p className="ReactMarkdown"><img alt="detail" src={item[1]} /></p>);
        case 'image/jpeg':
          return (<p className="ReactMarkdown"><img alt="detail" src={item[1]} /></p>);
        case 'image/bmp':
          return (<p className="ReactMarkdown"><img alt="detail" src={item[1]} /></p>);
        case 'image/gif':
          return (<p className="ReactMarkdown"><img alt="detail" src={item[1]} /></p>);
        case 'text/markdown':
          return (<ReactMarkdown
            renderers={{
              code: props => <CodeBlock {...props} />,
            }}
            className="ReactMarkdown"
            source={item[1]}
          />);
        default:
          return (<b>{item[1]}</b>);
      }
    } else {
      return (<div>no result</div>);
    }
  }
  /** *
    @param {object} element
    checks if element is too large for card area
    @return {boolean}
  */
  _checkOverflow(element) {
    if (element) {
      const curOverflow = element.style.overflow;

      if (!curOverflow || curOverflow === 'visible') { element.style.overflow = 'hidden'; }

      const isOverflowing = element.clientWidth < element.scrollWidth || element.clientHeight < element.scrollHeight;

      element.style.overflow = curOverflow;

      return isOverflowing;
    }
  }

  /** *
    @param {}
    sets
  */
  _setLinks() {
    // TODO rewrite this or add comments
    const elements = Array.prototype.slice.call(document.getElementsByClassName('ReactMarkdown'));
    const moreObj = {
      0: false,
      1: false,
      2: false,
    };

    elements.forEach((elOuter, index) => {
      if (this._checkOverflow(elOuter) === true) { moreObj[index] = true; }

      elOuter.childNodes.forEach((elInner) => {
        if (this._checkOverflow(elInner) === true) { moreObj[index] = true; }
      });
    });

    for (const key in this.refs) {
      if (!moreObj[key]) {
        ReactDOM.findDOMNode(this.refs[key]).className = 'hidden';

        if (ReactDOM.findDOMNode(this.refs[key]).previousSibling) {
          ReactDOM.findDOMNode(this.refs[key]).previousSibling.classList.add('hidden');
        }
      } else {
        ReactDOM.findDOMNode(this.refs[key]).className = 'RecentActivity__card-link';

        if (ReactDOM.findDOMNode(this.refs[key]).previousSibling) {
          ReactDOM.findDOMNode(this.refs[key]).previousSibling.classList.remove('hidden');
        }
      }
    }
  }
  /*
    @param {object}
    returns formated date
    @return {string}
  */
  _getDate(edge) {
    const date = new Date(edge.timestamp);
    return Moment((date)).format('hh:mm a');
  }
  /**
    @param {String} section
    handles redirect and scrolling to top
  */
  _handleRedirect(section) {
    const { owner, labbookName } = store.getState().routes;
    const { props } = this;
    props.scrollToTop();
    props.history.push(`/projects/${owner}/${labbookName}/${section}`);
  }

  render() {
    if (this.props.recentActivity) {
      const { owner, labbookName } = store.getState().routes;
      const { props, state } = this;
      const edge = props.recentActivity[0];
      const isImage = edge.detailObjects && edge.detailObjects[0].data[0] && edge.detailObjects[0].data[0][0] === 'image/png';
      const imageMetadata = isImage && edge.detailObjects[0].data[0][1];

      return (<div className="RecentActivity">
        <div className="RecentActivity__title-container">

          <h5 className="RecentActivity__header">
            Recent Activity
            <ToolTip section="recentActivity" />
          </h5>
        </div>

        <div className="RecentActivity__list grid">
          <div key={edge.id} className="RecentActivity__card Card Card--auto Card--no-hover column-3-span-4">
            <button
              className="Btn--redirect"
              onClick={() => this._handleRedirect('activity')}
            >
              <span>View more in Activity Feed</span>
            </button>
            <div className={`ActivityCard__badge ActivityCard__badge--${edge.type.toLowerCase()}`}
              title={edge.type}
            />
            <div className="RecentActivityCard__content">
              <div className="RecentActivityCard__text-content">
                <p className="RecentActivity__time">
                  {this._getDate(edge)}
                </p>
                <p className="RecentActivity__message">
                  <b>
                    {`${edge.username} - `}
                  </b>
                  {edge.message }
                </p>
              </div>
              {
                imageMetadata && state.imageExpanded &&
                <Lightbox
                  imageMetadata={imageMetadata}
                  onClose={() => this.setState({ imageExpanded: false })}
                />
              }
              <div className="RecentActivity__img-container">
                {
                  isImage &&
                  <img
                    onClick={() => this.setState({ imageExpanded: true })}
                    src={imageMetadata} alt="detail"
                  />
                }
                <div className="RecentActivity__expand">
                  Expand
                </div>
              </div>
            </div>
            </div>
        </div>
              </div>
      );
    }

    return (
      <div className="RecentActivity">
        <h5 className="RecentActivity__header">Activity</h5>
        <div className="RecentActivity__list grid">
          <div className="RecentActivity__card--loading" />
          <div className="RecentActivity__card--loading" />
          <div className="RecentActivity__card--loading" />
        </div>
      </div>);
  }
}
