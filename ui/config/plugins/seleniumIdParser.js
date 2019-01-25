


module.exports = function(babel) {
  var t = babel.types;
  console.log('asdasdadsdsashdasndashfebrweijokdasmcln dsfenaowckal')
  return {
    visitor: {
      Program: function(path, state) {
       console.log("ASASASSAASSASASASASAS")
      },
      JSXElement: function(path, state) {
        console.log("ASASASSAASSASASASASAS________________________JSXElement")
        _JSXOpeningElement(path.get('openingElement'), state);
      },
      JSXOpeningElement: function(path, state) {
         const seleniumId = `data-selenium-id`;
        console.log("ASASASSAASSASASASASAS________________________JSXOpeningElement")
         const attributes = path.container.openingElement.attributes;

         const newAttributes = [];
         newAttributes.push(t.jSXAttribute(
           t.jSXIdentifier(seleniumId),
           t.stringLiteral(path.container.openingElement.key))
         );
         // if (path.container && path.container.openingElement &&
         //   path.container.openingElement.key &&
         //   path.container.openingElement.key) {
         //   console.log(seleniumId, t);
         //
         //   newAttributes.push(t.jSXAttribute(
         //     t.jSXIdentifier(seleniumId),
         //     t.stringLiteral(path.container.openingElement.key))
         //   );
         // }

         attributes.push(...newAttributes);
      },
   }
  }
};
