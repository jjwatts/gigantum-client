// vendor
import React, { Component } from 'react';
import { QueryRenderer, graphql } from 'react-relay';
import ReactMarkdown from 'react-markdown';
// Components
import CodeBlock from 'Components/labbook/renderers/CodeBlock';
// environment
import environment from 'JS/createRelayEnvironment';
// store
import store from 'JS/redux/store';
// assets
import './DetailRecords.scss';

const DetailRecordsQuery = graphql`
query DetailRecordsQuery($name: String!, $owner: String!, $keys: [String]){
  labbook(name: $name, owner: $owner){
    id
    description
    detailRecords(keys: $keys){
      id
      action
      key
      data
      type
      show
      importance
      tags
    }
  }
}`;
const DetailRecordsDatasetsQuery = graphql`
query DetailRecordsDatasetsQuery($name: String!, $owner: String!, $keys: [String]){
  dataset(name: $name, owner: $owner){
    id
    description
    detailRecords(keys: $keys){
      id
      action
      key
      data
      type
      show
      importance
      tags
    }
  }
}`;


export default class UserNote extends Component {
  constructor(props) {
  	super(props);

    const { owner, labbookName } = store.getState().routes;

    this.state = {
      owner,
      labbookName,
    };
    this._setLinks = this._setLinks.bind(this);
  }

  /**
   * Lifecycle methods start
   */
  componentDidMount() {
    const self = this;
    setTimeout(() => {
      self._setLinks();
    }, 100);
    window.addEventListener('resize', this._setLinks.bind(this));
  }

  componentDidUpdate() {
    const self = this;
    setTimeout(() => {
      self._setLinks();
    }, 100);
  }

  componentWillUnmount() {
    window.removeEventListener('resize', this._setLinks.bind(this));
  }

  /**
   * Lifecycle methods end
   */
  _setLinks() {
    const elements = Array.prototype.slice.call(document.getElementsByClassName('ReactMarkdown'));
    const moreObj = {};
    elements.forEach((elOuter, index) => {
      if (this._checkOverflow(elOuter) === true) moreObj[index] = true;
      if (this._checkOverflow(elOuter.childNodes[elOuter.childNodes.length - 1]) === true) moreObj[index] = true;
    });
    const pElements = Array.prototype.slice.call(document.getElementsByClassName('DetailsRecords__link'));

    for (const key in pElements) {
      if (!moreObj[key]) {
        pElements[key].className = 'DetailsRecords__link hidden';
      } else {
        pElements[key].className = 'DetailsRecords__link';
      }
    }
    const fadeElements = Array.prototype.slice.call(document.getElementsByClassName('DetailsRecords__fadeout'));
    for (const key in fadeElements) {
      if (!moreObj[key]) {
        fadeElements[key].className = 'DetailsRecords__fadeout hidden';
      } else {
        fadeElements[key].className = 'DetailsRecords__fadeout';
      }
    }
  }

  /**
    @param {Object} element
    checks if elements scrollheight is greater than it's client height
    @return {boolean} isOverflowing
  */
  _checkOverflow(element) {
    if (element) {
      const curOverflow = element.style.overflow;
      if (!curOverflow || curOverflow === 'visible') { element.style.overflow = 'hidden'; }
      const isOverflowing = element.clientHeight + 3 < element.scrollHeight;
      return isOverflowing;
    }
  }

  /**
    @param {Array} item
    returns tag to render if item matches a case
    @return {JSX}
  */
  _renderDetail(item) {
    switch (item[0]) {
      case 'text/plain':
        return (<div className="ReactMarkdown"><p>{item[1]}</p></div>);
      case 'image/png':
        return (<img alt="detail" src={item[1]} />);
      case 'image/jpg':
        return (<img alt="detail" src={item[1]} />);
      case 'image/jpeg':
        return (<img alt="detail" src={item[1]} />);
      case 'image/bmp':
        return (<img alt="detail" src={item[1]} />);
      case 'image/gif':
        return (<img alt="detail" src={item[1]} />);
      case 'text/markdown':
        return (
          <ReactMarkdown
            renderers={{ code: props => <CodeBlock {...props} /> }}
            className="ReactMarkdown"
            source={item[1]}
          />
        );
      default:
        return (<b>{item[1]}</b>);
    }
  }

  /**
    @param {Object} target
    toggles content in a record when it has more to show
    @return {}
  */
  _moreClicked(target) {
    // TODO remove setting classNames in react, using state is preffered
    if (target.className !== 'DetailsRecords__link-clicked') {
      const elements = Array.prototype.slice.call(document.getElementsByClassName('ReactMarkdown'));
      const index = Array.prototype.slice.call(document.getElementsByClassName('DetailsRecords__link')).indexOf(target);
      elements[index].className = 'ReactMarkdown-long';
      target.className = 'DetailsRecords__link-clicked';
      target.textContent = 'Less...';
      target.previousSibling.className = 'hidden';
    } else {
      const elements = Array.prototype.slice.call(document.getElementsByClassName('ReactMarkdown-long'));
      const index = Array.prototype.slice.call(document.getElementsByClassName('DetailsRecords__link-clicked')).indexOf(target);
      elements[index].className = 'ReactMarkdown';
      target.className = 'DetailsRecords__link';
      target.textContent = 'More...';
      target.previousSibling.className = 'DetailsRecords__fadeout';
    }
  }

  render() {
    const { props, state } = this;
    const variables = {
      keys: props.keys,
      owner: state.owner,
      name: state.labbookName,
    };

    const query = props.sectionType === 'labbook' ? DetailRecordsQuery : DetailRecordsDatasetsQuery;

    return (
      <QueryRenderer
        environment={environment}
        query={query}
        variables={variables}
        render={(response) => {
          if (response && response.props) {
            return (
              <div className="DetailsRecords">
                <ul className="DetailsRecords__list">
                  {
                      response.props[props.sectionType].detailRecords.map((detailRecord) => {
                        const liCSS = detailRecord.type === 'NOTE' ? 'DetailsRecords__item-note' : 'DetailsRecords__item';
                        const containerCSS = detailRecord.type === 'NOTE' ? 'DetailsRecords__container note' : 'DetailsRecords__container';
                        return (
                          <div className={containerCSS} key={detailRecord.id}>
                            {
                              detailRecord.type !== 'NOTE'
                              && <div className={`DetailsRecords__action DetailsRecords__action--${detailRecord.action && detailRecord.action.toLowerCase()}`} />
                            }
                            {
                              detailRecord.data.map((item, index) => (
                                <li
                                  key={`${detailRecord.id}_${index}`}
                                  className={liCSS}
                                >
                                  {this._renderDetail(item)}
                                  <div className="DetailsRecords hidden" />
                                  <p className="DetailsRecords__link hidden" onClick={e => this._moreClicked(e.target)}>More...</p>
                                  {this._setLinks()}
                                </li>))
                            }
                          </div>
                        );
                      })
                    }
                </ul>
              </div>
            );
          }
          return (
            <div className="DetailsRecords__loader-group">
              <div className="DetailsRecords__loader" />
              <div className="DetailsRecords__loader" />
              <div className="DetailsRecords__loader" />
            </div>
          );
        }}
      />
    );
  }
}
