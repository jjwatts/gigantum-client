// vendor
import React, { Component } from 'react';
// assets
import './Summary.scss';
// config
import config from 'JS/config';

export default class Summary extends Component {
    constructor(props) {
        super(props);
        this.state = {

        };
    }
    render() {
        return (
            <div className="Summary">
                <div className="Summary__file-count">
                    <div className="Summary__subheader">Number of Files</div>
                    <div className="Summary__content">{this.props.numFiles}</div>
                </div>
                <div className="Summary__size">
                    <div className="Summary__total-size">
                        <div className="Summary__subheader">Total Size</div>
                        <div className="Summary__content">{config.humanFileSize(this.props.totalBytes)}</div>
                    </div>
                    <div className="Summary__disk-size">
                        <div className="Summary__subheader">Size On-Disk</div>
                        <div className="Summary__content">{config.humanFileSize(this.props.localBytes)}</div>
                    </div>
                </div>
                <div className="Summary__file-type">
                    <div className="Summary__subheader">Common File Types</div>
                    <ul className="Summary__list">
                        {
                            this.props.fileTypeDistribution.length ?
                            this.props.fileTypeDistribution.map((type) => {
                                const splitType = type.split('|');
                                return (
                                    <li key={type}>{`${splitType[1]} (${Number(splitType[0]) * 100}%)`}</li>
                                );
                            })
                            :
                            <li> No files found.</li>
                        }
                    </ul>
                </div>
                <div className="Summary__manage-type">
                    <div className="Summary__header">{this.props.isManaged ? 'Managed' : 'Unmanaged'}</div>
                </div>
            </div>
        );
    }
}
