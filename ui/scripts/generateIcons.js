const fs = require('fs');
const path = require('path');


const regex = /(fill="#)\w+/g;
const subFolders = fs.readdirSync(path.join(__dirname, '../src/images/icons-input'));

subFolders.forEach((subFolder) => {
    if (subFolder.split('.').length === 1) {
        const files = fs.readdirSync(path.join(__dirname, `../src/images/icons-input/${subFolder}`));
        files.forEach(((file) => {
            const fileName = file.split('.')[0];
            const icon = fs.readFileSync(path.join(__dirname, `../src/images/icons-input/${subFolder}/${file}`), 'utf8');
            fs.mkdirSync(path.join(__dirname, `../src/images/icons-output/${subFolder}/${fileName}`), { recursive: true });
            fs.writeFileSync(path.join(__dirname, `../src/images/icons-output/${subFolder}/${fileName}/${fileName}-white.svg`), icon.replace(regex, 'fill="#FFFFF'));
            fs.writeFileSync(path.join(__dirname, `../src/images/icons-output/${subFolder}/${fileName}/${fileName}-azure.svg`), icon.replace(regex, 'fill="#007EA8'));
            fs.writeFileSync(path.join(__dirname, `../src/images/icons-output/${subFolder}/${fileName}/${fileName}-turquise.svg`), icon.replace(regex, 'fill="#1ad8c1'));
            fs.writeFileSync(path.join(__dirname, `../src/images/icons-output/${subFolder}/${fileName}/${fileName}-grey.svg`), icon.replace(regex, 'fill="#9b9c9e'));
        }));
    }
});

