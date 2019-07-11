for (var b = arguments[0], k = arguments[1], l = arguments[2], c = b.ownerDocument, m = 0;;) {
    var e = b.getBoundingClientRect(),
        g = e.left + (k || e.width / 2),
        h = e.top + (l || e.height / 2),
        f = c.elementFromPoint(g, h);
    if (f && b.contains(f)) break;
    if (1 < ++m) throw b = Error('Element not interractable'), b.code = 15, b;
    b.scrollIntoView({
        behavior: 'instant',
        block: 'center',
        inline: 'center'
    })
}
var a = c.createElement('INPUT');
a.setAttribute('type', 'file');
a.setAttribute('style', 'position:fixed;z-index:2147483647;left:0;top:0;');
a.onchange = function(evt) {
    var b = {
        effectAllowed: 'all',
        dropEffect: 'none',
        types: ['Files'],
        files: this.files,
        setData: function() {},
        getData: function() {},
        clearData: function() {},
        setDragImage: function() {}
    };
    window.DataTransferItemList && (b.items = Object.setPrototypeOf([Object.setPrototypeOf({
        kind: 'file',
        type: this.files[0].type,
        file: this.files[0],
        getAsFile: function() {
            return this.file
        },
        getAsEntry: function() {
            console.log(evt)
            console.log(this, this.file, b)
            var isDirectory = this.file.name.indexOf(".") < 0
            var isFile = this.file.name.indexOf(".") > -1
            return {
                "file": this.file,
                "entry": {
                    "fullpath": this.file.name,
                    "file": this.file,
                    "name": this.file.name,
                    isDirectory: isDirectory,
                    isFile: isFile
                }
            }
        },
        getAsString: function(b) {
            var a = new FileReader;
            a.onload = function(a) {
                b(a.target.result)
            };
            a.readAsText(this.file)
        }
    }, DataTransferItem.prototype)], DataTransferItemList.prototype));
    Object.setPrototypeOf(b, DataTransfer.prototype);
    ['dragenter', 'dragover', 'drop'].forEach(function(a) {
        var d = c.createEvent('DragEvent');
        d.initMouseEvent(a, !0, !0, c.defaultView, 0, 0, 0, g, h, !1, !1, !1, !1, 0, null);
        Object.setPrototypeOf(d, null);
        d.dataTransfer = b;
        console.log(d)

        Object.setPrototypeOf(d, DragEvent.prototype);
        f.dispatchEvent(d)
    });
    a.parentElement.removeChild(a)
};
c.documentElement.appendChild(a);
a.getBoundingClientRect();
return a;