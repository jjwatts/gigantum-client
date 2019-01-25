var fs = require('fs');

function moveIdFile(oldPath, newPath, callback) {

    fs.copyFile(oldPath, newPath, (err) => {
      callback(err)
    });

}


module.exports = moveIdFile
