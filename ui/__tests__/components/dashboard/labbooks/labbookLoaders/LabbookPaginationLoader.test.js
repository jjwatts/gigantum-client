import React from 'react';
import renderer from 'react-test-renderer';
import { mount } from 'enzyme';
import LabbookPaginationLoader from 'Components/dashboard/shared/loaders/CardLoader';
import relayTestingUtils from '@gigantum/relay-testing-utils';

describe('Snapshot LabbookPaginationLoader', () => {
  it('LabbookPaginationLoader isLoading true', () => {
    const datasets = renderer.create(

       <LabbookPaginationLoader isLoadingMore={true}/>,

    );

    const tree = datasets.toJSON();

    expect(tree).toMatchSnapshot();
  });

  it('LabbookPaginationLoader isLoading false', () => {
    const datasets = renderer.create(

       <LabbookPaginationLoader isLoadingMore={false}/>,

    );

    const tree = datasets.toJSON();

    expect(tree).toMatchSnapshot();
  });
});
