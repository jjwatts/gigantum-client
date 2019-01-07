import React, { Component, Fragment } from 'react';
import classNames from 'classnames';
import { connect } from 'react-redux';
// store
import {
  setHelperVisibility,
  setResizeHelper,
} from 'JS/redux/reducers/helper';
import { setHelperVisible } from 'JS/redux/reducers/footer';


class Helper extends Component {
  constructor(props) {
    super(props);

    this.state = {
      helperMenuOpen: false,
      showPopup: false,
    };

    this._toggleIsVisible = this._toggleIsVisible.bind(this);
    this._resize = this._resize.bind(this);
  }

  /**
    * @param {}
    * subscribe to store to update state
  */
  componentDidMount() {
    window.addEventListener('resize', this._resize);
    this.props.auth.isAuthenticated().then((response) => {
      const guideShown = localStorage.getItem('guideShown');
      if (!guideShown && response) {
        this.setState({ showPopup: true });
        localStorage.setItem('guideShown', true);
        this._toggleIsVisible();
        this._toggleMenuView();
      }
    });
  }

  /**
    * @param {}
    * update store
  */
  _toggleIsVisible() {
    this.props.setHelperVisibility(!this.props.isVisible);
  }
  /**
    * @param {}
    * toggles menu view
  */
  _toggleMenuView() {
    setHelperVisible(!this.state.helperMenuOpen);
    this.setState({ helperMenuOpen: !this.state.helperMenuOpen });
  }

  /**
    * @param {}
    * update store to risize component
  */
  _resize() {
    this.props.setResizeHelper();
  }

  render() {
    const bodyWidth = document.body.clientWidth;

    const menuCSS = classNames({
      Helper__menu: this.state.helperMenuOpen,
      hidden: !this.state.helperMenuOpen,
      'Helper__men--footer-open': this.props.footerVisible,
    });

    const helperButtonCSS = classNames({
      Helper__button: true,
      'Helper__button--open': this.state.helperMenuOpen,
      'Helper__button--side-view': bodyWidth < 1600,
      'Helper__button--bottom': this.props.uploadOpen && !this.state.helperMenuOpen,
    });

    return (
      <div className="Helper">
      {
        this.state.showPopup &&
        <Fragment>
          <div className="Helper__prompt">
            <div>
              <p>Use the guide to view tips on how to use Gigantum. The guide can be toggled in the Help menu below.</p>
            </div>

            <div>
              <button
                className="button--green"
                onClick={() => this.setState({ showPopup: false })}>
                Got it!
              </button>
            </div>
          </div>
          <div className="Helper__prompt-pointer"/>
        </Fragment>
      }

        <div
          className={helperButtonCSS}
          onClick={() => this._toggleMenuView()}
        />
        <div className={menuCSS}>
          <div
            className="Helper__menu-feedback"
            onClick={() => window.open('https://feedback.gigantum.com')}
          >
            <h5>Feedback</h5>
            <div
              className="Helper__feedback-button"
            />
          </div>
          <div
            className="Helper__menu-discussion"
            onClick={() => window.open('https://docs.gigantum.com/discuss')}
          >
            <h5>Discuss</h5>
            <div
              className="Helper__discussion-button"
            />
          </div>
          <div
            className="Helper__menu-docs"
            onClick={() => window.open('https://docs.gigantum.com/docs')}
          >
            <h5>Docs</h5>
            <div
              className="Helper__docs-button"
            />
          </div>
          <div
            className="Helper__menu-guide"
          >
            <h5>Guide</h5>
            <label className="Helper-guide-switch">
              <input
                type="checkbox"
                defaultChecked={!localStorage.getItem('guideShown')}
                onClick={() => this._toggleIsVisible()}
              />
              <span className="Helper-guide-slider" />
            </label>
          </div>
        </div>
      </div>
    );
  }
}


const mapStateToProps = (state, ownProps) => ({
  resize: state.helper.resize,
  isVisible: state.helper.isVisible,
  footerVisible: state.helper.footerVisible,
  uploadOpen: state.footer.uploadOpen,
});

const mapDispatchToProps = dispatch => ({
  setHelperVisibility,
  setResizeHelper,
});

export default connect(mapStateToProps, mapDispatchToProps)(Helper);
