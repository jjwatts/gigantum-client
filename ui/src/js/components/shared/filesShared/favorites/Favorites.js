// vendor
import React, { Component } from 'react';
// componenets
import FavoritesList from './FavoritesList';

export default class Favorites extends Component {
  constructor(props) {
  	super(props);
    this.state = {
      loading: false,
    };
  }
  /*
    update component when props are reloaded
  */
  UNSAFE_componentWillReceiveProps(nextProps) {
    if (nextProps[this.props.section] && nextProps[this.props.section].favorites && nextProps[this.props.section].favorites.pageInfo.hasNextPage && nextProps[this.props.section].favorites.edges.length < 3) {
      this.props.relay.loadMore(
        1, // Fetch the next 1 feed items
        (response, error) => {
          if (error) {
            console.error(error);
          }
        },
      );
    }
  }

  /**
    handle state and addd listeners when component mounts
  */
  componentDidMount() {
    // this._loadMore() //routes query only loads 2, call loadMore
    if (this.props[this.props.section] && this.props[this.props.section].favorites && this.props[this.props.section].favorites.pageInfo.hasNextPage && this.props[this.props.section].favorites.edges.length < 3) {
      this.props.relay.loadMore(
        1, // Fetch the next 10 feed items
        (response, error) => {
          if (error) {
            console.error(error);
          }
        },
      );
    }
  }

  /**
    @param {}
    triggers relay pagination function loadMore
    increments by 10
    logs callback
  */
  _loadMore() {
    const self = this;

    this.setState({ loading: true });

    this.props.relay.loadMore(
      3, // Fetch the next 10 feed items
      (response, error) => {
        self.setState({ loading: false });

        if (error) {
          console.error(error);
        }
      },
    );
  }


  render() {
    if (this.props[this.props.section] && this.props[this.props.section].favorites) {
      const capitalSection = this.props.section[0].toUpperCase() + this.props.section.slice(1);
      if (this.props[this.props.section].favorites.edges.length > 0) {
        const favorites = this.props[this.props.section].favorites.edges.filter(edge => edge && (edge.node !== undefined));

        return (

          <div className="Favorite">
            <FavoritesList
              labbookName={this.props.labbookName}
              sectionId={this.props.sectionId}
              section={this.props.section}
              favorites={favorites}
              owner={this.props.owner}
            />
          </div>

        );
      }
      return (
        <div className="Favorite__none flex flex--column justify--center">
          <div className="Favorite__icon--star"></div>
          <p className="Favorite__p"><b>No {capitalSection} Favorites</b></p>
          <p className="Favorite__p">Add a favorite and enter a description to highlight important items.</p>
        </div>
      );
    }
    return (<div>No Files Found</div>);
  }
}
