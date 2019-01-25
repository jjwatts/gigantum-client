
      import React from 'react'
      import renderer from 'react-test-renderer';
      import json from './../__relaydata__/LocalLabbooks.json';
      import VisibilityLookup from 'Components/dashboard/labbooks/localLabbooks/lookups/VisibilityLookup';

      import relayTestingUtils from '@gigantum/relay-testing-utils';


      test('Test ContainerLookup', async () => {
        let id = json.data.labbookList.localLabbooks.edges[0].node.id;
        VisibilityLookup.query([id]).then((response) => {
          expect(response.data.ids.length).toEqual(0);
        });
      });
