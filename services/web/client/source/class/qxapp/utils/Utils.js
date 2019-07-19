/* ************************************************************************

   qxapp - the simcore frontend

   https://osparc.io

   Copyright:
     2018 IT'IS Foundation, https://itis.swiss

   License:
     MIT: https://opensource.org/licenses/MIT

   Authors:
     * Odei Maiz (odeimaiz)

************************************************************************ */

/**
 * Sandbox of static methods that do not fit in other utils classes.
 */

/* global window */
/* global document */
/* global XMLHttpRequest */
/* global Blob */

qx.Class.define("qxapp.utils.Utils", {
  type: "static",

  statics: {
    uuidv4: function() {
      return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
        (c ^ window.crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16));
    },

    getLoaderUri: function(arg) {
      let loadingUri = qx.util.ResourceManager.getInstance().toUri("qxapp/loading/loader.html");
      if (arg) {
        loadingUri += "?loading=- ";
        loadingUri += arg;
      }
      return loadingUri;
    },

    createLoadingIFrame: function(text) {
      const loadingUri = qxapp.utils.Utils.getLoaderUri(text);
      let iframe = new qx.ui.embed.Iframe(loadingUri);
      iframe.setBackgroundColor("transparent");
      return iframe;
    },

    compareVersionNumbers: function(v1, v2) {
      // https://stackoverflow.com/questions/6832596/how-to-compare-software-version-number-using-js-only-number/47500834
      // - a number < 0 if a < b
      // - a number > 0 if a > b
      // - 0 if a = b
      const regExStrip0 = /(\.0+)+$/;
      const segmentsA = v1.replace(regExStrip0, "").split(".");
      const segmentsB = v2.replace(regExStrip0, "").split(".");
      const l = Math.min(segmentsA.length, segmentsB.length);

      for (let i = 0; i < l; i++) {
        const diff = parseInt(segmentsA[i], 10) - parseInt(segmentsB[i], 10);
        if (diff) {
          return diff;
        }
      }
      return segmentsA.length - segmentsB.length;
    },

    // deep clone of nested objects
    // https://medium.com/@tkssharma/objects-in-javascript-object-assign-deep-copy-64106c9aefab#eeed
    deepCloneObject: function(src) {
      let target = {};
      for (let key in src) {
        if (src[key] !== null && typeof (src[key]) === "object") {
          target[key] = qxapp.utils.Utils.deepCloneObject(src[key]);
        } else {
          target[key] = src[key];
        }
      }
      return target;
    },

    replaceTemplateUUIDs: function(data) {
      const tempPrefix = "template-uuid";
      let myData = JSON.stringify(data);
      let tempIdIdx = myData.indexOf(tempPrefix);
      while (tempIdIdx !== -1) {
        let tempId = myData.substr(tempIdIdx, 36);
        let tempLocIdIdx = myData.indexOf(tempId);
        let newUuid = qxapp.utils.Utils.uuidv4();
        while (tempLocIdIdx !== -1) {
          myData = myData.replace(tempId, newUuid);
          tempLocIdIdx = myData.indexOf(tempId);
        }
        tempIdIdx = myData.indexOf(tempPrefix);
      }
      data = JSON.parse(myData);
      return data;
    },

    stringsMatch: function(a, b, caseSensitive = false) {
      let data = a;
      let searchString = b;
      if (caseSensitive === false) {
        data = data.toUpperCase();
        searchString = searchString.toUpperCase();
      }
      return data.search(searchString) != -1;
    },

    pretifyObject: function(object, short) {
      let uuidToName = qxapp.utils.UuidToName.getInstance();
      let myText = "";
      const entries = Object.entries(object);
      for (let i=0; i<entries.length; i++) {
        const entry = entries[i];
        myText += String(entry[0]);
        myText += ": ";
        // entry[1] might me a path of uuids
        let entrySplitted = String(entry[1]).split("/");
        if (short) {
          myText += entrySplitted[entrySplitted.length-1];
        } else {
          for (let j=0; j<entrySplitted.length; j++) {
            myText += uuidToName.convertToName(entrySplitted[j]);
            if (j !== entrySplitted.length-1) {
              myText += "/";
            }
          }
        }
        myText += "<br/>";
      }
      return myText;
    },

    getRandomColor: function() {
      let letters = "0123456789ABCDEF";
      let color = "#";
      for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
      }
      return color;
    },

    getColorLuminance: function(hexColor) {
      const rgb = qx.util.ColorUtil.hexStringToRgb(hexColor);
      const luminance = 0.2126*(rgb[0]/255) + 0.7152*(rgb[1]/255) + 0.0722*(rgb[2]/255);
      return luminance;
    },

    getKeyByValue(object, value) {
      return Object.keys(object).find(key => object[key] === value);
    },

    bytesToSize: function(bytes) {
      const sizes = ["Bytes", "KB", "MB", "GB", "TB"];
      if (bytes == 0) {
        return "0 Byte";
      }
      const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
      return Math.round(bytes / Math.pow(1024, i), 2) + " " + sizes[i];
    },

    downloadLink: function(url, fileName) {
      let xhr = new XMLHttpRequest();
      xhr.open("GET", url, true);
      xhr.responseType = "blob";
      xhr.onload = () => {
        console.log("onload", xhr);
        if (xhr.status == 200) {
          let blob = new Blob([xhr.response]);
          let urlBlob = window.URL.createObjectURL(blob);
          let downloadAnchorNode = document.createElement("a");
          downloadAnchorNode.setAttribute("href", urlBlob);
          downloadAnchorNode.setAttribute("download", fileName);
          downloadAnchorNode.click();
          downloadAnchorNode.remove();
        }
      };
      xhr.send();
    },

    fileNameFromPresignedLink: function(link) {
      // regex match /([^/]+)\?
      const fileNames = new URL(link).pathname.split("/");
      if (fileNames.length) {
        return fileNames.pop();
      }
      return null;
    },

    /**
     * Function that takes an indefinite number of strings as separated parameters, and concatenates them capitalizing the first letter.
     */
    capitalize: function() {
      let res = "";
      for (let i=0; i<arguments.length; i++) {
        if (typeof arguments[i] !== "string" && arguments[i] instanceof String === false) {
          continue;
        }
        const capitalized = arguments[i].charAt(0).toUpperCase() + arguments[i].slice(1);
        res = res.concat(capitalized);
      }
      return res;
    },

    /**
     * Copies the given text to the clipboard
     *
     * @param text {String} Text to be copied
     * @return {Boolean} True if it was successful
     */
    copyTextToClipboard: function(text) {
      // from https://stackoverflow.com/questions/400212/how-do-i-copy-to-the-clipboard-in-javascript
      const textArea = document.createElement("textarea");

      //
      // *** This styling is an extra step which is likely not required. ***
      //
      // Why is it here? To ensure:
      // 1. the element is able to have focus and selection.
      // 2. if element was to flash render it has minimal visual impact.
      // 3. less flakyness with selection and copying which **might** occur if
      //    the textarea element is not visible.
      //
      // The likelihood is the element won't even render, not even a
      // flash, so some of these are just precautions. However in
      // Internet Explorer the element is visible whilst the popup
      // box asking the user for permission for the web page to
      // copy to the clipboard.
      //

      // Place in top-left corner of screen regardless of scroll position.
      // Ensure it has a small width and height. Setting to 1px / 1em
      // doesn't work as this gives a negative w/h on some browsers.
      // We don't need padding, reducing the size if it does flash render.
      // Clean up any borders.
      // Avoid flash of white box if rendered for any reason.
      textArea.style = {
        position: "fixed",
        top: 0,
        left: 0,
        width: "2em",
        height: "2em",
        padding: 0,
        border: "none",
        outline: "none",
        boxShadow: "none",
        background: "transparent"
      };
      textArea.value = text;

      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();

      let copied = false;
      try {
        copied = document.execCommand("copy");
      } catch (err) {
        console.error("Oops, unable to copy");
      }

      document.body.removeChild(textArea);

      return copied;
    },

    cookie: {
      setCookie: (cname, cvalue, exdays) => {
        var d = new Date();
        d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
        var expires = "expires="+d.toUTCString();
        document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
      },

      getCookie: cname => {
        var name = cname + "=";
        var ca = document.cookie.split(";");
        for (var i = 0; i < ca.length; i++) {
          var c = ca[i];
          while (c.charAt(0) == " ") {
            c = c.substring(1);
          }
          if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
          }
        }
        return "";
      },

      deleteCookie: cname => {
        document.cookie = cname + "=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
      }
    },

    parseURLFragment: () => {
      let urlHash = window.location.hash.slice(1);
      const parsedFragment = {};
      if (urlHash.length) {
        urlHash = urlHash.split("?");
        if (urlHash.length < 3) {
          // Nav
          urlHash[0].split("/").forEach(fragmentPart => {
            if (fragmentPart.length) {
              parsedFragment.nav = parsedFragment.nav || [];
              parsedFragment.nav.push(decodeURIComponent(fragmentPart));
            }
          });
          if (urlHash.length === 2) {
            // Params
            parsedFragment.params = parsedFragment.params || {};
            urlHash[1].replace(/([^=&]+)=([^&]*)/g, function(m, key, value) {
              parsedFragment.params[decodeURIComponent(key)] = decodeURIComponent(value);
            });
          }
        } else {
          console.error("URL fragment doesn't have the correct format.");
          return null;
        }
      }
      return parsedFragment;
    },

    getThumbnailFromUuid: uuid => {
      const lastCharacters = uuid.substr(uuid.length-10);
      const aNumber = parseInt(lastCharacters, 16);
      const thumbnailId = aNumber%25;
      return "qxapp/img"+ thumbnailId +".jpg";
    },

    getThumbnailFromString: str => "qxapp/img" + Math.abs(this.self().stringHash(str)%25) + ".jpg",

    stringHash: str => {
      // Based on https://stackoverflow.com/questions/7616461/generate-a-hash-from-string-in-javascript
      let hash = 0;
      let i;
      let chr;
      if (str.length === 0) {
        return hash;
      }
      for (i=0; i<str.length; i++) {
        chr = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + chr;
        hash |= 0; // Convert to 32bit integer
      }
      return hash;
    }
  }
});
