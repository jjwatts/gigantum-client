// vendor
import React, { Component } from 'react';
import classNames from 'classnames';
import { WithContext as ReactTags } from 'react-tag-input';
// assets
import './AdvancedSearch.scss';

export default class Modal extends Component {
  constructor(props) {
    super(props);
    this.state = {
      expandedIndex: null,
      tooltipShown: false,
    };
    this._resetSelectedFilter = this._resetSelectedFilter.bind(this);
  }
  /**
     *  @param {}
     *  add event listeners
  */
  componentDidMount() {
    window.addEventListener('click', this._resetSelectedFilter);
  }
  /**
     *  @param {}
     *  cleanup event listeners
  */
  componentWillUnmount() {
    window.removeEventListener('click', this._resetSelectedFilter);
  }
  /**
   *  @param {event} evt
   *  resets expanded index state
   *
  */
  _resetSelectedFilter(evt) {
    if (evt.target.className.indexOf('AdvancedSearch__filter-section') === -1) {
      this.setState({ expandedIndex: null });
    }
    if (evt.target.className.indexOf('AdvancedSearch__info') === -1) {
      this.setState({ tooltipShown: false });
    }
  }
  /**
    @param {number} i
    removes tag from list
  */
  _handleDelete = (i) => {
    const { tags } = this.props;

    tags.splice(i, 1);

    this.props.setTags(tags);
  }
  /**
    @param {number} i
    add tag to list
  */
  _handleAddition = (tag, category) => {
    const { tags } = this.props;
    if (category) {
      tag.className = category;
    }
    tags.push(tag);

    this.props.setTags(tags);
  }

  render() {
    const { tags } = this.props;
    const suggestions = [];
    const rawKeys = [];
    Object.keys(this.props.filterCategories).forEach((category) => {
      this.props.filterCategories[category].forEach((key) => {
        if (rawKeys.indexOf(key) === -1) {
          rawKeys.push(key);
          suggestions.push({ id: key, text: key, className: category });
        }
      });
    });

    const advancedSearchCSS = classNames({
      AdvancedSearch: true,
      'AdvancedSearch--tagsExist': tags.length,
    });

    return (
      <div className={advancedSearchCSS}>
        <ReactTags
           id="TagsInput"
           tags={tags}
           autocomplete
           suggestions={suggestions}
           placeholder="Search by keyword, tags or filters"
           handleDelete={(index) => { this._handleDelete(index); }}
           handleAddition={(tag) => { this._handleAddition(tag); }}
         />
        <div className="AdvancedSearch__filters">
        {
          Object.keys(this.props.filterCategories).map((category, index) => <div
            key={category}
            className="AdvancedSearch__filter-container"
          >
            <div
                className={`AdvancedSearch__filter-section ${this.state.expandedIndex === index ? 'selected' : ''}`}
                onClick={() => this.setState({ expandedIndex: this.state.expandedIndex === index ? null : index })}
                key={category}
            >
                {category}
            </div>
            {
              category === 'CUDA Version' &&
              <div
                className="AdvancedSearch__info"
                onClick={() => this.setState({ tooltipShown: !this.state.tooltipShown })}
              >
                {
                  this.state.tooltipShown &&
                  <div className="InfoTooltip">
                    CUDA enabled bases will automatically use the NVIDIA Container Runtime when NVIDIA drivers on the host are compatible with the CUDA version installed in the Base.&nbsp;&nbsp;
                    <a
                      target="_blank" href="https://docs.gigantum.com/" rel="noopener noreferrer"
                    >
                      Learn more.
                    </a>
                  </div>
                }
              </div>
            }
            {
                this.state.expandedIndex === index &&
                <ul
                    className="AdvancedSearch__filter-list"
                >
                    {
                        this.props.filterCategories[category].map(filter => <li
                                key={filter}
                                onClick={() => this._handleAddition({ id: filter, text: filter }, category)}
                            >
                                {filter}
                            </li>)
                    }
                </ul>
            }
          </div>)
        }
        </div>
      </div>
    );
  }
}
