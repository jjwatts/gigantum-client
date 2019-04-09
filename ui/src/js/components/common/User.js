// vendor
import React, { Component } from 'react';
import classNames from 'classnames';
// assets
import './User.scss';

export default class User extends Component {
  constructor(props) {
    super(props);

    this.state = {
      familyName: localStorage.getItem('family_name') || '',
      username: localStorage.getItem('username') || '',
      givenName: localStorage.getItem('given_name') || '',
      email: localStorage.getItem('email') || '',
      dropdownVisible: false,
    };

    this._toggleDropdown = this._toggleDropdown.bind(this);
    this.handleClickOutside = this._handleClickOutside.bind(this);
  }

  componentDidMount() {
    document.addEventListener('mousedown', this._handleClickOutside.bind(this));
  }

  componentWillUnmount() {
    document.removeEventListener('mousedown', this._handleClickOutside.bind(this));
  }

  /**
    @param {}
    logout through Auth0
  */
  logout() {
    this.props.auth.logout();
    this._toggleDropdown();
  }

  /**
      @param {}
      handles click to update state
    */
  _handleClickOutside(event) {
    const userElementIds = ['user', 'username', 'logout', 'profile'];
    if (this.state.dropdownVisible && (userElementIds.indexOf(event.target.id) < 0)) {
      this.setState({
        dropdownVisible: false,
      });
    }
  }

  /**
    @param {}
    toggles dropdown state
  */
  _toggleDropdown() {
    this.setState({
      dropdownVisible: !this.state.dropdownVisible,
    });
  }


  render() {
    const usernameCSS = classNames({
      User__name: true,
      'User__name--active': this.state.dropdownVisible,
      'User__name--long': this.state.username.length >= 10,
    });


    const userDropdownCSS = classNames({
      User__dropdown: true,
      hidden: !this.state.dropdownVisible,
    });


    const arrowCSS = classNames({
      'User__dropdown--arrow': true,
      hidden: !this.state.dropdownVisible,
    });


    return (
      <div
        id="user"
        className="User"
        key="user"
      >
        <div className="User__image" />
        <h6
          id="username"
          onClick={() => { this._toggleDropdown(); }}
          className={usernameCSS}
          data-tooltip={this.state.username}
        >
          {this.state.username}
        </h6>

        <div className={arrowCSS} />

        <div className={userDropdownCSS}>
          <a
            id="profile"
            href="http://gigantum.com/profile"
            rel="noopener noreferrer"
            target="_blank"
            className="User__button"
          >
            Profile
          </a>
          <button
            id="logout"
            className="User__button btn-margin Btn Btn--flat"
            onClick={this.logout.bind(this)}
          >
            Logout
          </button>

        </div>


      </div>
    );
  }
}
