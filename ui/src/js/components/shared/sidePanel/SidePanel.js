// vendor
import React, { Component } from 'react';
import ReactDom from 'react-dom';
import classNames from 'classnames';
import { boundMethod } from 'autobind-decorator';
// config
import config from 'JS/config';
// assets
import './SidePanel.scss';

class SidePanel extends Component {
  state = {
    isPanelOpen: false,
  }

  /**
    @param {} -
    updates panelState
    @return {}
  */
  @boundMethod
  _togglePanel() {
    this.setState((state) => {
      const isPanelOpen = !state.isPanelOpen;
      return { isPanelOpen };
    });
  }

  render() {
    const { props } = this;

    const isPushedDownTwice = ((window.location.hostname === config.demoHostName)
      || props.diskLow) && props.isDeprecated;
    const isPushedDownOnce = (((window.location.hostname === config.demoHostName)
      || props.diskLow) || props.isDeprecated)
      && !isPushedDownTwice;

    // declare css here
    const sidePanelCSS = classNames({
      SidePanel: true,
      'SidePanel--sticky': props.isSticky && !props.isDeprecated,
      'SidePanel--is-deprecated': isPushedDownOnce && !props.isSticky,
      'SidePanel--is-deprecated-demo': isPushedDownTwice && !props.isSticky,
      'SidePanel--is-deprecated-demo-sticky': isPushedDownTwice && props.isSticky,
      'SidePanel--is-deprecated-sticky': isPushedDownOnce && props.isSticky,
    });

    return (
      ReactDom.createPortal(
        <div className={sidePanelCSS}>
          <div className="SidePanel__header">
            <div
              onClick={() => props.toggleSidePanel(false)}
              className="SidePanel__btn SidePanel__btn--close"
            />
          </div>
          <div className="SidePanel__body">
            { props.renderContent() }
          </div>
        </div>, document.getElementById('side_panel'),
      )
    );
  }
}

export default SidePanel;
