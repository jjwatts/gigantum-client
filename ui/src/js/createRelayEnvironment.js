
const {
  Environment, Network, RecordSource, Store, ConnectionHandler, ViewerHandler,
} = require('relay-runtime');

const parseParams = (str) => {
  const pieces = str.split('&');
  const data = {};
  let i;
  let parts;
  // process each query pair
  for (i = 0; i < pieces.length; i++) {
    parts = pieces[i].split('=');
    if (parts.length < 2) {
      parts.push('');
    }
    data[decodeURIComponent(parts[0])] = decodeURIComponent(parts[1]);
  }
  return data;
};

function fetchQuery(operation, variables, cacheConfig, uploadables) {
  /* eslint-disable */
  const globalObject = self || window;
  /* eslint-enable */
  const queryString = operation.params ? operation.params.text.replace(/(\r\n|\n|\r)/gm, '') : operation.text.replace(/(\r\n|\n|\r)/gm, '');
  let body;
  const headers = {
    accept: '*/*',
  };


  if (process.env.NODE_ENV === 'development') {
    headers['Access-Control-Allow-Origin'] = '*';
  }
  if (uploadables && uploadables[0]) {
    if (uploadables[1]) {
      headers.authorization = `Bearer ${uploadables[1]}`;
      headers.Identity = `${uploadables[2]}`;
    }
  } else if (globalObject.location.href.indexOf('access_token') > -1) {
    const hashObj = parseParams(globalObject.location.href.split('#')[1]);

    headers.authorization = `Bearer ${hashObj.access_token}`;
    headers.Identity = `${hashObj.id_token}`;

    globalObject.localStorage.setItem('access_token', hashObj.access_token);
    globalObject.localStorage.setItem('id_token', hashObj.id_token);

    globalObject.location.hash = '';
  } else if (globalObject.localStorage.getItem('access_token')) {
    const accessToken = globalObject.localStorage.getItem('access_token');
    const idToken = globalObject.localStorage.getItem('id_token');
    headers.authorization = `Bearer ${accessToken}`;
    headers.Identity = `${idToken}`;
  }

  if (uploadables === undefined) {
    headers['content-type'] = 'application/json';

    body = JSON.stringify({ query: queryString, variables });
  } else {
    body = new FormData();

    body.append('query', queryString);
    body.append('variables', JSON.stringify(variables));
    body.append('uploadChunk', uploadables[0]);
  }

  const apiHost = process.env.NODE_ENV === 'development'
    ? 'localhost:10000'
    : globalObject.location.host;
  const apiURL = `${globalObject.location.protocol}//${apiHost}${process.env.GIGANTUM_API}`;
  return fetch(apiURL, {
    method: 'POST',
    headers,
    body,
  }).then(response => response.json()).catch(error => error);
}

const network = Network.create(fetchQuery);

const handlerProvider = function handlerProvider(handle) {
  switch (handle) {
    // Augment (or remove from) this list
    case 'connection': return ConnectionHandler;
    case 'viewer': return ViewerHandler;
    default: return ConnectionHandler;
  }
};

const source = new RecordSource();
const store = new Store(source);
export default new Environment({ handlerProvider, network, store });

export {
  network,
  fetchQuery,
};
