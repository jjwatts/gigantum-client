// vendor
import React, { Component, Fragment } from 'react';
import classNames from 'classnames';
// store
import store from 'JS/redux/store';
// mutations
import SetLabbookDescriptionMutation from 'Mutations/SetLabbookDescriptionMutation';
// components
import Tooltip from 'Components/common/Tooltip';
import Description from './description/Description';
// assets
import './TitleSection.scss';

export default class TitleSection extends Component {
  render() {
    const { props } = this;


    const {
      sectionType,
    } = props;


    const section = props[sectionType];


    const {
      visibility,
    } = section;


    const visibilityIconCSS = classNames({
      [`TitleSection__${visibility}`]: true,
      [`TitleSection__${visibility}--sticky`]: props.isSticky,
      'Tooltip-data Tooltip-data--small': true,
    });


    const title = `${section.owner} / ${section.name}`;
    return (
      <div className="TitleSection">

        <div className="TitleSection__namespace">
          <div className="TitleSection__namespace-title">{title}</div>
          { ((visibility === 'private') || (visibility === 'public'))
              && (
              <div
                className={visibilityIconCSS}
                data-tooltip={visibility}
              />
              )
          }
        </div>

        {
          !props.isSticky && <Description {...props} />
        }
      </div>
    );
  }
}
