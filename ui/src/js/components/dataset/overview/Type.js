// vendor
import React, { Component } from 'react';
// assets
import './Type.scss';

export default class Type extends Component {

  render() {
    const { type, isManaged } = this.props;
    const manageType = isManaged ? 'Managed' : 'Unmanaged';
    return (
    <div className="Type">
        <div className="Type__info">
        <div className="Type__card Card--auto Card--no-hover">

            <div className="Type__imageContainer">
            <img
                className="Type__image"
                height="70"
                width="70"
                src={`data:image/jpeg;base64,${type.icon}`}
                alt={type.name}
            />

            <div className="Type__title">
                <h6 className="Type__name">{type.name}</h6>
                <p className="Type__paragraph">{manageType}</p>
            </div>

            </div>

            <div className="Type__cardText">

            <div>
                <p className="Type__paragraph">{type.description}</p>
            </div>

            </div>

        </div>

        </div>

    </div>
    );
}
}
