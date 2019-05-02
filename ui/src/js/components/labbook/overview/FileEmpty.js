import React, { Component } from 'react';
import { Link } from 'react-router-dom';
// store
import store from 'JS/redux/store';
// assets
import './FileEmpty.scss';

export default class FileEmpty extends Component {
  render() {
    const { props } = this;


    const {
      owner,
      name,
      sectionType,
      sectionLink,
    } = props;

    const sectionTitle = sectionType.charAt(0).toUpperCase() + sectionType.slice(1);
    return (
      (
        <div className="FilePreview__empty column-1-span-12">
          <button
            className="Btn Btn--feature Btn__redirect Btn__redirect--featurePosition"
            onClick={() => props.handleRedirect(sectionLink)}
          >
            <span>{`View ${sectionTitle} Files`}</span>
          </button>
          <div className="FilePreview__empty-content">
            <p className="FilePreview__empty-header">{`This Project has No ${sectionTitle} Favorites`}</p>
            <Link
              className="FilePreview__empty-action"
              to={{ pathname: `/projects/${owner}/${name}/${sectionLink}` }}
            >
              {`View and manage ${sectionTitle} Files`}
            </Link>
          </div>
        </div>
      )
    );
  }
}
