
var fetch = require('isomorphic-fetch');
var FormData = require('form-data');
require('raf/polyfill');
import Worker from 'jest-worker';

var { configure } = require('enzyme');
var Adapter = require('enzyme-adapter-react-16');
var uuid = require('uuid/v4');


configure({ adapter: new Adapter() });
// need to add root to JSDOM for mounting react
delete window.location;
function getLocation(href) {
    var match = href.match(/^(https?\:)\/\/(([^:\/?#]*)(?:\:([0-9]+))?)([\/]{0,1}[^?#]*)(\?[^#]*|)(#.*|)$/);
    return match && {
        href: href,
        protocol: match[1],
        host: match[2],
        hostname: match[3],
        port: match[4],
        pathname: match[5],
        search: match[6],
        hash: match[7],
    };
}

window.location = {}; // or stub/spy etc
window.location.assign = (url) => {
  let location = getLocation(url)
  window.location = location;
}
window.location.href = 'https://localhost:10000';
// set variables for the api
window.location.hostname = 'localhost';
window.location.protocol = 'https:';

// class Worker {
//   constructor(stringUrl) {
//     this.url = stringUrl;
//     this.onmessage = () => {};
//   }
//
//   addEventListener(eventType, callback) {
//     return window.addEventListener(eventType, callback);
//   }
//
//   removeEventListener(eventType, callback) {
//     return window.removeEventListener(eventType, callback);
//   }
//
//   postMessage(msg) {
//     this.onmessage(msg);
//   }
// }
function noOp() {}
if (typeof window.URL.createObjectURL === 'undefined') {
  Object.defineProperty(window.URL, 'createObjectURL', { value: noOp });
}

window.Worker = Worker;

var document = window.document;

var newDiv = document.createElement('div');
newDiv.setAttribute('id', 'root');
// set for proxy
process.env.GIGANTUM_API = process.env.USE_PROXY ? ':10010/api/labbook/' : ':10000/api/labbook/';

// add document globally
global.document = window.document;

// add window globally
global.window = window;

global.window.resizeTo = function (width, height) {
  global.window.innerWidth = width || global.window.innerWidth;
  global.window.innerHeight = width || global.window.innerHeight;
  global.window.dispatchEvent(new Event('resize'));
};


global.Worker = Worker;

// add node fetch for environment
global.fetch = fetch;

// add formdata api for multipart forms
global.FormData = FormData;

// add file api for uploads
global.File = window.File;

global.window.matchMedia = window.matchMedia || function () { return { matches: false, addListener: () => {}, removeListener: () => {} }; };

global.requestAnimationFrame = function (callback) {
  setTimeout(callback, 0);
};

(function () {
    var lastTime = 0;
    var vendors = ['ms', 'moz', 'webkit', 'o'];
    // for (var x = 0; x < vendors.length && !window.requestAnimationFrame; ++x) {
    //     window.requestAnimationFrame = window[vendors[x] + 'RequestAnimationFrame'];
    //     window.cancelAnimationFrame = window[vendors[x] + 'CancelAnimationFrame']
    //                                || window[vendors[x] + 'CancelRequestAnimationFrame'];
    // }

    for (var x = 0; x < vendors.length && !window.requestAnimationFrame; ++x) {
        window.requestAnimationFrame = window[`${vendors[x]}${RequestAnimationFrame}`];
        window.cancelAnimationFrame = window[`${vendors[x]}${CancelAnimationFrame}`]
                                   || window[`${vendors[x]}${CancelRequestAnimationFrame}`];
    }

    if (!window.requestAnimationFrame) {
        window.requestAnimationFrame = (callback, element) => {
            var currTime = new Date().getTime();
            var timeToCall = Math.max(0, 16 - (currTime - lastTime));
            var id = window.setTimeout(
              () => {
                var time = currTime + timeToCall;
                callback(time);
              },
              timeToCall,
            );
            lastTime = currTime + timeToCall;
            return id;
        };
     }

    if (!window.cancelAnimationFrame) {
        window.cancelAnimationFrame = function (id) {
            clearTimeout(id);
        };
    }
}());

// const oneHundredSeconds = 1 * 1000 * 100
// // set timout to one hundred seconds
// jasmine.DEFAULT_TIMEOUT_INTERVAL = oneHundredSeconds

// export default () => global;
