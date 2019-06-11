// vendor
import React, { Component } from 'react';
import { boundMethod } from 'autobind-decorator';
// assets
import './Requirements.scss';

export default class Requirements extends Component {
  /**
  *  @param {Object} file
  *  parses requirements file
  *  @return {}
  */
  @boundMethod
  _parseFile(file) {
    const { props } = this;
    const reader = new FileReader();
    reader.onload = (evt) => {
      const packages = evt.target.result.split('\n');
      packages.forEach((pkg) => {
        const splitPackage = pkg.split('==');
        const packageData = {
          manager: 'pip',
          package: splitPackage[0],
          version: splitPackage[1],
        }
        props.queuePackage(packageData);
      });
    };
    reader.readAsText(file);
  }

  render() {
    return (
      <div className="Requirements__file flex justify--center">
        <div className="Dropbox flex flex--column align-items--center">
          <div className="Dropbox--menu">
            Drag and drop pip requirements.txt file here
            <br />
            or
          </div>
          <label
            htmlFor="requirements_upload"
            className="Requirements__label"
          >
            <div
              className="Btn Btn--allStyling"
            >
              Choose Files...
            </div>
            <input
              id="requirements_upload"
              className="hidden"
              type="file"
              onChange={evt => this._parseFile(evt.target.files[0])}
            />
          </label>
        </div>
      </div>
    );
  }
}
