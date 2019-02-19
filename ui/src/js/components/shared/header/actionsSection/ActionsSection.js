// vendor
import React, { Component } from 'react';
import { Link } from 'react-router-dom';
import classNames from 'classnames';
// config
import Config from 'JS/config';
// components
import ToolTip from 'Components/common/ToolTip';
import ErrorBoundary from 'Components/common/ErrorBoundary';
import Collaborators from './collaborators/Collaborators';
import ActionsMenu from './actionsMenu/ActionsMenu';

import './ActionsSection.scss';

class ActionsSection extends Component {
  render() {
    const { props } = this,
          actionsSectionCSS = classNames({
            ActionsSection: true,
            hidden: props.isSticky,
          })

    return (

      <div className={actionsSectionCSS}>
          <Collaborators {...props} />
          <ActionsMenu {...props} />
      </div>
    );
  }
}

export default ActionsSection;
