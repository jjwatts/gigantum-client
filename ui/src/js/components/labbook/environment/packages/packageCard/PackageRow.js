// vendor
import React, { Component } from 'react';
import classNames from 'classnames';
// components
import PackageActions from './PackageActions';
// assets
import './PackageTable.scss';

export default (props) => {
  const isSelected = props.selectedPackages.has(props.id);
  const multiSelectButtonCSS = classNames({
    CheckboxMultiselect: true,
    CheckboxMultiselect__check: isSelected,
    CheckboxMultiselect__uncheck: !isSelected,
  });

  return (
    <div className="PackageRow Table__Row">
      <div className="flex">
        <button
          className={multiSelectButtonCSS}
          onClick={() => { props.selectSinglePackage(props.packageNode); }}
          disabled={props.fromBase}
          type="button"
        />
        <div className="PackageRow__manager">
          {props.manager}
        </div>
        <div className="PackageRow__name">
          <h5 className="margin--0">
            {props.package}
            {
              props.docsUrl
              && (
              <a
                href={props.docsUrl}
                rel="noopener noreferrer"
                target="_blank"
              >
                <div className="PackageRow__external" />
              </a>
              )
            }
          </h5>
          <div className="PackageRow__description">
            {props.description}
          </div>
        </div>
        <div className="flex">
          <div className="PackageRow__version-container">
            <h5 className="PackageRow__version margin--0">{props.version}</h5>
            {
              props.latestVersion
              && (
                <div className="PackageRow__description">
                  {`Latest: ${props.latestVersion}`}
                </div>
              )
            }
          </div>
          <div className="PackageRow__actions">
            <PackageActions
              {...props}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
